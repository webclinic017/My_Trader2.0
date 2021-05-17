import pymysql
import pandas as pd
import time
from datetime import datetime, timedelta
import numpy as np
import sqlalchemy as sa

# def connect_dw(sql,server_name = 'rkhrimdb01',tcon = 'yes'):
#     # return pandas dataframe
#     conn = pyodbc.connect(Driver='{ODBC Driver 11 for SQL Server}', host=server_name, trusted_connection=tcon)
#     cursor = conn.cursor()
#     return pd.read_sql(sql,conn) , cursor

# pd.options.display.max_rows = 2000
# pd.options.display.max_columns = 2000


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
        
        self.cursor = self.conn.cursor()

    def to_sql(self, data, database, table_name, dtype = None,if_exists = 'fail' ):
#         check = input("Caution!! Type 'Confirm to continue'")
#         if check != "Confirm":
#             print ("no action")
#             return 

        engine = sa.create_engine("mysql+pymysql://%s:@%s/%s"%(self.user,self.host,database), poolclass=sa.pool.StaticPool, creator=lambda: self.conn)#,fast_executemany = True)
        

        
    
        if dtype == None:
            data.to_sql(name=table_name,
                      con=engine,
                      schema=database ,
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
    

def read_file(path):
    with open(path, 'r') as f:
        return f.read()
    
    
def get_columns(database,table):
    conn = connect_sql(database =  database)

    col_list = []
    for row in conn.cursor.columns(table =table):
        col_list.append(row.column_name)

    return col_list


class mongo:
    

    def __init__(self,coll_name = "stocks_daily"):
        
        self.coll_name = coll_name
        self.conn = connect_sql("ken",readgateway(2))
        self.stock_list = "cantrade.csv"
        self.ETF_list = "ETFList.csv"
        self.initiate_list = [self.stock_list,self.ETF_list]
        print ("Connection Successful")
        


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
        
        
        sql = '''
        
        
        select * from `%s`.`%s`
        
        where TimeStamp between '%s' and '%s'
        
        order by TimeStamp
        
        
        '''%(self.coll_name,stock,start_date.date(),end_date.date())
        
#         print (sql)
        get_frame= self.conn.get_data(sql)
        

        if len(get_frame) == 0:
            print(("no data for " + stock))

        get_frame = get_frame.reindex()
        try:    
            get_frame = get_frame.drop("Adj Close",axis =1)
        except:
            pass
     
        return get_frame


    def update_db(self,test = False):
        pre = time.time()
       
        for j in self.initiate_list:
            all_stock = pd.read_csv(directory+j)
            for i in all_stock.Ticker:
                try:
                    print (i)
 
    
                    quote = da.get_quote_yahoo(i)
                    if self.coll_name == "stocks_daily":
                    
                        quote["regularMarketTime"] = datetime.today().date()
                        
                    else:
                         quote["regularMarketTime"] = datetime.now()
                    quote["Ticker"] = quote.index[0]
                    quote = quote.rename( {"regularMarketTime":"TimeStamp", "regularMarketDayHigh": "High","regularMarketDayLow": "Low", "regularMarketOpen":"Open", "regularMarketVolume":"Volume", "regularMarketPrice":"Close"},axis = "columns") 

                    if test:
                        return quote
                    self.conn.to_sql(quote,self.coll_name,i,if_exists="append")
                    clear_output()
                    print(("successed " + i))
                except Exception as e:
                    print ( e)
                    print(("error occored in updating "+ str(i)))
                    continue 
        post = time.time()
        return post - pre
    
    
    
    def update_db_multi(self):
        # Worker function defines in this file outside of the class
        pre = time.time()
#         now_time = datetime(datetime.utcnow().year,datetime.utcnow().month,datetime.utcnow().day,datetime.utcnow().hour,datetime.utcnow().minute)
        now_time = datetime.now()
        jobs = []
        pool = multiprocessing.pool.ThreadPool(processes = 4)
        for j in self.initiate_list:
            all_stock = pd.read_csv(directory+j)
            for i in range(0,len(all_stock.Ticker)+1,500):
                tickers = all_stock.Ticker.iloc[i:i+499]
                pool.apply_async(update_worker,args=(self.coll_name,tickers,now_time))

        pool.close()
        pool.join()
        post = time.time()
        return post - pre
        
    
    
    def update_db_new_minute(self):
        pre = time.time()
            
        db_name = "stocks_10minute"
        for j in self.initiate_list:
            all_stock = pd.read_csv(directory+j)
            for i in all_stock.Ticker:
                try:
                    print (i)
                    temp = pd.DataFrame()
                    quote = get_price_data([i], method = "intraday")
#                     quote.TimeStamp= quote.TimeStamp.apply(lambda x: \
#                                 datetime.strptime(x,"%Y-%m-%dT%H:%M:%SZ"))
                    
                    if len(quote) == 0:
                        print ("No data from quote")
                        continue
                    
                    try:
                        temp = self.conn.get_data("select * from `%s`.`%s`"%(db_name,i))
                        
                        temp.to_csv(directory + "Stock_10minutes_Backup/"+str(i)+".csv",index = False)
                    
                        self.conn.conn.cursor().execute("drop table `%s`.`%s`"%(db_name,i))
                        self.conn.conn.commit()
                        print ("Table Dropped")
                    except:
                        temp = quote
                        print ("Probably not exist")
                        pass
                    
                    temp = temp.append(quote).drop_duplicates(subset=["TimeStamp"])
                    self.conn.to_sql(temp,db_name,i,if_exists="append")
#                     clear_output()
                    print(("successed " + i))
                except Exception as e:
                    print ( e)
                    print(("error occored in updating "+ str(i)))
                    
               
                    continue 
        post = time.time()
        return post - pre
    
    
    def update_db_new_minute_quick(self):
        pre = time.time()
            
        db_name = "stocks_10minute"
        for j in self.initiate_list:
            all_stock = pd.read_csv(directory+j)
            for i in all_stock.Ticker:
                try:
                    print (i)
                    
                    quote = get_price_data([i], method = "intraday", back_day = 0)

                    if len(quote) == 0:
                        print ("No data from quote")
                        continue
           
                    self.conn.to_sql(quote,db_name,i,if_exists="append")
#                     clear_output()
                    print(("successed " + i))
                except Exception as e:
                    print ( e)
                    print(("error occored in updating "+ str(i)))
               
                    continue 
        post = time.time()
        return post - pre
    
    
    def update_db_new_day(self):
        pre = time.time()
            
        db_name = "stocks_daily"
        for j in self.initiate_list:
            all_stock = pd.read_csv(directory+j)
            for i in all_stock.Ticker:
                try:
                    print (i)
                    temp = pd.DataFrame()
                    quote = get_price_data([i], method = "realtimeday",back_day = 10)
#                     quote.TimeStamp= quote.TimeStamp.apply(lambda x: \
#                                 datetime.strptime(x,"%Y-%m-%dT%H:%M:%SZ"))
                    if len(quote) == 0:
                        print ("No data from quote")
                        continue
                    try:
                        temp = self.conn.get_data("select * from `%s`.`%s`"%(db_name,i))
                        temp.to_csv(directory + "Stock_daily_Backup/"+str(i)+".csv",index = False)
                    
                        self.conn.conn.cursor().execute("drop table `%s`.`%s`"%(db_name,i))
                        self.conn.conn.commit()
                        print ("Table Dropped")
                    except:
                        temp = pd.DataFrame()
                        print ("Probably not exist")
                        pass
                    
                    temp = temp.append(quote).drop_duplicates(subset=["TimeStamp"])
                    self.conn.to_sql(temp,db_name,i,if_exists="append")
#                     clear_output()
                    print(("successed " + i))
                except Exception as e:
                    print ( e)
                    print(("error occored in updating "+ str(i)))
                   
                    continue 
        post = time.time()
        return post - pre
    
    
    def update_db_new_day_quick(self):
        pre = time.time()
            
        db_name = "stocks_daily"
        for j in self.initiate_list:
            all_stock = pd.read_csv(directory+j)
            for i in all_stock.Ticker:
                try:
                    print (i)
                    
                    quote = get_price_data([i], method = "realtimeday", back_day = 0)

                    if len(quote) == 0:
                        print ("No data from quote")
                        continue
           
                    self.conn.to_sql(quote,db_name,i,if_exists="append")
#                     clear_output()
                    print(("successed " + i))
                except Exception as e:
                    print ( e)
                    print(("error occored in updating "+ str(i)))
                
                    continue 
        post = time.time()
        return post - pre
    
    
    def ifexist(self, tablename, target,target_col = "TimeStamp"):
        sql = '''
        select * from `%s`.`%s`

        where %s = '%s'

        '''%(self.coll_name,tablename,target_col,target)
        try:
            temp = self.conn.get_data(sql)
        except:
            return False
        if len(temp) == 0:
            return False
        else:
            return True     
 
    def frame_to_mongo(self,data,collection_str,drop_mode="append",index_col = None):
        if drop_mode not in ["drop","upsert","append"]:
            print ("Drop Mode can only be drop, upsert, or append")
        if drop_mode == "drop":
            try:
                self.conn.conn.cursor().execute("drop table `%s`.`%s`"%(self.coll_name,collection_str))
            except Exception as e:
                print (e)
                print ("\n probably table not exist")
            self.conn.to_sql(data,self.coll_name,collection_str,if_exists="append")
        elif drop_mode == "upsert":
            print ("In upsert mode, please make sure column name are matched")
            try:
                temp = self.conn.get_data("select * from `%s`.`%s`"%(self.coll_name,collection_str))
            except:
                print ("Probably table not exist")
                temp = pd.DataFrame()
            if index_col == None:
                print ("Please feed a index column for upsert")
                raise 
            elif type(index_col) != list:
                index_col = [index_col]
            temp = temp.append(data).drop_duplicates(subset=index_col)
            self.conn.to_sql(temp,self.coll_name,collection_str,if_exists="append")
        elif drop_mode == "append":
            self.conn.to_sql(data,self.coll_name,collection_str,if_exists="append")
        else:
            print ("drop_mode error")
def update_worker(db_name,tickers,now_time,test = False):
    
    for i in tickers:
        try:
            mongod = mongo(db_name)
#             mongod = db_name
            print (i)

            quote = da.get_quote_yahoo(i)

            if mongod.coll_name == "stocks_daily":

                quote["regularMarketTime"] = datetime(datetime.utcfromtimestamp(quote["regularMarketTime"]).year,datetime.utcfromtimestamp(quote["regularMarketTime"]).month,datetime.utcfromtimestamp(quote["regularMarketTime"]).day)

            else:
                 quote["regularMarketTime"] = now_time
            quote["Ticker"] = quote.index[0]
            quote = quote.rename( {"regularMarketTime":"TimeStamp", "regularMarketDayHigh": "High","regularMarketDayLow": "Low", "regularMarketOpen":"Open", "regularMarketVolume":"Volume", "regularMarketPrice":"Close"},axis = "columns") 

            if test:

                print ("Success")
                return
            # has to start a different instance
#             check_db = mongo()
#             check = check_db.ifexist(i,quote.TimeStamp.iloc[0])
#             check_db.conn.conn.close()
            check = mongod.ifexist(i,quote.TimeStamp.iloc[0])
            if check:
                continue
            mongod.conn.to_sql(quote,mongod.coll_name,i,if_exists="append")

    #             collection.update_many({"TimeStamp":quote[u'TimeStamp']},{"$set": quote },upsert=True)
            clear_output()
            print(("successed " + i))
        
        except Exception as e:
            print ( e)
            print(("error occored in updating "+ str(i)))
            continue 
    mongod.conn.conn.close()
    
def readgateway(line):
    with open("/home/ken/notebook/My_Trader2.0/record-Copy1.txt") as file:
        for i in range(line):
            abc = file.readline()
    abc = remove_salt(abc)    
    return abc



def remove_salt(x):
    return x.strip("\n").replace("$",'').replace("*",'')
