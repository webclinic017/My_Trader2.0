#############################################    
# check strategy opportunities
#############################################


# Check RSI strategy

from my_libs import * 


result = []
result_str = ""
data_method = "self_minute"

my_list = pd.read_csv("/home/ken/notebook/My_Trader2.0/file/cantrade.csv")

for i in my_list.Ticker:
    temp = mongo("all_symbol")
    temp = pd.DataFrame(temp.db["Stocks_info"].find())
    if temp.loc[temp.Ticker == i,"Industry"].iloc[0] != temp.loc[temp.Ticker == i,"Industry"].iloc[0]:
        continue
    elif "Fund" in temp.loc[temp.Ticker == i,"Industry"].iloc[0]:
        continue
    print (i)

    try:
        price = get_price_data([i], robinhood=robinhood,method=data_method,back_day = 200)
        price = price.set_index("TimeStamp")
    
        
        cerebro = bt.Cerebro()
        cerebro.addstrategy(rsiStrategy)
        cerebro.broker.setcommission(commission=0.001)



        # Create a Data Feed
        data = bt.feeds.PandasData(dataname=price)

        cerebro.adddata(data)
        cerebro.broker.setcash(2000.0)
        init = cerebro.broker.getvalue()
        #print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
        cerebro.run()
        post = cerebro.broker.getvalue()
        if post > init:
            print ("Good Trade")
            result.append((i,post))
        #print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
        #cerebro.plot()
        clear_output()
    except Exception as e:
        print (e)
        continue

result = pd.DataFrame(result).sort_values(1, ascending= False)[2:9]        

for i in result[0]:
    result_str += i + " "

mongod = mongo("Strategy_suggestion")
mongod.db["RSI"].drop()
mongod.db["RSI"].update({"TimeStamp":datetime.now()},{"$set":{"Ticker":result_str}},upsert=True)

send_email("Finished RSI check")