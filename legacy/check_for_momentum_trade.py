########################   
# Screen for candidate of momentum trade
########################
mongod = mongo("all_symbol")

# all_ticker = pd.DataFrame(mongod.db["cantrade"].find()).Ticker.tolist()
result = pd.DataFrame()
all_ticker = mongod.conn.get_data("select * from all_symbol.cantrade").Ticker.tolist()

for i in all_ticker:
    try:
        first = momentum_best_day(i,robinhood=robinhood).iloc[0]
        end_value = momentum_backtest(i,first["Lookback"],first["Holding"],robinhood=robinhood)
        temp = pd.DataFrame([(i,end_value, first["Lookback"],first["Holding"])],columns= ["Ticker", "End_Value","Lookback","Holding"])
        temp["Refresh_Date"] = datetime.today().date()
        result = result.append(temp)
    except Exception as e:
        print (e)
#         send_email("screen momentum trade error\n" + str(e))


mongod.frame_to_mongo(collection_str="momentum",data=temp,drop_mode = "drop") 
send_email("Finished screen for momentum trade")     
        