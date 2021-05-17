#!/usr/bin/python
from my_libs import *


# In[8]:


robinhood =robingateway()





 

########################################################   
# START of minute beta manual
#######################################################


try:

    
########################   
# Manual
########################
    strategy_name = "Manual"


    get = robinhood.get_my_positions()
    
    tickers = get[0]
    sizes = get[1]

    tic_frame = pd.DataFrame({"Tickers":tickers,"Sizes":sizes})
    tic_frame["Sizes"] = tic_frame.Sizes.astype(float)



    for i in tickers:
        log = get_trade_log(i)

        if ( len(log)==0 or log["size"].sum()  == 0) \
            and i not in trading_param["Long_Term_Tickers"]:
            log_trade(i,tic_frame[tic_frame.Tickers == i].Sizes.values[0] ,robinhood.get_average_cost(i), strategy_name)

        elif i in ["VIXY","SVXY"] and ( len(log)==0 or log["size"].sum()  == 0):
            log_trade(i,tic_frame[tic_frame.Tickers == i].Sizes.values[0] ,robinhood.get_average_cost(i), "vix_dayroll")

        elif i in trading_param["Long_Term_Tickers"]:
            continue
        log = get_trade_log(i)
        log = log[log.Strategy==strategy_name]
        log["Price"] = log.Price.astype(float)
        log["TimeStamp"] = log["TimeStamp"].apply(lambda x: x.astimezone(mytz))
        
       
        if log["size"].sum()!= 0 \
        and (datetime.now(mytz) - log.TimeStamp.iloc[-1]) >= timedelta(hours=15) \
        and i not in trading_param["Long_Term_Tickers"]:
            # define a list to avoid harvest profit

    #     if (datetime.now() - log.TimeStamp.iloc[-1] > timedelta(days=1)  and log.Strategy.iloc[-1] == strategy_name):

            if ((robinhood.get_last_price(i)- log.Price.iloc[-1])/log.Price.iloc[-1]) > trading_param["manual_harvest"] :
                print("harvest Profit")
                if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].iloc[-1]]) == "Trade Success!":
                    log_trade(i,-log["size"].sum(), robinhood.get_last_price(i), strategy_name)
                    send_email("manual_harvest sell")


            elif ((robinhood.get_last_price(i)- log.Price.iloc[-1])/log.Price.iloc[-1]) < trading_param["manual_cutloss"]:
                print("Stop Loss")

                if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].iloc[-1]])== "Trade Success!":
                    log_trade(i,-log["size"].sum(), robinhood.get_last_price(i), strategy_name)
                    send_email("manual_cutloss sell")


            elif datetime.now(mytz) - log.TimeStamp.iloc[-1] > timedelta(days=trading_param["manual_timeout_days"]):
                print("Timeout")
                if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].iloc[-1]])== "Trade Success!":
                    log_trade(i,-log["size"].sum(), robinhood.get_last_price(i), strategy_name)
                    send_email("manual_timeout sell")
        time.sleep(10)






#     ########################
#     # RSI
#     ########################


#     money = 200

#     database_name = "rsi"
#     strategy_name = "rsi"
#     tickers = get_open_opsition()

#     # Check sell signals

#     for i in tickers:
#         print (i)
#         i.encode("ASCII")
#         log = get_trade_log(i)
#         log = log[log.Strategy==strategy_name]
#         log["TimeStamp"] = log["TimeStamp"].apply(lambda x: x.astimezone(mytz))
#         if len(log) == 0:
#             continue
#     #     cost = (log.Price * log["size"] ).sum()/log["size"].sum()
#         cost = float(log.Price.iloc[-1])

#         if datetime.now(mytz) - log.TimeStamp.iloc[-1] >= timedelta(hours=15) \
#         and log["size"].sum() != 0 \
#         and i not in trading_param["Long_Term_Tickers"]:

#             if ta.RSI(get_price_data([i],method="self_minute", robinhood=robinhood,back_day = 80).Close, timeperiod=14).iloc[-1] >trading_param["rsi_sell"] :
#                 if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].iloc[-1]])== "Trade Success!":
#                     log_trade(i,-log["size"].sum(), realtimequote(i)["price"].iloc[0], strategy_name)
#                     send_email(body_html="",body_content="", title = "RSI Sell Signal")


#             elif ((realtimequote(i).price.values[0]- cost)/cost) < trading_param["strategy_cutloss"]:

#                 if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].iloc[-1]])== "Trade Success!":
#                     log_trade(i,-log["size"].sum(), realtimequote(i)["price"].iloc[0], strategy_name)
#                     send_email(body_html="",body_content="", title = "RSI Cut Losses")

#             elif ((realtimequote(i).price.values[0]- cost)/cost) > trading_param["strategy_harvest"]:

#                 if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].iloc[-1]])== "Trade Success!":
#                     log_trade(i,-log["size"].sum(), realtimequote(i)["price"].iloc[0], strategy_name)
#                     send_email(body_html="",body_content="", title = "RSI Harvest Profit")
#         time.sleep(10)



    # buy if signal

    #     mongod = mongo("Strategy_suggestion")

    #     try:
    #         ta_tickers = mongod.conn.get_data("select Ticker from Strategy_suggestion.RSI").Ticker[0].split()
    #         for i in ta_tickers:
    #             i.encode("ASCII")
    #             buy_ticker = i
    #             buy_price = robinhood.get_last_price(i)
    #             buy_size = int(money/buy_price)

    #             if ta.RSI(get_price_data([i], robinhood=robinhood,method="intraday",back_day = 80).Close, timeperiod=14).iloc[-1] < trading_param["rsi_buy"] \
    #             and (i not in get_open_opsition()) \
    #             and (get_price_data([i], robinhood=robinhood,method="intraday",back_day = 80).Close.mean()>trading_param["rsi_min_stock_price"]) \
    #             and robinhood.my_trader.buying_power()>=trading_param["cash_reserve"]:

    #                 if robinhood.place_buy_bulk_checkup(ticker_list=[buy_ticker], quantity_list=[buy_size],price_list=[buy_price])== "Trade Success!":
    #                     log_trade(i,buy_size, buy_price, strategy = database_name)
    #                     send_email(body_html="",body_content="", title = "Buy Signal: " + i)
    #         time.sleep(10)
    #     except Exception as e:
    #         print (e)

    #     html += "<br><br>  RSI check finished"





    ########################
    # CCI
    ########################

    # database_name = "cci"
    # strategy_name = "cci"
    # tickers = get_open_opsition()

    # # Check sell signals

    # for i in tickers:
    #     print (i)
    #     i.encode("ASCII")
    #     log = get_trade_log(i)
    #     cost = (log.Price * log["size"] ).sum()/log["size"].sum()

    #     if datetime.now() - log.TimeStamp.iloc[0] > timedelta(days=1) and log.Strategy.iloc[-1] == strategy_name:

    #         if ta.CCI(get_price_data([i],method="self_minute", robinhood=robinhood,back_day = 200).High,get_price_data([i],method="self_minute", robinhood=robinhood,back_day = 200).Low,get_price_data([i],method="self_minute", robinhood=robinhood,back_day = 200).Close, timeperiod=20).iloc[-1] >cci_sell:
    #             if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].sum()])== "Trade Success!":
    #                 log_trade(i,-log["size"].sum(), da.get_quote_yahoo(i).regularMarketPrice.values[0], strategy_name)
    #                 send_email(body_html="",body_content="", title = "CCI Sell Signal")


    #         elif ((da.get_quote_yahoo(i).regularMarketPrice.values[0]- cost)/cost) < -0.02:

    #             if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].sum()])== "Trade Success!":
    #                 log_trade(i,-log["size"].sum(), da.get_quote_yahoo(i).regularMarketPrice.values[0], strategy_name)
    #                 send_email(body_html="",body_content="", title = "CCI Cut Losses")

    #         elif ((da.get_quote_yahoo(i).regularMarketPrice.values[0]- cost)/cost) > 0.08:

    #             if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].sum()])== "Trade Success!":
    #                 log_trade(i,-log["size"].sum(), da.get_quote_yahoo(i).regularMarketPrice.values[0], strategy_name)
    #                 send_email(body_html="",body_content="", title = "CCI Havast Profit")
    #     time.sleep(10)


    # # buy if signal


    # mongod = mongo("Strategy_suggestion")

    # try:
    #     ta_tickers = pd.DataFrame(mongod.db["CCI"].find()).Ticker[0].split()
    #     for i in ta_tickers:
    #         i.encode("ASCII")
    #         buy_ticker = i
    #         buy_price = da.get_quote_yahoo(buy_ticker).regularMarketPrice.values[0]
    #         buy_size = int(money/buy_price)

    #         if ta.CCI(get_price_data([i],method="day", robinhood=robinhood,back_day = 200).High,get_price_data([i],method="day", robinhood=robinhood,back_day = 200).Low,get_price_data([i],method="day", robinhood=robinhood,back_day = 200).Close, timeperiod=20).iloc[-1] > cci_sell \
    #         and ta.CCI(get_price_data([i],method="self_minute", robinhood=robinhood,back_day = 200).High,get_price_data([i],method="self_minute", robinhood=robinhood,back_day = 200).Low,get_price_data([i],method="self_minute", robinhood=robinhood,back_day = 200).Close, timeperiod=20).iloc[-1] < cci_buy \
    #         and get_price_data([i],method="self_minute", robinhood=robinhood,back_day = 200).Close.mean() > 10\
    #         and (i not in get_open_opsition())\
    #         and (get_price_data([i], robinhood=robinhood,method="self_minute",back_day = 200).Close.mean()>10.0):
    #             if robinhood.place_buy_bulk_checkup(ticker_list=[buy_ticker], quantity_list=[buy_size],price_list=[buy_price])== "Trade Success!":
    #                 log_trade(i,buy_size, buy_price, strategy = database_name)
    #                 send_email(body_html="",body_content="", title = "Buy Signal: " + i)
    #     time.sleep(10)
    # except Exception as e:
    #     print (e)

    # html += "<br><br>  CCI check finished"



    ########################
    # Momentum Trade
    ########################




    
#     mongod = mongo("all_symbol","momentum_sharp")

#     tos = pd.DataFrame(mongod.conn.table.find({},{"Refresh_Date":1}).sort("Refresh_Date",-1).limit(1))["Refresh_Date"].iloc[0]
#     candidates = pd.DataFrame(mongod.conn.table.find({"Refresh_Date":tos})).drop_duplicates()
#     candidates = candidates[candidates.Holding <30].sort_values("Sharp_Ratio",ascending=False)
    
    
#     # candidates = pd.DataFrame(mongod.db["momentum"].find()).sort_values("End_Value", ascending=False)

# #     candidates = mongod.conn.get_data('''
    
# #     SELECT * FROM all_symbol.`Dist_momentum_sharp_TOS` where holding < 30 ORDER BY `Sharp_Ratio` DESC
    
# #     ''')

    
    
#     strategy_name = "momentum"
#     money = trading_param["momentum_money"]

#     trade_scale = "day"



#     # Enter signal

#     for i in candidates.Ticker.iloc[:5]:
#         try:
#             price = get_price_data([i], method=trade_scale,robinhood=robingateway(),back_day=90 )
#             price = price.set_index("TimeStamp")
#             lookback = int(candidates.loc[candidates.Ticker == i,"Lookback"].iloc[0])
#             holddays = int(candidates.loc[candidates.Ticker == i,"Holding"].iloc[0])
#     #     price["Return"] = np.log(price.Close/price.Close.shift(lookback))

#             fprice = np.log(fwd_price(i,mat=lookback,val_num_steps=30)/price.Close.iloc[-lookback])
#         except Exception as e:
#             send_email("Price in momentum check error %s, Error: %s. Process continues"%(i,str(e)))
#             continue


#     #     if price["Return"].iloc[-1] > 0.015: \
#         if fprice > 0.02 \
#             and robinhood.get_buying_power()>trading_param["cash_reserve"] \
#             and datetime.now(mytz).hour < 9 \
#             and (datetime.now(mytz).hour >= 6 and datetime.now(mytz).minute>=30) \
#             and len(get_open_opsition(stratgy_filter="momentum"))< trading_param["momentum_hold"]:

#             try:
#     #                 buy_price = robinhood.get_last_price(i)
#                 buy_price = round(vwap(i,back_day=2),2)
#                 send_email("VWAP Pass %s"%(i))

#             except Exception as e:
#                 print (e)
#                 print ("Symbol not tradable by Robinhood")
#                 send_email("Probably VWAP error %s, %s"%(i,str(e)))
#                 continue
#             buy_size = int(money/buy_price)

#             if robinhood.place_buy_bulk_checkup(ticker_list=[i],quantity_list=[buy_size],price_list=[buy_price])== "Trade Success!":
#                     log_trade(i,buy_size, buy_price, strategy_name,holddays)
#                     send_email(body_html="",body_content="", title = "momentum buy Signal "+str(i))

#             else:
#                 send_email("Trade fail %s"%(i))


#     # check sell signal

#     tickers = get_open_opsition()
#     strategy_name = "momentum"


#     for i in tickers:
#         print (i)
#         i.encode("ASCII")
#         log = get_trade_log(i)
#         log = log[log.Strategy==strategy_name]
#         log["TimeStamp"] = log["TimeStamp"].apply(lambda x: x.astimezone(mytz))
#         if len(log) == 0:
#             continue
#         #cost = (log.Price * log["size"] ).sum()/log["size"].sum()
#         cost = float(log.Price.iloc[-1])
#         holddays = log.Hold_days.iloc[-1]
#         if holddays != holddays:
#             holddays =1
#         if datetime.now(mytz) - log.TimeStamp.iloc[-1] >= timedelta(days=1) \
#         and log["size"].sum() != 0 \
#         and i not in trading_param["Long_Term_Tickers"]:
#     #             current_quote = round(realtimequote(i)["price"].iloc[0])
#             current_quote = float(robinhood.my_trader.get_quote(i)["last_trade_price"])

#             if ((current_quote- cost)/cost) < trading_param["momentum_cutloss"]:

#                 if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].iloc[-1]],price_list=[current_quote])== "Trade Success!":
#                     log_trade(i,-log["size"].sum(), current_quote, strategy_name)
#                     send_email(body_html="",body_content="", title = "momentum Cut Losses " +str(i))

#             elif ((current_quote- cost)/cost) > trading_param["momentum_harvest"]:

#                 if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].iloc[-1]],price_list=[current_quote])== "Trade Success!":
#                     log_trade(i,-log["size"].sum(), current_quote, strategy_name)
#                     send_email(body_html="",body_content="", title = "momentum Harvast Profit "+str(i))

#             elif datetime.now(mytz) - log.TimeStamp.iloc[-1] > timedelta(days=  holddays  ):
#     #             elif datetime.now() - log.TimeStamp.iloc[-1] > timedelta(days=  holddays/14  ):
#                 if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].iloc[-1]],price_list=[current_quote])== "Trade Success!":
#                     log_trade(i,-log["size"].sum(), current_quote, strategy_name)
#                     send_email(body_html="",body_content="", title = "momentum reach hold days limit "+str(i))

#             elif datetime.now(mytz) - log.TimeStamp.iloc[-1] > timedelta(days=  trading_param["momentum_timeout_days"]  ):
#                 if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].iloc[-1]],price_list=[current_quote])== "Trade Success!":
#                     log_trade(i,-log["size"].sum(), current_quote, strategy_name)
#                     send_email(body_html="",body_content="", title = "momentum reach set hold days limit "+str(i))

#         time.sleep(10)






########################################################   
# End of minute beta manual
#######################################################

        
except Exception as e:
    send_email("manual beta error " + str(e))
    

