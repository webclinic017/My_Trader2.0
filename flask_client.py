from my_libs import *
import flask as fl
# import io
# from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
# from matplotlib.figure import Figure
# import StringIO
# import base64
import waitress

def plot_ticker2(ticker,method,robinhood,fast_win=10,slow_win=25,past_days=90):
    #stock = da.DataReader(ticker,"yahoo","2017-01-01",datetime.now())
    stock = get_price_data([ticker],method=method,back_day = past_days,robinhood = robinhood)

    stock["mv_fast"]=stock["Close"].rolling(fast_win).mean()
    stock["mv_slow"]=stock["Close"].rolling(slow_win).mean()

    plot = stock[["Close","mv_fast","mv_slow"]].plot(figsize=(20,8))
    plot.legend(["Close","mv_fast","mv_slow"])
    fig = plot.get_figure()
    fig.savefig("stock.png")

    
    
    
template_folder = root_directory + "template/"
app = fl.Flask(__name__, template_folder = template_folder)

# trade_dashbaord_blueprint = fl.Blueprint("trade_dashboard",__name__)

# app.register_blueprint(trade_dashbaord_blueprint)



##################
# define global variables
##################


putcall = 0
table = pd.DataFrame()
curr_option= pd.DataFrame()
valuation = ""
text = ""    




@app.route("/clear_result")    
def clear_result(): 
    global putcall
    global table
    global curr_option
    global valuation
    global text
    robinhood = robingateway()
    option_status = robinhood.get_option_positions().to_html()
    my_beta_mins = mongod.conn.get_data(minute_sql)
    mongod = mongo("all_symbol","minute_beta")
    tos = pd.DataFrame(mongod.conn.table.find({},{"Refresh_Date":1}).sort("Refresh_Date",-1).limit(1))["Refresh_Date"].iloc[0]
    my_beta_mins = pd.DataFrame(mongod.conn.table.find({"Refresh_Date":tos}))
    
    putcall = 0
    table = pd.DataFrame()
    curr_option= pd.DataFrame()
    valuation = ""
    text = ""
    return fl.render_template('trade_dash.html', minute_beta = my_beta_mins.to_html(index=False),option_status=option_status)    

    
    
@app.route("/")
def index():
    global my_beta_mins
    robinhood = robingateway()
    option_status = robinhood.get_option_positions().to_html()
    mongod = mongo("all_symbol","minute_beta")
    tos = pd.DataFrame(mongod.conn.table.find({},{"Refresh_Date":1}).sort("Refresh_Date",-1).limit(1))["Refresh_Date"].iloc[0]
    my_beta_mins = pd.DataFrame(mongod.conn.table.find({"Refresh_Date":tos}))
    return fl.render_template('trade_dash.html', minute_beta = my_beta_mins.to_html(index=False),option_status=option_status)


@app.route("/price", methods = ["POST"])
def get_price():
    try:
        robinhood = robingateway()
        ## place minute beta
        option_status = robinhood.get_option_positions().to_html()
        ticker = str(fl.request.form["ticker"]).upper()
        quote = realtimequote(ticker).round(4)
#     [["ask","bid","regularMarketPrice","regularMarketChangePercent","fiftyDayAverage","twoHundredDayAverageChangePercent"]]
        quote_price = realtimequote(ticker)["price"].iloc[0]

        return fl.render_template('trade_dash.html',quote = quote.to_html(),ticker = ticker,minute_beta = my_beta_mins.to_html(index=False),quote_price=quote_price ,my_price = quote_price,option_status=option_status     )
    
    except Exception as e:
        print (e)
        return fl.render_template('trade_dash.html',quote = "Load Error",ticker = ticker,minute_beta = my_beta_mins.to_html(index=False),option_status=option_status )
    
    

    
@app.route("/stock_trade", methods = ["POST"])
def stock_trade():
    try:
        robinhood = robingateway()
        ## place minute beta
        option_status = robinhood.get_option_positions().to_html()
        ticker = str(fl.request.form["ticker"]).upper()
        quote = realtimequote(ticker).round(4)[["ask","bid","regularMarketPrice","regularMarketChangePercent","fiftyDayAverage","twoHundredDayAverageChangePercent"]]
        quote_price = realtimequote(ticker)["price"].iloc[0]
        bs = str(fl.request.form["stock_bs"])
        quantity = int(fl.request.form["stock_quantity"])
        limit_price = float(fl.request.form["limit_price"])
        
        
        
        if bs == "sell":
            if robinhood.place_sell_bulk_checkup(ticker_list=[ticker],quantity_list=[quantity],price_list=[limit_price])== "Trade Success!":
                log_trade(ticker,-quantity,limit_price , "Manual")
                send_email(body_html="",body_content="", title = "web client sell")
                stock_trade_result = "Success"
            else:
                stock_trade_result = "Fail"
        
        elif bs == "buy":
            
            if robinhood.place_buy_bulk_checkup(ticker_list=[ticker], quantity_list=[quantity],price_list=[limit_price],skip_check = True)== "Trade Success!":
                log_trade(ticker,quantity,limit_price , "Manual")
                send_email(body_html="",body_content="", title = "web client buy")
            else:
                stock_trade_result = "Fail"


                
                
        return fl.render_template('trade_dash.html',quote = quote.to_html(),ticker = ticker,minute_beta = my_beta_mins.to_html(index=False),stock_trade_result=stock_trade_result ,option_status=option_status )
    
    except Exception as e:
        print (e)
        return fl.render_template('trade_dash.html',quote = "Load Error",ticker = ticker,minute_beta = my_beta_mins.to_html(index=False),stock_trade_result=stock_trade_result   ,option_status=option_status  )
    
    
    
    
    
@app.route("/option", methods = ["POST"])
def get_option():
    try:
        global table
        robinhood = robingateway()
        ## place minute beta
        option_status = robinhood.get_option_positions().to_html()
        ticker = str(fl.request.form["ticker"]).upper()
        method = 'intraday'
        exp_pos = int(fl.request.form["exp_pos"])
        pc = str(fl.request.form["pc"]).lower()
        bs = str(fl.request.form["option_bs"]).lower()
        strike_price = float(fl.request.form["strike_price"])
        list_len = int(fl.request.form["list_len"])
        my_price =realtimequote(ticker)["price"].iloc[0]
        ## Get option table function
   
        def get_option_table(ticker,pc,bs,exp_pos,my_price = my_price,list_len=list_len):

            table = pd.DataFrame()
            
            get_record = []
            op = option_trading(robinhood,ticker,pc,bs,exp_pos)
            for i in range(0,list_len,1):
                try:
                    if pc == "call":
                        i = -i
                    temp_strike_price = op.closest_strick_price(my_price*(1-i/100.0))
                    if temp_strike_price in get_record:
                        continue

                    op = option_trading(robinhood,ticker,pc,bs,exp_pos,strike = temp_strike_price)
                    op_table = op.current_Option()
                    op_table_tick = op.get_option()["min_ticks"].iloc[0]

                    op_table.set_value("Below_tick",op_table_tick["below_tick"])

                    op_table.set_value("Experition",op.get_exp_date()[exp_pos])
                    op_table.set_value("Strike",op.strike)
                    op_table.set_value("Symbol",ticker)
                    table = table.append(op_table,ignore_index=True)
                    get_record.append(temp_strike_price)
#                     time.sleep(1)
                except Exception as e:
                    print ("Error occor: %s on %s"%(e,i/100.0))
                    continue
            return [table,table.open_interest.mean()]

                ##table too long
        
        table = get_option_table(ticker,pc,bs,exp_pos,my_price=strike_price)[0]
        table=table.drop\
    (["Below_tick","adjusted_mark_price","low_price","high_price","instrument","mark_price","previous_close_date"],axis=1)


#         print (strike_price)
#         op = option_trading(robinhood,ticker,pc,bs,exp_pos,strike =strike_price)
#         op.gen_leg()
#         curr_option = op.current_Option()
#         curr_option["Expiration"]=op.get_exp_date()[exp_pos]
#         curr_option["Strike"]=op.strike
#         curr_option["Symbol"]=ticker
#         curr_option=pd.DataFrame(curr_option,columns=[ticker]).drop(["instrument"])


        return fl.render_template('trade_dash.html'  ,ticker = ticker, minute_beta = my_beta_mins.to_html(index=False),option = table.to_html() ,my_price=my_price ,exp_pos=exp_pos,option_status=option_status)
    
    except Exception as e:
        print (e)
        return fl.render_template('trade_dash.html',option = "Get Option Table Error, try lower the list length",ticker = ticker,minute_beta = my_beta_mins.to_html(index=False) ,my_price=my_price ,exp_pos=exp_pos,option_status=option_status ) 
        
        ##################

@app.route("/putcall", methods = ["POST"])    
def get_putcall():
    try:
        global putcall
        robinhood = robingateway()
        ## place minute beta
        option_status = robinhood.get_option_positions().to_html()
        ticker = str(fl.request.form["ticker"]).upper()
        method = 'intraday'
        exp_pos = int(fl.request.form["exp_pos"])
        pc = str(fl.request.form["pc"]).lower()
        bs = str(fl.request.form["option_bs"]).lower()
        strike_price = float(fl.request.form["strike_price"])
        list_len = int(fl.request.form["list_len"])
        my_price = realtimequote(ticker)["price"].iloc[0]
        ## Get option table function
   
        def get_option_table(ticker,pc,bs,exp_pos,my_price = my_price,list_len=list_len):
            
            table = pd.DataFrame()
            
            get_record = []
            op = option_trading(robinhood,ticker,pc,bs,exp_pos)
            for i in range(0,list_len,1):
                try:
                    if pc == "call":
                        i = -i
                    temp_strike_price = op.closest_strick_price(my_price*(1-i/100.0))
                    if temp_strike_price in get_record:
                        continue

                    op = option_trading(robinhood,ticker,pc,bs,exp_pos,strike = temp_strike_price)
                    op_table = op.current_Option()
                    op_table_tick = op.get_option()["min_ticks"].iloc[0]

                    op_table.set_value("Below_tick",op_table_tick["below_tick"])

                    op_table.set_value("Experition",op.get_exp_date()[exp_pos])
                    op_table.set_value("Strike",op.strike)
                    op_table.set_value("Symbol",ticker)
                    table = table.append(op_table,ignore_index=True)
                    get_record.append(temp_strike_price)
                    time.sleep(2)
                except Exception as e:
                    print ("Error occor: %s on %s"%(e,i/100.0))
                    continue
            return [table,table.open_interest.mean()]

                ##table too long


        pc = "put"

        put_open = get_option_table(ticker,pc,bs,exp_pos,list_len=5,my_price = strike_price)[1]

        pc = "call"
        call_open = get_option_table(ticker,pc,bs,exp_pos,list_len=5,my_price = strike_price)[1]
        
    
        
        putcall = put_open - call_open


        return fl.render_template('trade_dash.html'  ,ticker = ticker, minute_beta = my_beta_mins.to_html(index=False),option = table.to_html() ,my_price=my_price ,exp_pos=exp_pos,option_status=option_status, putcall = putcall )
    
    except Exception as e:
        print (e)
        return fl.render_template('trade_dash.html',option = "Get Option Table Error, try lower the list length",ticker = ticker,minute_beta = my_beta_mins.to_html(index=False) ,my_price=my_price ,exp_pos=exp_pos,option_status=option_status , putcall = putcall ) 
        
        ##################

        
@app.route("/option_report", methods = ["POST"])
def option_report():
    try:
        ticker = str(fl.request.form["ticker"]).upper()
        exp_pos = int(fl.request.form["exp_pos"])
        pc = str(fl.request.form["pc"]).lower()
        my_price = realtimequote(ticker)["price"].iloc[0]
        
        option_report = option_strategy_table(robingateway(),ticker,pc)
        option_report = option_report.to_html()

        ##################

        return fl.render_template('option_pricing.html',  ticker = ticker ,my_price=my_price ,exp_pos=exp_pos,option_report = option_report)

    except Exception as e:
        print (e)
        return fl.render_template('option_pricing.html',ticker = ticker,my_price=my_price ,exp_pos=exp_pos,option_report = option_report)        
     


@app.route("/curr_option", methods = ["POST"])
def curr_option():
    try:
        global curr_option
        robinhood = robingateway()
        ## place minute beta
        option_status = robinhood.get_option_positions().to_html()
        ticker = str(fl.request.form["ticker"]).upper()
        method = 'intraday'
        exp_pos = int(fl.request.form["exp_pos"])
        pc = str(fl.request.form["pc"]).lower()
        bs = str(fl.request.form["option_bs"]).lower()
       
        strike_price = float(fl.request.form["strike_price"])
        my_price = realtimequote(ticker)["price"].iloc[0]




        op = option_trading(robinhood,ticker,pc,bs,exp_pos,strike =strike_price)
        op.gen_leg()
        curr_option = op.current_Option()
        curr_option["Expiration"]=op.get_exp_date()[exp_pos]
        curr_option["Strike"]=op.strike
        curr_option["Symbol"]=ticker
        curr_option=pd.DataFrame(curr_option,columns=[ticker]).drop(["instrument"])

        ##################

        return fl.render_template('trade_dash.html',  ticker = ticker, curr_option=curr_option.to_html() ,minute_beta = my_beta_mins.to_html(index=False) ,my_price=my_price ,exp_pos=exp_pos,strike_price=strike_price,option_status=option_status)
    
    except Exception as e:
        print (e)
        return fl.render_template('trade_dash.html',ticker = ticker ,curr_option=curr_option.to_html(),minute_beta = my_beta_mins.to_html(index=False) ,my_price=my_price ,exp_pos=exp_pos,strike_price=strike_price,option_status=option_status)         
     
   
    
    
@app.route("/option_trade", methods = ["POST"])
def option_trade():
    try:
        robinhood = robingateway()
        ## place minute beta
        option_status = robinhood.get_option_positions().to_html()
        ticker = str(fl.request.form["ticker"]).upper()
        method = 'intraday'
        exp_pos = int(fl.request.form["exp_pos"])
        pc = str(fl.request.form["pc"]).lower()
        bs = str(fl.request.form["option_bs"]).lower()
        quantity = int(fl.request.form["option_quantity"])
        strike_price = float(fl.request.form["strike_price"])
        my_price = realtimequote(ticker)["price"].iloc[0]




        op = option_trading(robinhood,ticker,pc,bs,exp_pos,strike =strike_price)
        op.gen_leg()
        curr_option = op.current_Option()
        curr_option["Expiration"]=op.get_exp_date()[exp_pos]
        curr_option["Strike"]=op.strike
        curr_option["Symbol"]=ticker
        curr_option=pd.DataFrame(curr_option,columns=[ticker]).drop(["instrument"])

        result = op.place_order(quantity=quantity)
        result = pd.DataFrame(result)
        ##################




        return fl.render_template('trade_dash.html',  option_trade_result = result.to_html()  ,ticker = ticker, curr_option=curr_option.to_html() ,minute_beta = my_beta_mins.to_html(index=False) ,my_price=my_price ,exp_pos=exp_pos,strike_price=strike_price,option_status=option_status)
    
    except Exception as e:
        print (e)
        return fl.render_template('trade_dash.html',option_trade_result = "Trade Error: %s"%str(e),ticker = ticker ,curr_option=curr_option.to_html(),minute_beta = my_beta_mins.to_html(index=False) ,my_price=my_price ,exp_pos=exp_pos,strike_price=strike_price,option_status=option_status)           
        
 
    


@app.route("/option_pricing_index")    
def option_pricing_index():
    
    
    return fl.render_template('option_pricing.html')
  
    
    
@app.route("/option_pricing", methods = ["POST"])
def option_pricing():
    try:
        global curr_option
        robinhood = robingateway()
        
#         my_beta_mins = mongod.conn.get_data(minute_sql)
#         option_status = robinhood.get_option_positions().to_html()
        ticker = str(fl.request.form["ticker"]).upper()
        method = 'intraday'
        exp_pos = int(fl.request.form["exp_pos"])
        pc = str(fl.request.form["pc"]).lower()
        bs = 'buy' # just dummy
    
        riskless_rate =float(fl.request.form["riskless_rate"])
        volatility =float(fl.request.form["volatility"])
        strike_price = float(fl.request.form["strike_price"])
        my_price = realtimequote(ticker)["price"].iloc[0]


        op = option_trading(robinhood,ticker,pc,bs,exp_pos,strike =strike_price)
        op.gen_leg()
        curr_option = op.current_Option()
        curr_option["Expiration"]=op.get_exp_date()[exp_pos]
        curr_option["Strike"]=op.strike
        curr_option["Symbol"]=ticker
        curr_option=pd.DataFrame(curr_option,columns=[ticker]).drop(["instrument"])
        
        ##################
    
        #*********
        #option info

        exp = datetime.strptime(curr_option.loc["Expiration"].iloc[0],"%Y-%m-%d")
        vol = volatility
        daytomat = None
        opt_type=pc

        # asset information
        spot=robinhood.get_last_price(ticker)
        today = datetime.now()

        if daytomat == None:

            mat=float((exp-today).days)/365
        else:
            mat = daytomat

        temp_price=get_price_data([ticker],"day",start_date = datetime.now()-timedelta(days =256),end_date=datetime.now())
        temp_price["return"]=log(temp_price["Close"].shift(-1)/temp_price["Close"])

        if vol == None:
            vol = temp_price['return'].std()
        exer_type=OptionExerciseType.AMERICAN

        my_pricing = Option(opt_type,spot,strike_price,mat,riskless_rate= riskless_rate,vol=vol,exer_type=exer_type)
        option_pricing = my_pricing.run_model(model=OptionModel.BINOMIAL_TREE)
        option_pricing =pd.DataFrame(option_pricing,index= [0])[["value","delta","gamma","rho","theta","vega"]]
        option_pricing["Ticker"] = ticker
        option_pricing["PC"] = pc
        option_pricing["Strike"] = strike_price
        option_pricing["volatility"] = volatility
        option_pricing["Expiration"] = op.get_exp_date()[exp_pos]
        
        # to_html altogether
        option_pricing = option_pricing.to_html()
        curr_option=curr_option.to_html()



        return fl.render_template('option_pricing.html',  ticker = ticker, curr_option=curr_option,my_price=my_price ,exp_pos=exp_pos,strike_price=strike_price,option_pricing = option_pricing,volatility=volatility,riskless_rate=riskless_rate)

    except Exception as e:
        print (e)
        return fl.render_template('option_pricing.html',ticker = ticker ,curr_option=curr_option,my_price=my_price ,exp_pos=exp_pos,strike_price=strike_price,option_pricing = option_pricing,volatility=volatility,riskless_rate=riskless_rate)


    

@app.route("/trading_param")
def my_trading_param():
    return fl.render_template('trading_param.html',  
          Long_Term_Tickers = ",".join(trading_param["Long_Term_Tickers"]),
          cash_reserve = trading_param["cash_reserve"],
          VIX_cutloss = trading_param["VIX_cutloss"],
          VIX_harvest = trading_param["VIX_harvest"],
          cci_buy = trading_param["cci_buy"],
          cci_sell = trading_param["cci_sell"],
          manual_cutloss = trading_param["manual_cutloss"],
          manual_harvest = trading_param["manual_harvest"],
          manual_timeout_days = trading_param["manual_timeout_days"],
          momentum_hold = trading_param["momentum_hold"],
          momentum_cutloss = trading_param["momentum_cutloss"],
          momentum_harvest = trading_param["momentum_harvest"],
          momentum_money = trading_param["momentum_money"],
          momentum_timeout_days = trading_param["momentum_timeout_days"],
          rsi_buy = trading_param["rsi_buy"],
          rsi_min_stock_price = trading_param["rsi_min_stock_price"],
          rsi_money = trading_param["rsi_money"],
          rsi_sell = trading_param["rsi_sell"],
          strategy_cutloss = trading_param["strategy_cutloss"],
          strategy_harvest = trading_param["strategy_harvest"],
          strategy_timeout_days = trading_param["strategy_timeout_days"]
                             
                             )





@app.route("/set_trading_param", methods = ["POST"])
def set_trading_param():
    
    try:
        
    
        trading_param["Long_Term_Tickers"]=fl.request.form["Long_Term_Tickers"].split(",")
    
        trading_param["cash_reserve"]=float(fl.request.form["cash_reserve"])
 
        trading_param["VIX_cutloss"]=float(fl.request.form["VIX_cutloss"])

        trading_param["VIX_harvest"]=float(fl.request.form["VIX_harvest"])

        trading_param["cci_buy"]=float(fl.request.form["cci_buy"])
             
        trading_param["cci_sell"]=float(fl.request.form["cci_sell"])
                
        trading_param["manual_cutloss"]=float(fl.request.form["manual_cutloss"])
        trading_param["manual_harvest"]=float(fl.request.form["manual_harvest"])
        trading_param["manual_timeout_days"]=float(fl.request.form["manual_timeout_days"])

        trading_param["momentum_cutloss"]=float(fl.request.form["momentum_cutloss"])

        trading_param["momentum_harvest"]=float(fl.request.form["momentum_harvest"])

        trading_param["momentum_money"]=float(fl.request.form["momentum_money"])

        trading_param["momentum_timeout_days"]=float(fl.request.form["momentum_timeout_days"])
        
        trading_param["momentum_hold"]=float(fl.request.form["momentum_hold"])
        
        trading_param["rsi_buy"]=float(fl.request.form["rsi_buy"])
                
        trading_param["rsi_min_stock_price"]=float(fl.request.form["rsi_min_stock_price"])

        trading_param["rsi_money"]=float(fl.request.form["rsi_money"])
                
        trading_param["rsi_sell"]=float(fl.request.form["rsi_sell"])
                
        trading_param["strategy_cutloss"]=float(fl.request.form["strategy_cutloss"])

        trading_param["strategy_harvest"]=float(fl.request.form["strategy_harvest"])

        trading_param["strategy_timeout_days"]=float(fl.request.form["strategy_timeout_days"])
        
        with open(directory + 'trading_param.json', 'w') as outfile:
            json.dump(trading_param, outfile)

    
    
    
        return fl.render_template_string("Set Trading Parameter Succeed!")
    
    except Exception as e:
        print (e)
        return fl.render_template_string("Set Trading Parameter Failed!")

    
    

@app.route("/robinhood_login")    
def robinhood_login():    
    robinhood = robingateway()
#     option_status = robinhood.get_option_positions().to_html()
    
#     my_beta_mins = mongod.conn.get_data(minute_sql)
    
    code = robinhood.my_trader.get_mfa_token("PQZJUCVO4CNVUWYP")
    
#     return fl.render_template('robinhood_login.html', minute_beta = my_beta_mins.to_html(index=False),option_status=option_status, code = code)
    return fl.render_template('robinhood_login.html', code = code)

@app.route("/valutation")    
def valution_index():
    
    
    return fl.render_template('valuation.html')
    

    
@app.route("/valutation_dcf", methods = ["POST"])    
def get_dcf():
    global valuation 
    
    ticker=str(fl.request.form["ticker"])

    period=str(fl.request.form["period"]).lower()
    
    try:
        result = dcf(ticker,period).set_index("date")
        if period != "today":
            result["Growth%"] = np.log(result["dcf"]/result["price"])
        else:    
            result["Growth%"] = np.log(result["dcf"]/result["Stock Price"])
    
        result = result.round(3).to_html()
        
        valuation =     result + "<br><br>" + valuation

        return fl.render_template('valuation.html', v_type = "DCF", valuation=valuation )
    except Exception as e:
        print (e)
        return fl.render_template('valuation.html', v_type = "DCF", valuation = valuation, alert = "Valuation Error Try Again")
    

    
@app.route("/valutation_f_statement_growth", methods = ["POST"])    
def get_f_statement_growth():
    global valuation 
    ticker=str(fl.request.form["ticker"])

    period=str(fl.request.form["period"])
    
    try:
    
        result = financial_statements_growth(ticker,period).set_index("date").transpose().to_html()
        valuation =     result + "<br><br>" + valuation

        return fl.render_template('valuation.html', v_type = "financial_statements_growth", valuation=valuation )
    except Exception as e:
        print (e)
        return fl.render_template('valuation.html', v_type = "financial_statements_growth", valuation = valuation, alert = "Valuation Error Try Again")

@app.route("/valutation_keymetrics", methods = ["POST"])    
def get_keymetrics():
    global valuation 
    ticker=str(fl.request.form["ticker"])

    period=str(fl.request.form["period"])
    
    try:
        result = key_metrics(ticker,period).set_index("date").transpose().to_html()
        valuation =     result + "<br><br>" + valuation

        return fl.render_template('valuation.html', v_type = "Key Metrics", valuation=valuation )
    except Exception as e:
        print (e)
        return fl.render_template('valuation.html', v_type = "Key Metrics", valuation = valuation, alert = "Valuation Error Try Again")

    
@app.route("/feed")    
def get_feed():

    try:

        result = rss_feed().drop(["form_type","date"],axis=1)
        result = result[result.ticker != "None"].to_html()
        valuation  =  result

        return fl.render_template('feed.html', v_type = "rss_feed", valuation=valuation )
    except Exception as e:
        print (e)
        return fl.render_template('feed.html', v_type = "rss_feed", valuation = valuation, alert = "Valuation Error Try Again")


    
    
    
    
    
    
    
@app.route("/news_index")    
def news_index():
    
    
    return fl.render_template('news.html')    
    
    
    
@app.route("/news/", methods = ["POST"])      
def get_news():
    try:
        global text
        
        ticker=str(fl.request.form["ticker"]).upper()

        number=str(fl.request.form["number"])
    
    
    
        def translate_time(time, timezone = "US/Pacific"):
            return change_timezone(datetime.utcfromtimestamp(0) + timedelta(milliseconds= time), timezone)
        
        pd.set_option('display.max_colwidth', 1000)
        
        url = "https://cloud.iexapis.com/stable/stock/{}/news/last/{}".format(ticker.upper(),number)
        payload = {
            "token" :"pk_9ddc48f862f64a3888125e82035a9b07"    
        }
        result = pd.DataFrame( r.get(url, params = payload).json())
        result.datetime = result.datetime.apply(translate_time)
        result = result[["datetime","headline","summary","related"]]

        for i in result.index:

            text += "Headline: " + "<b>" +result.loc[i].headline + "</b>" + "<br><br>"
            text += "Time: " + str(result.loc[i].datetime) + "<br><br>"
            text += "Summary: " + result.loc[i].summary + "<br><br>"
            text += "Related tickers: " + result.loc[i].related + "<br><br>"
            text += "<hr>"
        return fl.render_template('news.html',ticker = ticker, news_text = text )
    except Exception as e:
        print (e)
        return fl.render_template('news.html',ticker = ticker, news_text = text , alert = "Valuation Error Try Again")
    
    
    
# app.run(host='0.0.0.0', port=5001)
waitress.serve(app, host='0.0.0.0', port=5000)