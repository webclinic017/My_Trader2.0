from my_libs_py3 import *
import multiprocessing

########################
# Screen for candidate of momentum trade
########################

def pair_screen(start,end):
    for i in ALL_TICKER[start:end]:
        for j in ALL_TICKER:
            if i == j:
                continue

            if i in TICKER_1 and j in TICKER_2:
                continue

            try:
                trade = self_pair_trade(i, j, cash=500)

                end_value = trade.iloc[-1]["total_value"]
                max_return = round(np.log(trade["total_value"].shift(-1) / trade["total_value"]).max(), 4)
                min_return = round(np.log(trade["total_value"].shift(-1) / trade["total_value"]).min(), 4)
                avg_return = round(np.log(trade["total_value"].shift(-1) / trade["total_value"]).mean(), 4)
                vol = round(np.log(trade["total_value"].shift(-1) / trade["total_value"]).std(), 4)
                sharpratio = avg_return / vol

                #             temp = pd.DataFrame([(i,j,end_value)]\
                #     ,columns= ["Ticker_1","Ticker_2","End_Value"])

                temp = pd.DataFrame([(i, j, end_value, avg_return, sharpratio, min_return, max_return)] \
                                    , columns=["Ticker_1", "Ticker_2", "End_Value", "Avg_Return", "Sharp_Ratio",
                                               "Min_Return", "Max_Return"])
                temp["Refresh_Date"] = today
                mongod = mongo("all_symbol", "pair_trade_sharp_2021_500")
                mongod.conn.frame_to_mongo(temp)

                print("Done %s and %s" % (i, j))
            except Exception as e:
                print("--------------")
                print(e)
                print("--------------")


if __name__ == "__main__":

    # try:

    mongod = mongo("all_symbol","screener")
    ## This line gets the max refresh_date
    tos = pd.DataFrame(mongod.conn.table.find({},{"Refresh_Date":1}).sort("Refresh_Date",-1).limit(1))["Refresh_Date"].iloc[0]
    ALL_TICKER = pd.DataFrame(mongod.conn.table.find({"Refresh_Date":tos}))


    # ## Initialization
    # mongod.conn.conn.cursor().execute("truncate table all_symbol.pair_trade_sharp")
    # mongod.conn.conn.cursor().execute("truncate table all_symbol.pair_trade_screen_save")
    # mongod.conn.conn.commit()


    # ALL_TICKER = pd.DataFrame(mongod.db["cantrade"].find()).Ticker.tolist()
    result = pd.DataFrame()


    ALL_TICKER = ALL_TICKER[ALL_TICKER.Volume > ALL_TICKER.Volume.quantile(0.5)]
    ALL_TICKER = ALL_TICKER[ALL_TICKER["Institutional Ownership"] > ALL_TICKER["Institutional Ownership"].quantile(0.5)]

    ALL_TICKER = ALL_TICKER.Ticker.to_list()

    today = datetime.today().date()
    robinhood = robingateway()
    trade_scale = "day"
    backdays = 80

    mongod = mongo("all_symbol","pair_trade_screen_save")
    get = pd.DataFrame(mongod.conn.table.find({},{"Ticker_1":1,"Ticker_2":1}))
    TICKER_1 = get.Ticker_1.to_list()
    TICKER_2 = get.Ticker_2.to_list()

    ## CP Id
    START = 0
    END = len(ALL_TICKER)
    n_thread = 5
    steps = int((END - START) / n_thread)
    print("each length:%s" % steps)
    # pro = multiprocessing.get_context("spawn")
    with multiprocessing.Pool(n_thread) as pool:
        pool.starmap(pair_screen,
                     [(start, start + steps) for start in range(START, END, steps)])

    send_email("Finished screen for momentum trade")




# except Exception as e:
#     send_email("Error! screen for momentum trade: %s"%str(e))
