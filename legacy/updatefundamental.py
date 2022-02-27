from my_libs_py3 import *

robinhood = robingateway()





########################   
# Fix unsetteled trade
########################

# try:
#
#     log_pos = get_open_opsition()
#     temp = robinhood.get_my_positions()
#     pos_frame = pd.DataFrame([temp[0],temp[1]]).transpose()
#     pos_frame.columns = ["Ticker","Shares"]
#     #     act_pos = robinhood.get_my_positions()[0]
#     note = ""
#     for i in log_pos:
#         if i not in pos_frame.Ticker.to_list():
#     #             note += ("fix "+ i +"\n")
#             fix_unsettled_trade_update(i)
#             send_email("Fixed unsettled trade to size 0 " + str(i))
#         elif get_trade_log(i)["size"].iloc[0] != pos_frame.loc[pos_frame.Ticker == i,"Shares"].iloc[0]:
#             fix_unsettled_trade_update(i, size=pos_frame.loc[pos_frame.Ticker == i,"Shares"].iloc[0], partial=True)
#             send_email("Fixed unsettled trade to match size " + str(i))
#
# except Exception as e:
#     send_email("Fixed unsettled trade Fail\n" + str(e))



########################   
# New Minute Data
########################


try:

    mongod = mongo()
    runtime = mongod.update_db_new_minute_mongo()
    send_email("New Minute Data mongo runtime: " + str(runtime))
    
    # runtime = mongod.update_db_new_minute()
    # send_email("New Minute Data runtime: " + str(runtime))

except Exception as e:
    send_email("New Minute Data error: " + str(e))







        
        
        




# ########################   
# # Fundamental Run
# ########################   



# #update_fundamentals(robinhood, skip_can=False)


# mongod = mongo("all_symbol")


# all_stocks = pd.DataFrame(mongod.db["cantrade"].find())
# all_stocks.to_csv(universe_file_name)
# all_stocks.drop(["Price"],axis = 1,inplace=True)

# my_list = pd.read_csv(directory+"mylist.csv")
# my_list = list(my_list.Ticker)

# robinhood = robingateway()
# get_frame = pd.DataFrame()
# for i in my_list:
#     try:
#         get_frame = get_frame.append(get_price_data([i],method="self_minute",robinhood = robinhood).iloc[-1])
#     except:
#         pass

# result = all_stocks.set_index("Ticker").join(get_frame.set_index("Ticker"),rsuffix = "_2" )

# result.drop(["_id","_id_2"],axis = 1,inplace=True)

# result = result.reset_index()

# def get_avg(x,days=20):
#     try:
#         return get_price_data([x],method="day",robinhood = robingateway(),back_day = days).Return.mean()
#     except:
#         return np.NaN

# def get_std(x,days=20):
#     try:
#         return get_price_data([x],method="day",robinhood = robingateway(),back_day = days).Return.std()
#     except:
#         return np.NaN    

# try:    
    
#     result.loc[:,"Avg_Return10"] = result.Ticker.apply(lambda x: get_avg(x,10))
#     result.loc[:,"Std10"] = result.Ticker.apply(lambda x: get_std(x,10))
#     result["Sharp_Ratio10"] = result.Avg_Return10/result.Std10

#     result.loc[:,"Avg_Return20"] = result.Ticker.apply(lambda x: get_avg(x))
#     result.loc[:,"Std20"] = result.Ticker.apply(lambda x: get_std(x))
#     result["Sharp_Ratio20"] = result.Avg_Return20/result.Std20

#     result.loc[:,"Avg_Return30"] = result.Ticker.apply(lambda x: get_avg(x,30))
#     result.loc[:,"Std30"] = result.Ticker.apply(lambda x: get_std(x,30))
#     result["Sharp_Ratio30"] = result.Avg_Return30/result.Std30

#     result.loc[:,"Avg_Return40"] = result.Ticker.apply(lambda x: get_avg(x,40))
#     result.loc[:,"Std40"] = result.Ticker.apply(lambda x: get_std(x,40))
#     result["Sharp_Ratio40"] = result.Avg_Return40/result.Std40

#     result.loc[:,"Avg_Return50"] = result.Ticker.apply(lambda x: get_avg(x,50))
#     result.loc[:,"Std50"] = result.Ticker.apply(lambda x: get_std(x,50))
#     result["Sharp_Ratio50"] = result.Avg_Return50/result.Std50


#     result = result.drop(["language","longName","quoteType","shortName","shortName","triggerable","messageBoardId","sourceInterval","priceHint","fullExchangeName","gmtOffSetMilliseconds","region","firstTradeDateMilliseconds"],axis=1)


#     result["Refresh_Date"] = str(datetime.now().date())
#     mongod.db["Stocks_info"].drop()
#     mongod.frame_to_mongo(result, "Stocks_info")
#     print ("Done")
#     send_email("Finished updatefundamental done")

# except Exception as e:
#     send_email(title="Updatefundamental Error", body_html = str(e))
    
    
    
    
