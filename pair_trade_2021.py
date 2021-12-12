from my_libs_py3 import *


########################
# Screen for candidate of momentum trade
########################




# try:

mongod = mongo("all_symbol","screener")
## This line gets the max refresh_date
tos = pd.DataFrame(mongod.conn.table.find({},{"Refresh_Date":1}).sort("Refresh_Date",-1).limit(1))["Refresh_Date"].iloc[0]
all_ticker = pd.DataFrame(mongod.conn.table.find({"Refresh_Date":tos}))


# ## Initialization
# mongod.conn.conn.cursor().execute("truncate table all_symbol.pair_trade_sharp")
# mongod.conn.conn.cursor().execute("truncate table all_symbol.pair_trade_screen_save")
# mongod.conn.conn.commit()


# all_ticker = pd.DataFrame(mongod.db["cantrade"].find()).Ticker.tolist()
result = pd.DataFrame()


all_ticker = all_ticker[all_ticker.Volume > all_ticker.Volume.quantile(0.5)]
all_ticker = all_ticker[all_ticker["Institutional Ownership"] > all_ticker["Institutional Ownership"].quantile(0.5)]

all_ticker = all_ticker.Ticker.to_list()

today = datetime.today().date()
robinhood = robingateway()
trade_scale = "day"
backdays = 80

mongod = mongo("all_symbol","pair_trade_screen_save")
get = pd.DataFrame(mongod.conn.table.find({},{"Ticker_1":1,"Ticker_2":1}))
ticker_1 = get.Ticker_1.to_list()
ticker_2 = get.Ticker_2.to_list()


for i in all_ticker:
    for j in all_ticker:
        if i == j:
            continue


        try:
            trade = self_pair_trade(i,j,cash=500)
            
            end_value = trade.iloc[-1]["total_value"]
            max_return = round(np.log(trade["total_value"].shift(-1)/trade["total_value"]).max(),4)
            min_return = round(np.log(trade["total_value"].shift(-1)/trade["total_value"]).min(),4)
            avg_return = round(np.log(trade["total_value"].shift(-1)/trade["total_value"]).mean(),4)
            vol = round(np.log(trade["total_value"].shift(-1)/trade["total_value"]).std(),4)
            sharpratio = avg_return/vol

#             temp = pd.DataFrame([(i,j,end_value)]\
#     ,columns= ["Ticker_1","Ticker_2","End_Value"])
            
            temp = pd.DataFrame([(i,j,end_value,avg_return,sharpratio,min_return,max_return)]\
    ,columns= ["Ticker_1","Ticker_2","End_Value", "Avg_Return" ,"Sharp_Ratio","Min_Return","Max_Return"])
            temp["Refresh_Date"] = today
            mongod = mongo("all_symbol","pair_trade_sharp_2021_500")
            mongod.conn.frame_to_mongo(temp)
     
            print("Done %s and %s"%(i,j))
        except Exception as e:
            print ("--------------")
            print (e)
            print ("--------------")



# except Exception as e:
#     send_email("Error! screen for momentum trade: %s"%str(e))
