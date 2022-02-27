from .my_libs_py3 import *
from selenium import webdriver as se
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
import os


########################
# New Minute Data
########################


def update_minute_data():

    try:

        mongod = mongo()
        runtime = mongod.update_db_new_minute_mongo()


        send_email("New Minute Data runtime: " + str(runtime))

    except Exception as e:
        send_email("New Minute Data error: " + str(e))
        
        

########################   
# New Daily Data
########################

def update_day_data():
    try:

        mongod = mongo()
        runtime = mongod.update_db_new_day_mongo()
        send_email("New day Data mongo runtime: " + str(runtime))
        # runtime = mongod.update_db_new_day()
        # send_email("New day Data runtime: " + str(runtime))

    except Exception as e:
        send_email("New day Data error: " + str(e))
        
        

        
        
########################   
# Future price
########################
    
def update_future_data_day():
    try: 
        my_future = future()



        symbol =  "VX" + "/" + my_future.monthCode(datetime.now().month+1) + str(int(datetime.now().year)+1)[-1:] if datetime.now().month + 1 > 12 \
                  else "VX" + "/" + my_future.monthCode(datetime.now().month + 1) + str(datetime.now().year)[-1:]

        new_frame = pd.DataFrame({"TimeStamp":datetime(datetime.now().year,datetime.now().month,datetime.now().day),"Close":[my_future.get_future_price(datetime.now().year,datetime.now().month)],"VIX_Day_Roll":((my_future.get_future_price(datetime.now().year,datetime.now().month) - realtimequote("^VIX").price.values[0])/my_future.get_historic_data(my_future.get_future_expiration(datetime.now().year,datetime.now().month)).Close.std())/30, "symbol":symbol}).reset_index()
        new_frame = new_frame.drop("index",axis = 1)


        # table_name = "VX" + my_future.monthCode(datetime.now().month+1)+str(datetime.now().year)[-2:]

        # mongod.conn.to_sql(new_frame,"future",symbol,if_exists="append")
        mongo_conn = connect_mongo("future",symbol)
        mongo_conn.update_to_mongo(new_frame,"TimeStamp")


    #     new_frame=json.loads(new_frame.T.to_json()).values()[0]

    #     mongod.db["VX" + my_future.monthCode(datetime.now().month+1)+str(datetime.now().year)[:-2]].update_many({"TimeStamp":new_frame["TimeStamp"]},{"$set":new_frame},upsert=True)


    #     update_fundamentals(robingateway(), skip_can=False)

        send_email(body_html="",body_content="", title = "future price update done")



    except Exception as e:

        send_email(body_html="",body_content="", title = str(e) +" future price update error") 
        
        
        

########################   
# Future price
########################
    
def update_future_data_minute():
    try:

        my_future = future()



        symbol = "VX" + "/" + my_future.monthCode(datetime.now().month + 1) + str(int(datetime.now().year) + 1)[-1:] if datetime.now().month + 1 > 12 \
            else "VX" + "/" + my_future.monthCode(datetime.now().month + 1) + str(datetime.now().year)[-1:]

        new_frame = pd.DataFrame({"TimeStamp":datetime.now(),"Close":[my_future.get_future_price(datetime.now().year,datetime.now().month)],"VIX_Day_Roll":((my_future.get_future_price(datetime.now().year,datetime.now().month) - realtimequote("^VIX").price.values[0])/my_future.get_historic_data(my_future.get_future_expiration(datetime.now().year,datetime.now().month)).Close.std())/30, "symbol":symbol}).reset_index()
        new_frame = new_frame.drop("index",axis = 1)
    #     new_frame=json.loads(new_frame.T.to_json()).values()[0]

        # table_name = "VX" + my_future.monthCode(datetime.now().month+1)+str(datetime.now().year)[:-2]

        # mongod.conn.to_sql(new_frame,"future_minute",symbol,if_exists = "append")
        mongo_conn = connect_mongo("future_minute",symbol)
        mongo_conn.update_to_mongo(new_frame,"TimeStamp")

    #     mongod.db["VX" + my_future.monthCode(datetime.now().month+1)+str(datetime.now().year)[:-2]].update_many({"TimeStamp":new_frame["TimeStamp"]},{"$set":new_frame},upsert=True)


    except Exception as e:

        send_email(body_html="",body_content="", title = str(e) + "future minute price update error") 
        
        
        
        
########################   
# Finviz Data
########################       

def finviz_data():
    success = 0

    while success < 3:

        try:
            ## path defined in my_lib.py

            options = se.FirefoxOptions()
            # options = se.firefox.options.Options()
            options.add_argument("--headless")
            # options.add_argument("/home/airflow/t0itviv0.default-release")
            # options.binary_location = "/usr/lib/firefox/firefox"


            # fp = se.FirefoxProfile()
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.manager.showWhenStarting", False)
            options.set_preference("browser.download.dir", gecko_download_path)
            options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv,application/octet-stream,application/vnd.ms-excel,application/csv")
            driver = se.Remote(gecko_path, options=options)


#             driver = se.Firefox(executable_path=home_dir+"notebook/My_Trader/chromedriver",options=options,firefox_profile=fp,
#                                 )

            driver.set_window_size(8000,5000)

            # options = se.ChromeOptions()
            # options.add_argument("--headless")
            # options.add_argument("--no-sandbox")
            # options.add_argument("–-disable-dev-shm-usage")
            # options.add_argument("--window-size=8000,5000")
            # prefs = {'download.default_directory' : path}
            # options.add_experimental_option('prefs', prefs)
            # driver = se.Chrome(executable_path=home_dir+"notebook/My_Trader/chromedriver",
            #                     options=options)

            # get cookies from file
            cookies = pickle.load(open(gecko_download_path+"cookies.pkl", "rb"))

            driver.get('https://finviz.com')
            for i in cookies:
                try:
                    driver.add_cookie(i)
                except:
                    continue
            driver.refresh()

            time.sleep(8)
            



            driver.get("https://elite.finviz.com/screener.ashx?v=152&c=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,19,21,22,23,24,26,27,28,29,35,36,37,38,39,40,41,42,43,44,48,51,52,53,54,57,58,59,60,61,62,63,64,65,66,67,69")


            export = driver.find_element_by_link_text("export")

             ## Remove the file if exists

            if os.path.exists(gecko_download_path + "finviz.csv") and success == 0:
                os.remove(gecko_download_path + "finviz.csv")
                print ("Old file removed")



            export.click()

            time.sleep(10)
            data = pd.read_csv(gecko_download_path + "finviz.csv")
            data = data.drop(["No."],axis=1)

            driver.get('https://finviz.com')
            cookies = driver.get_cookies()


            time.sleep(2)
            pickle.dump( cookies , open(gecko_download_path+"cookies.pkl","wb"),protocol=2)
            driver.close()
            ## parser

            def parser (data):
                if data != data or data is None:
                    return data
                data = data.replace("%","")
                return float(data)/100.0

            for i in data.columns:
                row = 0 
                while data.loc[row,i] != data.loc[row,i] or data.loc[row,i] == None:
                    row = row +1
                try:
                    if "%" in data.loc[row,i]:
                        data.loc[:,i] = data[i].apply(lambda x: parser(x))

                except:
                    continue

            data["Refresh_Date"] = datetime.today()   #.date()

            screener = data

            screener = screener.set_index("Ticker")

            screener["toTarget"] = screener.Price -screener["Target Price"]

            screener = screener[screener["EPS (ttm)"]>0]

        #         lowerbetter = screener.groupby(["Sector"]).agg({"P/S":"rank",'P/Cash':"rank",'P/E':"rank",'P/Free Cash Flow':"rank",'Analyst Recom':"rank",'Total Debt/Equity':"rank"},ascending = True, method = "First")
            lowerbetter= screener.groupby(["Sector"])[["P/S",'P/Cash','P/E','P/Free Cash Flow','Analyst Recom','Total Debt/Equity']].rank(ascending = True,method = "first")

        #         higherbetter = screener.groupby(["Sector"]).agg({'Current Ratio':"rank",'Quick Ratio':"rank",'Sales growth quarter over quarter':"rank",'Performance (Week)':"rank",'Profit Margin':"rank",'EPS (ttm)':"rank",'Operating Margin':"rank",'Insider Ownership':"rank",'Institutional Ownership':"rank",'Gross Margin':"rank"},ascending = False, method = "First")

            higherbetter= screener.groupby(["Sector"])[['Performance (Week)','Current Ratio','Quick Ratio','Sales growth quarter over quarter','Profit Margin','EPS (ttm)','Operating Margin','Insider Ownership','Institutional Ownership','Gross Margin']].rank(ascending = False,method = "first")

            neutral = screener.groupby(["Sector"]).agg({'Average Volume':"rank",'Market Cap':"rank",'Shares Outstanding':"rank","toTarget":"rank",'Volatility (Month)':"rank",'Relative Volume':"rank"},ascending = False, method = "First")

            screenermodel = screener[["Sector","Industry","Refresh_Date"]].join(lowerbetter).join(higherbetter).reset_index()

            screenervol = screener[["Sector","Industry","Refresh_Date"]].join(neutral).reset_index()


            mongod = mongo("all_symbol","screener")
        #         mongod.db.drop_collection("screener")
            mongod.conn.frame_to_mongo(data)

            mongod.conn.table = mongod.conn.db["screenerModel"]
            mongod.conn.frame_to_mongo(screenermodel)
            mongod.conn.table = mongod.conn.db["screenerVol"]
            mongod.conn.frame_to_mongo(screenervol)

            success = 3
            send_email(title = "Finviz download done",body_html="")

        except Exception as e:
            if success > 1:
                send_email(title = "Finviz download error", body_html = str(e))
                raise Exception(e)
            success += 1