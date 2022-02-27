

from .my_libs_py3 import *




    
########################   
# Fix unsetteled trade
########################


def fix_unsettel_trade():

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
            elif get_trade_log(i)["size"].sum() != pos_frame.loc[pos_frame.Ticker == i,"Shares"].iloc[0]:
                fix_unsettled_trade_update(i, size=pos_frame.loc[pos_frame.Ticker == i,"Shares"].iloc[0], partial=True)
                send_email("Fixed unsettled trade to match size " + str(i))

    except Exception as e:
        send_email("Fixed unsettled trade Fail\n" + str(e))

    
    

def minute_beta():

    robinhood =robingateway()


    hedge = robinhood.hedge()


    # In[6]:


    my_beta_mins = robinhood.get_my_position_beta_minute()

    my_beta_mins["Refresh_Date"] = datetime.now()
    my_beta_mins = my_beta_mins.reset_index().rename({"index":"Ticker"},axis =1)
    my_beta_mins=my_beta_mins.round(4)
    mongod = mongo("all_symbol","minute_beta")
    mongod.conn.frame_to_mongo(my_beta_mins)

    ## ES Calculation

    var_table_mins = []
    var_table_day = []
    for i in range(500,0,-5):
        i = i/1000.0
        beta_table = robinhood.get_my_position_beta_minute(sv=i)
        var_table_mins.append((i,beta_table.Mins_VaR.sum()))
        var_table_day.append((i,beta_table.Day_VaR.sum()))
    var_table_mins = pd.DataFrame(var_table_mins)
    var_table_day = pd.DataFrame(var_table_day)
    var_table_mins.columns = ["sv","Mins_VaR"]
    var_table_day.columns = ["sv","Day_VaR"]
    es_mins = var_table_mins["Mins_VaR"].mean()    
    es_day = var_table_day["Day_VaR"].mean() 


    # var_table = []
    # for i in range(500,0,-5):
    #     i = i/1000.0
    #     var_table.append((i,robinhood.get_my_position_beta_minute(sv=i).Mins_VaR.sum()))
    # var_table = pd.DataFrame(var_table)
    # var_table.columns = ["sv","Mins_VaR"]
    # es_mins = var_table["Mins_VaR"].mean()    



    # var_table = []
    # for i in range(500,0,-5):
    #     i = i/1000.0
    #     var_table.append((i,robinhood.get_my_position_beta_minute(sv=i).Day_VaR.sum()))
    # var_table = pd.DataFrame(var_table)
    # var_table.columns = ["sv","Day_VaR"]
    # es_day = var_table["Day_VaR"].mean()   


    ##############################################
    # In[ ]:


    html = my_beta_mins.style.set_table_attributes('border="1" class="dataframe table table-hover table-bordered"')

    html = html.render()

    html += "<br><br>" + hedge[0]


    html += "<br><br>The sum Day VaR of this portfolio is {:.2f}".format((my_beta_mins.Day_VaR).sum())
    html += "<br>The sum Minute VaR of this portfolio is {:.2f}".format((my_beta_mins.Mins_VaR).sum())

    html += "<br><br>The Day ES of this portfolio is {:.2f}".format(es_day)
    html += "<br>The Minute ES of this portfolio is {:.2f}".format(es_mins)



########################
# End of minute beta
########################

    send_email(body_html=html, title = "Minute_Beta")

#############################################    
# Rotation check
#############################################    

# strategy_name = "Manual"


# get = robinhood.get_my_positions()
# tickers = get[0]
# sizes = get[1]

# tic_frame = pd.DataFrame({"Tickers":tickers,"Sizes":sizes})
    


# for i in tickers:
#     i.encode("ASCII")

#     if len(get_trade_log(i))  == 0 and i != "SPY":
#         log_trade(i,tic_frame[tic_frame.Tickers == i].Sizes.values[0] ,da.get_quote_yahoo(i).regularMarketPrice.values[0], strategy_name)
    
    
#     log = get_trade_log(i)

#     if log[log.Strategy=="Manual"]["size"].sum()!= 0 :
        
# #     if (datetime.now() - log.TimeStamp.iloc[-1] > timedelta(days=1)  and log.Strategy.iloc[-1] == strategy_name):
    
#         if ((da.get_quote_yahoo(i).regularMarketPrice.values[0]- log.Price.iloc[-1])/log.Price.iloc[-1]) > 0.08 and datetime.now() - log.TimeStamp.iloc[-1] > timedelta(days=1):
#             print("harvest Profit")
            
#             if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].sum()]) == "Trade Success!":
#                 log_trade(i,-log["size"].sum(), da.get_quote_yahoo(i).regularMarketPrice.values[0], strategy_name)


#         elif ((da.get_quote_yahoo(i).regularMarketPrice.values[0]- log.Price.iloc[-1])/log.Price.iloc[-1]) < -0.015:
#             print("Stop Loss")

#             if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].sum()])== "Trade Success!":
#                 log_trade(i,-log["size"].sum(), da.get_quote_yahoo(i).regularMarketPrice.values[0], strategy_name)
            

#         elif datetime.now() - log.TimeStamp.iloc[-1] > timedelta(days=7):
#             print("Timeout")
#             if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].sum()])== "Trade Success!":
#                 log_trade(i,-log["size"].sum(), da.get_quote_yahoo(i).regularMarketPrice.values[0], strategy_name)
#     time.sleep(10)
    

    
# html += "<br><br> Manual rotation check finished"
    
    

#############################################    
# Rotation check
#############################################

## The database name is actually the strategy column in the table


# database_name = "rotation"
# strategy_name = "rotation"

# tickers = get_open_opsition()

# for i in tickers:
#     i.encode("ASCII")
#     log = get_trade_log(i)
    
        
#     if (datetime.now() - log.TimeStamp.iloc[-1] > timedelta(days=1)  and log.Strategy.iloc[-1] == strategy_name):
    
#         if ((da.get_quote_yahoo(i).regularMarketPrice.values[0]- log.Price.iloc[-1])/log.Price.iloc[-1]) > 0.08:
#             print("harvest Profit")
            
#             if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].sum()]) == "Trade Success!":
#                 log_trade(i,-log["size"].sum(), da.get_quote_yahoo(i).regularMarketPrice.values[0], strategy_name)


#         elif ((da.get_quote_yahoo(i).regularMarketPrice.values[0]- log.Price.iloc[-1])/log.Price.iloc[-1]) < -0.015:
#             print("Stop Loss")

#             if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].sum()])== "Trade Success!":
#                 log_trade(i,-log["size"].sum(), da.get_quote_yahoo(i).regularMarketPrice.values[0], strategy_name)
            

#         elif datetime.now() - log.TimeStamp.iloc[-1] > timedelta(days=7):
#             print("Timeout")
#             if robinhood.place_sell_bulk_checkup(ticker_list=[i],quantity_list=[log["size"].sum()])== "Trade Success!":
#                 log_trade(i,-log["size"].sum(), da.get_quote_yahoo(i).regularMarketPrice.values[0], strategy_name)
#     time.sleep(10)
    

    
# html += "<br><br> rotation check finished"
#############################################    
# check strategy opportunities
#############################################    





