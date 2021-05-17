#import needed modules



#from my_trader import *
#from mongo_lib import *
from .my_lib import *
import math




def mean_reversion(stock,method,usr_input = None, robinhood = None,past_days = 90):

    print ("If you use outside data feed please enter random inputs for the first two arguments")
    result = []
    if usr_input is None:
        
        result.append(str(stock))
        mongodb = mongo()
        start_date=datetime.now()-timedelta(days=past_days)
        end_date= datetime.now()
        #***************************************

        # load price data

        #***************************************



        stock = stock.upper()
    
    
    
    
        if robinhood == None and method == "minute":
            print ("Please feed a logined Robinhood Instance")
            return

        st_price = get_price_data([stock],method=method,robinhood=robinhood,start_date=start_date,end_date=end_date)
        
        usr_input = st_price.Close
        #usr_input = usr_input.dropna()
    
   
    
    #st_price = da.DataReader(stock,"yahoo",start_date,end_date)
        #st_price=get_price_data(["aapl"],"realtimeday")


    print ("***********************************************")
    print(("**********" + str(stock) + "*******************"))

    #***************************************

    #Augmented Dickey Fuller test

    #***************************************

    

    cadf = ts.adfuller(usr_input)
    print('Augmented Dickey Fuller test statistic =',cadf[0])
    print('Augmented Dickey Fuller p-value =',cadf[1])
    print('Augmented Dickey Fuller 1%, 5% and 10% test statistics =',cadf[4])

    #cadf[4]['1%'] get 1% statistic value

    '''
    p value should < 0.05

    ADF test statistic is larger than the benchmark in absolute value means we can reject 
    the null hypothesis that there is a unit root in the time series, 
    and is therefore not mean reverting. We should look for a smaller value than benchmark to 
    keep the null hypothesis to confirm mean-reverting

    '''

    if cadf[1] > 0.05:
        cadf_interpret = "Augmented Dickey Fuller: Not significant"

    elif cadf[1] < 0.05 and (cadf[0] < cadf[4]['1%'] or cadf[0] < cadf[4]['10%'] or cadf[0] < cadf[4]['5%']):

        cadf_interpret = "Augmented Dickey Fuller: Not significant"
    else:
        cadf_interpret = "Augmented Dickey Fuller: significant"

    result.append(cadf_interpret)

    #***************************************

    # Calculate Hurst Exponent

    #***************************************
    
    """10/28/2019 changed the calculation of Hurst Exponent"""
    lags = list(range(2,(len(usr_input)-1)/3))


    variancetau = []; tau = []

    for lag in lags: 

        #  Write the different lags into a vector to compute a set of tau or lags
        tau.append(float(lag))

        # Compute the log returns on all days, then compute the variance on the difference in log returns
        # call this pp or the price difference
        pp = subtract(usr_input[lag:], usr_input[:-lag])
        variancetau.append(pp.var())


    matrix = pd.DataFrame()

    matrix.loc[:,'tau'] = tau
    matrix.loc[:,'variancetau'] = variancetau

    matrix.tau = matrix.tau.apply(lambda x: math.log(x,10))
    matrix.variancetau = matrix.variancetau.apply(lambda x: math.log(x,10))
    
    matrix = matrix.dropna()

    # we now have a set of tau or lags and a corresponding set of variances.
    #print tau
    #print variancetau

    # plot the log of those variance against the log of tau and get the slope
    m = polyfit(matrix.tau,matrix.variancetau,1)

    H = m[0] / 2
    print(H)

    
    
    
#     """Returns the Hurst Exponent of the time series vector ts"""
#     # Create the range of lag values
#     lags = range(2, len(usr_input)-1)

#     # Calculate the array of the variances of the lagged differences
#     tau2 = [sqrt(np.std(np.subtract(usr_input[lag:], usr_input[:-lag]))) for lag in lags]

#     # Use a linear fit to estimate the Hurst Exponent
#     lags = [log(i) for i in lags]
#     tau = [log(i) for i in tau2]

#     poly = np.polyfit(lags,tau , 1)

    # Return the Hurst exponent from the polyfit output

#     H= round(poly[0]*2.0,2)
#     # print the result
#     print "Hurst Exponent =", H
#     result.append("Hurst Exponent = " + str(H))

    if H <0.5:
        result.append("Hurst Exponent:mean reverting")
    elif H == 0.5:
        result.append("Hurst Exponent:Geometric Brownian Motion")
    elif H >0.5:
        result.append("Hurst Exponent:trending")

    #H < 0.5  The time series is mean reverting 
    #H = 0.5  The time series is a Geometric Brownian Motion 
    #H > 0.5  The time series is trending




    #***************************************

    # Calculate Half life

    #***************************************


    #Run OLS regression on spread series and lagged version of itself

    df1 = usr_input

    lag = df1.shift(1)
    lag.iloc[0] = lag.iloc[1]
    ret = df1 - lag
    ret.iloc[0] = ret.iloc[1]
    lag2 = sm.add_constant(lag)
    #lag2= lag2.values
    #ret = ret.values
    model = sm.OLS(ret.astype(float),lag2.astype(float))
    res = model.fit()


    halflife = round(-np.log(2) / res.params[1],0)

    print('Halflife = ', halflife)
    print ("\n")

    result.append("Halflife: "+str(halflife)+ " "+str(method))
    print(result)
    print ("***********************************************")
    return     [result,halflife]

def moving_cross_backtest_day(stock, short_ma, long_ma,X = 10):
    #read in data from Yahoo Finance for the relevant ticker

    # You can change to other moving indicator as well
    stock['short_ma'] = np.round(stock['Close'].astype(float).rolling(window=short_ma).mean(),2)
    stock['long_ma'] = np.round(stock['Close'].astype(float).rolling(window=long_ma).mean(),2)

    #create column with moving average spread differential
    stock['short_ma-long_ma'] = stock['short_ma'] - stock['long_ma']

    #set desired number of points as threshold for spread difference and create column containing strategy 'Stance'
    
    stock['Stance'] = np.where(stock['short_ma-long_ma'] > X, 1, 0)
    stock['Stance'] = np.where(stock['short_ma-long_ma'] < X, -1, stock['Stance'])
    stock['Stance'].value_counts()

    #create columns containing daily market log returns and strategy daily log returns
    stock['Market Returns'] = np.log(stock['Close'].astype(float) / stock['Close'].astype(float).shift(1))
    stock['Strategy'] = stock['Market Returns'] * stock['Stance'].shift(1)

    #set strategy starting equity to 1 (i.e. 100%) and generate equity curve
    stock['Strategy Equity'] = stock['Strategy'].cumsum() + 1

    sharpe = annualised_sharpe(stock['Strategy'])

    cum_ret=stock['Strategy'].cumsum().iloc[-1]
    result = [cum_ret,sharpe]
    return result
 
#function to calculate Sharpe Ratio - Risk free rate element excluded for simplicity
def annualised_sharpe(returns, N=252):
    try:
        return np.sqrt(N) * (returns.mean() / returns.std())
    except ZeroDivisionError: 
        return 0





def moving_cross_backtest_10minute(ticker, short_ma, long_ma,X = 10):
    #read in data from Yahoo Finance for the relevant ticker
    
    ticker = ticker.upper()
    stock = robinhood.get_historical(ticker,interval="10minute",span="week")
    # You can change to other moving indicator as well
    stock['short_ma'] = np.round(stock['close_price'].astype(float).rolling(window=short_ma).mean(),2)
    stock['long_ma'] = np.round(stock['close_price'].astype(float).rolling(window=long_ma).mean(),2)

    #create column with moving average spread differential
    stock['short_ma-long_ma'] = stock['short_ma'] - stock['long_ma']

    #set desired number of points as threshold for spread difference and create column containing strategy 'Stance'
    
    stock['Stance'] = np.where(stock['short_ma-long_ma'] > X, 1, 0)
    stock['Stance'] = np.where(stock['short_ma-long_ma'] < X, -1, stock['Stance'])
    stock['Stance'].value_counts()

    #create columns containing daily market log returns and strategy daily log returns
    stock['Market Returns'] = np.log(stock['close_price'].astype(float) / stock['close_price'].astype(float).shift(1))
    stock['Strategy'] = stock['Market Returns'] * stock['Stance'].shift(1)

    #set strategy starting equity to 1 (i.e. 100%) and generate equity curve
    stock['Strategy Equity'] = stock['Strategy'].cumsum() + 1

    sharpe = annualised_sharpe(stock['Strategy'],9828)

    cum_ret=stock['Strategy'].cumsum().iloc[-1]
    result = [cum_ret,sharpe]
    return result

def moving_cross_backtest(ticker, period):
    
    #---------------------------------------------------------------
    period = period.lower()
    if period == "day":
        stock = da.DataReader(ticker,"yahoo","2017-01-01",datetime.now())
        try:
            
            reversion_test = mean_reversion(ticker,"day")
            short_ma = np.linspace(10,10+5*reversion_test[2],20,dtype=int)
            long_ma = np.linspace(60,60+5*reversion_test[2],20,dtype=int)
            results_cum_ret = np.zeros((len(short_ma),len(long_ma)))
            results_sharpe = np.zeros((len(short_ma),len(long_ma)))
        except:
            
            short_ma = np.linspace(10,10+5*20,20,dtype=int)
            long_ma = np.linspace(60,60+20,20,dtype=int)
            results_cum_ret = np.zeros((len(short_ma),len(long_ma)))
            results_sharpe = np.zeros((len(short_ma),len(long_ma)))
            raise "except used, probably cannot convert"
            exit()
        
        for i, shortma in enumerate(short_ma):
            for j, longma in enumerate(long_ma):
                results = moving_cross_backtest_day(stock,shortma,longma)
                results_cum_ret[i,j] = results[0]
                results_sharpe[i,j] = results[1]
        #plt.figure(figsize=(8,8))
        plt.pcolor(short_ma,long_ma,results_cum_ret)
        plt.colorbar()
        plt.show()

    elif period =="minute":
        try:
            
            reversion_test = mean_reversion(ticker,"minute")
            short_ma = np.linspace(10,10+5*reversion_test[2],20,dtype=int)
            long_ma = np.linspace(60,60+5*reversion_test[2],20,dtype=int)
            results_cum_ret = np.zeros((len(short_ma),len(long_ma)))
            results_sharpe = np.zeros((len(short_ma),len(long_ma)))
        except:
            
            short_ma = np.linspace(10,10+5*20,20,dtype=int)
            long_ma = np.linspace(60,60+5*20,20,dtype=int)
            results_cum_ret = np.zeros((len(short_ma),len(long_ma)))
            results_sharpe = np.zeros((len(short_ma),len(long_ma)))
            raise "except used, probably cannot convert"
            exit()
        short_ma = np.linspace(10,10+5*reversion_test[2],20,dtype=int)
        long_ma = np.linspace(60,60+5*reversion_test[2],20,dtype=int)
        results_cum_ret = np.zeros((len(short_ma),len(long_ma)))
        results_sharpe = np.zeros((len(short_ma),len(long_ma)))
        for i, shortma in enumerate(short_ma):
            for j, longma in enumerate(long_ma):
                results = moving_cross_backtest_10minute(stock,shortma,longma)
                results_cum_ret[i,j] = results[0]
                results_sharpe[i,j] = results[1]
        #plt.figure(figsize=(8,8))
        plt.pcolor(short_ma,long_ma,results_cum_ret)
        plt.colorbar()
        plt.show()

def plot_ticker(ticker,method,robinhood,fast_win=10,slow_win=25,past_days=90):
    #stock = da.DataReader(ticker,"yahoo","2017-01-01",datetime.now())
    stock = get_price_data([ticker],method=method,back_day = past_days,robinhood = robinhood)
#     stock.loc[:,"TimeStamp"] = stock.loc[:,"TimeStamp"].apply(lambda x: datetime(x.year,\
#                                                                                  x.month,\
#                                                                                  x.day,\
#                                                                                  x.hour,\
#                                                                                  x.minute)) 

#     stock.loc[:,"TimeStamp_num"] = plt.matplotlib.dates.date2num(stock["TimeStamp"])
#     stock = stock.set_index("TimeStamp")
    stock["mv_fast"]=stock["Close"].rolling(fast_win).mean()
    stock["mv_slow"]=stock["Close"].rolling(slow_win).mean()
#     plt.title(ticker)
    #my_plt = plt.plot(stock[["Adj Close","mv_fast","mv_slow"]])
#     plt.figure(figsize=(20,10))
#     plt.plot_date(stock["TimeStamp"],stock[["Close","mv_fast","mv_slow"]],"b-")
    stock[["Close","mv_fast","mv_slow"]].plot(figsize=(20,8))
    plt.legend(["Close","mv_fast","mv_slow"])
    
    plt.show()


def plot_position(tickers, quantity,method = "day",past_days=90):
    robinhood = robingetway()


    #temp = da.DataReader(tickers[0],"yahoo",datetime.now()-timedelta(days=90),datetime.now())
    temp = get_price_data([tickers[0]],method,datetime.now()-timedelta(days=past_days),datetime.now())

    temp = temp.rename(columns={"Adj Close":str(tickers[0]) + "_Close"})
    temp = temp.rename(columns={"High":str(tickers[0]) + "_High"})
    temp = temp.rename(columns={"Low":str(tickers[0]) + "_Low"})


    data = pd.DataFrame()

    data = pd.concat([data,temp[["TimeStamp",str(tickers[0]) + "_Close",str(tickers[0]) + "_High",str(tickers[0]) + "_Low"]]], axis=1)

    
    for i in tickers[1:]:
        
        #temp = da.DataReader(i,"yahoo",datetime.now()-timedelta(days=90),datetime.now())
        temp = get_price_data([i],method,datetime.now()-timedelta(days=past_days),datetime.now())
        temp = temp.rename(columns={"Adj Close":str(i) + "_Close"})
        temp = temp.rename(columns={"High":str(i) + "_High"})
        temp = temp.rename(columns={"Low":str(i) + "_Low"})


        data = pd.concat([data,temp[["TimeStamp",str(i) + "_Close",str(i) + "_High",str(i) + "_Low"]]], axis=1)
        
        data = data.set_index("TimeStamp")
        
    data_weighted = pd.DataFrame()

    for i, j in zip(data.columns,list(range(len(data.columns)))):
        #j = int(np.ceil(j / 3))
        j = j/3
        data_weighted = pd.concat([data_weighted,data[i] * quantity[j]],axis=1)
    data_weighted["Sum_Close"] = data_weighted.filter(regex="Close").sum(axis=1)
    data_weighted["Sum_High"] = data_weighted.filter(regex="High").sum(axis=1)
    data_weighted["Sum_Low"] = data_weighted.filter(regex="Low").sum(axis=1)
    data_weighted["Sum_Close_MA_F"] = data_weighted.Sum_Close.rolling(5).mean()
    data_weighted["Sum_Close_MA_S"] = data_weighted.Sum_Close.rolling(20).mean()

    data_weighted["STOCH_slowk"], data_weighted["STOCH_slowd"] = ta.STOCHF(data_weighted["Sum_High"].values, data_weighted["Sum_Low"].values, data_weighted["Sum_Close"].values, fastk_period=5, fastd_period=3, fastd_matype=0)
    
    plt.figure(1,figsize = (18,18))
    sub = plt.subplot(211)
    plt.title("Position")
    data_weighted.Sum_Close.plot()
    data_weighted.Sum_Close_MA_F.plot()
    data_weighted.Sum_Close_MA_S.plot()
    plt.legend()
    plt.subplot(212,sharex=sub)
    plt.title("STOCH")
    data_weighted.STOCH_slowd.plot()
    data_weighted.STOCH_slowk.plot()

    plt.show()
    print(data_weighted.head())
    

def get_data_table(tickers,interval,bench_ticker='SPY'):
    if interval  == "day":
        temp = da.DataReader(tickers[0],"yahoo",datetime.now()-timedelta(days=90),datetime.now())
        bench = da.DataReader(bench_ticker,"yahoo",datetime.now()-timedelta(days=90),datetime.now())
        bench = bench.rename(columns={"Adj Close":str(bench_ticker) + "_Close"})
 
        data = pd.DataFrame(index=temp.index)
        temp = temp.rename(columns={"Adj Close":str(tickers[0]) + "_Close"})
        temp = temp.rename(columns={"High":str(tickers[0]) + "_High"})
        temp = temp.rename(columns={"Low":str(tickers[0]) + "_Low"})
        temp = temp.rename(columns={"Open":str(tickers[0]) + "_Open"})
        data = pd.concat([data,temp[[str(tickers[0]) + "_Close",str(tickers[0]) + "_High",str(tickers[0]) + "_Low",str(tickers[0]) + "_Open"]]], axis=1)
    
        for i in tickers[1:]:
            temp = da.DataReader(i,"yahoo",datetime.now()-timedelta(days=90),datetime.now())
            temp = temp.rename(columns={"Adj Close":str(i) + "_Close"})
            temp = temp.rename(columns={"High":str(i) + "_High"})
            temp = temp.rename(columns={"Low":str(i) + "_Low"})
            temp = temp.rename(columns={"Open":str(i) + "_Open"})
            data = pd.concat([data,temp[[str(i) + "_Close",str(i) + "_High",str(i) + "_Low",str(i) + "_Open"]]], axis=1)
    elif interval == "minute":
        temp = robinhood.get_historical(tickers[0],interval="10minute",span = "week")
        bench = robinhood.get_historical(bench,interval="10minute",span = "week")
        bench = bench.index("begin_at")
        temp = temp.index("begin_at")
        bench = bench.rename(columns={"close_price":str(bench_ticker) + "_Close"})
        bench = bench[str(bench_ticker) + "_Close"].astype(float)
        bench["Bench_rte"] = log(bench[str(bench_ticker) + "_Close"]/bench[str(bench_ticker) + "_Close"].shift(-1))
        data = pd.DataFrame(index=temp.index)
        temp = temp.rename(columns={"close_price":str(tickers[0]) + "_Close"})
        temp = temp.rename(columns={"high_price":str(tickers[0]) + "_High"})
        temp = temp.rename(columns={"low_price":str(tickers[0]) + "_Low"})
        temp = temp.rename(columns={"open_price":str(tickers[0]) + "_Open"})
        temp = temp[str(tickers[0]) + "_Close"].astype(float)
        temp = temp[str(tickers[0]) + "_High"].astype(float)
        temp = temp[str(tickers[0]) + "_Low"].astype(float)
        temp = temp[str(tickers[0]) + "_Open"].astype(float)
        data = pd.concat([data,temp[[str(tickers[0]) + "_Close",str(tickers[0]) + "_High",str(tickers[0]) + "_Low",str(tickers[0]) + "_Open"]]], axis=1)
    
        for i in tickers[1:]:
            temp = robinhood.get_historical(i,interval="10minute",span = "week")
            temp = temp.index("begin_at")
            temp = temp.rename(columns={"close_price":str(i) + "_Close"})
            temp = temp.rename(columns={"high_price":str(i) + "_High"})
            temp = temp.rename(columns={"low_price":str(i) + "_Low"})
            temp = temp.rename(columns={"open_price":str(i) + "_Open"})
            temp = temp[str(i) + "_Close"].astype(float)
            temp = temp[str(i) + "_High"].astype(float)
            temp = temp[str(i) + "_Low"].astype(float)
            temp = temp[str(i) + "_Open"].astype(float)
            data = pd.concat([data,temp[[str(i) + "_Close",str(i) + "_High",str(i) + "_Low",str(i) + "_Open"]]], axis=1)
    return data



def pair_trade(stock1, stock2,initial,robinhood,method = "self_minute",window = 3,data_len = 210, continuous = False,trade_on_day_start=False):

    get_succeed = False
    trial = 0
    
    def trade_signal(data_frame):
        size1= np.ceil((initial/(1+data_frame["relative_mv"])/data_frame[stock1+"_close"]))
        size2 =  np.ceil((initial/(1+data_frame["relative_mv"])*data_frame["relative_mv"]/data_frame[stock2+"_close"]))
        if size1 * data_frame[stock1+"_close"] + size2 * data_frame[stock2+"_close"]< initial:
            return 1
        else:
            return 0

    def stock1_trade_share(data_frame,i,initial):
        #i = table.index.get_loc(data_frame.name)
        trade_cash = initial/2
        
        table = data_frame
        data_frame = data_frame.loc[i]
        pos = table.index.get_loc(data_frame.name)
        if data_frame.z_score < data_frame.buy_line and initial >0 :
            size= np.ceil((trade_cash/(1+data_frame["relative_mv"])/data_frame[stock1+"_close"]))
            initial = initial - size * data_frame[stock1+"_close"]
            return size,initial
            
        elif data_frame.z_score > data_frame.sell_line:
            return 0,initial + table[stock1+"_shares"].iloc[pos-1] * data_frame[stock1+"_close"]

        else:
#             i = table.index.get_loc(data_frame.name)
            if pos > 0:
                return table[stock1+"_shares"].iloc[pos-1], initial
            else:
                return 0,initial + table[stock1+"_shares"].iloc[pos-1] * data_frame[stock1+"_close"]

    def stock2_trade_share(data_frame,i,initial):
        #i = table.index.get_loc(data_frame.name)
        trade_cash = initial/2
        table = data_frame
        data_frame = data_frame.loc[i]
        pos = table.index.get_loc(data_frame.name)
        if data_frame.z_score < data_frame.buy_line and initial > 0:
            size =  np.ceil((trade_cash/(1+data_frame["relative_mv"])*data_frame["relative_mv"]/data_frame[stock2+"_close"]))
            initial = initial - size * data_frame[stock2+"_close"]
            return size, initial

        elif data_frame.z_score > data_frame.sell_line:
            return 0,initial + table[stock2+"_shares"].iloc[pos-1] * data_frame[stock2+"_close"]

        else:
#             i = table.index.get_loc(data_frame.name)
            if pos>0:
                return table[stock2+"_shares"].iloc[pos-1] , initial     
            else:
                return 0,initial + table[stock2+"_shares"].iloc[pos-1] * data_frame[stock2+"_close"]

        
    def slope(data_frame,table):
        i = table.index.get_loc(data_frame.name)

        if i < window:
            return np.NaN
        else:
            return stats.linregress(table[stock1+"_log_ret"].iloc[(i-window):i],table[stock2+"_log_ret"].iloc[(i-window):i])[0]



        
    # stock1 = "VIXY"
    # stock2 = "SPY"
    print(("Rolling window = {}, Backtest length= {}".format(window,data_len)))
    
#     while not get_succeed and trial < 1:
#         try:
    price1 = get_price_data([stock1],method = method,back_day = data_len, robinhood = robinhood)
    price2 = get_price_data([stock2],method = method,back_day = data_len, robinhood = robinhood)
    price1 = price1.rename(columns={"Close":stock1+"_close"})
    price2 = price2.rename(columns={"Close":stock2+"_close"})
    price1 = price1.set_index("TimeStamp")
    price2 = price2.set_index("TimeStamp")

    


    price_table = pd.concat([price1[stock1+"_close"],price2[stock2+"_close"]],axis = 1)
    price_table = price_table.fillna(method="bfill")
    price_table[stock1+"_close"] = price_table[stock1+"_close"].astype(float)
    price_table[stock2+"_close"] = price_table[stock2+"_close"].astype(float)
    price_table[stock1+"_log_ret"] = log(price_table[stock1+"_close"] / price_table[stock1+"_close"].shift(1))
    price_table[stock2+"_log_ret"] = log(price_table[stock2+"_close"] / price_table[stock2+"_close"].shift(1))

    price_table[stock1 + "_log_ret_mv"] = price_table[stock1 + "_log_ret"].rolling(window).mean()
    price_table[stock2 + "_log_ret_mv"] = price_table[stock2 + "_log_ret"].rolling(window).mean()

    #price_table["relative"] = price_table[stock1 + "_log_ret_mv"] / price_table[stock2 + "_log_ret_mv"]
    price_table["relative"] = price_table[stock1 + "_log_ret_mv"] / price_table[stock2 + "_log_ret_mv"]

    price_table["relative_mv"] = price_table["relative"].rolling(window, min_periods=window).mean()
    price_table["relative_mv"] = abs(price_table["relative_mv"])


    price_table.relative.fillna(method="bfill")


    price_table[stock1+"_volatility"] = price_table[stock1+"_log_ret"].rolling(window,min_periods=window-5).std()
    price_table[stock2+"_volatility"] = price_table[stock2+"_log_ret"].rolling(window,min_periods=window-5).std()
    #price_table=price_table.fillna(1)


    #price_table["relative_mv"]=price_table[stock1+"_log_ret_mv"]/price_table[stock2+"_log_ret_mv"]
    price_table["z_score"] =( price_table["relative"]-price_table["relative_mv"])/price_table.relative.std()
    price_table.fillna(method="bfill")
    # price_table.fillna(method="bfill")
    # price_table["trade_signal"]=np.NaN


    price_table["cash"] = initial



    price_table["slope"]= price_table.apply(slope,axis=1,args=(price_table,))

    print ("Log return done, 10%")

    def buy_line(data_frame):
        data_frame = data_frame.slope
        if data_frame>0.5:
            return -1.25
        elif data_frame>0.75:
            return -1.75
        elif data_frame:
            return -2.25
        elif data_frame<-0.75:
            return -2.75
        else:
            return -2
    def sell_line(data_frame):
        data_frame = data_frame.slope
        if data_frame>0.5:
            return 1.25
        elif data_frame>0.75:
            return 1.75
        elif data_frame:
            return 2.25
        elif data_frame<-0.75:
            return 2.75
        else:
            return 2

    price_table["buy_line"] = price_table.apply(buy_line,axis=1)
    price_table["sell_line"] = price_table.apply(sell_line,axis=1)

    print ("Signal Line done, 30%")           
    #no short sell




    #set live trade signal and backtest 
    price_table[stock1+"_shares"] = 0 
    price_table[stock2+"_shares"] = 0
#     price_table["trade"] = 0



#     price_table["trade"]=price_table.apply(trade_signal,axis=1)
    
    ###################
    
    # Trade iterator
    
    ##################
    
    for i in price_table.index:

#         size1= np.ceil((initial/(1+price_table.loc[i,"relative_mv"])/price_table.loc[i,stock1+"_close"]))
#         size2 =  np.ceil((initial/(1+price_table.loc[i,"relative_mv"])*price_table.loc[i,"relative_mv"]/price_table.loc[i,stock2+"_close"]))
#         if size1 * price_table.loc[i,stock1+"_close"] + size2 * price_table.loc[i,stock2+"_close"]< initial: 

        price_table.loc[i,stock1+"_shares"],initial = stock1_trade_share(price_table,i,initial)
        price_table.loc[i,stock2+"_shares"],initial = stock2_trade_share(price_table,i,initial)
        price_table.loc[i,"cash"] = initial
        print(initial)
            
        



    print ("Trade singal done, 60%") 
    if trade_on_day_start:
        calculation_log_ret_stock1 =  price_table[stock1+"_log_ret"].shift(1)
        calculation_log_ret_stock2 =  price_table[stock2+"_log_ret"].shift(1)
    else:
        calculation_log_ret_stock1 =  price_table[stock1+"_log_ret"]
        calculation_log_ret_stock2 =  price_table[stock2+"_log_ret"]


    # This calculation show P&L up do date with previouse position.


    ### P/L has problem, please check
    if not continuous:
        price_table[stock1+"_value"] = price_table[stock1+"_shares"]*price_table[stock1+"_close"].shift(1)
        price_table[stock2+"_value"] = price_table[stock2+"_shares"]*price_table[stock2+"_close"].shift(1)
        price_table["p_L"] = price_table[stock1+"_value"].shift(1) *calculation_log_ret_stock1  +  \
        price_table[stock2+"_value"].shift(1) * calculation_log_ret_stock2

    else:    
        price_table[stock1+"_value"] = price_table[stock1+"_suggest_shares"]*price_table[stock1+"_close"].shift(1)
        price_table[stock2+"_value"] = price_table[stock2+"_suggest_shares"]*price_table[stock2+"_close"].shift(1)
        price_table["p_L"] = price_table[stock1+"_value"].shift(1) * calculation_log_ret_stock1 +  \
        price_table[stock2+"_value"].shift(1) * calculation_log_ret_stock2

    print ("Finalizing, 90%")
   
    price_table["total_p_L"] = price_table.p_L.sum()
    return price_table
    exam_data = price_table.iloc[-1]






def pair_trade_short(stock1, stock2, initial, method="day", window=10, data_len=210, continuous=False,
               trade_on_day_start=False):
    robinhood = get_robinhood()
    mongodb = mongo()
    get_succeed = False
    trial = 0

    # stock1 = "VIXY"
    # stock2 = "SPY"
    print(("Rolling window = {}, Backtest length= {}".format(window, data_len)))

    while not get_succeed and trial < 1:
        try:
            

            price1 = get_price_data([stock1],method="day",start_date=datetime.now()-timedelta(days=data_len),end_date=datetime.now()-timedelta(days=0))
            price2 = get_price_data([stock2],method="day",start_date=datetime.now()-timedelta(days=data_len),end_date=datetime.now()-timedelta(days=0))

            price1 = price1.rename(columns={"Adj Close": stock1 + "_close"})
            price2 = price2.rename(columns={"Adj Close": stock2 + "_close"})

    
            price1 = price1.set_index("TimeStamp")
            price2 = price2.set_index("TimeStamp")

            price_table = pd.concat([price1[stock1 + "_close"], price2[stock2 + "_close"]], axis=1)
            price_table = price_table.fillna(price_table.shift(1))
            price_table[stock1 + "_close"] = price_table[stock1 + "_close"].astype(float)
            price_table[stock2 + "_close"] = price_table[stock2 + "_close"].astype(float)
            price_table[stock1 + "_log_ret"] = log(
                price_table[stock1 + "_close"] / price_table[stock1 + "_close"].shift(1))
            price_table[stock2 + "_log_ret"] = log(
                price_table[stock2 + "_close"] / price_table[stock2 + "_close"].shift(1))

            price_table[stock1 + "_log_ret_mv"] = price_table[stock1 + "_log_ret"].rolling(window).mean()
            price_table[stock2 + "_log_ret_mv"] = price_table[stock2 + "_log_ret"].rolling(window).mean()
    #TODO
            price_table["relative"] = price_table[stock1 + "_log_ret_mv"] / price_table[stock2 + "_log_ret_mv"]
            #price_table["relative"] = abs(price_table[stock1 + "_log_ret_mv"] / price_table[stock2 + "_log_ret_mv"])

            price_table["relative_mv"] = price_table["relative"].rolling(window, min_periods=window).mean()
            price_table["relative_mv"] = abs(price_table["relative_mv"])

            price_table.relative.fillna(method="bfill")

    #TODO
            price_table.relative.loc[price_table.relative == -np.inf] = \
                price_table.loc[price_table.relative != -np.inf].sort_values("relative", ascending=True).iloc[0][
                    "relative"]
            # price_table.relative.loc[price_table.relative==np.NaN]=price_table.relative.shift(1)
            price_table.relative.loc[price_table.relative == np.inf] = \
                price_table.loc[price_table.relative != np.inf].sort_values("relative", ascending=False).iloc[0][
                    "relative"]

            price_table[stock1 + "_volatility"] = price_table[stock1 + "_log_ret"].rolling(window,
                                                                                           min_periods=window - 5).std()
            price_table[stock2 + "_volatility"] = price_table[stock2 + "_log_ret"].rolling(window,
                                                                                           min_periods=window - 5).std()
            # price_table=price_table.fillna(1)

            # price_table["relative_mv"]=price_table[stock1+"_log_ret_mv"]/price_table[stock2+"_log_ret_mv"]
            price_table["z_score"] = (price_table["relative"] - price_table["relative_mv"]) / price_table.relative.std()
            price_table.fillna(method="bfill")

            # price_table.fillna(method="bfill")
            # price_table["trade_signal"]=np.NaN

            # for i in range(window-1,len(price_table)):
            #     price_table["slope"].iloc[i] = stats.linregress(price_table[stock1+"_log_ret"]\
            #                                                     .iloc[i-(window-1):i],price_table[stock2+"_log_ret"].iloc[i-(window-1):i])[0]
            # price_table["buy_line"] = np.NaN
            # price_table["sell_line"] = np.NaN

            def slope(data_frame, table):
                i = table.index.get_loc(data_frame.name)

                if i < window:
                    return np.NaN
                else:
                    return stats.linregress(table[stock1 + "_log_ret"].iloc[(i - window):i],
                                            table[stock2 + "_log_ret"].iloc[(i - window):i])[0]

            price_table["slope"] = price_table.apply(slope, axis=1, args=(price_table,))

            print ("Log return done, 10%")

            def buy_line(data_frame):
                data_frame = data_frame.slope
                if data_frame > 0.75:
                    return -2.50
                elif data_frame > 0.5:
                    return -2.25
                elif data_frame < -0.5:
                    return -1.50
                elif data_frame < -0.75:
                	return -1.25
                else:
                    return -2

            def sell_line(data_frame):
                data_frame = data_frame.slope
                if data_frame > 0.75:
                    return 1.50
                elif data_frame > 0.5:
                    return 1.25
                elif data_frame < -0.5:
                    return 2.50
                elif data_frame < -0.75:
                	return 2.25
                else:
                    return -2

            price_table["buy_line"] = price_table.apply(buy_line, axis=1)
            price_table["sell_line"] = price_table.apply(sell_line, axis=1)
            # for i in range(window-1,len(price_table)):
            #     if price_table.slope.iloc[i]>0.5:
            #         price_table["buy_line"].iloc[i] = -1.25
            #     elif price_table.slope.iloc[i]>0.75:
            #         price_table["buy_line"].iloc[i]= -1.75
            #     elif price_table.slope.iloc[i]<-0.5:
            #         price_table["buy_line"].iloc[i] -2.25
            #     elif price_table.slope.iloc[i]<-0.75:
            #         price_table["buy_line"].iloc[i]= -2.75
            #     else:
            #         price_table["buy_line"].iloc[i] = -2

            # price_table["sell_line"] = np.NaN
            # for i in range(window-1,len(price_table)):
            #     if price_table.slope.iloc[i]>0.5:
            #         price_table["sell_line"].iloc[i] = 1.25
            #     elif price_table.slope.iloc[i]>0.75:
            #         price_table["sell_line"].iloc[i] = 1.75
            #     elif price_table.slope.iloc[i]<-0.5:
            #         price_table["sell_line"].iloc[i] = 2.25
            #     elif price_table.slope.iloc[i]<-0.75:
            #         price_table["sell_line"].iloc[i] = 2.75
            #     else:
            #         price_table["sell_line"].iloc[i] = 2
            print ("Signal Line done, 30%")
            # no short sell

            # price_table["cost_per_trade"] =abs( price_table[stock1+"_close"]+price_table[stock2+"_close"]*price_table["relative_mv"])
            
            # price_table[stock1 + "_suggest_shares"] = np.floor(
            #     (initial / (1 + price_table["relative_mv"]) / price_table[stock1 + "_close"]))
            # price_table[stock2 + "_suggest_shares"] = np.floor((initial / (1 + price_table["relative_mv"]) *
            #                                                     price_table["relative_mv"] / price_table[
            #                                                         stock2 + "_close"]))

            # set live trade signal and backtest
            price_table[stock1 + "_shares"] = 0
            price_table[stock2 + "_shares"] = 0
            price_table["trade"] = 0

            def trade_signal(data_frame, table):
                i = table.index.get_loc(data_frame.name)
                if data_frame.z_score < data_frame.buy_line:
                    return 1

                elif data_frame.z_score > data_frame.sell_line:
                    return -1

                elif data_frame.z_score > data_frame.buy_line and data_frame.z_score < data_frame.sell_line:
                	return 0

                else:
                    return table.trade.iloc[i - 1]

            def stock1_trade_share(data_frame, table):
                i = table.index.get_loc(data_frame.name)
                if data_frame.z_score < data_frame.buy_line:
                    return np.ceil((initial / (1 + data_frame["relative_mv"]) / data_frame[stock1 + "_close"]))

                elif data_frame.z_score > data_frame.sell_line:
                    return 0

                else:
                    return table[stock1 + "_shares"].iloc[i - 1]

            def stock2_trade_share(data_frame, table):
                i = table.index.get_loc(data_frame.name)
                if data_frame.z_score < data_frame.buy_line:
                    return np.ceil((initial / (1 + data_frame["relative_mv"]) * data_frame["relative_mv"] / data_frame[stock2 + "_close"]))

                elif data_frame.z_score > data_frame.sell_line:
                    return 0

                else:
                    return table[stock2 + "_shares"].iloc[i - 1]

            price_table["trade"] = price_table.apply(trade_signal, args=(price_table,), axis=1)
            # price_table[stock1 + "_shares"] = price_table.apply(stock1_trade_share, args=(price_table,), axis=1)
            # price_table[stock2 + "_shares"] = price_table.apply(stock2_trade_share, args=(price_table,), axis=1)

            # price_table[stock1 + "_shares"] = np.floor((initial / (1 + price_table["relative_mv"]) / price_table[stock1 + "_close"])) * price_table["trade"]
            # price_table[stock2 + "_shares"] = np.floor((initial / (1 + price_table["relative_mv"]) * price_table["relative_mv"] / price_table[stock2 + "_close"])) * - price_table["trade"]


            # if option trade
            price_table[stock1 + "_shares"] = np.floor((initial / (1 + price_table["relative_mv"]))) * price_table["trade"]
            price_table[stock2 + "_shares"] = np.floor((initial / (1 + price_table["relative_mv"])) * price_table["relative_mv"]) * (- price_table["trade"])

            # for i in range(window-1,len(price_table)):
            #     if price_table.z_score.iloc[i] < price_table.buy_line.iloc[i]:
            #         price_table["trade"].iloc[i] = 1
            #         # price_table["trade_signal"].iloc[i] = 1
            #         price_table[stock1+"_shares"].iloc[i] = price_table[stock1+"_suggest_shares"].iloc[i]
            #         price_table[stock2+"_shares"].iloc[i] = price_table[stock2+"_suggest_shares"].iloc[i]
            #     elif price_table.z_score.iloc[i] > price_table.sell_line.iloc[i]:
            #         price_table["trade"].iloc[i] = 0
            #         # price_table["trade_signal"].iloc[i] = 0
            #         price_table[stock1+"_shares"].iloc[i] = 0
            #         price_table[stock2+"_shares"].iloc[i] = 0
            #     else:
            #         price_table["trade"].iloc[i] = price_table.trade.iloc[i-1]
            #         price_table[stock1+"_shares"].iloc[i] = price_table[stock1+"_shares"].iloc[i-1]
            #         price_table[stock2+"_shares"].iloc[i] = price_table[stock2+"_shares"].iloc[i-1]

            print ("Trade singal done, 60%")


            if trade_on_day_start:
                calculation_log_ret_stock1 = price_table[stock1 + "_log_ret"].shift(1)
                calculation_log_ret_stock2 = price_table[stock2 + "_log_ret"].shift(1)
            else:
                calculation_log_ret_stock1 = price_table[stock1 + "_log_ret"]
                calculation_log_ret_stock2 = price_table[stock2 + "_log_ret"]

            # This calculation show P&L up do date with previouse position.

            if not continuous:
                price_table[stock1 + "_value"] = price_table[stock1 + "_shares"] * price_table[stock1 + "_close"].shift(1)
                price_table[stock2 + "_value"] = price_table[stock2 + "_shares"] * price_table[stock2 + "_close"].shift(1)
                price_table["p_L"] = price_table[stock1 + "_value"].shift(1) * calculation_log_ret_stock1 * abs(price_table.trade.shift(1)) + \
                                     price_table[stock2 + "_value"].shift(1) * calculation_log_ret_stock2 * abs(price_table.trade.shift(1))

            else:
                price_table[stock1 + "_value"] = price_table[stock1 + "_suggest_shares"] * price_table[stock1 + "_close"].shift(1)
                price_table[stock2 + "_value"] = price_table[stock2 + "_suggest_shares"] * price_table[stock2 + "_close"].shift(1)
                price_table["p_L"] = price_table[stock1 + "_value"].shift(1) * calculation_log_ret_stock1 + \
                                     price_table[stock2 + "_value"].shift(1) * calculation_log_ret_stock2

            print ("Finalizing, 90%")
            price_table["rolling_p_L"] = price_table.p_L.rolling(window).sum()
            exam_data = price_table.iloc[-1]

            if (exam_data[stock1 + "_shares"] != exam_data[stock1 + "_shares"]) or \
                    (exam_data[stock2 + "_shares"] != exam_data[stock2 + "_shares"]):
                print ("pair trade function problem")
                print ("Getting the most recent valid input")

                trial += 1
                print(price_table.iloc[-1].name)
                price_table = price_table.iloc[:-1]
                return price_table


            else:
                print ("Done!")
                get_success = True
                return price_table

       	except Exception as e:
            print(e)
            trial += 1
            continue

        
        
 









            
            
##############################

# Momentum Strategy Functions
    
##############################



def momentum_best_day(ticker,robinhood,method = "day"):

    price = get_price_data([ticker], method = method, robinhood=robinhood,back_day=200)
    price = price.set_index("TimeStamp")
#     clear_output()
    result = pd.DataFrame()
    for lookback in range(5,250,5):
        for holding in range(5,250,5):
            shorter = holding if holding <= lookback else lookback
            ret_pre= log(price.Close/price.Close.shift(lookback))

            ret_pre = ret_pre.fillna(0)

            ret_post = log(price.Close.shift(-holding)/price.Close)

            ret_post = ret_post.fillna(0)

            ret_pre= ret_pre.iloc[:-shorter]

            ret_post= ret_post.iloc[shorter:]
            corr,p_value = stats.pearsonr(ret_pre,ret_post)
            result = result.append({"Lookback":lookback,"Holding":holding,"Correlation":corr,"P_Value":p_value},ignore_index=True)
            result.columns = ["Lookback","Holding","Correlation","P_Value"]

    result["P_Rank"] = result["P_Value"].rank()
    result["Cor_Rank"] = result["Correlation"].rank(ascending = False)
    result["Score"] = result["P_Rank"]+result["Cor_Rank"]

    return result.sort_values("Score")







import pyfolio as pf

def momentum_backtest(ticker,lookback,holddays,robinhood,method="realtimeday",analysis = False,):
    lookback = int(lookback)
    holddays = int(holddays)
    
    trade_returns = []
    last_trade = []
    last_price = []
    
    
    class momentumData(bt.feeds.PandasData):
        lines = ('datetime','open','high','low','close','volume','openinterest','log_ret','log_ret_mv','volatility',"Return")
        params = (
                ('datetime', None),
                ('open', "Open"),
                ('high', "High"),
                ('low', "Low"),
                ('close', "Close"),
                ('volume', "Volume"),
                ('openinterest', -1),
                ('log_ret', -1),
            ('log_ret_mv', -1),
            ('volatility', -1),
            ("Return","Return")


            )

    class momentumStrategy(bt.Strategy):

        def __init__(self):

            self.Return = self.datas[0].Return
            self.buyprice = None
            self.buycomm = None
            self.days = 0
            
            
        

#         def log(self, txt, dt=None):
#             dt = dt or self.datas[0].datetime.date(0)
#             print('%s, %s' % (dt.isoformat(), txt))
            
        def log(self, txt, dt=None):
            ''' Logging function fot this strategy'''
            dt = dt or self.data.datetime[0]
            if isinstance(dt, float):
                dt = bt.num2date(dt)
            print('%s, %s' % (dt.isoformat(), txt))
        
        def notify_order(self, order):
            if order.status in [order.Submitted, order.Accepted]:
                # Buy/Sell order submitted/accepted to/by broker - Nothing to do
                self.log('ORDER ACCEPTED/SUBMITTED', dt=order.created.dt)
#                 self.order = order
                

            if order.status in [order.Expired]:
                self.log('BUY EXPIRED')

            elif order.status in [order.Completed]:
                if order.isbuy():
                    self.buyprice = order.executed.price
                    self.log(
                        'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                        (order.executed.price,
                         order.executed.value,
                         order.executed.comm))
                    last_price.append(order.executed.price)

                else:  # Sell
                    self.log('SELL EXECUTED, Price: %.2f, Gain: %.2f, Comm %.2f' %
                             (order.executed.price,
                              order.executed.value,
                              order.executed.comm))
                    self.buyprice = None

            # Sentinel to None: new orders allowed
#             self.order = None

        

        def next(self):
            if self.buyprice is not None:
                print (np.log(self.datas[0].close[0]/self.buyprice))
                print (self.data.datetime.datetime())



            if  self.position.size <=0:
                if (self.Return[0]>0):
                    self.log('BUY CREATE, %.2f, position value: %.2f' % (self.datas[0].close[0], self.broker.getvalue()))
                    self.buy(size=int(self.broker.cash/self.datas[0].close[0]))
#                     self.notify_order(self.order)
                    self.days =0
                    last_trade.append(self.data.datetime.datetime())
                    

            elif self.position.size>0:
                self.days +=1
                if (self.days == holddays) or np.log(self.datas[0].close[0]/self.buyprice) < trading_param["momentum_cutloss"]:
                    self.log('SELL CREATE, %.2f, position value: %.2f' % (self.datas[0].close[0], self.broker.getvalue()))                
                    self.sell(size = self.position.size)
                    trade_returns.append(np.log(self.datas[0].close[0]/self.buyprice))
#                     self.notify_order(self.order)


    
    price = get_price_data([ticker], method=method,robinhood=robinhood,back_day=200 )
    price = price.set_index("TimeStamp")
    price["Return"] = log(price.Close/price.Close.shift(lookback))


    cerebro = bt.Cerebro()
    cerebro.addstrategy(momentumStrategy)
    cerebro.broker.setcommission(commission=0.001)
#     cerebro.addobserver(DrawDownLength)
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

    # Create a Data Feed
    data = momentumData(dataname=price)

    cerebro.adddata(data)
    cerebro.broker.setcash(2000.0)
    init = cerebro.broker.getvalue()
    #print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    results = cerebro.run()
    strat = results[0]
    pyfoliozer = strat.analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()

    post = cerebro.broker.getvalue()
    if post > init:
        print ("Good Trade")

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # cerebro.plot(iplot=False)
    if analysis:
        
        pf.create_full_tear_sheet(
            returns,
            positions=positions,
            transactions=transactions,
        #     gross_lev=gross_lev,
        #     live_start_date='2005-05-01',  # This date is sample specific
            round_trips=True)
        pf.create_full_tear_sheet(
            returns,
            positions=positions,
            transactions=transactions,
        #     gross_lev=gross_lev,
        #     live_start_date='2005-05-01',  # This date is sample specific
            round_trips=True)
#     return cerebro.broker.getvalue()
    return cerebro.broker.getvalue(),np.log(cerebro.broker.getvalue()/2000)/np.std(trade_returns),last_trade[-1],last_price[-1],np.max(trade_returns),np.min(trade_returns)


##########################


# Following code is the back up of non-sharp-ration momentum backtest

##############

# def momentum_backtest(ticker,lookback,holddays,robinhood,method="realtimeday",analysis = False,):
#     lookback = int(lookback)
#     holddays = int(holddays)
    
#     class momentumData(bt.feeds.PandasData):
#         lines = ('datetime','open','high','low','close','volume','openinterest','log_ret','log_ret_mv','volatility',"Return")
#         params = (
#                 ('datetime', None),
#                 ('open', "Open"),
#                 ('high', "High"),
#                 ('low', "Low"),
#                 ('close', "Close"),
#                 ('volume', "Volume"),
#                 ('openinterest', -1),
#                 ('log_ret', -1),
#             ('log_ret_mv', -1),
#             ('volatility', -1),
#             ("Return","Return")


#             )

#     class momentumStrategy(bt.Strategy):


# #         def log(self, txt, dt=None):
# #             dt = dt or self.datas[0].datetime.date(0)
# #             print('%s, %s' % (dt.isoformat(), txt))
            
#         def log(self, txt, dt=None):
#             ''' Logging function fot this strategy'''
#             dt = dt or self.data.datetime[0]
#             if isinstance(dt, float):
#                 dt = bt.num2date(dt)
#             print('%s, %s' % (dt.isoformat(), txt))
        
#         def notify_order(self, order):
#             if order.status in [order.Submitted, order.Accepted]:
#                 # Buy/Sell order submitted/accepted to/by broker - Nothing to do
#                 self.log('ORDER ACCEPTED/SUBMITTED', dt=order.created.dt)
#                 self.order = order
#                 return

#             if order.status in [order.Expired]:
#                 self.log('BUY EXPIRED')

#             elif order.status in [order.Completed]:
#                 if order.isbuy():
#                     self.log(
#                         'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
#                         (order.executed.price,
#                          order.executed.value,
#                          order.executed.comm))

#                 else:  # Sell
#                     self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
#                              (order.executed.price,
#                               order.executed.value,
#                               order.executed.comm))

#             # Sentinel to None: new orders allowed
#             self.order = None

#         def __init__(self):

#             self.Return = self.datas[0].Return
#             self.order = None
#             self.buyprice = None
#             self.buycomm = None
#             self.days = 0

#         def next(self):
       

#             if  self.position.size <=0:
#                 if (self.Return[0]>0):
#                     self.log('BUY CREATE, %.2f, position value: %.2f' % (self.datas[0].close[0], self.broker.getvalue()))
#                     self.order = self.buy(size=int(self.broker.cash/self.datas[0].close[0]))
#                     self.notify_order(self.order)
#                     self.days =0

#             elif self.position.size>0:
#                 self.days +=1
#                 if (self.days == holddays):
# #                     self.log('SELL CREATE, %.2f' % self.datas[0].close[0])
#                     self.log('SELL CREATE, %.2f, position value: %.2f' % (self.datas[0].close[0], self.broker.getvalue()))                
#                     self.order = self.sell(size = self.position.size)
#                     self.notify_order(self.order)



    
#     price = get_price_data([ticker], method=method,robinhood=robinhood,back_day=200 )
#     price = price.set_index("TimeStamp")
#     price["Return"] = log(price.Close/price.Close.shift(lookback))


#     cerebro = bt.Cerebro()
#     cerebro.addstrategy(momentumStrategy)
#     cerebro.broker.setcommission(commission=0.001)
# #     cerebro.addobserver(DrawDownLength)
#     cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

#     # Create a Data Feed
#     data = momentumData(dataname=price)

#     cerebro.adddata(data)
#     cerebro.broker.setcash(2000.0)
#     init = cerebro.broker.getvalue()
#     #print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
#     results = cerebro.run()
#     strat = results[0]
#     pyfoliozer = strat.analyzers.getbyname('pyfolio')
#     returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()

#     post = cerebro.broker.getvalue()
#     if post > init:
#         print ("Good Trade")

#     print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
#     return cerebro.broker.getvalue()

#     # cerebro.plot(iplot=False)
#     if analysis:
        
#         pf.create_full_tear_sheet(
#             returns,
#             positions=positions,
#             transactions=transactions,
#         #     gross_lev=gross_lev,
#         #     live_start_date='2005-05-01',  # This date is sample specific
#             round_trips=True)
#         pf.create_full_tear_sheet(
#             returns,
#             positions=positions,
#             transactions=transactions,
#         #     gross_lev=gross_lev,
#         #     live_start_date='2005-05-01',  # This date is sample specific
#             round_trips=True)