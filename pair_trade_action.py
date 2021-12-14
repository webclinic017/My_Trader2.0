from my_libs_py3 import *

TRADE_CASH = 500

def record_not_shortable(ticker):
    mongod = mongo("all_symbol","td_not_shortable")
    mongod.conn.table.insert_one({"TimeStamp":datetime.now(),"symbol":ticker})

def pair_trade_action(ticker1,ticker2,cash=TRADE_CASH,close_action=False):
    today_trade = self_pair_trade(ticker1,ticker2,method = "realtimeday",cash = cash).iloc[-1]

    ticker_combo = ticker1+"_"+ticker2
    log = get_pair_trade_log(ticker_combo)

    # day_diff = log["TimeStamp"].astimezone(mytz) - datetime.now(mytz)

    new_size1 = today_trade["size1"]
    new_size2 = today_trade["size2"]

    if len(log) == 0:
        current_size1 = 0
        current_size2 = 0
        if new_size1 == 0 or new_size2 == 0:
            print("One of the stock has 0 in size. We don't trade one stock.")
            return None
    else:
        # log = log.iloc[0]
        current_size1 = log["size1"].sum()
        current_size2 = log["size2"].sum()

    trade_size1 = new_size1 - current_size1
    trade_size2 = new_size2 - current_size2

    now_cash = client.accountsDF().loc[0,"currentBalances.availableFunds"]
    try:
        td_trade = order_equity(order_type.LIMIT)

        ## need to trade the short sell first to test whether it's short
        ## check signal
        if (trade_size1 != 0 or trade_size2 != 0) and (now_cash>TRADE_CASH or close_action):
            send_email("",title="!Important! Pair Trade Order Placing for %s and %s"%(ticker1,ticker2))
            ## if one of them trade_size == 0
            if trade_size1 == 0:
                orderid = td_trade.place(ticker2, trade_size2)
                if get_order_by_id(orderid)["status"] != "REJECTED":
                    log_pair_trade(ticker1, ticker2, trade_size1, trade_size2, None, None)
                    send_email("Trade process done.",
                               title="!Important! Pair Trade Order Placed for %s and %s" % (ticker1, ticker2))
                else:
                    if not cancel_order(orderid):
                        send_email("Please manually cancel order for %s",
                                   title="!Important! Cancel Order Failed" % orderid)
                    raise Exception("{ticker2} short not filled for {ticker1} and {ticker2}".format(ticker1=ticker1,
                                                                                                    ticker2=ticker2))
            elif trade_size2 == 0:
                orderid = td_trade.place(ticker1, trade_size1)
                if get_order_by_id(orderid)["status"] != "REJECTED":
                    log_pair_trade(ticker1, ticker2, trade_size1, trade_size2, None, None)
                    send_email("Trade process done.",
                               title="!Important! Pair Trade Order Placed for %s and %s" % (ticker1, ticker2))
                else:
                    if not cancel_order(orderid):
                        send_email("Please manually cancel order for %s",
                                   title="!Important! Cancel Order Failed" % orderid)
                    raise Exception("{ticker1} short not filled for {ticker1} and {ticker2}".format(ticker1=ticker1,
                                                                                                    ticker2=ticker2))
            ## short ticker1
            elif trade_size1 < 0:
                orderid = td_trade.place(ticker1,trade_size1)
                if get_order_by_id(orderid)["status"] != "REJECTED":
                    time.sleep(45)
                    if get_order_by_id(orderid)["status"] == "FILLED":
                        orderid = td_trade.place(ticker2,trade_size2)
                        if get_order_by_id(orderid)["status"] != "REJECTED":
                            log_pair_trade(ticker1,ticker2,trade_size1,trade_size2,None,None)
                            send_email("Trade process done.",title="!Important! Pair Trade Order Placed for %s and %s"%(ticker1,ticker2))
                    else:
                        if not cancel_order(orderid):
                            send_email("Please manually cancel order for %s",title="!Important! Cancel Order Failed"%orderid)
                        raise Exception("{ticker2} short not filled for {ticker1} and {ticker2}".format(ticker1=ticker1,ticker2=ticker2))
                        
                else:
                    record_not_shortable(ticker1)
                    raise Exception("{ticker1} probably not shortable for {ticker1} and {ticker2}".format(ticker1=ticker1,ticker2=ticker2))
            
            ## long ticker1
            elif trade_size1 > 0:
                orderid = td_trade.place(ticker2,trade_size2)
                if get_order_by_id(orderid)["status"] != "REJECTED":
                    time.sleep(45)
                    if get_order_by_id(orderid)["status"] == "FILLED":
                        orderid = td_trade.place(ticker1,trade_size1)
                        if get_order_by_id(orderid)["status"] != "REJECTED":
                            log_pair_trade(ticker1,ticker2,trade_size1,trade_size2,None,None)
                            send_email("Trade process done.",title="!Important! Pair Trade Order Placed for %s and %s"%(ticker1,ticker2))
                    else:
                        if not cancel_order(orderid):
                            send_email("Please manually cancel order for %s",title="!Important! Cancel Order Failed"%orderid)
                        raise Exception("{ticker1} short not filled for {ticker1} and {ticker2}".format(ticker1=ticker1,ticker2=ticker2))
                        
                else:
                    record_not_shortable(ticker2)
                    raise Exception("{ticker2} probably not shortable for {ticker1} and {ticker2}".format(ticker1=ticker1,ticker2=ticker2))
        ## no signal to trade   
        else:
            print("No trade or no cash, skiped for %s and %s"%(ticker1,ticker2))
    except Exception as e:
        send_email(str(e),title="!Important! Pair Trade Place Order Error for {ticker1} and {ticker2}".format(ticker1=ticker1,ticker2=ticker2))

def pair_trade_smaple():
    mongod = mongo("all_symbol","pair_trade_sharp_2021_500")
    candid = pd.DataFrame(mongod.conn.table.find({"Sharp_Ratio":{"$exists":True}}))
    top_return = candid.describe().loc["75%","Avg_Return"]
    top_sharp = candid.describe().loc["75%","Sharp_Ratio"]

    pipeline = [
        {"$match":{"End_Value":{"$gt":TRADE_CASH},"Sharp_Ratio":{"$gt":top_sharp},"Avg_Return":{"$gt":top_return}}},
        {"$sample":{"size":10}}
    ]

    candid = pd.DataFrame(mongod.conn.table.aggregate(pipeline))

    return candid  

def pair_trade_top():
    mongod = mongo("all_symbol","pair_trade_sharp_2021_500")
    candid = pd.DataFrame(mongod.conn.table.find({"Sharp_Ratio":{"$exists":True}}))
    top_return = candid.describe().loc["75%","Avg_Return"]
    top_sharp = candid.describe().loc["75%","Sharp_Ratio"]

    candid = pd.DataFrame(mongod.conn.table.find({"End_Value":{"$gt":TRADE_CASH},
                                                  "Sharp_Ratio":{"$gt":top_sharp},
                                                  "Avg_Return":{"$gt":top_return}}).sort("Sharp_Ratio",-1).limit(10))
    return candid

# buy check
candid = pair_trade_top()

for ticker1, ticker2 in zip(candid.Ticker_1,candid.Ticker_2):
    pair_trade_action(ticker1,ticker2,cash=TRADE_CASH)


#TODO
# sell check

## position adjustment
pos = get_pair_open_opsition()
for p in pos:
    p_log = get_pair_trade_log(p)
    ticker1 = p_log.loc[0,"Ticker1"]
    ticker2 = p_log.loc[0, "Ticker2"]
    # current_size1 = p_log.loc[0,"size1"]
    # current_size2 = p_log.loc[0, "size2"]
    # today_trade = self_pair_trade(ticker1, ticker2, method="realtimeday", cash=500).iloc[-1]
    # size1 = today_trade["size1"]
    # size2 = today_trade["size2"]
    # if size1 == 0:
    #     trade_size1 = 0 - current_size1
    #     trade_size2 = 0 - current_size2
    pair_trade_action(ticker1, ticker2, close_action=True)
