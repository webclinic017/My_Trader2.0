########################   
# Get Finviz Data
########################        

from my_libs import *
from selenium import webdriver as se
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
import os


success = 0

while success < 3:

    try:
        options = se.FirefoxOptions()
        options.add_argument("--headless")

        path = home_dir + "notebook/My_Trader2.0/file/"
    #     download_path = "C:/Users/gli26/Downloads/"
        fp = se.FirefoxProfile()
        fp.set_preference("browser.download.folderList", 2)
        fp.set_preference("browser.download.manager.showWhenStarting", False)
        fp.set_preference("browser.download.dir", path)
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv,application/octet-stream,application/vnd.ms-excel,application/csv")


        driver = se.Firefox(executable_path=home_dir+"/notebook/My_Trader2.0/geckodriver",options=options,firefox_profile=fp)

        driver.set_window_size(8000,5000)

        # get cookies from file
        cookies = pickle.load(open(path+"cookies.pkl", "rb"))




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

        if os.path.exists(path + "finviz.csv") and success == 0:
            os.remove(path + "finviz.csv")
            print ("Old file removed")



        export.click()

        time.sleep(10)
        data = pd.read_csv(path + "finviz.csv")
        data = data.drop(["No."],axis=1)

        driver.get('https://finviz.com')
        cookies = driver.get_cookies()


        time.sleep(2)
        pickle.dump( cookies , open(path+"cookies.pkl","wb"),protocol=2)
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
                row +1
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
        success += 1