

from my_lib import *
from my_strategies import *
from option import *
from send_email import *
from fmp import *

#
#def hedge(self,hedge_int = "UVXY"):
#    robinhood = get_robinhood()
#    hedge_int_beta =beta([hedge_int],interval ="minute")[0].iloc[0][0]
#    hedge_int_price = robinhood.get_ask_price(hedge_int)
#    position_beta = robinhood.get_my_position_beta_minute()[0]
#    position_value = robinhood.my_trader.market_value()
#    shares = abs(np.floor(position_value*position_beta/hedge_int_beta/hedge_int_price))
#
#    return shares



#********************************************************

#   Price Modeling

#********************************************************

def fwd_price(ticker,spot0 = None,riskless_rate=0,mat = 1,val_num_steps = 30,val_num_paths = 50000,yield_ = 0 ):
    if spot0 is None:
        spot0=realtimequote(ticker).price.values[0]


    try:
        option = option_trading(robingateway(),ticker,"call","buy",0)
        vol = float(option.current_Option()["implied_volatility"])
    except:
        vol = get_price_data([ticker],method = "realtimeday", robinhood = robingateway(),back_day= 30).Return.std()

#     vol = get_price_data([ticker],method = "self_minute", robinhood = robingateway()).Return.std()
    
    val_random_seed =  int(time.time())
    np.random.seed(val_random_seed)
    dt = float(mat)/ val_num_steps
    sqrt_dt = dt ** 0.5
    
    drift = (riskless_rate - yield_ - (vol ** 2) / 2) * dt
    result = np.empty([val_num_paths, val_num_steps])
    for path_num in xrange(val_num_paths):
        result1 = np.empty([val_num_steps])
        spot = spot0
        result1[0] = spot
        for step_num in xrange(1, val_num_steps):
            spot *= np.exp(drift + vol * np.random.normal() * sqrt_dt)
            if hasattr(yield_, '__call__'):
                div_t1, div_t2 = dt * step_num, dt * (step_num + 1)
                div = yield_(div_t1, div_t2)
                if is_number(div): spot -= div
            result1[step_num] = spot

        result[path_num] = result1
    return pd.DataFrame(result).mean().iloc[-1]
    

def fwd_return(ticker,riskless_rate=0,mat = 1,val_num_steps = 30,val_num_paths = 50000):
    spot = get_price_data([ticker],method = "self_minute", robinhood = robingateway()).Close.iloc[-1]

    fprice = fwd_price(ticker,spot,riskless_rate,mat,val_num_steps,val_num_paths)
    print (fprice)
        
    return np.log(fprice/spot)


def fix_unsettled_trade_update(ticker, size=0, partial=False):
    log = get_trade_log(ticker)
    if len(log)== 0:
        return
    ID = get_trade_log(ticker).iloc[-1]["TimeStamp"]
    if not partial:
        mongod = mongo("trade_log",ticker)
        
        mongod.conn.table.update({"TimeStamp":ID},{"$set":{"size":0}})
        

           
    elif size == 0:
        print ("Please enter size for partial size fix") 
    else:
        mongod = mongo("trade_log",ticker)
        
        mongod.conn.table.update({"TimeStamp":ID},{"$set":{"size":size}})

    
    
# def fix_unsettled_trade_update(ticker, size=0, partial=False):
#     mongod = mongo("trade_log")
#     db = mongod.db[ticker]
#     log = get_trade_log(ticker)
#     ID = get_trade_log(ticker).iloc[-1]["_id"]
#     if not partial:
#         log = get_trade_log(ticker)
#         ID = get_trade_log(ticker).iloc[-1]["_id"]
#         db.update_one({"_id":ID},{"$set":{"size":0}},upsert=False)
           
#     elif size == 0:
#         print ("Please enter size for partial size fix") 
#     else:
#         db.update_one({"_id":ID},{"$set":{"size":size}},upsert=False)




def fix_unsettled_trade(ticker, size=0, partial=False):
    if not partial:
        log = get_trade_log(ticker)
        log_trade(ticker,-log.iloc[-1]["size"],log.iloc[-1]["Price"],log.iloc[-1]["Strategy"])
    elif size == 0:
        print ("Please enter size for partial size fix") 
    else:
        log_trade(ticker,-(log.iloc[-1]["size"]-size),log.iloc[-1]["Price"],log.iloc[-1]["Strategy"])

def log_trade(ticker,size, price, strategy , hold_days = None, database = "trade_log"):
    timestamp = datetime.now()
    mongod = mongo(database,ticker)
    if hold_days == None:
        upload_data = pd.DataFrame([{"TimeStamp":timestamp, "Ticker":ticker,"size":size,"Price":price,"Strategy":strategy}])
    else:
        upload_data = pd.DataFrame([{"TimeStamp":timestamp, "Ticker":ticker,"size":size,"Price":price,"Strategy":strategy, "Hold_days":hold_days}])
    
    mongod.conn.frame_to_mongo(upload_data)


def log_pair_trade(ticker1,ticker2,size1,size2, price1,price2 , database = "pair_trade_log"):
    timestamp = datetime.now()
    mongod = mongo(database,ticker)

    upload_data = pd.DataFrame([{"TimeStamp":timestamp, "Ticker1":ticker1,"Ticker2":ticker2,"size1":size1,"size2":size2,"Price1":price1,"Price2":price2}])

    mongod.conn.frame_to_mongo(upload_data)

# def log_trade(ticker,size, price, strategy , database = "trade_log"):
#     timestamp = datetime.now()
#     mongod = mongo(database)
#     mongod.db[ticker].insert({"TimeStamp":timestamp, "Ticker":ticker,"size":size,"Price":price,"Strategy":strategy})
#     collection = mongod.db[ticker]
#     get = collection.find().sort("TimeStamp",pymongo.ASCENDING)
#     get= pd.DataFrame(get)
# #     if get["size"].sum() == 0:
# #         collection.drop()

def is_open(ticker):
    if get_trade_log(ticker)["size"].sum() == 0:
        return False
    else:
        return True

def fix_unsettled_trade(ticker, size=0, partial=False):
    if not partial:
        log = get_trade_log(ticker)
        log_trade(ticker,-log.iloc[-1]["size"],log.iloc[-1]["Price"],log.iloc[-1]["Strategy"])
    elif size == 0:
        print ("Please enter size for partial size fix") 
    else:
        log_trade(ticker,-(log.iloc[-1]["size"]-size),log.iloc[-1]["Price"],log.iloc[-1]["Strategy"])    

        
def get_open_opsition(database = "trade_log", stratgy_filter = None): 
    mongod = mongo(database)
    working = mongod.conn.db.list_collection_names()
    sent = []
    if stratgy_filter == None:
        for i in working:
            temp = get_trade_log(i)
            if len(temp) > 0 and temp["size"].sum() != 0:
                sent.append(i)
    else:
        for i in working:
            temp = get_trade_log(i)
            if len(temp) > 0 and temp["size"].sum() != 0 and temp["Strategy"].iloc[0] == stratgy_filter:
                sent.append(i)

    return sent     

def get_trade_log(ticker,database = "trade_log"): 
    mongod = mongo(database,ticker)
    try:
        result = pd.DataFrame(mongod.conn.table.find()) 
    except Exception as e:
        print (e)
        result = pd.DataFrame()
    return result 
         
            
     
#     return sent    

# def get_trade_log(ticker,database = "trade_log"): 
#     mongod = mongo(database)
#     return pd.DataFrame(mongod.db[ticker].find().sort("TimeStamp",pymongo.ASCENDING))    




def vwap(ticker,method = "intraday", back_day = 1, return_table= False ):
    price = get_price_data([ticker],method=method,robinhood=robingateway(),back_day=back_day)

    price["Traded_Cash"] = price.Close * price.Volume

    price["Traded_Cash_cum"] = price["Traded_Cash"].cumsum()

    price["Volume_cum"] = price.Volume.cumsum()

    price["VWAP"] = price["Traded_Cash_cum"]/price["Volume_cum"]
    
    vwap = price["Traded_Cash"].sum()/price.Volume.sum()

    if return_table:
        return price
    else:
        return vwap


def var_normal(ticker, method = "intraday", sv= 0.05, timeperiod=50):
    robinhood = robingateway()
    price = get_price_data([ticker],method=method,robinhood=robinhood)
    price["Return"] = (price.Close-price.Close.shift(1))/price.Close.shift(1)
    mean = price.Return[-timeperiod:].mean()
    std = price.Return[-timeperiod:].std()
    return abs(mean + std*scipy.special.ndtri(sv))*price.Close.iloc[-1]


def hedge(ticker,robinhood,method = "self_minute",hedge_int = "VIXY",target_beta =0.0):
    hedge_int_beta =beta([hedge_int],interval ="minute",robinhood=robinhood)[0].iloc[0][0]
    hedge_int_price = realtimequote(hedge_int).price.iloc[0]
    position_beta = beta([ticker],interval ="minute",robinhood=robinhood)[0].iloc[0][0]
    position_value = realtimequote(ticker).price.iloc[0]
    shares = np.floor(position_value*(target_beta-position_beta)/hedge_int_beta/hedge_int_price)
    clear_output()
    return ("To headge %s beta to "%ticker + str(target_beta) + " please trade " + str(shares) + " share of " +str(hedge_int) + "<br>" + "Total Beta is {:1.4f}".format(position_beta))\
            ,shares


def beta(ticker_list,bench = "SPY", interval="day", robinhood = None, past_days = 90 ):    
    # will return a dataframe

    betas = []
    volos = []
    ben_mark=pd.DataFrame()
    if interval == "day":
        ben_mark= get_price_data([bench],"realtimeday",start_date = datetime.now()-timedelta(days=past_days),robinhood = robinhood)      
        ben_mark=ben_mark.rename(columns ={"Close":bench})
        ben_mark[bench]=ben_mark[bench].astype(float)
        
    elif interval == "minute":
        ben_mark = get_price_data([bench],"self_minute",start_date = datetime.now()-timedelta(days=past_days),robinhood = robinhood)
        ben_mark=ben_mark.rename(columns ={"Close":bench})
        ben_mark[bench]=ben_mark[bench].astype(float)
    ben_mark[bench + "_bench_re"] = log(ben_mark[bench]/ben_mark[bench].shift(1))
    #print ben_mark[bench + "_bench_re"]
    for i in list(ticker_list):

        new=[]
        ticker = str(i)
        
        try:
            if interval =="day":
                #stock = da.DataReader(str(ticker),"yahoo",datetime.now()-timedelta(days=90),datetime.now())
                stock= get_price_data([ticker],"realtimeday",start_date = datetime.now()-timedelta(days=past_days),robinhood = robinhood)
                stock = stock.rename(columns = {"Close":ticker})
                stock[ticker] = stock[ticker].astype(float)
            elif interval == "minute":
                stock= get_price_data([ticker],"self_minute",start_date = datetime.now()-timedelta(days=past_days),robinhood = robinhood)
                stock=stock.rename(columns ={"Close":ticker})
                stock[ticker] = stock[ticker].astype(float)
        except:
            print (ticker+" ticker maybe wrong. Error in getting data")
            betas.append(np.NaN)
            continue

        # get return and put them in a new dataframe
        
        stock[ticker + "_stock_re"] = log(stock[ticker]/stock[ticker].shift(1))
        #new = pd.concat([ben_mark,stock],axis =1)
        new = pd.DataFrame({bench:ben_mark[bench],bench + "_bench_re":ben_mark[bench + "_bench_re"],ticker:stock[ticker],ticker + "_stock_re":stock[ticker + "_stock_re"]})
        #new = new[[bench,bench + "_bench_re",ticker, ticker + "_bench_re"]]
        new = new.dropna()
        
        #calculate beta using covariance matrix
        print ("Bench first")
        covmat = np.cov(new[bench+ "_bench_re"],new[ticker+ "_stock_re"])
        print covmat
        #beta = covmat[0,1]/  np.sqrt(covmat[1,1]*covmat[0,0])
        beta = covmat[0,1]/ covmat[0,0]
        volotity = sqrt(covmat[1,1])
        betas.append(beta)
        volos.append(volotity)
    betas = pd.DataFrame(betas)
    betas.index = ticker_list
    betas.columns=["Beta"]
    return betas, covmat, volos

class get_robinhood:

    my_trader = Robinhood()

    # Placing buy orders (Robinhood.place_buy_order)
    # Placing sell order (Robinhood.place_sell_order)
    # Quote information (Robinhood.quote_data)
    # User portfolio data (Robinhood.portfolios)
    # User positions data (Robinhood.positions)
    # Examples:
    # stock_instrument = my_trader.instruments("GEVO")[0]
    # quote_info = my_trader.quote_data("GEVO")
    # buy_order = my_trader.place_buy_order(stock_instrument, 1)
    # sell_order = my_trader.place_sell_order(stock_instrument, 1)
    def get_option_positions(self):
        op_position = pd.DataFrame()

        url = 'https://api.robinhood.com/options/positions/'

        try:
            data = self.my_trader.session.get(url)

            results = data.json()["results"]

            results = pd.DataFrame(results)

            results.quantity=results.quantity.astype(float)

            results = results[results.quantity>0]

            results["real_id"] = results.option.apply(lambda x: x.split("/")[-2])

            results = results[["average_price","chain_symbol","quantity","real_id","updated_at","pending_expiration_quantity"]]


            for i in range(len(results)):

                get = self.my_trader.get_option_market_data(results.iloc[i]["real_id"])
                op_position= op_position.append(get,ignore_index=True)

            op_position["real_id"] = op_position.instrument.apply(lambda x: x.split("/")[-2])

            results = results.set_index("real_id")    
            op_position= op_position.set_index("real_id")
            op_position = op_position[["ask_price","bid_price","mark_price","chance_of_profit_long","chance_of_profit_short","delta","gamma","implied_volatility","previous_close_date"]]
            results = results.join(op_position)
    #         results.average_price = float(results.average_price)/100
            results = results.reset_index()
            results = results.drop("real_id",axis =1)
            return results
        
        
        except Exception as e:
            print(e)
            return pd.DataFrame()

    
    
    def get_universe(self):
        universe = all_stock_list()

#         universe=universe[universe.exchange.apply(lambda x: x.upper() in ["NASDAQ", "NYSE","NEW YORK STOCK EXCHANGE"])]
        universe=universe[universe.exchange.apply(lambda x: "NASDAQ" in x.upper() or "NYSE" in x.upper()  or "NEW YORK STOCK EXCHANGE" in x.upper())]

        return universe
        # must inclue Stock.xlsx in the dir
#         self.universe=pd.read_csv(directory + 'Stock.csv',header=0)
#         self.universe.columns.astype(str)
#         return self.universe['Ticker']



    #Setup


    #Get stock information
    #Note: Sometimes more than one instrument may be returned for a given stock symbol

    #login
    def login(self,username,password):
        #username=str(input("Please input username"))
        #password = str(input("Please input password"))
        self.my_trader.login(username, password)

    def logout(self):
        self.my_trader.logout()


    def get_instrument(self,stock):


        profile = self.my_trader.instruments(stock)
        #profile = DataFrame(profile[0])
        profile = DataFrame(profile[0],index=[stock])


        return profile

    def get_fundamentals(self,stock):

        fundamentals = self.my_trader.get_fundamentals(stock)
        fundamentals = DataFrame(fundamentals,index=[stock])
        return fundamentals


    def get_stock_data(self,stock):

        quote = self.my_trader.quote_data(stock)

        quote = DataFrame(quote,index=[stock])

        return quote    

    def get_last_price(self,stock):

        quote = self.my_trader.quote_data(stock)

        quote = DataFrame(quote,index=[stock])

        return quote['last_trade_price'].astype(float)[0]

    def get_ask_price(self,stock):

        quote = self.my_trader.quote_data(stock)

        quote = pd.DataFrame(quote,index=[stock])

        return quote['ask_price'].astype(float)[0]

    def get_bid_price(self,stock):

        quote = self.my_trader.quote_data(stock)

        quote = DataFrame(quote,index=[stock])

        return quote['bid_price'].astype(float)[0]

    def order_history(self):

        orders = self.my_trader.order_history()
        orders = DataFrame(orders['results']).T
        

        return orders

    def positions_symbol(self):
        data = self.my_trader.positions()
        data = DataFrame(data['results'])
        data = data['instrument']
        out=list()
        
        for i in data:

            out.append(self.my_trader.get_url(i)['symbol'])

        return out

    def istradeable(self,stock):
        profile = self.my_trader.instruments(stock)
   
        if(profile == []):
            return Series(False,[str(stock)])

        profile_temp = DataFrame(profile[0],index=[stock])
        

        if (profile_temp['tradeable'][0]!= False | profile_temp['tradeable'][0] != True):
            i = i +1
            print "Connection may fail ", i

            return Series(False,[str(stock)])

        return profile_temp['tradeable']

    def place_buy(self, ticker,num,price=None,order_type="limit",slippage = 0.05):
        if price ==None:
            price = self.get_last_price(ticker)
            price = round(price * (1+slippage),2)
        
        
        trial = 0
        
            
        for i in self.my_trader.instruments(ticker):
            while trial < 3:
                try:
                    stock_inst = i
                    if stock_inst["symbol"]==ticker:
                        print ("Ticker found in instruments :", ticker)


                        if str(self.my_trader.place_order(stock_inst,num,price,"buy",order=order_type)) == "<Response [201]>":
                            trial = 3
                            time.sleep(5)
                            print ("Trade Success!: " + ticker)
                            return "Trade Success!"

                        else:
                            trial += 1
                            time.sleep(5)
                            print ("Trade Fail: " + ticker)


                    else:
                        trial += 1
                        print ("Ticker not found in instruments")
                except Exception as e:
                    trial += 1
                    print e
                    print ("Trade Fail: " + ticker)
                    pass

    
    
    def place_sell(self, ticker,num,price=None,order_type="limit",slippage = 0.05):
        if price ==None:
            price = self.get_last_price(ticker)
            price = round(price * (1-slippage),2)
        
        trial = 0
        
            
        for i in self.my_trader.instruments(ticker):
            while trial < 3:
                try:
                    stock_inst = i
                    if stock_inst["symbol"]==ticker:
                        print ("Ticker found in instruments :", ticker)


                        if str(self.my_trader.place_order(stock_inst,num,price,"sell",order=order_type)) == "<Response [201]>":
                            trial = 3
                            time.sleep(5)
                            print ("Trade Success!: " + ticker)
                            return "Trade Success!"

                        else:
                            trial += 1
                            time.sleep(5)
                            print ("Trade Fail: " + ticker)
                            


                    else:
                        trial += 1
                        print ("Ticker not found in instruments")
                except Exception as e:
                    trial += 1
                    print e
                    print ("Trade Fail: " + ticker)
                    pass
        
        

    def get_my_positions(self):   
        my_positions=[]
        position_quantity = []
        for i in self.my_trader.positions()["results"]:
            if float(i["quantity"])>0:
                position_quantity.append(float(i["quantity"]))
                ticker = self.my_trader.get_url(i["instrument"])
                my_positions.append(ticker["symbol"].encode("ascii"))
                print ticker["symbol"] + " "+ str(i["quantity"])
        return my_positions, position_quantity
    def get_buying_power(self):
        buy = self.my_trader.get_account()["crypto_buying_power"]
        print str(buy)
        return float(buy)

    def get_my_position_beta_minute(self,sv=0.05):

        stocks, quantity =self.get_my_positions()
        quantity = pd.DataFrame(quantity,index = stocks,columns=["Quantity"])
        betas = beta(stocks,interval = "minute",robinhood = self)
        #betas = pd.DataFrame(betas[0])
        data = pd.concat([betas[0],quantity],axis=1)
        data = data.fillna(0)
        data["Last_price"]=np.NaN
        for i in data.index:
            now_price = float(self.my_trader.quote_data(i)["last_trade_price"])
            pre_price = float(self.my_trader.quote_data(i)[u'previous_close'])
            data.loc[data.index == i,"Last_price"]= now_price
            data.loc[data.index == i,"Day_Change"]= (now_price-pre_price)/pre_price
#         data.Last_price = data.Last_price.astype(float)
        data["Volotity"] = betas[2]
        data["Weight"] = data.Last_price * data.Quantity/np.dot(data.Last_price,data.Quantity)
        for i in stocks:
            data.loc[i,"Day_VaR"] = var_normal(i,method="day",sv=sv)
            data.loc[i,"Mins_VaR"] = var_normal(i,method="minute",sv=sv)
        data.Day_VaR = data.Day_VaR * data.Quantity
        data.Mins_VaR = data.Mins_VaR * data.Quantity
        #total_beta = self.get_protfolio(stocks,quantity,"minute")[1]

        #print ("Total beta is " + total_beta)

        print data
        return data

  
    


    def place_buy_bulk_checkup(self, ticker_list, quantity_list,price_list=None , skip_check = False ):
        if skip_check:
            my_positions=[]
        else:
            my_positions = self.get_my_positions()[0]
        if price_list == None:
            for t, q in zip(ticker_list, quantity_list):
                if t not in my_positions:
                    return self.place_buy(t,q)
                     
                    
                        
        else:
            for t, q,p in zip(ticker_list, quantity_list,price_list):
                if t not in my_positions:
                    return self.place_buy(t,q,p)
                      

    def place_sell_bulk_checkup(self, ticker_list, quantity_list,price_list=None):
        my_positions = self.get_my_positions()[0]
        if price_list == None:
            for t, q in zip(ticker_list, quantity_list):
                if t  in my_positions:
                    return self.place_sell(t,q)
                    
        else:
            for t, q,p in zip(ticker_list, quantity_list,price_list):
                if t  in my_positions:
                    return self.place_sell(t,q,p)  
                    
    def get_average_cost(self,symbol):
        pos_list = self.my_trader.positions()["results"]
        target = self.get_instrument(symbol)["url"].values[0]
        tmp = filter(lambda x: x["instrument"] == target, pos_list)
        if len(tmp) == 0:
            try:
                return get_trade_log(symbol).Price.iloc[-1]
            except:
                return 0
        elif tmp[0]["average_buy_price"] != tmp[0]["average_buy_price"] or tmp[0]["average_buy_price"] == None:
            try:
                return get_trade_log(symbol).Price.iloc[-1]
            except:
                return 0
        else:
            return tmp[0]["average_buy_price"]
        

    def get_protfolio(self,tickers,quantity,interval = "day",bench_ticker="SPY",past_days=90):
    
        bench_ticker = "SPY"
        ticker_frame = pd.DataFrame(quantity,index = tickers)
        
        
        bench = get_price_data([bench_ticker],interval,robinhood = self,start_date = datetime.now()-timedelta(days=past_days))
        #bench = bench.set_index("TimeStamp")
        bench = bench[["Close","High","Low","Open"]]
        bench = bench.rename(columns={"Close":str(bench_ticker) + "_Close"})
        bench = bench.rename(columns={"High":str(bench_ticker) + "_High"})
        bench = bench.rename(columns={"Low":str(bench_ticker) + "_Low"})
        bench = bench.rename(columns={"Open":str(bench_ticker) + "_Open"})

        data = pd.DataFrame()

        for i in tickers:
            #temp = da.DataReader(i,"yahoo",datetime.now()-timedelta(days=90),datetime.now())
            temp = get_price_data([i],interval,robinhood = self,start_date = datetime.now()-timedelta(days=past_days))
            #temp = temp.set_index("TimeStamp")
            temp = temp[["Close","High","Low","Open"]]

            temp = temp.rename(columns={"Close":str(i) + "_Close"})
            temp = temp.rename(columns={"High":str(i) + "_High"})
            temp = temp.rename(columns={"Low":str(i) + "_Low"})
            temp = temp.rename(columns={"Open":str(i) + "_Open"})
            data = pd.concat([data,temp],axis = 1)
        
        #    quantity.append(1)
        

        for i, j in zip(data.columns,range(len(data.columns))):
                #j = int(np.ceil(j / 3))
                #print i, j
                j = j/4
                data[i] = data[i] * quantity[j]

        data["Sum_Close"] = data.filter(regex="Close").sum(axis=1)
        data["Sum_High"] = data.filter(regex="High").sum(axis=1)
        data["Sum_Low"] = data.filter(regex="Low").sum(axis=1)
        data["Sum_Open"] = data.filter(regex="Open").sum(axis=1)
        if bench_ticker + "_Close" not in data.columns:
            data = pd.concat([data,bench],axis = 1)
        data = data.astype(float)
        print "Length: ", len(data)
        data = data.dropna()
        print "Length after drop ", len(data)
        #one day trade backtest
        # return data_weighted
        data["Protfolio_return"] = np.log(data.Sum_Close / data.Sum_Close.shift(1))
        data["Bench_rte"] = log(data[str(bench_ticker) + "_Close"] / data[str(bench_ticker) + "_Close"].shift(1))
        #data_weighted["intraday_return_prt"] = (data_weighted.Sum_Close - data_weighted.Sum_Close.shift(1))/data_weighted.Sum_Close.shift(1)
        print "Length: ", len(data)
        data = data.dropna()
        print "Length after drop ", len(data)
        covmat = np.cov(data["Bench_rte"],data["Protfolio_return"])
        #beta = covmat[0,1]/  np.sqrt(covmat[1,1]*covmat[0,0])
        beta = covmat[0,1]/ covmat[0,0]
        volatility = sqrt(covmat[1,1])
        
        
        
        return (data,beta,volatility)

    def get_last_order_ticker(self,date):
        history = self.my_trader.order_history()
        history = pd.DataFrame.from_dict(history["results"])
        for i in history.index:
            history.loc[i, "created_at"] = history.iloc[i].created_at[0:10]
        #recent_dates = list(set(history.created_at))[-1]
        last_order = history.loc[history.created_at==date]
        last_order_ticker =[]
        quantity = []
        for i in range(len(last_order)):
            if last_order.iloc[i].side == "buy" and last_order.iloc[i].executions:
                last_order_ticker.append(self.my_trader.get_url(last_order.iloc[i].instrument)["symbol"])
                quantity.append(last_order.iloc[i].cumulative_quantity)
        print "DONE"
        result = pd.DataFrame( [list(last_order_ticker),quantity]).T
        result.columns = ["Ticker","Quantity"]
        result = result.dropna()
        return result
    def hedge(self,method = "self_minute",hedge_int = "VIXY",target_beta =0.0):
        hedge_int_beta =beta([hedge_int],interval ="minute",robinhood=self)[0].iloc[0][0]
        hedge_int_price = self.get_ask_price(hedge_int)
        stocks, quantity =self.get_my_positions()
        position_beta = self.get_protfolio(stocks, quantity,interval = method)[1]
        position_value = float(self.my_trader.portfolios()["last_core_equity"])
        shares = np.floor(position_value*(target_beta-position_beta)/hedge_int_beta/hedge_int_price)
        clear_output()
        return ("To headge the position beta to " + str(target_beta) + " please trade " + str(shares) + " share of " +str(hedge_int) + "<br>" + "Total Beta is {:1.4f}".format(position_beta),shares)
    
    def hedge_addup(self,interval ="minute",hedge_int = "VIXY",target_beta =0.0):
        hedge_int_beta =beta([hedge_int],interval =interval,robinhood=self)[0].iloc[0][0]
        hedge_int_price = self.get_ask_price(hedge_int)
        stocks, quantity =self.get_my_positions()
        #position_beta = self.get_protfolio(stocks, quantity,interval = "self_minute")[1]
        if interval == "minute":
            position_beta = self.get_my_position_beta_minute()
        else:
            position_beta = self.get_my_position_beta()
        position_beta.loc[:,'Weighted_beta'] = position_beta.Beta * position_beta.Weight
        position_beta = position_beta.Weighted_beta.sum()
        position_value = float(self.my_trader.portfolios()["last_core_equity"])
        shares = np.floor(position_value*(target_beta-position_beta)/hedge_int_beta/hedge_int_price)
        clear_output()
        return ("To headge the position beta to " + str(target_beta) + " please trade " + str(shares) + " share of " +str(hedge_int) + "<br>" + "Total Beta is {:1.4f}".format(position_beta))
        
        #return shares  
        
        

def update_price(method = "day",test = False, interval = 1, freq = 'minutes',robinhood=None,back_day = 30,save_file = True):
    tradeable = pd.DataFrame()
    price = pd.DataFrame()
    my_list = pd.read_csv("/home/ken/notebook/My_Trader2.0/file/cantrade.csv")
   
    if test:
        print "Test mode is on!!"
        my_list =  my_list[0:300]
    
    price = get_price_data(my_list.Ticker, method=method,robinhood = robinhood, back_day=back_day)
    
    #for i in my_list.Ticker:
    #    price =price.append( get_price_data([i], method=method,robinhood = robinhood,back_day=back_day))
    for i in set(price.Ticker):
        tradeable = tradeable.append(price[price.Ticker == i].iloc[-1])
   
    #for i in range(len(my_list.Ticker)): 
    #    try:
    #        tradeable = tradeable.append(get_price_data([my_list.iloc[i].Ticker], method=method,robinhood = robinhood).iloc[-1])
    #        clear_output()
    #    except:
    #        print (str(i) +" error!")
# =============================================================================
    #select universe
    if method == "self_minute" or method == "day":
        tradeable["volume_rank"] = tradeable["averageDailyVolume10Day"].rank(ascending = False)
        tradeable = tradeable.loc[tradeable["Close"]>10]
        tradeable = tradeable.loc[tradeable["volume_rank"]<=500]
    elif method =="minute":
        tradeable["volume_rank"] = tradeable["Volume"].rank(ascending = False)
        tradeable = tradeable.loc[tradeable["Close"]>10]
        tradeable = tradeable.loc[tradeable["volume_rank"]<=500]
# =============================================================================

    tradeable = tradeable.dropna(subset=["volume_rank"])
    #robinhood = get_robinhood()
    error = []
    
    for i in set(price.Ticker):
        if i not in list(tradeable.Ticker):
            price = price[price.Ticker != i]
    
    #tic_list = set(tradeable.index)
    
   
    
    price["High"] = price["High"].astype(float)
    price["Low"] = price["Low"].astype(float)
    price["Close"] = price["Close"].astype(float)
    price["Return"] = price["Return"].astype(float)
    #price["Return"] = np.log(price["Close"]/price["Close"].shift(-1))
    #price["Return"] = (price["Close"] - price["Close"].shift(-1)) /price["Close"].shift(-1)
    
    price = price.dropna(subset = ["High","Low","Close","Volume","Ticker","TimeStamp"])
    
    
    industry_sector_earnings = pd.read_csv("/home/ken/notebook/My_Trader2.0/file/my_universe_industry_sector_marketcap_earnings.csv")
    #earnings = pd.read_csv("my_universe_earnings.csv")

    #industry_sector_earnings = industry_sector_earnings.dropna()

    
        

    for i in list(set(price.Ticker)):

        #print price .loc[price.Ticker==i]
        #price.groupby('Ticker').get_group(list(set(price.Ticker))[i])
        price.loc[price.Ticker==i,"ADX"]= ta.ADX(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
        price.loc[price.Ticker==i,"ADXR"]= ta.ADXR(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
        price.loc[price.Ticker==i,"APO"]= ta.APO(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, matype=0)
        price.loc[price.Ticker==i,"AROONOSC"]= ta.AROONOSC(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
        price.loc[price.Ticker==i,"CCI"]= ta.CCI(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Low.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
        price.loc[price.Ticker==i,"MFI"]= ta.MFI(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, price.loc[price.Ticker==i].Volume.values.astype(float),timeperiod=14)
        price.loc[price.Ticker==i,"MACD"], price.loc[price.Ticker==i,"MACD_signal"], price.loc[price.Ticker==i,"MACD_hist"] = ta.MACD(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, signalperiod=9)
        price.loc[price.Ticker==i,"ROCP"]= ta.ROCP(price.loc[price.Ticker==i].Close.values, timeperiod=10)
        #price.loc[price.Ticker==i,"ROCR100"]= ta.ROCR100(price.loc[price.Ticker==i].Close.values, timeperiod=10)
        price.loc[price.Ticker==i,"RSI"]= ta.RSI(price.loc[price.Ticker==i].Close.values, timeperiod=14)
        price.loc[price.Ticker==i,"MA_fast"] = price.loc[price.Ticker==i].Close.rolling(10).mean()
        price.loc[price.Ticker==i,"MA_slow"] = price.loc[price.Ticker==i].Close.rolling(30).mean()

        print "\nDone:", i
    
    final_update = pd.DataFrame()
    
    for i in list(set(price.Ticker)):

        final_update = final_update.append(price.loc[price.Ticker==i].iloc[-1])

    price = 0 
    
    final_update["Industry"] = np.NaN
    final_update["Sector"] = np.NaN
    final_update["Earnings_date"] = np.NaN
    final_update["Market_cap"] = np.NaN
    final_update["Industry_weight"] = np.NaN
    
    for i in list(set(final_update.Ticker)):
        try:
            final_update.loc[final_update.Ticker==i,"Industry"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Industry"].values[0]
            final_update.loc[final_update.Ticker==i,"Sector"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Sector"].values[0]
            final_update.loc[final_update.Ticker==i,"Earnings_date"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Earnings_date"].values[0]
            final_update.loc[final_update.Ticker==i,"Market_cap"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Market_cap"].values[0]
        except:

            print "nan occorded"

    

    #final_update.to_csv("final"+str(price.loc[price.Ticker==i][-1]["Date"])+".csv")


    #get industrial makcap_weight

    for ind in set(final_update.Industry):
        for tic in set(final_update.loc[final_update.Industry==ind].Ticker):
            final_update.loc[final_update.Ticker==tic,'Industry_weight']=final_update.loc[final_update.Ticker==tic,"Market_cap"] / final_update.loc[final_update.Industry==ind,"Market_cap"].sum()


    #final_update = final_update[['Ticker','TimeStamp', 'Open', 'High', 'Low', 'Close', 'Volume',
    #        'Return','ADXR','AROONOSC','APO','CCI','MACD', 'MACD_hist',
    #       'MACD_signal','MFI','ROCP','RSI','Industry','Sector']]
    final_update = final_update[['Ticker','TimeStamp', 'Open', 'High', 'Low', 'Close', 'Volume',
            'Return','ADXR','AROONOSC','APO','CCI','MACD', 'MACD_hist',
           'MACD_signal','MFI','ROCP','RSI','Industry','Sector','Market_cap','Industry_weight','Earnings_date']]



    final_update =final_update.set_index("Ticker")

    #final_update= final_update.dropna()

    

    # Technical points rule

    final_update["Technical_points"]=0
    final_update["Signals"] = ""
    for i in final_update.index:
        if final_update.loc[i].ADXR >= final_update.loc[final_update.Sector==final_update.loc[i].Sector].max().ADXR:
            final_update.loc[i,'Technical_points'] += 1
            final_update.loc[i,'Signals'] += "ADXR "
        if final_update.loc[i].APO >0:
            final_update.loc[i,'Technical_points'] += 1
            final_update.loc[i,'Signals'] += "APO "
        if final_update.loc[i].AROONOSC >= final_update.loc[final_update.Sector==final_update.loc[i].Sector].max().AROONOSC:
            final_update.loc[i,'Technical_points'] += 1
            final_update.loc[i,'Signals'] += "AROONOSC "
        if final_update.loc[i].CCI <-100:
            final_update.loc[i,'Technical_points'] += 1
            final_update.loc[i,'Signals'] += "CCI "
        if final_update.loc[i].MACD > final_update.loc[i].MACD_signal:
            final_update.loc[i,'Technical_points'] += 1
            final_update.loc[i,'Signals'] += "MACD "
        if final_update.loc[i].MFI <20:
            final_update.loc[i,'Technical_points'] += 1
            final_update.loc[i,'Signals'] += "MFI "
        if final_update.loc[i].ROCP >0:
            final_update.loc[i,'Technical_points'] += 1
            final_update.loc[i,'Signals'] += "ROCP "
        if final_update.loc[i].RSI < 30:
            final_update.loc[i,'Technical_points'] += 1
            final_update.loc[i,'Signals'] += "RSI "
        

        print "Technical_points done: ", i
    
    #if test:
    #    return final_update

    
    final_update= final_update.dropna()
    
    if len(final_update) <7:
        send_email("Result length error")
        
    
    #if save_file:
    #    final_update.to_csv(directory + save_file_name)

    #***************************************

    # get result

    #***************************************
     
    result = final_update.sort_values("Technical_points").iloc[-7:]
    result5 = result[result.Technical_points > 4]
    
    
    #-------------------------------
    #meanrevertion test
    
    #result = result.reset_index()
    #try:
    #    result["MR"] = result.Ticker.apply(lambda x: mean_reversion(x.encode("ascii"),"minute",robinhood=robinhood))
    #except Exception as e:
    #    print (e)
    
    
    #-------------------------------
    
    
    
    #-------------------------------
    #VaR
    result = result.reset_index()
    try:
        result["VaR_50day"] = result.Ticker.apply(lambda x: var_normal(x.encode("ascii"), method="day"))
    except Exception as e:
        print (e)
    
    
    #-------------------------------
    
    #result = final_update.sort_values("Technical_points")

    #result.to_csv( directory + save_file_name + "_1st"  +str(test) + str(result.TimeStamp[0])[0:10].replace(":","-")+".csv")
    
    html = result.style.set_table_attributes('border="1" class="dataframe table table-hover table-bordered"')
    
    html = html.render()
    
    send_email(html)
    
    return result5


#     '''


#     industry_sector_earnings = pd.read_csv("file/my_universe_industry_sector_marketcap_earnings.csv")
#     #earnings = pd.read_csv("my_universe_earnings.csv")

#     industry_sector_earnings = industry_sector_earnings.dropna()



#     for i in list(set(price.Ticker)):

#         #print price .loc[price.Ticker==i]

#         #price.groupby('Ticker').get_group(list(set(price.Ticker))[i])
#         #price.loc[price.Ticker==i,"ADX"]= ta.ADX(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"ADXR"]= ta.ADXR(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"APO"]= ta.APO(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, matype=0)
#         price.loc[price.Ticker==i,"AROONOSC"]= ta.AROONOSC(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"CCI"]= ta.CCI(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Low.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"MFI"]= ta.MFI(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, price.loc[price.Ticker==i].loc[price.Ticker==i].Volume.values.astype(float),timeperiod=14)
#         price.loc[price.Ticker==i,"MACD"], price.loc[price.Ticker==i,"MACD_signal"], price.loc[price.Ticker==i,"MACD_hist"] = ta.MACD(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, signalperiod=9)
#         price.loc[price.Ticker==i,"ROCP"]= ta.ROCP(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         #price.loc[price.Ticker==i,"ROCR100"]= ta.ROCR100(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         price.loc[price.Ticker==i,"RSI"]= ta.RSI(price.loc[price.Ticker==i].Close.values, timeperiod=14)

#         print "\nDone:", i



#     final_update = pd.DataFrame()

#     for i in list(set(price.Ticker)):

#         final_update = final_update.append(price.loc[price.Ticker==i].iloc[-1])


#     final_update["Industry"] = np.NaN
#     final_update["Sector"] = np.NaN
#     final_update["Earnings_date"] = np.NaN
#     final_update["Market_cap"] = np.NaN
#     final_update["Industry_weight"] = np.NaN

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Industry"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Industry"].values[0]
    #     except:

    #         print "nan occorded"

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Sector"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Sector"].values[0]
    #     except:
#     '''


#     industry_sector_earnings = pd.read_csv("file/my_universe_industry_sector_marketcap_earnings.csv")
#     #earnings = pd.read_csv("my_universe_earnings.csv")

#     industry_sector_earnings = industry_sector_earnings.dropna()



#     for i in list(set(price.Ticker)):

#         #print price .loc[price.Ticker==i]

#         #price.groupby('Ticker').get_group(list(set(price.Ticker))[i])
#         #price.loc[price.Ticker==i,"ADX"]= ta.ADX(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"ADXR"]= ta.ADXR(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"APO"]= ta.APO(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, matype=0)
#         price.loc[price.Ticker==i,"AROONOSC"]= ta.AROONOSC(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"CCI"]= ta.CCI(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Low.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"MFI"]= ta.MFI(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, price.loc[price.Ticker==i].loc[price.Ticker==i].Volume.values.astype(float),timeperiod=14)
#         price.loc[price.Ticker==i,"MACD"], price.loc[price.Ticker==i,"MACD_signal"], price.loc[price.Ticker==i,"MACD_hist"] = ta.MACD(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, signalperiod=9)
#         price.loc[price.Ticker==i,"ROCP"]= ta.ROCP(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         #price.loc[price.Ticker==i,"ROCR100"]= ta.ROCR100(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         price.loc[price.Ticker==i,"RSI"]= ta.RSI(price.loc[price.Ticker==i].Close.values, timeperiod=14)

#         print "\nDone:", i



#     final_update = pd.DataFrame()

#     for i in list(set(price.Ticker)):

#         final_update = final_update.append(price.loc[price.Ticker==i].iloc[-1])


#     final_update["Industry"] = np.NaN
#     final_update["Sector"] = np.NaN
#     final_update["Earnings_date"] = np.NaN
#     final_update["Market_cap"] = np.NaN
#     final_update["Industry_weight"] = np.NaN

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Industry"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Industry"].values[0]
    #     except:

    #         print "nan occorded"

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Sector"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Sector"].values[0]
    #     except:
#     '''


#     industry_sector_earnings = pd.read_csv("file/my_universe_industry_sector_marketcap_earnings.csv")
#     #earnings = pd.read_csv("my_universe_earnings.csv")

#     industry_sector_earnings = industry_sector_earnings.dropna()



#     for i in list(set(price.Ticker)):

#         #print price .loc[price.Ticker==i]

#         #price.groupby('Ticker').get_group(list(set(price.Ticker))[i])
#         #price.loc[price.Ticker==i,"ADX"]= ta.ADX(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"ADXR"]= ta.ADXR(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"APO"]= ta.APO(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, matype=0)
#         price.loc[price.Ticker==i,"AROONOSC"]= ta.AROONOSC(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"CCI"]= ta.CCI(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Low.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"MFI"]= ta.MFI(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, price.loc[price.Ticker==i].loc[price.Ticker==i].Volume.values.astype(float),timeperiod=14)
#         price.loc[price.Ticker==i,"MACD"], price.loc[price.Ticker==i,"MACD_signal"], price.loc[price.Ticker==i,"MACD_hist"] = ta.MACD(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, signalperiod=9)
#         price.loc[price.Ticker==i,"ROCP"]= ta.ROCP(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         #price.loc[price.Ticker==i,"ROCR100"]= ta.ROCR100(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         price.loc[price.Ticker==i,"RSI"]= ta.RSI(price.loc[price.Ticker==i].Close.values, timeperiod=14)

#         print "\nDone:", i



#     final_update = pd.DataFrame()

#     for i in list(set(price.Ticker)):

#         final_update = final_update.append(price.loc[price.Ticker==i].iloc[-1])


#     final_update["Industry"] = np.NaN
#     final_update["Sector"] = np.NaN
#     final_update["Earnings_date"] = np.NaN
#     final_update["Market_cap"] = np.NaN
#     final_update["Industry_weight"] = np.NaN

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Industry"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Industry"].values[0]
    #     except:

    #         print "nan occorded"

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Sector"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Sector"].values[0]
    #     except:
#     '''


#     industry_sector_earnings = pd.read_csv("file/my_universe_industry_sector_marketcap_earnings.csv")
#     #earnings = pd.read_csv("my_universe_earnings.csv")

#     industry_sector_earnings = industry_sector_earnings.dropna()



#     for i in list(set(price.Ticker)):

#         #print price .loc[price.Ticker==i]

#         #price.groupby('Ticker').get_group(list(set(price.Ticker))[i])
#         #price.loc[price.Ticker==i,"ADX"]= ta.ADX(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"ADXR"]= ta.ADXR(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"APO"]= ta.APO(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, matype=0)
#         price.loc[price.Ticker==i,"AROONOSC"]= ta.AROONOSC(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"CCI"]= ta.CCI(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Low.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"MFI"]= ta.MFI(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, price.loc[price.Ticker==i].loc[price.Ticker==i].Volume.values.astype(float),timeperiod=14)
#         price.loc[price.Ticker==i,"MACD"], price.loc[price.Ticker==i,"MACD_signal"], price.loc[price.Ticker==i,"MACD_hist"] = ta.MACD(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, signalperiod=9)
#         price.loc[price.Ticker==i,"ROCP"]= ta.ROCP(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         #price.loc[price.Ticker==i,"ROCR100"]= ta.ROCR100(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         price.loc[price.Ticker==i,"RSI"]= ta.RSI(price.loc[price.Ticker==i].Close.values, timeperiod=14)

#         print "\nDone:", i



#     final_update = pd.DataFrame()

#     for i in list(set(price.Ticker)):

#         final_update = final_update.append(price.loc[price.Ticker==i].iloc[-1])


#     final_update["Industry"] = np.NaN
#     final_update["Sector"] = np.NaN
#     final_update["Earnings_date"] = np.NaN
#     final_update["Market_cap"] = np.NaN
#     final_update["Industry_weight"] = np.NaN

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Industry"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Industry"].values[0]
    #     except:

    #         print "nan occorded"

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Sector"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Sector"].values[0]
    #     except:
#     '''


#     industry_sector_earnings = pd.read_csv("file/my_universe_industry_sector_marketcap_earnings.csv")
#     #earnings = pd.read_csv("my_universe_earnings.csv")

#     industry_sector_earnings = industry_sector_earnings.dropna()



#     for i in list(set(price.Ticker)):

#         #print price .loc[price.Ticker==i]

#         #price.groupby('Ticker').get_group(list(set(price.Ticker))[i])
#         #price.loc[price.Ticker==i,"ADX"]= ta.ADX(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"ADXR"]= ta.ADXR(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"APO"]= ta.APO(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, matype=0)
#         price.loc[price.Ticker==i,"AROONOSC"]= ta.AROONOSC(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"CCI"]= ta.CCI(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Low.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"MFI"]= ta.MFI(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, price.loc[price.Ticker==i].loc[price.Ticker==i].Volume.values.astype(float),timeperiod=14)
#         price.loc[price.Ticker==i,"MACD"], price.loc[price.Ticker==i,"MACD_signal"], price.loc[price.Ticker==i,"MACD_hist"] = ta.MACD(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, signalperiod=9)
#         price.loc[price.Ticker==i,"ROCP"]= ta.ROCP(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         #price.loc[price.Ticker==i,"ROCR100"]= ta.ROCR100(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         price.loc[price.Ticker==i,"RSI"]= ta.RSI(price.loc[price.Ticker==i].Close.values, timeperiod=14)

#         print "\nDone:", i



#     final_update = pd.DataFrame()

#     for i in list(set(price.Ticker)):

#         final_update = final_update.append(price.loc[price.Ticker==i].iloc[-1])


#     final_update["Industry"] = np.NaN
#     final_update["Sector"] = np.NaN
#     final_update["Earnings_date"] = np.NaN
#     final_update["Market_cap"] = np.NaN
#     final_update["Industry_weight"] = np.NaN

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Industry"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Industry"].values[0]
    #     except:

    #         print "nan occorded"

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Sector"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Sector"].values[0]
    #     except:

def robingateway():
    

   
    my_p = readgateway(3)
    robinhood = get_robinhood()

    robinhood.login("lgyhz1234@gmail.com", my_p)
    return robinhood


#     '''


#     industry_sector_earnings = pd.read_csv("file/my_universe_industry_sector_marketcap_earnings.csv")
#     #earnings = pd.read_csv("my_universe_earnings.csv")

#     industry_sector_earnings = industry_sector_earnings.dropna()



#     for i in list(set(price.Ticker)):

#         #print price .loc[price.Ticker==i]

#         #price.groupby('Ticker').get_group(list(set(price.Ticker))[i])
#         #price.loc[price.Ticker==i,"ADX"]= ta.ADX(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"ADXR"]= ta.ADXR(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"APO"]= ta.APO(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, matype=0)
#         price.loc[price.Ticker==i,"AROONOSC"]= ta.AROONOSC(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"CCI"]= ta.CCI(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Low.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"MFI"]= ta.MFI(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, price.loc[price.Ticker==i].loc[price.Ticker==i].Volume.values.astype(float),timeperiod=14)
#         price.loc[price.Ticker==i,"MACD"], price.loc[price.Ticker==i,"MACD_signal"], price.loc[price.Ticker==i,"MACD_hist"] = ta.MACD(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, signalperiod=9)
#         price.loc[price.Ticker==i,"ROCP"]= ta.ROCP(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         #price.loc[price.Ticker==i,"ROCR100"]= ta.ROCR100(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         price.loc[price.Ticker==i,"RSI"]= ta.RSI(price.loc[price.Ticker==i].Close.values, timeperiod=14)

#         print "\nDone:", i



#     final_update = pd.DataFrame()

#     for i in list(set(price.Ticker)):

#         final_update = final_update.append(price.loc[price.Ticker==i].iloc[-1])


#     final_update["Industry"] = np.NaN
#     final_update["Sector"] = np.NaN
#     final_update["Earnings_date"] = np.NaN
#     final_update["Market_cap"] = np.NaN
#     final_update["Industry_weight"] = np.NaN

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Industry"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Industry"].values[0]
    #     except:

    #         print "nan occorded"

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Sector"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Sector"].values[0]
    #     except:
#     '''


#     industry_sector_earnings = pd.read_csv("file/my_universe_industry_sector_marketcap_earnings.csv")
#     #earnings = pd.read_csv("my_universe_earnings.csv")

#     industry_sector_earnings = industry_sector_earnings.dropna()



#     for i in list(set(price.Ticker)):

#         #print price .loc[price.Ticker==i]

#         #price.groupby('Ticker').get_group(list(set(price.Ticker))[i])
#         #price.loc[price.Ticker==i,"ADX"]= ta.ADX(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"ADXR"]= ta.ADXR(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"APO"]= ta.APO(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, matype=0)
#         price.loc[price.Ticker==i,"AROONOSC"]= ta.AROONOSC(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"CCI"]= ta.CCI(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Low.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"MFI"]= ta.MFI(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, price.loc[price.Ticker==i].loc[price.Ticker==i].Volume.values.astype(float),timeperiod=14)
#         price.loc[price.Ticker==i,"MACD"], price.loc[price.Ticker==i,"MACD_signal"], price.loc[price.Ticker==i,"MACD_hist"] = ta.MACD(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, signalperiod=9)
#         price.loc[price.Ticker==i,"ROCP"]= ta.ROCP(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         #price.loc[price.Ticker==i,"ROCR100"]= ta.ROCR100(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         price.loc[price.Ticker==i,"RSI"]= ta.RSI(price.loc[price.Ticker==i].Close.values, timeperiod=14)

#         print "\nDone:", i



#     final_update = pd.DataFrame()

#     for i in list(set(price.Ticker)):

#         final_update = final_update.append(price.loc[price.Ticker==i].iloc[-1])


#     final_update["Industry"] = np.NaN
#     final_update["Sector"] = np.NaN
#     final_update["Earnings_date"] = np.NaN
#     final_update["Market_cap"] = np.NaN
#     final_update["Industry_weight"] = np.NaN

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Industry"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Industry"].values[0]
    #     except:

    #         print "nan occorded"

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Sector"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Sector"].values[0]
    #     except:
#     '''


#     industry_sector_earnings = pd.read_csv("file/my_universe_industry_sector_marketcap_earnings.csv")
#     #earnings = pd.read_csv("my_universe_earnings.csv")

#     industry_sector_earnings = industry_sector_earnings.dropna()



#     for i in list(set(price.Ticker)):

#         #print price .loc[price.Ticker==i]

#         #price.groupby('Ticker').get_group(list(set(price.Ticker))[i])
#         #price.loc[price.Ticker==i,"ADX"]= ta.ADX(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"ADXR"]= ta.ADXR(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"APO"]= ta.APO(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, matype=0)
#         price.loc[price.Ticker==i,"AROONOSC"]= ta.AROONOSC(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"CCI"]= ta.CCI(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Low.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"MFI"]= ta.MFI(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, price.loc[price.Ticker==i].loc[price.Ticker==i].Volume.values.astype(float),timeperiod=14)
#         price.loc[price.Ticker==i,"MACD"], price.loc[price.Ticker==i,"MACD_signal"], price.loc[price.Ticker==i,"MACD_hist"] = ta.MACD(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, signalperiod=9)
#         price.loc[price.Ticker==i,"ROCP"]= ta.ROCP(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         #price.loc[price.Ticker==i,"ROCR100"]= ta.ROCR100(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         price.loc[price.Ticker==i,"RSI"]= ta.RSI(price.loc[price.Ticker==i].Close.values, timeperiod=14)

#         print "\nDone:", i



#     final_update = pd.DataFrame()

#     for i in list(set(price.Ticker)):

#         final_update = final_update.append(price.loc[price.Ticker==i].iloc[-1])


#     final_update["Industry"] = np.NaN
#     final_update["Sector"] = np.NaN
#     final_update["Earnings_date"] = np.NaN
#     final_update["Market_cap"] = np.NaN
#     final_update["Industry_weight"] = np.NaN

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Industry"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Industry"].values[0]
    #     except:

    #         print "nan occorded"

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Sector"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Sector"].values[0]
    #     except:
#     '''


#     industry_sector_earnings = pd.read_csv("file/my_universe_industry_sector_marketcap_earnings.csv")
#     #earnings = pd.read_csv("my_universe_earnings.csv")

#     industry_sector_earnings = industry_sector_earnings.dropna()



#     for i in list(set(price.Ticker)):

#         #print price .loc[price.Ticker==i]

#         #price.groupby('Ticker').get_group(list(set(price.Ticker))[i])
#         #price.loc[price.Ticker==i,"ADX"]= ta.ADX(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"ADXR"]= ta.ADXR(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"APO"]= ta.APO(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, matype=0)
#         price.loc[price.Ticker==i,"AROONOSC"]= ta.AROONOSC(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"CCI"]= ta.CCI(price.loc[price.Ticker==i].High.values,price.loc[price.Ticker==i].Low.values,price.loc[price.Ticker==i].Close.values, timeperiod=14)
#         price.loc[price.Ticker==i,"MFI"]= ta.MFI(price.loc[price.Ticker==i].High.values, price.loc[price.Ticker==i].Low.values, price.loc[price.Ticker==i].Close.values, price.loc[price.Ticker==i].loc[price.Ticker==i].Volume.values.astype(float),timeperiod=14)
#         price.loc[price.Ticker==i,"MACD"], price.loc[price.Ticker==i,"MACD_signal"], price.loc[price.Ticker==i,"MACD_hist"] = ta.MACD(price.loc[price.Ticker==i].Close.values, fastperiod=12, slowperiod=26, signalperiod=9)
#         price.loc[price.Ticker==i,"ROCP"]= ta.ROCP(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         #price.loc[price.Ticker==i,"ROCR100"]= ta.ROCR100(price.loc[price.Ticker==i].Close.values, timeperiod=10)
#         price.loc[price.Ticker==i,"RSI"]= ta.RSI(price.loc[price.Ticker==i].Close.values, timeperiod=14)

#         print "\nDone:", i



#     final_update = pd.DataFrame()

#     for i in list(set(price.Ticker)):

#         final_update = final_update.append(price.loc[price.Ticker==i].iloc[-1])


#     final_update["Industry"] = np.NaN
#     final_update["Sector"] = np.NaN
#     final_update["Earnings_date"] = np.NaN
#     final_update["Market_cap"] = np.NaN
#     final_update["Industry_weight"] = np.NaN

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Industry"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Industry"].values[0]
    #     except:

    #         print "nan occorded"

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Sector"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Sector"].values[0]
    #     except:
