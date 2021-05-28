from my_libs_py3 import *

# directory = "/home/ken/notebook/My_Trader2.0/file/"
# working_suggestion = "/home/ken/notebook/My_Trader2.0/Trade_suggestion_minute_1st"
# universe_file_name = "/home/ken/notebook/My_Trader2.0/my_universe_industry_sector_marketcap_earnings.csv"


# try:

#     mongod = mongo()

#     runtime = mongod.update_db()
# #     runtime = mongod.update_db_multi()
#     send_email(body_html="",body_content="", title = "daily price: %s"%runtime) 
    
    
    
# except Exception as e:
    
#     send_email(body_html="",body_content="", title = str(e) +" daily price update error") 
    
    
    
    
########################   
# Fix unsetteled trade
########################
robinhood = robingateway()



try:

    log_pos = get_open_opsition()
    temp = robinhood.get_my_positions()
    pos_frame = pd.DataFrame([temp[0],temp[1]]).transpose()
    pos_frame.columns = ["Ticker","Shares"]
    #     act_pos = robinhood.get_my_positions()[0]
    note = ""
    for i in log_pos:
        if i not in pos_frame.Ticker.to_list():
    #             note += ("fix "+ i +"\n")
            fix_unsettled_trade_update(i)
            send_email("Fixed unsettled trade to size 0 " + str(i))
        elif get_trade_log(i)["size"].iloc[0] != pos_frame.loc[pos_frame.Ticker == i,"Shares"].iloc[0]:
            fix_unsettled_trade_update(i, size=pos_frame.loc[pos_frame.Ticker == i,"Shares"].iloc[0], partial=True)
            send_email("Fixed unsettled trade to match size " + str(i))

except Exception as e:
    send_email("Fixed unsettled trade Fail\n" + str(e))
    

########################   
# Future price
########################
    
    
try: 
    my_future = future()



    symbol =  "VX" + "/" + my_future.monthCode(datetime.now().month+1) + str(int(datetime.now().year)+1)[-1:] if datetime.now().month + 1 > 12 \
              else "VX" + "/" + my_future.monthCode(datetime.now().month + 1) + str(datetime.now().year)[-1:]

    new_frame = pd.DataFrame({"TimeStamp":datetime(datetime.now().year,datetime.now().month,datetime.now().day),"Close":[my_future.get_future_price(datetime.now().year,datetime.now().month)],"VIX_Day_Roll":((my_future.get_future_price(datetime.now().year,datetime.now().month) - realtimequote("^VIX").price.values[0])/my_future.get_historic_data(my_future.get_future_expiration(datetime.now().year,datetime.now().month)).Close.std())/30, "symbol":symbol}).reset_index()
    new_frame = new_frame.drop("index",axis = 1)
    
    
    # table_name = "VX" + my_future.monthCode(datetime.now().month+1)+str(datetime.now().year)[-2:]

    # mongod.conn.to_sql(new_frame,"future",symbol,if_exists="append")
    mongo_conn = connect_mongo("future",symbol)
    mongo_conn.update_to_mongo(new_frame,"TimeStamp")
        
    
#     new_frame=json.loads(new_frame.T.to_json()).values()[0]

#     mongod.db["VX" + my_future.monthCode(datetime.now().month+1)+str(datetime.now().year)[:-2]].update_many({"TimeStamp":new_frame["TimeStamp"]},{"$set":new_frame},upsert=True)

    
#     update_fundamentals(robingateway(), skip_can=False)
    
    send_email(body_html="",body_content="", title = "daily price update done") 
    
    
    
except Exception as e:
    
    send_email(body_html="",body_content="", title = str(e) +" future price update error") 
    
    

########################   
# New Daily Data
########################


try:

    mongod = mongo()
    runtime = mongod.update_db_new_day_mongo()
    send_email("New day Data mongo runtime: " + str(runtime))
    # runtime = mongod.update_db_new_day()
    # send_email("New day Data runtime: " + str(runtime))

except Exception as e:
    send_email("New day Data error: " + str(e))
