import requests
import json
import csv
import time
import timeit
import pytz
import talib as ta
import numpy as np
from Robinhood import Robinhood
from pandas import *
import xlrd
import  talib as ta
from datetime import datetime
import pandas as pd
import numpy as np
from numpy import log, polyfit, sqrt, std, subtract
import statsmodels
import statsmodels.tsa.stattools as ts
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
from statsmodels.tsa.tsatools import lagmat, add_trend
from statsmodels.tsa.adfvalues import mackinnonp
import matplotlib.pyplot as plt
import seaborn as sns
import pprint
from datetime import timedelta
from scipy import stats
import scipy
import pymongo
import requests as r
from bs4 import BeautifulSoup as bs
# import yahoo_finance
# from yahoo_finance import Share
# from pandas_datareader import data as pdr
# import pandas_datareader as da
from tqdm import tqdm
from IPython.display import clear_output
import backtrader as bt
import urllib2
import datetools 
# import multiprocessing
import pymysql
import sqlalchemy as sa
from sqlalchemy import event
from fmp import *

############################################

## Must use full path for CRONTAB to work

############################################


pd.options.display.float_format = '{:,.4f}'.format



def read_json(filepath):
    read = []
    with open(filepath, "r") as f:
        read.append(f.readlines())
    read = "".join(read[0]).replace("\n"," ")
    return json.loads(read)


home_dir = "/home/ken/"

#directory = "file/"
directory = home_dir + "notebook/My_Trader2.0/file/"
working_suggestion = "Trade_suggestion_minute_1st"
universe_file_name = "my_universe_industry_sector_marketcap_earnings.csv"
root_directory = home_dir + "notebook/My_Trader2.0/"



## Timezone
mytz = pytz.timezone("US/Pacific")

#Read trading parameter


trading_param = read_json(directory+"trading_param.json")


def unix_time_millis(dt):
    epoch = datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds() * 1000

def read_mongo_time(x, timezone = "US/Pacific"):
    return change_timezone(datetime.utcfromtimestamp(0) + timedelta(milliseconds= x), timezone)


def variance_ratio(ts, lag = 2):
    """
    Returns the variance ratio test result
    """
    # make sure we are working with an array, convert if necessary
    ts = np.asarray(ts)
    
    # Apply the formula to calculate the test
    n = len(ts)
    mu  = sum(ts[1:n]-ts[:n-1])/n;
    m=(n-lag+1)*(1-lag/n);
    b=sum(np.square(ts[1:n]-ts[:n-1]-mu))/(n-1)
    t=sum(np.square(ts[lag:n]-ts[:n-lag]-lag*mu))/m
    return t/(lag*b);


 
def adf(ts, maxlag=1):
    """
    Augmented Dickey-Fuller unit root test
    """
    # make sure we are working with an array, convert if necessary
    ts = np.asarray(ts)
     
    # Get the dimension of the array
    nobs = ts.shape[0]
         
    # Calculate the discrete difference
    tsdiff = np.diff(ts)
     
    # Create a 2d array of lags, trim invalid observations on both sides
    tsdall = statsmodels.tsa.tsatools.lagmat(tsdiff[:, None], maxlag, trim='both', original='in')
    # Get dimension of the array
    nobs = tsdall.shape[0] 
     
    # replace 0 xdiff with level of x
    tsdall[:, 0] = ts[-nobs - 1:-1]  
    tsdshort = tsdiff[-nobs:]
     
    # Calculate the linear regression using an ordinary least squares model    
    results = statsmodels.regression.linear_model.OLS(tsdshort, statsmodels.tsa.tsatools.add_trend(tsdall[:, :maxlag + 1], 'c')).fit()
    adfstat = results.tvalues[0]
     
    # Get approx p-value from a precomputed table (from stattools)
    pvalue = mackinnonp(adfstat, 'c', N=1)
    return pvalue
 
def cadf(x, y):
    """
    Returns the result of the Cointegrated Augmented Dickey-Fuller Test
    """
    # Calculate the linear regression between the two time series
    ols_result = statsmodels.regression.linear_model.OLS(x, y).fit()
     
    # Augmented Dickey-Fuller unit root test
    return adf(ols_result.resid)





#********************************************************

# Some functions

#********************************************************


def change_timezone(utctime, timezonestr):
    
    local = pytz.timezone(timezonestr)
    return utctime.replace(tzinfo = pytz.utc).astimezone(tz = local)




#********************************************************

# Class File

#********************************************************



class write_my_csv:
    def __init__(self, filename, header_list,new_flag=True):
        self.filename = filename
        if new_flag:
            with open(self.filename,"wb") as myfile:
                writer = csv.writer(myfile,delimiter=',')
                writer.writerows(header_list)

    def write_row(self,data_list_tuple):
        with open(self.filename,"ab") as myfile:
            writer = csv.writer(myfile,delimiter=',')
            writer.writerows(data_list_tuple)

        

                
            
####  SORT THE PRICE SERIES ASCENDING            
def get_price_data(tic_list,method,interval = "30min",robinhood= None,start_date= None, end_date= None, back_day=90, last_record= False):
    
    if method not in ["minute","day", "self_minute","realtimeday","intraday","minute_to_day"]:
        print ("method not correct")
        return 
#     if back_day == 0:
#         print("back_day cannot be 0, setting to 1 to get today's price series")
#         back_day =1
    if start_date is None:
        start_date = pd.Timestamp(datetime.now().date())-timedelta(days =back_day)
    if end_date is None:
        end_date=pd.Timestamp(datetime.now().date())+timedelta(days =1)
    print ("All price data of Close is actually Adj Close")
    
  ############ Temporary #######################  
    #if method =="minute":
    #    method = "self_minute"
  ###################################    

    error = []
    price = pd.DataFrame()
    if method == "minute":
        if robinhood == None:
            print ("Please feed a logined robinhood instance")
            return None
        
        robinhood = robinhood.my_trader
        counter = 0
        for i in tic_list:
            trial = 0
             
            while trial <2:
                try:
                    ''' 
                    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol='+i +'&interval=5min&apikey=+R9KJYWUBMIDAXNW7+&outputsize=full&datatype=json'
                    fp = requests.get(url)
                    temp = pd.DataFrame(json.loads(fp.content)["Time Series (5min)"]).transpose().astype(float)
                    fp.close()
                    
                    temp["Ticker"] = i
                   '''
                    temp = robinhood.get_historical_quotes(i.upper(),interval="5minute",span = "week")
                    temp = pd.DataFrame(temp["historicals"])
      
                    temp = temp.drop(["session","interpolated"],axis=1)
#                     temp["Close"] = temp["close_price"]
        #price["Adj Close"] = price["close_price"]
                    temp = temp.rename(columns={'begins_at':"TimeStamp","high_price":"High","low_price":"Low","open_price":"Open","volume":"Volume","close_price":"Close"})
                    for j in temp.columns[1:]:
                        temp[j] = temp[j].astype(float)
                    temp["Return"]= (temp.Close.diff(1)/temp.Close)
                    temp["Fwd_Return"] = np.log(temp.Close.shift(-1)/temp.Close)
    
                    temp["Ticker"] = i
                    price = price.append(temp)

                    print(("Finished", i))
                    counter += 1
                    if int(counter/15) == counter/15.0:
                        #time.sleep(5)
                        print ("every 15 counts")
                    trial=2

                except Exception as e:
                    print(("error occorded in getting robinhood for ", i))
                    print (e)
                    trial +=1
                    #time.sleep(3)
                    if trial == 2:
                        error.append([i,'get_robinhood_historicals'])

        
    elif method == "day":
        save_file_name = "Trade_suggestion_day"
        mongodb = mongo()
        for i in tic_list:
            trial = 0
            while trial <3:
                try:
                    
                    temp = mongodb.query_database(i.upper(),start_date=start_date,end_date=end_date)
                    
                    index= pd.MultiIndex.from_product([[i],temp.index])
                    temp=pd.DataFrame(data=temp.values,index=index,columns=temp.columns)
                    temp = temp.reset_index()
                    temp["Close"] = temp["adjClose"]
                    if len(temp)< 54:
                        raise
                    
                    #temp["Fwd_Return"] = (temp.Close.diff(-1)/temp.Close)
                    price = price.append(temp)
                    price = price.drop("level_0",axis=1)
                    price = price.drop("level_1",axis=1)
                    price.loc[:,"Close"] = price.Close.astype(float)
                    price.loc[:,"Open"] = price.Open.astype(float)
                    price.loc[:,"High"] = price.High.astype(float)
                    price.loc[:,"Low"] = price.Low.astype(float)
                    price["Return"]= (price.Close.diff(1)/price.Close)
                    price["Fwd_Return"] = np.log(price.Close.shift(-1)/price.Close)
                                        
                    print(("Finished", i))
                    trial = 3
                except Exception as e:
                    try:
                        print (e)
                        print ("switching to realtimeday method")
                        temp = get_price_data([i], method = "realtimeday",start_date=start_date,end_date=end_date)
                        price = price.append(temp)
#                         #return get_price_data(tic_list,"realtimeday",interval, freq,start_date,end_date)
#                         temp =da.DataReader(i,'yahoo',start_date ,end_date)
#                         index= pd.MultiIndex.from_product([[i],temp.index])
#                         temp=pd.DataFrame(data=temp.values,index=index,columns=temp.columns)
#                         temp["Return"]= (temp.Close.diff(1)/temp.Close)
#                         temp["Fwd_Return"] = np.log(temp.Close.shift(-1)/temp.Close)
#                         price = price.append(temp)
#                         price["Close"] = price["Adj Close"]
                        print(("Finished", i))
                        trial = 3
                    except Exception as e:
                        print (e)
                        trial +=1
                        continue
            
        price = price.reset_index() 

        price = price.rename(columns={'level_0':'Ticker','level_1':"TimeStamp"})
        # get rid of the multiindex
    
    
    elif method == "self_minute":
        save_file_name = "Trade_suggestion_day"
        mongodb = mongo("stocks_10minute") 
        if robinhood == None:
            print ("Please feed a logined robinhood instance")
            return None
        
        robinhood = robinhood.my_trader
        alter = False
        for i in tic_list: 
            print (i)
#             i = i.decode("ascii")
            trial = 0
            while trial <3:
                
                try:
                    
                    temp = mongodb.query_database(i.upper(),start_date=start_date,end_date=end_date)
                    
                    #index= pd.MultiIndex.from_product([[i],temp.index])
                    #temp=pd.DataFrame(data=temp.values,index=index,columns=temp.columns)
                    temp["Return"]= (temp.Close.diff(1)/temp.Close)
                    temp["Fwd_Return"] = np.log(temp.Close.shift(-1)/temp.Close)
                    #temp = temp.reset_index()
                    if len(temp)< back_day*(2.0/7.0):
                        print ("Data rows not enough for the back days")
                        raise
                    if last_record :
                        price = price.append(temp.iloc[-1])
                    else:
                        price = price.append(temp)
                    
                    #price = price.drop("level_0",axis=1)
                    #price = price.drop("level_1",axis=1)

                    print(("Finished", i))
                    trial = 3
                except Exception as e:
                    print (e)
                    alter = True
                    try:
                        print ("switching to robinhood method")
                        temp = robinhood.get_historical_quotes(i.upper(),interval="5minute",span = "week")
                        temp = pd.DataFrame(temp["historicals"])
                        temp["Close"] = temp["close_price"]
                        
                        temp = temp.drop(["session","interpolated"],axis=1)
                        for j in temp.columns[1:]:
                            temp[j] = temp[j].astype(float)
                        temp["Return"]= (temp.Close.diff(1)/temp.Close)
                        temp["Fwd_Return"] = np.log(temp.Close.shift(-1)/temp.Close)
                        temp["Ticker"] = i
                        if last_record:
                            price = price.append(temp.iloc[-1])
                        else:
                            price = price.append(temp)
                        print(("Finished", i))
                        trial = 3
                       
                    except Exception as e:
                        trial +=1
                        print (e)
                        continue
        
        if alter:
            
            
            #price["Adj Close"] = price["close_price"]
            price = price.reset_index()
            price = price.rename(columns={'begins_at':"TimeStamp","high_price":"High","low_price":"Low","open_price":"Open","volume":"Volume"})
        
        else:
            price = price.reset_index() 
            price = price.rename(columns={'level_0':'Ticker','level_1':"TimeStamp"})
            # get rid of the multiindex
    
    
    
#     elif method == "realtimeday" or method == "day":
#         save_file_name = "Trade_suggestion_day"
#         for i in tic_list:
#             i = i.decode("ascii")
#             trial = 0
#             while trial <3:
#                 try:
#                     temp =da.DataReader(i,'yahoo',start_date ,end_date)
#                     #print temp
#                     index= pd.MultiIndex.from_product([[i],temp.index])
#                     temp=pd.DataFrame(data=temp.values,index=index,columns=temp.columns)
#                     temp["Close"] = temp["Adj Close"]
#                     temp["Return"]= (temp.Close.diff(1)/temp.Close)
#                     temp["Fwd_Return"] = np.log(temp.Close.shift(-1)/temp.Close)
#                     price = price.append(temp)
#                     print ("Finished", i)
#                     trial = 3
#                 except Exception as e:
#                     print ("error occorded in getting yahool historicals for ", i)
#                     trial +=1
#                     time.sleep(10)
#                     if trial == 3:
#                         error.append([i,'get_yahoo_historicals'])
#         price = price.reset_index()


        
#         price = price.rename(columns={'level_0':'Ticker','level_1':"TimeStamp"})
    
    elif method == "realtimeday":
     
        def parse_date(x):
            try:
                the_date = datetime.strptime(x,"%Y-%m-%d %H:%M %p")
            except:
                the_date = datetime.strptime(x,"%Y-%m-%d %H %p")
            return the_date
    
        for i in tic_list:
#             i = i.decode("ascii")
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

#             url = "https://cloud.iexapis.com/stable/stock/{}/intraday-prices".format(i)
            url = "https://fmpcloud.io/api/v3/historical-price-full/{}".format(i)
            payload = {
                "apikey": "f49024a02ed51582a55c94a9485223c7" ,
            }
        
            try:
                re=r.get(url, params=payload,headers = headers)

                data = pd.DataFrame(re.json()["historical"])
                data["Ticker"] = i
                data = data.rename({"close":"Close","high":"High","low":"Low",\
                  "open":"Open","volume":"Volume","date":"TimeStamp"},axis = 1)
                

#                 data["Time"] = data.TimeStamp.apply(lambda x: int(x[-8:].replace(":","")))
                data.TimeStamp = data.TimeStamp.\
                            apply(lambda x: datetime.strptime(x,"%Y-%m-%d"))
                
                data = data.sort_values("TimeStamp")
                data = data[data.TimeStamp >= start_date]
                
                data["Return"]= (data.Close.diff(1)/data.Close)
                data["Fwd_Return"] = np.log(data.Close.shift(-1)/data.Close)
                price = price.append(data)
                print(("Finished", i))
                time.sleep(1)
            except Exception as e:
                print(("error occorded in getting historicals for ", i))
                print((e,"\n"))
                print((re.text))
                error.append([i,'get_intraday'])
#                 trial +=1
                time.sleep(10)
    
    elif method == "minute_to_day":
        mongodb = mongo("stocks_10minute") 
        for i in tic_list:
            try:
                sql = '''

                select
                * 
                from stocks_10minute.{}
                where hour(timestamp) = 16

                '''.format(i)

                temp = mongodb.conn.get_data(sql)

                #index= pd.MultiIndex.from_product([[i],temp.index])
                #temp=pd.DataFrame(data=temp.values,index=index,columns=temp.columns)
                temp["Return"]= (temp.Close.diff(1)/temp.Close)
                temp["Fwd_Return"] = np.log(temp.Close.shift(-1)/temp.Close)
                #temp = temp.reset_index()
                if len(temp)< back_day*(2.0/7.0):
                    print ("Data rows not enough for the back days")
                    raise
                if last_record :
                    price = price.append(temp.iloc[-1])
                else:
                    price = price.append(temp)
                    print(("Finished", i))
                    time.sleep(1)
            except Exception as e:
                print(("error occorded in getting historicals for ", i))
                print((e,"\n"))
                print(("Switching to realtimeday method"))
                try:
                    
                    temp = mongodb.query_database(i.upper(),start_date=start_date,end_date=end_date)
                    
                    index= pd.MultiIndex.from_product([[i],temp.index])
                    temp=pd.DataFrame(data=temp.values,index=index,columns=temp.columns)
                    temp = temp.reset_index()
                    temp["Close"] = temp["adjClose"]
                    if len(temp)< 54:
                        raise
                    
                    #temp["Fwd_Return"] = (temp.Close.diff(-1)/temp.Close)
                    price = price.append(temp)
                    price = price.drop("level_0",axis=1)
                    price = price.drop("level_1",axis=1)
                    price.loc[:,"Close"] = price.Close.astype(float)
                    price.loc[:,"Open"] = price.Open.astype(float)
                    price.loc[:,"High"] = price.High.astype(float)
                    price.loc[:,"Low"] = price.Low.astype(float)
                    price["Return"]= (price.Close.diff(1)/price.Close)
                    price["Fwd_Return"] = np.log(price.Close.shift(-1)/price.Close)
                                        
                    print(("Finished", i))
                except Exception as e:
                    print(e)
                    continue

    
    
    elif method == "intraday":
        def parse_date(x):
            try:
                the_date = datetime.strptime(x,"%Y-%m-%d %H:%M %p")
            except:
                the_date = datetime.strptime(x,"%Y-%m-%d %H %p")
            return the_date
    
        for i in tic_list:
          
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

#             url = "https://cloud.iexapis.com/stable/stock/{}/intraday-prices".format(i)
            url = "https://fmpcloud.io/api/v3/historical-chart/{}/{}".format(interval,i)
            payload = {
                "apikey": "f49024a02ed51582a55c94a9485223c7" ,
            }
            try:
                re=r.get(url, params=payload,headers = headers)
#                 re=r.get(url,headers = headers)

                data = pd.DataFrame(re.json())
                data["Ticker"] = i
                data = data.rename({"close":"Close","high":"High","low":"Low",\
                  "open":"Open","volume":"Volume","date":"TimeStamp"},axis = 1)
                

                data["Time"] = data.TimeStamp.apply(lambda x: int(x[-8:].replace(":","")))
                data.TimeStamp = data.TimeStamp.\
                            apply(lambda x: datetime.strptime(x,"%Y-%m-%d %H:%M:%S"))
                
                data = data.sort_values("TimeStamp")
                data = data[data.TimeStamp >= start_date]
                
                data["Return"]= (data.Close.diff(1)/data.Close)
                data["Fwd_Return"] = np.log(data.Close.shift(-1)/data.Close)
                price = price.append(data)
                print(("Finished", i))
                time.sleep(1)
            except Exception as e:
                print(("error occorded in getting historicals for ", i))
                print((e,"\n"))
                print((re.text))
                error.append([i,'get_intraday'])
#                 trial +=1
                time.sleep(10)
    #price = price.drop("index",axis=1)
    return price


class finviz:

    def get_finviz(self,symbol, data):
        try:
            base_url = 'http://finviz.com/quote.ashx?t={}'\
                .format(symbol.lower())

            html = r.get(base_url)
            soup = bs(html.content, "html.parser")
            main_div = soup.find('div', attrs = {'id':'screener-content'})
            pb =  soup.find(text = data)
            pb_ = pb.find_next(class_='snapshot-td2').text

            return pb_

        except:
            return np.NaN

    def get_finviz_sector(self,symbol):

        try:
            base_url = 'http://finviz.com/quote.ashx?t={}'\
            .format(symbol.lower())

            html = r.get(base_url)
            soup = bs(html.content, "html.parser")
            main_div = soup.find_all('td','fullview-links')
            sector = main_div[1].contents[0].text
            industry = main_div[1].contents[2].text

            return str(sector)
        except:
            return np.NaN

    def get_finviz_industry(self, symbol):
        try:
            base_url = 'http://finviz.com/quote.ashx?t={}'\
            .format(symbol.lower())

            html = r.get(base_url)
            soup = bs(html.content, "html.parser")
            main_div = soup.find_all('td','fullview-links')
            sector = main_div[1].contents[0].text
            industry = main_div[1].contents[2].text

            return str(industry)
        except:
            return np.NaN

    def get_marketcap(self,symbol):
        mkcap=self.get_finviz(symbol,"Market Cap")
        if type(mkcap) != unicode:
            return np.NaN
        else:
            if mkcap[-1]=="B":
                return float(mkcap[:-1])*1000000000
            elif mkcap[-1]=="M":
                return float(mkcap[:-1])*1000000
            else:
                return float(mkcap)


    def all_in_one(self, symbol):

        base_url = 'https://finviz.com/quote.ashx?t={}'\
            .format(symbol.lower())
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        html = r.get(base_url,headers=headers)
        
        soup = bs(html.content, "html.parser")
        main_div = soup.find_all('td','fullview-links')
        sector = main_div[1].contents[0].text
        industry = main_div[1].contents[2].text

        def get_text(data, check = True):
            get = soup.find(text = data)
            #get = get.find_next(class_='snapshot-td2').text
            try:
                get = get.find_next().text
            except:
                get = get.find_next(class_='snapshot-td2').text
            
            try:
                if check:
                    if  get =="-":
                        get = 0
                    else:
                        if get[-1]=="B":
                            get = float(get[:-1])*1000000000
                        elif get[-1]=="M":
                            get = float(get[:-1])*1000000
                        elif get[-1] =="K":
                            get = float(get[:-1])*1000
                        elif get[-1]=="%":
                            get = float (get[:-1])*0.01
                        else:
                            get = float(get)
            except:
                return get
                
            return get

        def conver_cap (mkt_cap):
            if type(mkt_cap) != unicode or mkt_cap =="-":
                mkt_cap = np.NaN
            else:
                if mkt_cap[-1]=="B":
                    mkt_cap = float(mkt_cap[:-1])*1000000000
                elif mkt_cap[-1]=="M":
                    mkt_cap = float(mkt_cap[:-1])*1000000
                else:
                    mkt_cap = float(mkt_cap)
#
#
#        def conver_pet(data):
#
#                return data
#            else:
#                return float (data[:-1])*0.01
#
#        def none_result(data):
#            if data== "-":
#                data = 0
#                return data

        main_div = soup.find('div', attrs = {'id':'screener-content'})
#        mkt_cap =  soup.find(text = "Market Cap")
#        mkt_cap = mkt_cap.find_next(class_='snapshot-td2').text
#        mkt_cap = conver_cap(mkt_cap)
        mkt_cap = get_text("Market Cap")
        #earning_date = soup.find(text = "Earnings")
        #earning_date = earning_date.find_next(class_='snapshot-td2').text
        PEG = get_text("PEG")
        earning_date = get_text("Earnings")

#        P_E = soup.find(text = "P/E")
#        P_E = P_E.find_next(class_='snapshot-td2').text

        Profit_Margin = get_text("Profit Margin")
#        Profit_Margin = conver_pet(Profit_Margin)
        Avg_Volume = get_text("Avg Volume")
#        Avg_Volume = conver_cap(Avg_Volume)
        Current_Ratio = get_text("Current Ratio")
#        Current_Ratio = conver_pet(Current_Ratio)
        Inst_Own = get_text("Inst Own")
#        Inst_Own = conver_pet(Inst_Own)
        Beta = get_text("Beta")
    
        PB = get_text("P/B")

        Debt_to_Equity = get_text("Debt/Eq")

        LDebt_to_Equity = get_text("LT Debt/Eq")

        Sales = get_text("Sales")
        ROE = get_text("ROE")
    
#        if type(mkt_cap) != unicode:
#            mkt_cap = np.NaN
#        else:
#            if mkt_cap[-1]=="B":
#                mkt_cap = float(mkt_cap[:-1])*1000000000
#            elif mkt_cap[-1]=="M":
#                mkt_cap = float(mkt_cap[:-1])*1000000
#            else:
#                mkt_cap = float(mkt_cap)

        return str(industry), str(sector), mkt_cap,earning_date,\
                            float(PEG), Profit_Margin,\
                            Avg_Volume,float(Inst_Own),float(Beta), float(Current_Ratio),float(PB),float(Debt_to_Equity),float(LDebt_to_Equity),float(Sales),float(ROE)

        
finviz = finviz()


#yahoo finance


# class yahoo_historicals:



#     def get_historicals(self,stock, start,end):

#         # download dataframe
#         #start ="2017-01-01"
#         #end="2017-04-30"
#         data = pdr.get_data_yahoo(stock, start, end)

#         return data


# def update_price():
#     tradeable = pd.read_csv("file/cantrade.csv")
#     tradeable = tradeable.dropna()

#     error = []


#     yahoo = yahoo_historicals()
#     start ="2017-10-1"
#     end=datetime.now()
#     price=pd.DataFrame()




#     for i in list(tradeable.Ticker):
#         trial = 0
#         while trial <3:
#             try:
#                 temp = da.DataReader(i,"yahoo",start,end)
#                 index= pd.MultiIndex.from_product([[i],temp.index])
#                 temp=pd.DataFrame(data=temp.values,index=index,columns=temp.columns)
#                 price = price.append(temp)

#                 print "Finished", i
#                 #time.sleep(5)
#                 trial=3

#             except:
#                 print "error occorded in getting yahool historicals for ", i
#                 trial +=1
#                 if trial == 3:
#                     error.append([i,'get_yahoo_historicals'])
#     # get rid of the multiindex
#     price = price.reset_index()


#     price.Close = price["Adj Close"]
#     price = price.rename(columns={'Unnamed: 0':'Ticker','Unnamed: 1':"TimeStamp"})
#     price["Return"]= price.Close.diff(1)/price.Close

#     '''
#     # make sure DataFrames are the same length

#     price_date = pd.DataFrame()

#     min_date = max(price.loc[price.Ticker==i].TimeStamp.iloc[0] for i in price.Ticker)
#     max_date = min(price.loc[price.Ticker==i].TimeStamp.iloc[-1] for i in price.Ticker)
#     print "2"
#     for i in price.Ticker:
#         price_date = price_date.append(price.loc[price.Ticker==i][(price.loc[price.Ticker==i].TimeStamp>= min_date) & (price.loc[price.Ticker==i].TimeStamp <= max_date)] )

#     price = price_date

#     print "done"

#     '''
gateway = home_dir + "notebook/My_Trader2.0/record-Copy1.txt"

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

    #         print "nan occorded"
    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Earnings_date"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Earnings_date"].values[0]
    #     except:

    #         print "nan occorded"

    # for i in list(set(final_update.Ticker)):
    #     try:
    #         final_update.loc[final_update.Ticker==i,"Market_cap"] = industry_sector_earnings.loc[industry_sector_earnings.Ticker == i, "Market_cap"].values[0]
    #     except:

    #         print "nan occorded"



#     #final_update.to_csv("final"+str(price.loc[price.Ticker==i][-1]["Date"])+".csv")


#     #get industrial makcap_weight

#     for ind in set(final_update.Industry):
#         for tic in set(final_update.loc[final_update.Industry==ind].Ticker):
#             final_update.loc[final_update.Ticker==tic,'Industry_weight']=final_update.loc[final_update.Ticker==tic,"Market_cap"] / final_update.loc[final_update.Industry==ind,"Market_cap"].sum()


#     #final_update = final_update[['Ticker','TimeStamp', 'Open', 'High', 'Low', 'Close', 'Volume',
#     #        'Return','ADXR','AROONOSC','APO','CCI','MACD', 'MACD_hist',
#     #       'MACD_signal','MFI','ROCP','RSI','Industry','Sector']]
#     final_update = final_update[['Ticker','TimeStamp', 'Open', 'High', 'Low', 'Close', 'Volume',
#             'Return','ADXR','AROONOSC','APO','CCI','MACD', 'MACD_hist',
#            'MACD_signal','MFI','ROCP','RSI','Industry','Sector','Market_cap','Industry_weight','Earnings_date']]

#     final_update =final_update.set_index("Ticker")

#     #final_update= final_update.dropna()




#     # Technical points rule

#     final_update["Technical_points"]=0
#     for i in final_update.index:
#         if final_update.loc[i].ADXR >= final_update.loc[final_update.Sector==final_update.loc[i].Sector].max().ADXR:
#             final_update.loc[i,'Technical_points'] += 1
#         if final_update.loc[i].APO >0:
#             final_update.loc[i,'Technical_points'] += 1
#         if final_update.loc[i].AROONOSC >= final_update.loc[final_update.Sector==final_update.loc[i].Sector].max().AROONOSC:
#             final_update.loc[i,'Technical_points'] += 1
#         if final_update.loc[i].CCI <-100:
#             final_update.loc[i,'Technical_points'] += 1
#         if final_update.loc[i].MACD > final_update.loc[i].MACD_signal:
#             final_update.loc[i,'Technical_points'] += 1
#         if final_update.loc[i].MFI <20:
#             final_update.loc[i,'Technical_points'] += 1
#         if final_update.loc[i].ROCP >0:
#             final_update.loc[i,'Technical_points'] += 1

#         print "Technical_points done: ", i
#     final_update= final_update.dropna()

#     final_update.to_csv("file/final_update.csv")
#     #***************************************

#     # get result

#     #***************************************

#     result = pd.DataFrame()
#     for i in set(final_update.Sector):
#         print i
#         print final_update.groupby("Sector").get_group(i).sort_values("Technical_points").iloc[-1].name
#         result = result.append(final_update.groupby("Sector").get_group(i).sort_values("Technical_points").iloc[-1])

#     result.to_csv("file/Trade_suggestion_1st" + str(result.TimeStamp[0])+".csv")

#     result = pd.DataFrame()
#     for i in set(final_update.Sector):
#         print i
#         print final_update.groupby("Sector").get_group(i).sort_values("Technical_points").iloc[-2].name
#         result = result.append(final_update.groupby("Sector").get_group(i).sort_values("Technical_points").iloc[-2])

#     result.to_csv("file/Trade_suggestion_2nd" + str(result.TimeStamp[0])+".csv")

#     result = pd.DataFrame()
#     for i in set(final_update.Sector):
#         print i
#         print final_update.groupby("Sector").get_group(i).sort_values("Technical_points").iloc[-2].name
#         result = result.append(final_update.groupby("Sector").get_group(i).sort_values("Technical_points").iloc[-2])

#     result.to_csv("file/Trade_suggestion_3rd" + str(result.TimeStamp[0])+".csv")
#     #"file/Trade_suggestion_minute_1st" + str(datetime.now())[0:10]+".csv"


#################################################################

#FOLLOWING IS BY SECTORS

#    result = pd.DataFrame()
#    for i in set(final_update.Sector):
#        try:
#            print i
#            print final_update.groupby("Sector").get_group(i).sort_values("Technical_points").iloc[-1].name
#            result = result.append(final_update.groupby("Sector").get_group(i).sort_values("Technical_points").iloc[-1])
#
#        except Exception as e:
#            result = result.append(pd.Series(([np.NaN])),ignore_index=True)
#            print e," no 1st suggestion", i
#            raise
#    if save_file:
#        result.to_csv( directory + save_file_name + "_1st"  +test + str(result.TimeStamp[0])[0:10].replace(":","-")+".csv")
#
#    result_1 = result
#
#    result = pd.DataFrame(columns = result.columns)
#    for i in set(final_update.Sector):
#        try:
#            print i
#            print final_update.groupby("Sector").get_group(i).sort_values("Technical_points").iloc[-2].name
#            result = result.append(final_update.groupby("Sector").get_group(i).sort_values("Technical_points").iloc[-2])
#        except Exception as e:
#            print e," no 2nd suggestion", i
#            result = result.append(pd.Series(pd.Series([np.NaN])),ignore_index=True)
#            pass
#    if save_file:
#        result.to_csv(directory + save_file_name + "_2nd" +test+ str(result.TimeStamp[0])[0:10].replace(":","-")+".csv")
#
#
#    result_2 = result
#
#    result = pd.DataFrame(columns = result.columns)
#    for i in set(final_update.Sector):
#        try:
#            print i
#            print final_update.groupby("Sector").get_group(i).sort_values("Technical_points").iloc[-3].name
#            result =

def remove_salt(x):
    return x.strip("\n").replace("$",'').replace("*",'')
#result.append(final_update.groupby("Sector").get_group(i).sort_values("Technical_points").iloc[-3])
#        except Exception as e:
#            print e," no 3rd suggestion, ", i
#            result = result.append(pd.Series([np.NaN]),ignore_index=True)
#            pass
#    if save_file:
#        result.to_csv(directory + save_file_name + "_3rd" +test+ str(result.TimeStamp[0])[0:10]+".csv")
#
#    result_3 = result
#
#    return result_1, result_2,result_3


#################################################################




#################################################################

def update_fundamentals(robinhood,my_list = False, test_mode=False,skip_can=True):
    # need to feed a logined robinhood instance
    error=[]
    mongod = mongo("all_symbol","screener")
    ## This line gets the max refresh_date
    tos = pd.DataFrame(mongod.conn.table.find({},{"Refresh_Date":1}).sort("Refresh_Date",-1).limit(1))["Refresh_Date"].iloc[0]
    
    if not skip_can:
        
#         ## Option 1: use FMP list
#         if type(my_list) ==bool:
#             if test_mode:
#                 universe = robinhood.get_universe()[1:10]
#             else:
#                 universe = robinhood.get_universe()
#         else:
#             universe = my_list
#         stock = list()
 
#         tradeable = universe[universe.price > 10]
#         tradeable.loc[:,"Ticker"] = tradeable["symbol"]
        
        
        ## Option 2: use Finviz list
        if type(my_list) ==bool:
            if test_mode:
                universe = pd.DataFrame(mongod.conn.table.find({"Refresh_Date":tos}).limit(10))
            else:
                universe = pd.DataFrame(mongod.conn.table.find({"Refresh_Date":tos}))
        else:
            universe = my_list
        stock = list()

        tradeable = universe[(universe.Price > 5) & (universe.Volume > 0)]
        
        
        
        tradeable.loc[:,"Symbol"] = tradeable["Ticker"]
        tradeable["Refresh_Date"] = datetime.now().strftime("%Y-%m-%d")
        mongod = mongo("all_symbol","cantrade")
        mongod.conn.frame_to_mongo(tradeable)
################# getting list directly from FMP ###########################
################  
#         tradeable_list = []
#         i = 0
#         trial = 0 
#         while i < len(universe.index):
#         #for i in range(len(universe.index)):
#             try:
#                 if robinhood.istradeable(str(universe.iloc[i])).values[0]:
#                     trade_price= get_price_data([str(universe.iloc[i])],method = "day").iloc[-1]["Close"]
#                     if trade_price > 5.00:
#                         new_get = {"Ticker":str(universe.iloc[i]),"Symbol":str(universe.iloc[i]), "Price":trade_price,"Refresh_Date":datetime.now().strftime("%Y-%m-%d")}
#                         tradeable_list.append(new_get)
#                         mongod.conn.to_sql(pd.DataFrame(new_get,index = [i]),"all_symbol","cantrade",if_exists="append")
                    
# #                         mongod.db["cantrade"].update_one({"Ticker":str(universe.iloc[i])},{"$set":{"Symbol":str(universe.iloc[i]), "Price":trade_price,"Refresh_Date":datetime.now().strftime("%Y-%m-%d")}},upsert=True)
#                     print ("Got cantrade: " + universe.iloc[i])
#                 i+=1
#                 trial = 0
# #                 time.sleep(1)
#             except Exception as e:
#                 print (str(e) + ". Timeout error, waiting\n" +str(universe.iloc[i]) )
#                 time.sleep(2)
#                 if trial >0:
#                     i+=1
#                     trial = 0
#                 trial += 1


#         tradeable = pd.DataFrame(tradeable_list)
        
#         mongod.frame_to_mongo(tradeable,"cantrade",drop_mode = "upsert", index_col = "Ticker")
        ## My own list
        mylist = pd.read_csv(directory+"mylist.csv")
        mylist["Refresh_Date"] = datetime.now().strftime("%Y-%m-%d")
        mylist.loc[:,"Ticker"] = mylist["Symbol"]
        mongod = mongo("all_symbol","cantrade")
        mongod.conn.frame_to_mongo(pd.DataFrame(mylist))
        tradeable = tradeable.append(mylist)
#         ## ETF List
#         mylist = pd.read_csv(directory+"ETFList.csv")
#         mylist["Refresh_Date"] = datetime.now().strftime("%Y-%m-%d")
#         mylist.loc[:,"Ticker"] = mylist["Symbol"]
#         mongod.conn.to_sql(pd.DataFrame(mylist),"all_symbol","cantrade",if_exists="append")
#         tradeable = tradeable.append(mylist)
        #get stock volumn
        
        tradeable.to_csv(directory+'cantrade.csv')
        

#         mongod.frame_to_mongo(tradeable,"cantrade",drop_mode = "drop", index_col = "Ticker")
        print ("cantrade done!\n")


#     start = timeit.default_timer()
#     if  type(my_list) ==bool:
#         tradeable = pd.read_csv(directory +"cantrade.csv")
#         tradeable = tradeable.drop("Unnamed: 0",axis = 1)
#     else:       
#         tradeable = pd.DataFrame(my_list,columns=["Ticker"])

# #        tradeable = tradeable.rename(columns={"0":"Ticker"})

#     tradeable['Industry']=np.NaN
#     tradeable['Sector']=np.NaN
#     tradeable['Market_cap']=np.NaN
#     tradeable['Earnings_date']=np.NaN
#     tradeable["PEG"]=np.NaN
#     tradeable["Avg_Volume"]=np.NaN
#     tradeable["Current_Ratio"]=np.NaN
#     tradeable["Inst_Own"]=np.NaN
#     tradeable["Beta"]=np.NaN
#     tradeable["Profit_Margin"] = np.NaN
#     tradeable["Beta"] = np.NaN
#     tradeable["PB"] = np.NaN
#     tradeable["Debt_to_Equity"] = np.NaN
#     tradeable["LDebt_to_Equity"] = np.NaN
#     tradeable["Sales"] = np.NaN
#     tradeable["ROE"] = np.NaN
# #
# #Avg_Volume = get_text("Avg Volume")
# #        Current_Ratio = get_text("Current Ratio")
# #        Inst_Own = get_text("Inst Own")
# #        Beta = get_text("Beta")
#     mongod.conn.cursor.execute("drop table all_symbol.cantrade")
#     for i in range(len(tradeable.index)):
#         try:
#             tradeable.loc[tradeable.iloc[i].name,'Industry'],\
#             tradeable.loc[tradeable.iloc[i].name,'Sector'],\
#             tradeable.loc[tradeable.iloc[i].name,'Market_cap'],\
#             tradeable.loc[tradeable.iloc[i].name,'Earnings_date'],\
#             tradeable.loc[tradeable.iloc[i].name,"PEG"],\
#             tradeable.loc[tradeable.iloc[i].name,"Profit_Margin"],\
#             tradeable.loc[tradeable.iloc[i].name,"Avg_Volume"],\
#             tradeable.loc[tradeable.iloc[i].name,"Inst_Own"],\
#             tradeable.loc[tradeable.iloc[i].name,"Beta"],\
#             tradeable.loc[tradeable.iloc[i].name,"Current_Ratio"],\
#             tradeable.loc[tradeable.iloc[i].name,"PB"],\
#             tradeable.loc[tradeable.iloc[i].name,"Debt_to_Equity"],\
#             tradeable.loc[tradeable.iloc[i].name,"LDebt_to_Equity"],\
#             tradeable.loc[tradeable.iloc[i].name,"Sales"],\
#             tradeable.loc[tradeable.iloc[i].name,"ROE"]\
#             =finviz.all_in_one(tradeable['Ticker'].iloc[i])
            
# #             tradeable_json = json.loads(tradeable.iloc[i].to_json())
# #             mongod.db["cantrade"].update_one({"Ticker":tradeable_json["Ticker"]},{"$set":tradeable_json},upsert=True)
            
#             print ("get done! ", tradeable['Ticker'].iloc[i])
#             time.sleep(1)
#             if i % 8 == 0 and i != 0:
#                 mongod.frame_to_mongo(tradeable,"cantrade",drop_mode = "drop", index_col = "Ticker")
#                 time.sleep(20)
#         except Exception as e:
# #             if test_mode:
# #                 raise
#             print ("get error ", tradeable['Ticker'].iloc[i])
#             print (e)
#             error.append([tradeable['Ticker'].iloc[i],'get_S_I_M_E'])

#     error = pd.DataFrame(error)
# #     mongod.conn.cursor.execute("drop table all_symbol.cantrade")
# #     mongod.to_sql(tradeable,"all_symbol","cantrade")
# #     mongod.frame_to_mongo(tradeable,"cantrade",drop_mode = "drop", index_col = "Ticker")
#     if  type(my_list) == "bool":
#         tradeable.to_csv(directory + "from_error_my_universe_industry_sector_marketcap_earnings.csv")
#         error.to_csv(directory + "from_error.csv")
#     else:
#         tradeable.to_csv(directory + "my_universe_industry_sector_marketcap_earnings.csv")
#         error.to_csv(directory + "error.csv")

#     stop = timeit.default_timer()

#     runtime = stop - start
#     print ( runtime)

#################################################################

# Mongo Class

#################################################################


# This function is for mongo class update_db_multi method


# def update_worker(mongo,tickers,now_time):
    
#     for i in tickers:
#         try:
            
#             print (i)

#             quote = da.get_quote_yahoo(i)
#             quote["Ticker"] = quote.index[0]
#             quote = quote.rename( {"regularMarketTime":"TimeStamp", "regularMarketDayHigh": "High","regularMarketDayLow": "Low", "regularMarketOpen":"Open", "regularMarketVolume":"Volume", "regularMarketPrice":"Close"},axis = "columns") 

#             mongo.db = mongo.client["stocks_daily"]
#             collection = mongo.db[i]
            
#             quote["TimeStamp"] = datetime(datetime.utcfromtimestamp(quote["TimeStamp"]).year,datetime.utcfromtimestamp(quote["TimeStamp"]).month,datetime.utcfromtimestamp(quote["TimeStamp"]).day)

            
#             quote_json = json.loads(quote.T.to_json()).values()[0]   
#             collection.update_many({"TimeStamp":quote_json[u'TimeStamp']},{"$set": quote_json },upsert=True)
            
#             ######################

#             mongo.db = mongo.client["stocks_10minute"]
#             collection = mongo.db[i]     
                
#             quote["TimeStamp"] = now_time
          
#             quote_json = json.loads(quote.T.to_json()).values()[0]

#             collection.update_many({"TimeStamp":quote_json[u'TimeStamp']},{"$set": quote_json },upsert=True)
            
#             clear_output()
#             print ("successed " + i)
#         except Exception as e:
#             print ( e)
#             print ("error occored in updating "+ str(i))
#             continue 

# def update_worker(mongo,tickers,now_time,test = False):
    
#     for i in tickers:
#         try:
            
#             print (i)

#             collection = mongo.db[i]
#             quote = da.get_quote_yahoo(i)

#             if mongo.coll_name == "stocks_daily":

#                 quote["regularMarketTime"] = datetime(datetime.utcfromtimestamp(quote["regularMarketTime"]).year,datetime.utcfromtimestamp(quote["regularMarketTime"]).month,datetime.utcfromtimestamp(quote["regularMarketTime"]).day)

#             else:
#                  quote["regularMarketTime"] = now_time
#             quote["Ticker"] = quote.index[0]
#             quote = quote.rename( {"regularMarketTime":"TimeStamp", "regularMarketDayHigh": "High","regularMarketDayLow": "Low", "regularMarketOpen":"Open", "regularMarketVolume":"Volume", "regularMarketPrice":"Close"},axis = "columns") 
#             quote = json.loads(quote.T.to_json()).values()[0]
#             if test:
#                 print ("Success")
#                 return
#             collection.update_many({"TimeStamp":quote[u'TimeStamp']},{"$set": quote },upsert=True)
#             clear_output()
#             print ("successed " + i)
#         except Exception as e:
#             print ( e)
#             print ("error occored in updating "+ str(i))
#             continue 

# def update_worker2(mongo,tickers,test = False):
#     all_quote = pd.DataFrame()
#     now_time = datetime(datetime.utcnow().year,datetime.utcnow().month,datetime.utcnow().day,datetime.utcnow().hour,datetime.utcnow().minute)
#     for i in tickers:
#         try:
#             
#             print (i)

#             collection = mongo.db[i]
#             quote = da.get_quote_yahoo(i)
            
#             if mongo.coll_name == "stocks_daily":

#                 quote["regularMarketTime"] = datetime(datetime.utcfromtimestamp(quote["regularMarketTime"]).year,datetime.utcfromtimestamp(quote["regularMarketTime"]).month,datetime.utcfromtimestamp(quote["regularMarketTime"]).day)

#             else:
#                  quote["regularMarketTime"] = now_time
            
#             quote["Ticker"] = quote.index[0]
#             quote = quote.rename( {"regularMarketTime":"TimeStamp", "regularMarketDayHigh": "High","regularMarketDayLow": "Low", "regularMarketOpen":"Open", "regularMarketVolume":"Volume", "regularMarketPrice":"Close"},axis = "columns")
#             all_quote = all_quote.append(quote)
#             all_quote
#         except Exception as e:
#             print ( e)
#             print ("error occored in updating "+ str(i))
#             continue 

            
#     for j in  tickers:
#         quote = all_quote[all_quote.Ticker == i]


#         quote = json.loads(quote.T.to_json()).values()[0]
#         if test:
#             print ("Success Test")
#             return
#         collection.update_many({"TimeStamp":quote[u'TimeStamp']},{"$set": quote },upsert=True)
#         clear_output()
#         print ("successed " + i)


class connect_sql():
    
    def __init__(self, user, pwd ,host='localhost', database = None):
        # return pandas dataframe
        self.host = host
        self.user = user
        if database == None:
            self.conn = pymysql.connect(host,
                                        user=user,
                                        passwd=pwd,                        
                                        connect_timeout=5)
        else:
            self.conn = pymysql.connect(host,
                                        user=user,
                                        passwd=pwd,
                                        db=database,
                                        connect_timeout=5)
        
#         self.cursor = self.conn.cursor()

    def to_sql(self, data, database, table_name, dtype = None,if_exists = 'fail' ):
#         check = input("Caution!! Type 'Confirm to continue'")
#         if check != "Confirm":
#             print ("no action")
#             return 

        

        engine = sa.create_engine("mysql+pymysql://%s:@%s/%s"%(self.user,self.host,database), creator=lambda: self.conn)
        
        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(
               conn, cursor, statement, params, context, executemany
                ):
                    if executemany:
                        cursor.fast_executemany = True
        
    
        if dtype == None:
            data.to_sql(name=table_name,
                      con=engine,
                      schema=database,
                      index=False,
                      if_exists=if_exists)    
        else:
            data.to_sql(name=table_name,
                      con=engine,
                      schema=database,
                      index=False,
                      if_exists=if_exists,dtype=dtype)
            
        
        print ("If no error message, task completed")
#         self.conn.close()

    def get_data(self, sql):
        get = pd.DataFrame()
        for chunk in pd.read_sql(sql, self.conn,chunksize = 10000):
            get = get.append(chunk)
#             print("Finish 1 chunk")
        
        return get

    
    

class connect_mongo:
    def __init__(self, coll_name, table = None):
        self.client = pymongo.MongoClient('mongodb://localhost:27000',tz_aware=True)
        self.db = self.client[coll_name]
        if table is not None:
            self.table = self.db[table]
    
    def set_table_name(self,table):
        self.table = self.db[table]
    
    
    def delete_duplicates(self,key):

        cursor = self.table.aggregate(
            [
                {"$group": {"_id": "$%s"%key, "unique_id": {"$addToSet": "$_id"}, "count": {"$sum": 1}}},
                {"$match": {"count": { "$gte": 2 }}}
            ]
        )

        response = []
        
        for doc in cursor:
            del doc["unique_id"][0]
            for id in doc["unique_id"]:
                response.append(id)
        return response
    
    def frame_to_mongo(self,data):
        for col in data.columns:
            if "datetime.date" in str(type(data[col].iloc[0])):
                data[col] = data[col].apply(lambda x: datetime.combine(x,datetime.min.time()))
        self.table.insert_many(data.T.to_dict().values())
        
    def update_to_mongo(self,data,key):
        for col in data.columns:
            if "datetime.date" in str(type(data[col].iloc[0])):
                data[col] = data[col].apply(lambda x: datetime.combine(x,datetime.min.time()))
        data_index = list(data.to_dict()[key].values())
        data = list(data.T.to_dict().values())
        for i in range(len(data)):
            self.table.update_one({key:data_index[i]},{"$set":data[i]},upsert=True)
    
    

def read_file(path):
    with open(path, 'r') as f:
        return f.read()
    
    
def get_columns(database,table):
    conn = connect_sql(database =  database)

    col_list = []
    for row in conn.cursor.columns(table =table):
        col_list.append(row.column_name)

    return col_list

    
def readgateway(line):
    with open(gateway) as file:
        for i in range(line):
            abc = file.readline()
    abc = remove_salt(abc)    
    return abc




####  SORT THE PRICE SERIES ASCENDING

# class mongo:
    

#     def __init__(self,coll_name = "stocks_daily"):
#         try:
#             self.coll_name = coll_name
#             self.conn = connect_sql("ken",readgateway(2))
#             self.stock_list = "cantrade.csv"
#             self.ETF_list = "ETFList.csv"
#             self.initiate_list = [self.stock_list,self.ETF_list]
#             print ("Connection Successful")
#         except:
#             print ("Connection Failed")


#     def get_all_quote(self):
#         result = pd.DataFrame()
#         all_stock_1 = pd.read_csv(directory + self.stock_list)
#         all_stock_2 = pd.read_csv(directory + self.ETF_list)
#         all_stock_2 = all_stock_2.rename(columns={"Symbol":"Ticker"})
#         all_stock = all_stock_1.append(all_stock_2)
#         all_stock = all_stock.reset_index()
#         for i in range(99,len(all_stock),100):
#             tic_list = all_stock.Ticker.iloc[i-99:i].astype(str)
#             result = result.append(self.get_ondemand_quote(tic_list))   
#         return result

#     def query_database(self,stock, start_date = datetime.now()-timedelta(days =200),end_date=datetime.now()+timedelta(days = 1)):
        
        
#         sql = '''
        
        
#         select * from `%s`.`%s`
        
#         where TimeStamp between '%s' and '%s'
        
#         order by TimeStamp
        
        
#         '''%(self.coll_name,stock,start_date.date(),end_date.date())
        
# #         print (sql)
#         get_frame= self.conn.get_data(sql)
        

#         if len(get_frame) == 0:
#             print ("no data for " + stock)

#         get_frame = get_frame.reindex()
#         try:    
#             get_frame = get_frame.drop("Adj Close",axis =1)
#         except:
#             pass
     
#         return get_frame


#     def update_db(self,test = False):
#         pre = time.time()
       
#         for j in self.initiate_list:
#             all_stock = pd.read_csv(directory+j)
#             for i in all_stock.Ticker:
#                 try:
#                     print (i)
 
    
#                     quote = da.get_quote_yahoo(i)
#                     if self.coll_name == "stocks_daily":
                    
#                         quote["regularMarketTime"] = datetime.today().date()
                        
#                     else:
#                          quote["regularMarketTime"] = datetime.now()
#                     quote["Ticker"] = quote.index[0]
#                     quote = quote.rename( {"regularMarketTime":"TimeStamp", "regularMarketDayHigh": "High","regularMarketDayLow": "Low", "regularMarketOpen":"Open", "regularMarketVolume":"Volume", "regularMarketPrice":"Close"},axis = "columns") 

#                     if test:
#                         return quote
#                     self.conn.to_sql(quote,self.coll_name,i,if_exists="append")
#                     clear_output()
#                     print ("successed " + i)
#                 except Exception as e:
#                     print ( e)
#                     print ("error occored in updating "+ str(i))
#                     continue 
#         post = time.time()
#         return post - pre
    
    
# #
# #     def update_db_multi(self):
# #         # Worker function defines in this file outside of the class
# #         pre = time.time()
# # #         now_time = datetime(datetime.utcnow().year,datetime.utcnow().month,datetime.utcnow().day,datetime.utcnow().hour,datetime.utcnow().minute)
# #         now_time = datetime.now()
# #         jobs = []
# #         pool = multiprocessing.pool.ThreadPool(processes = 4)
# #         for j in self.initiate_list:
# #             all_stock = pd.read_csv(directory+j)
# #             for i in range(0,len(all_stock.Ticker)+1,500):
# #                 tickers = all_stock.Ticker.iloc[i:i+499]
# #                 pool.apply_async(update_worker,args=(self.coll_name,tickers,now_time))
# #
# #         pool.close()
# #         pool.join()
# #         post = time.time()
# #         return post - pre
        
    
    
#     def update_db_new_minute(self):
#         pre = time.time()
            
#         db_name = "stocks_10minute"
#         for j in self.initiate_list:
#             all_stock = pd.read_csv(directory+j)
#             for i in all_stock.Ticker:
#                 try:
#                     print (i)
#                     temp = pd.DataFrame()
#                     quote = get_price_data([i], method = "intraday")
# #                     quote.TimeStamp= quote.TimeStamp.apply(lambda x: \
# #                                 datetime.strptime(x,"%Y-%m-%dT%H:%M:%SZ"))
                    
#                     if len(quote) == 0:
#                         print ("No data from quote")
#                         continue
                    
#                     try:
#                         temp = self.conn.get_data("select * from `%s`.`%s`"%(db_name,i))
                        
#                         temp.to_csv(directory + "Stock_10minutes_Backup/"+str(i)+".csv",index = False)
                    
#                         self.conn.conn.cursor().execute("drop table `%s`.`%s`"%(db_name,i))
#                         self.conn.conn.commit()
#                         print ("Table Dropped")
#                     except:
#                         temp = quote
#                         print ("Probably not exist")
#                         pass
                    
#                     temp = temp.append(quote).drop_duplicates(subset=["TimeStamp"])
#                     self.conn.to_sql(temp,db_name,i,if_exists="append")
# #                     clear_output()
#                     print ("successed " + i)
#                 except Exception as e:
#                     print ( e)
#                     print ("error occored in updating "+ str(i))
#                     send_email("error occored in updating " + str(i) + "\n\n" + str(e))

                    
               
#                     continue 
#         post = time.time()
#         return post - pre
    
    
#     def update_db_new_minute_quick(self):
#         pre = time.time()
            
#         db_name = "stocks_10minute"
#         for j in self.initiate_list:
#             all_stock = pd.read_csv(directory+j)
#             for i in all_stock.Ticker:
#                 try:
#                     print (i)
                    
#                     quote = get_price_data([i], method = "intraday", back_day = 0)

#                     if len(quote) == 0:
#                         print ("No data from quote")
#                         continue
           
#                     self.conn.to_sql(quote,db_name,i,if_exists="append")
# #                     clear_output()
#                     print ("successed " + i)
#                 except Exception as e:
#                     print ( e)
#                     print ("error occored in updating "+ str(i))
               
#                     continue 
#         post = time.time()
#         return post - pre
    
    
#     def update_db_new_minute_mongo(self):
#         pre = time.time()
#         db_name = "stocks_10minute"
#         mongo_conn = connect_mongo(db_name)
            
        
#         for j in self.initiate_list:
#             all_stock = pd.read_csv(directory+j)
#             for i in all_stock.Ticker:
#                 try:
#                     print (i)
#                     mongo_conn.set_table_name(i)
                    
#                     quote = get_price_data([i], method = "intraday", back_day = 0)

#                     if len(quote) == 0:
#                         print ("No data from quote")
#                         continue
           
#                     mongo_conn.update_to_mongo(quote,"TimeStamp")
# #                     clear_output()
#                     print(("successed " + i))
#                 except Exception as e:
#                     print ( e)
#                     print(("error occored in updating "+ str(i)))
               
#                     continue 
#         post = time.time()
#         return post - pre
    
    
#     def update_db_new_day(self):
#         pre = time.time()
            
#         db_name = "stocks_daily"
#         for j in self.initiate_list:
#             all_stock = pd.read_csv(directory+j)
#             for i in all_stock.Ticker:
#                 try:
#                     print (i)
#                     temp = pd.DataFrame()
#                     quote = get_price_data([i], method = "realtimeday")
# #                     quote.TimeStamp= quote.TimeStamp.apply(lambda x: \
# #                                 datetime.strptime(x,"%Y-%m-%dT%H:%M:%SZ"))
#                     if len(quote) == 0:
#                         print ("No data from quote")
#                         continue
#                     try:
#                         temp = self.conn.get_data("select * from `%s`.`%s`"%(db_name,i))
#                         temp.to_csv(directory + "Stock_daily_Backup/"+str(i)+".csv",index = False)
                    
#                         self.conn.conn.cursor().execute("drop table `%s`.`%s`"%(db_name,i))
#                         self.conn.conn.commit()
#                         print ("Table Dropped")
#                     except:
#                         temp = pd.DataFrame()
#                         print ("Probably not exist")
#                         pass
                    
#                     temp = temp.append(quote).drop_duplicates(subset=["TimeStamp"])
#                     self.conn.to_sql(temp,db_name,i,if_exists="append")
# #                     clear_output()
#                     print ("successed " + i)
#                 except Exception as e:
#                     print ( e)
#                     print ("error occored in updating "+ str(i))
#                     send_email("error occored in updating "+ str(i) + "\n\n" + str(e))
                   
#                     continue 
#         post = time.time()
#         return post - pre
    
    
#     def update_db_new_day_quick(self):
#         pre = time.time()
            
#         db_name = "stocks_daily"
#         for j in self.initiate_list:
#             all_stock = pd.read_csv(directory+j)
#             for i in all_stock.Ticker:
#                 try:
#                     print (i)
                    
#                     quote = get_price_data([i], method = "realtimeday", back_day = 0)

#                     if len(quote) == 0:
#                         print ("No data from quote")
#                         continue
           
#                     self.conn.to_sql(quote,db_name,i,if_exists="append")
# #                     clear_output()
#                     print ("successed " + i)
#                 except Exception as e:
#                     print ( e)
#                     print ("error occored in updating "+ str(i))
                
#                     continue 
#         post = time.time()
#         return post - pre
    
    
#     def update_db_new_day_mongo(self):
#         pre = time.time()
#         db_name = "stocks_daily"
#         mongo_conn = connect_mongo(db_name)
            
        
#         for j in self.initiate_list:
#             all_stock = pd.read_csv(directory+j)
#             for i in all_stock.Ticker:
#                 try:
#                     print (i)
#                     mongo_conn.set_table_name(i)
                    
#                     quote = get_price_data([i], method = "realtimeday", back_day = 3)

#                     if len(quote) == 0:
#                         print ("No data from quote")
#                         continue
           
#                     mongo_conn.update_to_mongo(quote,"TimeStamp")
# #                     clear_output()
#                     print(("successed " + i))
#                 except Exception as e:
#                     print ( e)
#                     print(("error occored in updating "+ str(i)))
               
#                     continue 
#         post = time.time()
#         return post - pre
    
    
    
#     def ifexist(self, tablename, target,target_col = "TimeStamp"):
#         sql = '''
#         select * from `%s`.`%s`

#         where %s = '%s'

#         '''%(self.coll_name,tablename,target_col,target)
#         try:
#             temp = self.conn.get_data(sql)
#         except:
#             return False
#         if len(temp) == 0:
#             return False
#         else:
#             return True     
 
#     def frame_to_mongo(self,data,collection_str,drop_mode="append",index_col = None):
#         if drop_mode not in ["drop","upsert","append"]:
#             print ("Drop Mode can only be drop, upsert, or append")
#         if drop_mode == "drop":
#             try:
#                 self.conn.conn.cursor().execute("drop table `%s`.`%s`"%(self.coll_name,collection_str))
#             except Exception as e:
#                 print (e)
#                 print ("\n probably table not exist")
#             self.conn.to_sql(data,self.coll_name,collection_str,if_exists="append")
#         elif drop_mode == "upsert":
#             print ("In upsert mode, please make sure column name are matched")
#             try:
#                 temp = self.conn.get_data("select * from `%s`.`%s`"%(self.coll_name,collection_str))
#             except:
#                 print ("Probably table not exist")
#                 temp = pd.DataFrame()
#             if index_col == None:
#                 print ("Please feed a index column for upsert")
#                 raise 
#             elif type(index_col) != list:
#                 index_col = [index_col]
#             temp = temp.append(data).drop_duplicates(subset=index_col)
#             self.conn.to_sql(temp,self.coll_name,collection_str,if_exists="append")
#         elif drop_mode == "append":
#             self.conn.to_sql(data,self.coll_name,collection_str,if_exists="append")
#         else:
#             print ("drop_mode error")
# def update_worker(db_name,tickers,now_time,test = False):
    
#     for i in tickers:
#         try:
#             mongod = mongo(db_name)
# #             mongod = db_name
#             print (i)

#             quote = da.get_quote_yahoo(i)

#             if mongod.coll_name == "stocks_daily":

#                 quote["regularMarketTime"] = datetime(datetime.utcfromtimestamp(quote["regularMarketTime"]).year,datetime.utcfromtimestamp(quote["regularMarketTime"]).month,datetime.utcfromtimestamp(quote["regularMarketTime"]).day)

#             else:
#                  quote["regularMarketTime"] = now_time
#             quote["Ticker"] = quote.index[0]
#             quote = quote.rename( {"regularMarketTime":"TimeStamp", "regularMarketDayHigh": "High","regularMarketDayLow": "Low", "regularMarketOpen":"Open", "regularMarketVolume":"Volume", "regularMarketPrice":"Close"},axis = "columns") 

#             if test:

#                 print ("Success")
#                 return
#             # has to start a different instance
# #             check_db = mongo()
# #             check = check_db.ifexist(i,quote.TimeStamp.iloc[0])
# #             check_db.conn.conn.close()
#             check = mongod.ifexist(i,quote.TimeStamp.iloc[0])
#             if check:
#                 continue
#             mongod.conn.to_sql(quote,mongod.coll_name,i,if_exists="append")

#     #             collection.update_many({"TimeStamp":quote[u'TimeStamp']},{"$set": quote },upsert=True)
#             clear_output()
#             print ("successed " + i)
        
#         except Exception as e:
#             print ( e)
#             print ("error occored in updating "+ str(i))
#             continue 
#     mongod.conn.conn.close()
    
class mongo:
    

    def __init__(self,coll_name = "stocks_daily",table_name=None):
        try:
            self.coll_name = coll_name
            self.conn = connect_mongo(self.coll_name,table_name)
            self.stock_list = "cantrade.csv"
            self.ETF_list = "ETFList.csv"
            self.initiate_list = [self.stock_list,self.ETF_list]
            print ("Connection Successful")
        except:
            print ("Connection Failed")

#     def get_ondemand_quote(self,sym):
#         api_key = 'b59b144a62e058b6c4e265c049dc679f'
#         sym = "%2C".join(sym)
#         # This is the required format for datetimes to access the API

#         api_url = 'https://marketdata.websol.barchart.com/getQuote.csv?' +\
#                         'apikey={}&symbols={}&mode=D'\
#                              .format(api_key,sym)

#         csvfile = pd.read_csv(api_url)
#         csvfile = csvfile.rename(columns={"symbol":"Ticker","serverTimestamp":"TimeStamp",\
#                            "open":"Open","high":"High","low":"Low","close":"Close",\
#                            "volume":"Volume","lastPrice":"Adj Close","netChange":"net_Return","percentChange":"Return"})
#         #csvfile.set_index('timestamp', inplace=True)
#         return csvfile

    def get_all_quote(self):
        result = pd.DataFrame()
        all_stock_1 = pd.read_csv(directory + self.stock_list)
        all_stock_2 = pd.read_csv(directory + self.ETF_list)
        all_stock_2 = all_stock_2.rename(columns={"Symbol":"Ticker"})
        all_stock = all_stock_1.append(all_stock_2)
        all_stock = all_stock.reset_index()
        for i in range(99,len(all_stock),100):
            tic_list = all_stock.Ticker.iloc[i-99:i].astype(str)
            result = result.append(self.get_ondemand_quote(tic_list))   
        return result

    def query_database(self,stock, start_date = datetime.now()-timedelta(days =200),end_date=datetime.now()+timedelta(days = 1)):
        
        collection = self.conn.db[stock]
        #self.delete_duplicates(stock)
#         start_date=(start_date-datetime.utcfromtimestamp(0)).total_seconds()*1000

#         end_date = (end_date-datetime.utcfromtimestamp(0)).total_seconds()*1000

        get = collection.find({"Ticker":stock,"TimeStamp":{"$gte":start_date,"$lte":end_date}}).sort("TimeStamp",pymongo.ASCENDING)
        get_frame = pd.DataFrame(list(get))
        if len(get_frame) == 0:
            print ("no data for " + stock)
            return
#         if self.coll_name == "stocks_10minute": 
#             get_frame[u'TimeStamp'] = get_frame[u'TimeStamp'].apply(lambda x: change_timezone(datetime.utcfromtimestamp(0) + timedelta(milliseconds= x), "US/Pacific"))
#         else:
#             get_frame[u'TimeStamp'] = get_frame[u'TimeStamp'].apply(lambda x: datetime.utcfromtimestamp(0) + timedelta(milliseconds= x))
        #get_frame = get_frame.rename(columns={"Close":"Adj_close"})
        get_frame = get_frame.reindex()
        try:    
            get_frame = get_frame.drop("Adj Close",axis =1)
        except:
            pass
     
        return get_frame

#     def frame_to_mongo(self,data,collection_str):
#         collection = self.conn.db[collection_str]
#         records = json.loads(data.T.to_json()).values()
#         collection.insert_many(records)
#         collection.find().close()


    def update_db_new_minute_mongo(self):
        pre = time.time()
        db_name = "stocks_10minute"
        mongo_conn = connect_mongo(db_name)
            
        
        for j in self.initiate_list:
            all_stock = pd.read_csv(directory+j)
            for i in all_stock.Ticker:
                try:
                    print (i)
                    mongo_conn.set_table_name(i)
                    
                    quote = get_price_data([i], method = "intraday", back_day = 0)

                    if len(quote) == 0:
                        print ("No data from quote")
                        continue
           
                    mongo_conn.update_to_mongo(quote,"TimeStamp")
#                     clear_output()
                    print(("successed " + i))
                except Exception as e:
                    print ( e)
                    print(("error occored in updating "+ str(i)))
               
                    continue 
        post = time.time()
        return post - pre
        
   
    def update_db_new_day_mongo(self):
        pre = time.time()
        db_name = "stocks_daily"
        mongo_conn = connect_mongo(db_name)
            
        
        for j in self.initiate_list:
            all_stock = pd.read_csv(directory+j)
            for i in all_stock.Ticker:
                try:
                    print (i)
                    mongo_conn.set_table_name(i)
                    
                    quote = get_price_data([i], method = "realtimeday", back_day = 3)

                    if len(quote) == 0:
                        print ("No data from quote")
                        continue
           
                    mongo_conn.update_to_mongo(quote,"TimeStamp")
#                     clear_output()
                    print(("successed " + i))
                except Exception as e:
                    print ( e)
                    print(("error occored in updating "+ str(i)))
               
                    continue 
        post = time.time()
        return post - pre        
        
    
  

#     def translate_time(time, timezone = "US/Pacific"):
#         return change_timezone(datetime.utcfromtimestamp(0) + timedelta(milliseconds= time), timezone)
    
    
#     def clean_up(self,reduce=False):
#         error = pd.DataFrame()
        
#         for j in self.initiate_list:
#             all_stock = pd.read_csv(directory+j)
#             collection = self.db[all_stock.Ticker[0]]
#             first = collection.find({"Ticker":all_stock.Ticker[0]}).sort("TimeStamp",pymongo.ASCENDING)
#             first = pd.DataFrame(list(first))
#             for i in all_stock.Ticker:
#                 collection = self.db[str(i)]
#                 delete_list = collection.find({"Ticker":str(i)}).sort("TimeStamp",pymongo.ASCENDING)
#                 delete_list = pd.DataFrame(list(delete_list))
#                 if not reduce:
#                     if len(first) >= len(delete_list) - len(list(delete_list[:len(delete_list)/4])):
#                         print ("Skipped: " + str(i))
#                         continue
#                 try:
                    
#                     delete_list[u'TimeStamp'] = delete_list[u'TimeStamp'].apply(lambda x: datetime.utcfromtimestamp(0) + timedelta(milliseconds= x))
#                     collection.delete_many({"_id":{"$in":list(delete_list[:len(delete_list)/4]._id)}})
#                     print ("Cleaned " + str(i))
#                 except Exception as e:
#                     print (e)
#                     error = error.append([(i,e)])
#         return error
    
 






    
        
                
    
#********************************************************
#********************************************************
#********************************************************
#********************************************************
#********************************************************
#********************************************************
#********************************************************

# import smtplib, ssl
# from email.parser import Parser
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

# def send_email(body_html, sent_from="lgyhz1234@gmail.com", sent_to="lgyhz1234@gmail.com", title="Daily Position",
#                body_content=""):
#     must_have = readgateway(2)

#     sent_to = sent_to.strip('[]').split(',')

#     if len(sent_to) > 1:

#         headers = Parser().parsestr('From: <' + sent_from + '>\n'
#             'To: <' + ", ".join(sent_to) + '>\n'
#             'Subject: ' + title + '\n'
#                                  '\n' +
#             body_content +
#             '\n')
#     else:
#         headers = Parser().parsestr('From: <' + sent_from + '>\n'
#         'To: <' + sent_to[0] + '>\n'
#         'Subject: ' + title + '\n'
#                  '\n' +
#         body_content +
#         '\n')

#     message = MIMEMultipart("alternative")
#     message["Subject"] = title
#     message["From"] = sent_from

#     plain = MIMEText(body_content, "plain")
#     message.attach(plain)
#     if body_html is not None:
#         message.attach(MIMEText(body_html, "html"))

#     #  Now the header items can be accessed as a dictionary:
#     print ('To: %s' % headers['to'])
#     print ('From: %s' % headers['from'])
#     print ('Subject: %s' % headers['subject'])

#     context = ssl.create_default_context()
#     s = smtplib.SMTP("smtp.gmail.com:587")

#     # s.connect("stmp.gmail.com")

#     s.ehlo()
#     s.starttls()
#     s.login(sent_from, must_have)

#     for receiver in sent_to:
#         message["To"] = receiver
#         s.sendmail(sent_from, receiver, message.as_string())
#     s.close()


# if __name__ == "__main__":
#     send_email()
