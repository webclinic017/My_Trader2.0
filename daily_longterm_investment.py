
from my_libs_py3 import *





robinhood =robingateway()







########################################################
# START of daily investment
#######################################################


try:


    ########################
    # Fundamental Cumulation
    ########################

    strategy_name = "Fundamental"

    money = 500

    mongod = mongo("all_symbol")

    mongod = mongo("all_symbol","screenerModel")
    ## This line gets the max refresh_date
    tos = pd.DataFrame(mongod.conn.table.find({},{"Refresh_Date":1}).sort("Refresh_Date",-1).limit(1))["Refresh_Date"].iloc[0]
    fun_table = pd.DataFrame(mongod.conn.table.find({"Refresh_Date":tos}))


    fun_table["sum_rank"] = \
        fun_table["P/Cash"] + fun_table["Analyst Recom"]  + fun_table["P/S"] + fun_table["Total Debt/Equity"] +\
        fun_table["P/Free Cash Flow"] + fun_table["P/E"] + fun_table["Insider Ownership"] + fun_table["Gross Margin"] \
        + fun_table["Current Ratio"] + fun_table["Sales growth quarter over quarter"] + fun_table["Profit Margin"] \
        + fun_table["Quick Ratio"] + fun_table["Performance (Week)"] + fun_table["Institutional Ownership"] + \
        fun_table["EPS (ttm)"] + fun_table["Operating Margin"]

    fun_table["avg_rank"] = (fun_table["P/Cash"] + fun_table["Analyst Recom"]  + fun_table["P/S"] + \
                             fun_table["Total Debt/Equity"] + fun_table["P/Free Cash Flow"] + fun_table["P/E"] +\
                             fun_table["Insider Ownership"] + fun_table["Gross Margin"] + fun_table["Current Ratio"] + \
                             fun_table["Sales growth quarter over quarter"] + fun_table["Profit Margin"] + \
                             fun_table["Quick Ratio"] + fun_table["Performance (Week)"] + \
                             fun_table["Institutional Ownership"] + fun_table["EPS (ttm)"] + \
                             fun_table["Operating Margin"])/21

    fun_table = fun_table.sort_values("sum_rank")

    target_list = fun_table.Ticker[:3]


    ##  Check buy signal

    for i in target_list:
        price = get_price_data([i],method = 'day',back_day=7)
        quote = realtimequote(i).price.iloc[0]
        size = np.ceil(money/quote)
        if quote < price.Close.mean():
            if robinhood.place_buy_bulk_checkup(ticker_list=[i],quantity_list=[size],skip_check= True) == "Trade Success!":
                log_trade(i,size, robinhood.get_last_price(i), strategy_name)
                send_email("Fundamental Cumulation Buy: %s"%i)


    ##  Check sell signal

    tickers = get_open_opsition()

    for i in tickers:
        i.encode("ASCII")
        log = get_trade_log(i)
        log = log[log.Strategy==strategy_name]
        if len(log) == 0:
            continue
        quote = realtimequote(i).price.iloc[0]
        size = np.ceil(log["size"].iloc[-1]/3)
        try:
            cost = robinhood.get_average_cost(i)
        except:
            send_email("%s not in portfolio"%i)
            continue
        if (quote - cost)/cost > 0.08:
            if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[size])== "Trade Success!":
                log_trade(i,-log["size"].sum(), robinhood.get_last_price(i), strategy_name)
                send_email("Fundamental Cumulation Sell: %s"%i)

########################################################
# End of daily investment
#######################################################


except Exception as e:
    send_email("daily investment error " + str(e))
