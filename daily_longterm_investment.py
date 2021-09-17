
from my_libs_py3 import *





robinhood =robingateway()







########################################################
# START of daily investment
#######################################################


try:


    ########################
    # Fundamental Cumulation
    ########################

    strategy_name = "Fundamental"

    cash_reserve = trading_param["cash_reserve"]

    money = trading_param["fundamental_money"]

#     mongod = mongo("all_symbol","screenerModel")
#     ## This line gets the max refresh_date
#     tos = pd.DataFrame(mongod.conn.table.find({},{"Refresh_Date":1}).sort("Refresh_Date",-1).limit(1))["Refresh_Date"].iloc[0]
#     fun_table = pd.DataFrame(mongod.conn.table.find({"Refresh_Date":tos}))


#     fun_table["sum_rank"] = \
#         fun_table["P/Cash"] + fun_table["Analyst Recom"]  + fun_table["P/S"] + fun_table["Total Debt/Equity"] +\
#         fun_table["P/Free Cash Flow"] + fun_table["P/E"] + fun_table["Insider Ownership"] + fun_table["Gross Margin"] \
#         + fun_table["Current Ratio"] + fun_table["Sales growth quarter over quarter"] + fun_table["Profit Margin"] \
#         + fun_table["Quick Ratio"] + fun_table["Performance (Week)"] + fun_table["Institutional Ownership"] + \
#         fun_table["EPS (ttm)"] + fun_table["Operating Margin"]

#     fun_table["avg_rank"] = (fun_table["P/Cash"] + fun_table["Analyst Recom"]  + fun_table["P/S"] + \
#                              fun_table["Total Debt/Equity"] + fun_table["P/Free Cash Flow"] + fun_table["P/E"] +\
#                              fun_table["Insider Ownership"] + fun_table["Gross Margin"] + fun_table["Current Ratio"] + \
#                              fun_table["Sales growth quarter over quarter"] + fun_table["Profit Margin"] + \
#                              fun_table["Quick Ratio"] + fun_table["Performance (Week)"] + \
#                              fun_table["Institutional Ownership"] + fun_table["EPS (ttm)"] + \
#                              fun_table["Operating Margin"])/21

#     fun_table = fun_table.sort_values("sum_rank")

#     target_list = fun_table.Ticker[:3]

    
    mongod = mongo("all_symbol","screenerModel")
    
    ## This line gets the max refresh_date
    tos = pd.DataFrame(mongod.conn.table.find({},{"Refresh_Date":1,"_id":0}).sort("Refresh_Date",-1).limit(1))["Refresh_Date"].iloc[0]
    
    fun_table = pd.DataFrame(mongod.conn.table.find({"Refresh_Date":tos},{"_id":0}))

    target = ["P/Cash","Analyst Recom","P/S","Total Debt/Equity","P/Free Cash Flow","P/E","Insider Ownership",
             "Gross Margin","Current Ratio","Sales growth quarter over quarter","Profit Margin","Quick Ratio","Performance (Week)","Institutional Ownership","EPS (ttm)","Operating Margin"]

    fun_table["sum_rank"] = pd.DataFrame.sum(fun_table[target],axis=1,skipna=True,numeric_only=True)

    fun_table["avg_rank"] = pd.DataFrame.mean(fun_table[target],axis=1,skipna=True,numeric_only=True)

    fun_table = fun_table.sort_values("avg_rank")

    target_list = fun_table.Ticker[:8]

    ##  Check buy signal
    # check we have enough buying power after reserver
    if robinhood.get_buying_power() > cash_reserve:
        for i in target_list:
            price = get_price_data([i],method = 'day',back_day=7)
            quote = realtimequote(i).price.iloc[0]
            size = np.ceil(money/quote)
            if quote < price.Close.mean():
                if robinhood.place_buy_bulk_checkup(ticker_list=[i],quantity_list=[size],skip_check= True) == "Trade Success!":
                    log_trade(i,size, robinhood.get_last_price(i), strategy_name)
                    send_email("Fundamental Cumulation Buy: %s"%i)

                
    print("pass buy signal")

    ##  Check sell signal
    tickers = get_open_opsition()

    for i in tickers:
        i.encode("ASCII")
        log = get_trade_log(i)
        log = log[log.Strategy==strategy_name]
        if len(log) == 0:
            continue
            
        quote = realtimequote(i).price.iloc[0]
        
        
        try:
            cost = robinhood.get_average_cost(i)
        except:
            send_email("%s not in portfolio"%i)
            continue
        print("pass log check")
        
        ## clear the position if no longer rank high when pofit
        if i not in fun_table.Ticker[:20].to_list(): # and quote >= cost:
            if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].sum()])== "Trade Success!":
                log_trade(i,-log["size"].sum(), robinhood.get_last_price(i), strategy_name)
                send_email("Fundamental Out-Of-List Sell: %s"%i)
        
        print("pass position check")
            
        ## clean a portion of the position if it reaches the havest threshold    
        size = np.ceil(log["size"].sum()*trading_param["fundamental_harvest_prop"])    
        if (quote - cost)/cost > trading_param["fundamental_harvest"]:
            if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[size])== "Trade Success!":
                log_trade(i,-size, robinhood.get_last_price(i), strategy_name)
                send_email("Fundamental Cumulation Sell: %s"%i)
                
        print("pass fundamental")

########################################################
# End of daily investment
#######################################################


except Exception as e:
    send_email("daily investment error " + str(e))
