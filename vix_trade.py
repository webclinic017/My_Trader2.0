from .my_libs_py3 import *

########################   
# VIX Dayroll Trade
########################
def vix_trade():
    #check buy signals and exit signals
    
    robinhood = robingateway()

    vix_trade = vix_dayroll_trade(robinhood,initial= 800)

    vix_trade.trade_action()
    
    html = "<br><br>  VIX Dayroll check finished"
    html += "<br> Dayroll is {:.3f}".format(vix_trade.vix_dayroll())


    vix_enter, vix_exit, vix_buy_enter, vix_buy_exit = vix_trade.vix_trade_signal()

    html += "<br><br> Short VIX Enter: %.3f, Short VIX Exit: %.3f;<br>Long VIX Enter: %.3f, Long VIX Exit: %.3f"%(vix_enter, vix_exit, vix_buy_enter, vix_buy_exit)

    #Check sell signals

    tickers = get_open_opsition()
    strategy_name = "vix_dayroll"
    for i in tickers:
        print (i)
        i.encode("ASCII")
        log = get_trade_log(i)
        log = log[log.Strategy==strategy_name]
        if len(log) == 0:
            continue
        #cost = (log.Price * log["size"] ).sum()/log["size"].sum()
        cost = float(log.Price.iloc[-1])
        tzz = pytz.timezone('US/Pacific')
        if datetime.now(tzz) - log.TimeStamp.iloc[-1].replace(tzinfo=tzz) >= timedelta(hours=15) \
            and log["size"].sum() != 0:

            if ((realtimequote(i)["price"].iloc[0]- cost)/cost) < trading_param["VIX_cutloss"]:

                if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].sum()])== "Trade Success!":
                    log_trade(i,-log["size"].sum(), realtimequote(i)["price"].iloc[0], strategy_name)
                    send_email(body_html="",body_content="", title = "vix_dayroll Cut Losses")

            elif ((realtimequote(i)["price"].iloc[0]- cost)/cost) > trading_param["VIX_harvest"]:

                if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].sum()])== "Trade Success!":
                    log_trade(i,-log["size"].sum(), realtimequote(i)["price"].iloc[0], strategy_name)
                    send_email(body_html="",body_content="", title = "vix_dayroll Harvast Profit")
        time.sleep(10)
        
########################
# End of VIX
########################

    send_email(body_html=html, title = "VIX")