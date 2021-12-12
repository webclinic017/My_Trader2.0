from my_libs_py3 import *
import multiprocessing
import warnings
warnings.WarningMessage("ignore")

########################
# Screen for candidate of momentum trade
########################

LOG_DB = "pair_trade_sharp_2021_500"


def pair_screen(start,end):
    for i in ALL_TICKER[start:end]:
        i = np.random.choice(ALL_TICKER[start:end])
        # for j in ALL_TICKER:
        j = np.random.choice(ALL_TICKER)
        if i == j:
            continue

        checkLogMongo = mongo("all_symbol", LOG_DB)
        get = pd.DataFrame(checkLogMongo.conn.table.find({"Ticker_1":i,"Ticker_2":j}))
        if len(get) > 0:
            continue

        try:
            trade = self_pair_trade(i, j, cash=500)

            end_value = trade.iloc[-1]["total_value"]
            max_return = round(np.log(trade["total_value"].shift(-1) / trade["total_value"]).max(), 4)
            min_return = round(np.log(trade["total_value"].shift(-1) / trade["total_value"]).min(), 4)
            avg_return = round(np.log(trade["total_value"].shift(-1) / trade["total_value"]).mean(), 4)
            vol = round(np.log(trade["total_value"].shift(-1) / trade["total_value"]).std(), 4)
            sharpratio = avg_return / vol


            temp = pd.DataFrame([(i, j, end_value, avg_return, sharpratio, min_return, max_return)] \
                                , columns=["Ticker_1", "Ticker_2", "End_Value", "Avg_Return", "Sharp_Ratio",
                                           "Min_Return", "Max_Return"])
            temp["Refresh_Date"] = today
            mongod = mongo("all_symbol", LOG_DB)
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
