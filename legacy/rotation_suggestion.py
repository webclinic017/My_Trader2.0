


from my_libs import *



robinhood =robingateway()




########################   
# Screen for candidate of momentum trade
########################




try:
    

    result = pd.DataFrame()
    mongod = mongo("all_symbol","cantrade")
    ## This line gets the max refresh_date
    tos = pd.DataFrame(mongod.conn.table.find({},{"Refresh_Date":1}).sort("Refresh_Date",-1).limit(1))["Refresh_Date"].iloc[0]
    all_ticker = pd.DataFrame(mongod.conn.table.find({"Refresh_Date":tos})).Ticker.tolist()
    today = datetime.today().date()
    
    trade_scale = "day"
    for i in all_ticker:
        try:
            mongod = mongo("all_symbol","momentum_sharp")
            existing = pd.DataFrame(mongod.conn.table.find({"Ticker":i,"Refresh_Date":datetime.today()}))
            
            
            volume = get_price_data([i], robinhood=robingateway(),method =trade_scale).Volume.iloc[0]
            if len(existing) == 0 and volume != None:
                first = momentum_best_day(i,robinhood=robingateway(),method =trade_scale).iloc[0]
                end_value,sharpratio, last_trade, last_price, max_return,min_return = momentum_backtest(i,first["Lookback"],first["Holding"],robinhood=robingateway(),method = trade_scale)
                temp = pd.DataFrame([(i,end_value,sharpratio, first["Lookback"],first["Holding"],last_trade,last_price, max_return,min_return)]\
    ,columns= ["Ticker","End_Value", "Sharp_Ratio","Lookback","Holding","Last_Buy_Date","Last_Buy_Price","Max_Return","Min_Return"])
                temp["Refresh_Date"] = today
                result = result.append(temp)

                mongod.frame_to_mongo(temp)
            mongod.conn.conn.close()
        except Exception as e:
            print (e)
            
    send_email("Finished screen for momentum trade")
   
        
except Exception as e:
    send_email("Error! screen for momentum trade: %s"%str(e)) 




    
    
#############################################    
# check strategy opportunities
#############################################


# # Check RSI strategy

# try:

#     result = []
#     result_str = ""
#     data_method = "self_minute"

#     my_list = pd.read_csv("/users/ken/notebook/My_Trader2.0/file/cantrade.csv")
#     temp = mongo("all_symbol")
#     # temp = pd.DataFrame(temp.db["Stocks_info"].find())

#     temp = temp.conn.get_data("select * from all_symbol.screener")

#     for i in my_list.Ticker:
#         try:
#             if temp.loc[temp.Ticker == i,"Industry"].iloc[0] != temp.loc[temp.Ticker == i,"Industry"].iloc[0] or temp.loc[temp.Ticker == i,"Industry"].iloc[0] == None:
#                 continue
#             elif "Fund" in temp.loc[temp.Ticker == i,"Industry"].iloc[0]:
#                 continue
#             print (i)

#             price = get_price_data([i], robinhood=robinhood,method=data_method,back_day = 200)
#             price = price.set_index("TimeStamp")


#             cerebro = bt.Cerebro()
#             cerebro.addstrategy(rsiStrategy)
#             cerebro.broker.setcommission(commission=0.001)



#             # Create a Data Feed
#             data = bt.feeds.PandasData(dataname=price)

#             cerebro.adddata(data)
#             cerebro.broker.setcash(trading_param["rsi_money"])
#             init = cerebro.broker.getvalue()
#             #print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
#             cerebro.run()
#             post = cerebro.broker.getvalue()
#             if post > init:
#                 print ("Good Trade")
#                 result.append((i,post))
#             #print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
#             #cerebro.plot()
#             clear_output()
#         except Exception as e:
#             print (e)
#             continue

#     mongod = mongo("Strategy_suggestion")

#     if len(result) > 0:
#         result = pd.DataFrame(result).sort_values(1, ascending= False)[2:9]        
#         for i in result[0]:
#             result_str += i + " "

#         # mongod.db["RSI"].drop()
#         # mongod.db["RSI"].update({"TimeStamp":datetime.now()},{"$set":{"Ticker":result_str}},upsert=True)

# #         result["TimeStamp"] = datetime.now()
#         mongod.conn.conn.cursor().execute("update Strategy_suggestion.RSI set ticker = '%s', timestamp = '%s'"%(result_str,datetime.now()))
# #         mongod.to_sql(result,"Strategy_suggestion","RSI")

#     else:
#         mongod.conn.conn.cursor().execute("update Strategy_suggestion.RSI set ticker = '', timestamp = '%s'")

#     mongod.conn.conn.commit()
#     send_email("Finished RSI check")

# except Exception as e:
#      send_email("Finished RSI check error " + str(e))



        
        


########################
# Check CCI Strategy

# result = []
# result_str = ""
# data_method = "self_minute"


# for i in my_list.Ticker:
#     #price = da.DataReader(i,'yahoo',datetime(2019,5,1),datetime.now())
#     print (i)

#     try:
#         price = get_price_data([i], robinhood=robinhood,method=data_method,back_day = 200)
#         price = price.set_index("TimeStamp")
    
        
#         cerebro = bt.Cerebro()
#         cerebro.addstrategy(cciStrategy)
#         cerebro.broker.setcommission(commission=0.001)



#         # Create a Data Feed
#         data = bt.feeds.PandasData(dataname=price)

#         cerebro.adddata(data)
#         cerebro.broker.setcash(2000.0)
#         init = cerebro.broker.getvalue()
#         #print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
#         cerebro.run()
#         post = cerebro.broker.getvalue()
#         if post > init:
#             print ("Good Trade")
#             result.append((i,post))
#         #print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
#         #cerebro.plot()
#         clear_output()
#     except Exception as e:
#         print (e)
#         continue

# result = pd.DataFrame(result).sort_values(1, ascending= False)[2:9]        

# for i in result[0]:
#     result_str += i + " "

# mongod = mongo("Strategy_suggestion")
# mongod.db["CCI"].drop()
# mongod.db["CCI"].update({"TimeStamp":datetime.now()},{"$set":{"Ticker":result_str}},upsert=True)

# send_email("Finished CCI check")
