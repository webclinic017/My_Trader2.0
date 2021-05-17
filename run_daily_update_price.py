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
