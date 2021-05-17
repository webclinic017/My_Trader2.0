"""
toolset working with cboe data
@author: Jev Kuznetsov
Licence: BSD
"""
from .my_lib import *
from .my_trader import *
from selenium import webdriver as se
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class future ():


    def monthCode(self, month):
        """ 
        perform month->code and back conversion

        Input: either month nr (int) or month code (str)
        Returns: code or month nr

        """
        if month == 13:
            month = 1
        
        codes = ('F','G','H','J','K','M','N','Q','U','V','X','Z')

        if isinstance(month,int):
            return codes[month-1]
        elif isinstance(month,str):
            return codes.index(month)+1
        else:
            raise ValueError('Function accepts int or str')



    def getPutCallRatio(self):
        """ download current Put/Call ratio"""
        urlStr = 'http://www.cboe.com/publish/ScheduledTask/MktData/datahouse/totalpc.csv'

        try:
            lines = urllib.request.urlopen(urlStr).readlines()
        except Exception as e:
            s = "Failed to download:\n{0}".format(e);
            print(s)

        headerLine = 2

        header = lines[headerLine].strip().split(',')

        data =   [[] for i in range(len(header))]

        for line in lines[(headerLine+1):]:
            fields = line.rstrip().split(',')
            data[0].append(datetime.strptime(fields[0],'%m/%d/%Y'))
            for i,field  in enumerate(fields[1:]):
                data[i+1].append(float(field))


        return DataFrame(dict(list(zip(header[1:],data[1:]))), index = Index(data[0]))


    def get_historic_data(self,date):
        ''' get historic data from CBOE
            symbol: VIX or VXV
            return dataframe
        '''
        if not isinstance(date,datetime):
            return "Please feed a datetime object"

        date = date.strftime("%Y-%m-%d")
        print('Downloading Date: %s' % date)
        urls = "http://markets.cboe.com/us/futures/market_statistics/historical_data/products/csv/VX/{}".format(date)
        #urlStr = urls[date]


        with open("temp.csv", "w") as f:
            f.write( r.get(urls).content.decode() )
            
           
        result = pd.read_csv("temp.csv")
        
        if result.iloc[-1].Close == 0:
            result = result[:-1]
        return result

        #return DataFrame(dict(zip(header,data)),index=Index(dates)).sort_index()



    def get_future_expiration(self,year,month):
        if isinstance(year,int):
            year = str(year)[-1:]
        elif isinstance(year,str):
            year = year[-1:]
        else:
            return ("year format wrong")
        if isinstance(month,str):
            month = int(month)
        if month > 12 or month < 1:
            return ("month format wrong")
        # symbol = "VX" + self.monthCode(month)+year
        symbol = "VX" + "/" + self.monthCode(month) + year
        print (symbol)

        # try:
            # page = r.get("https://www.cboe.com/delayedquote/vix/futures-quotes")
            # soup = bs(page.content, "html.parser")
            # soup.find( attrs= {"title":symbol}).find_next("span").find_next("span").text.split()[0]

        options = se.FirefoxOptions()
        options.add_argument("--headless")
        driver = se.Firefox(executable_path=home_dir + "/notebook/My_Trader2.0/geckodriver.exe", options=options)

        driver.set_window_size(2100, 4000)

        driver.get('https://www.cboe.com/delayed_quotes/vix')
        driver.implicitly_wait(5)
        try:
            element = WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.LINK_TEXT, symbol)))
        except:
            if month + 1 > 12:
                symbol = "VX" + "/" + self.monthCode(month+1) + str(int(year)+1)
            else:
                symbol = "VX" + "/" + self.monthCode(month + 1) + year
            element = WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.LINK_TEXT, symbol)))

        expiration_date = element.find_element_by_xpath(
            "//div[contains(text(),'"+symbol +"')]/ancestor::td[1]/following-sibling::td")

        # except:
        #     if month +1 >12:
        #
        #         # symbol = "VX" + self.monthCode(month+1)+str(int(year)+1)
        #         symbol = "VX" + "/" +self.monthCode(month + 1) +year
        #
        #     else:
        #         # symbol = "VX" + self.monthCode(month+1)+year
        #         symbol = "VX" + "/" + self.monthCode(month + 1) + year
        #
        #     print(("The previous symbol not available, changed to: "+symbol))
        # # page = r.get("https://www.cboe.com/delayedquote/vix/futures-quotes")
        # # soup = bs(page.content, "html.parser")
        # # return datetime.strptime(soup.find( attrs= {"title":symbol}).find_next("span").text.split()[0],"%m/%d/%Y")
        #     expiration_date = element.find_element_by_xpath(
        #         "//div[contains(text(),'" + symbol + "')]/ancestor::td[1]/following-sibling::td")
        result = expiration_date.text
        driver.close()
        return datetime.strptime(result,"%m/%d/%Y")

    def get_future_price(self,year,month,average = False):
        trial = 0 
        while trial < 3:
            try:
                if isinstance(year,int):
                    year = str(year)[-1:]
                elif isinstance(year,str):
                    year = year[-1:]
                else:
                    return ("year format wrong")
                if isinstance(month,str):
                    month = int(month)
                if month > 12 or month < 1:
                    return ("month format wrong")
                # symbol = "VX" + self.monthCode(month)+year
                symbol = "VX" + "/" + self.monthCode(month) + year
                print (symbol)
                # page = r.get("https://www.cboe.com/delayedquote/vix/futures-quotes")
                # soup = bs(page.content, "html.parser")
                options = se.FirefoxOptions()
                options.add_argument("--headless")
                driver = se.Firefox(executable_path=home_dir + "/notebook/My_Trader2.0/geckodriver",options=options)

                driver.set_window_size(2100, 4000)

                driver.get('https://www.cboe.com/delayed_quotes/vix')
                driver.implicitly_wait(5)
                try:
                    element = WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.LINK_TEXT, symbol)))
                except:
                    if month + 1 > 12:
                        symbol = "VX" + "/" + self.monthCode(month + 1) + str(int(year)+1)
                    else:
                        symbol = "VX" + "/" + self.monthCode(month + 1) + year

                    element = WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.LINK_TEXT, symbol)))
                # try:
                    # soup.find( attrs= {"title":symbol}).find_next("span").find_next("span").text.split()[0]
                Last_Price = element.find_element_by_xpath(
                        "//div[contains(text(),'" + symbol + "')]/ancestor::td[1]/following-sibling::td/following-sibling::td")


                # except:
                #     if month +1 >12:
                #
                #         # symbol = "VX" + self.monthCode(month+1)+str(int(year)+1)
                #         symbol = "VX" + "/" + self.monthCode(month + 1) + year
                #     else:
                #         # symbol = "VX" + self.monthCode(month+1)+year
                #         symbol = "VX" + "/" + self.monthCode(month + 1) + year
                #
                #     print(("The previous symbol not available, changed to: "+symbol))
                #
                # Last_Price = element.find_element_by_xpath(
                #     "//div[contains(text(),'" + symbol + "')]/ancestor::td[1]/following-sibling::td/following-sibling::td")
                result = Last_Price.text
                driver.close()
                return float(result)
                # if not average:
                #     return float(soup.find( attrs= {"title":symbol}).find_next("span").find_next("span").text.split()[0])
                # else:
                #     print ("Getting average price")
                #     print("VX" + monthCode(month+1)+year)
                #     return (float(soup.find( attrs= {"title":symbol}).find_next("span").find_next("span").text.split()[0]) + float(soup.find( attrs= {"title":"VX" + monthCode(month+1)+year}).find_next("span").find_next("span").text.split()[0]))/2
            except:
                trial +=1
        
        raise
        
        
class vix_dayroll_trade():
    
    def __init__(self,robinhood,initial = 300,day_range = 54):
        
        self.initial = initial
        self.short_symbol = "SVXY"
        self.long_symbol = "VIXY"
        self.robinhood = robinhood
        self.day_range = day_range
    
    def vix_dayroll(self):

        my_future = future()
        ##Changed to use faward price 6/22/2020
        day_roll = ((my_future.get_future_price(datetime.now().year,datetime.now().month) - fwd_price("^VIX",mat=3,val_num_steps=42))/my_future.get_historic_data(my_future.get_future_expiration(datetime.now().year,datetime.now().month)).Close.std())/30

#         return day_roll.values[0]
        return day_roll   ## returns float after 6/22/2020 change


    def vix_trade_signal(self):

        my_future = future()
        

        vix = get_price_data(["^VIX"],method = "realtimeday",back_day=self.day_range)[-self.day_range:].set_index("TimeStamp")

        vfx = my_future.get_historic_data(my_future.get_future_expiration(datetime.now().year,datetime.now().month))[-self.day_range:].reset_index()
       
       
        vfx = vfx.rename({"Trade Date":"TimeStamp"},axis=1)
        vfx["TimeStamp"] = vfx["TimeStamp"].apply(lambda x: datetime.strptime(x,"%Y-%m-%d"))
        vfx = vfx[vfx.Close != 0 ]

        roll_table = vix.merge(vfx,on="TimeStamp",how="inner")

        roll_table= roll_table.set_index("TimeStamp")

        roll_table["Day_Roll"] = ((roll_table.Close_y - roll_table.Close_x)/roll_table.Close_x.rolling(10).std())/30

        #roll_table.Day_Roll.plot()



        exit = roll_table[["Close_x","Close_y","Day_Roll"]].Day_Roll.quantile(0.3)

        enter = roll_table[["Close_x","Close_y","Day_Roll"]].Day_Roll.quantile(0.6)
        
        buy_enter = roll_table[["Close_x","Close_y","Day_Roll"]].Day_Roll.quantile(0)
        
        buy_exit = roll_table[["Close_x","Close_y","Day_Roll"]].Day_Roll.quantile(0.1)
        
        print ("\nEnter larger than, Exit less than")
        print((roll_table[["Close_x","Close_y","Day_Roll"]]))
        return enter,exit, buy_enter,buy_exit
    
    def trade_action(self):
        # default is the sell strategy
        
        strategy_name = "vix_dayroll"
        
        enter_signal, exit_signal, buy_enter_signal, buy_exit_signal = self.vix_trade_signal()
        
        log = get_trade_log(self.short_symbol)
        log_buy = get_trade_log(self.long_symbol)
        log = log[log.Strategy==strategy_name]
        log_buy = log_buy[log_buy.Strategy==strategy_name]
        
        vix_quote = self.vix_dayroll()
        #vix_quote = -0.0050
        short_size = int(self.initial/realtimequote(self.short_symbol).price.values[0])
        long_size =  int(self.initial/realtimequote(self.long_symbol).price.values[0])
        
        if vix_quote > enter_signal:
            if self.robinhood.place_buy_bulk_checkup(ticker_list=[self.short_symbol],quantity_list=[short_size],price_list=[realtimequote(self.short_symbol).price.values[0]] )== "Trade Success!":
                log_trade(self.short_symbol,short_size, realtimequote(self.short_symbol).price.values[0], "vix_dayroll")
                send_email(body_html="",body_content="", title = "VIX Dayroll enter Signal")
        
        elif vix_quote < exit_signal and log["size"].sum() != 0:
            if self.robinhood.place_sell_bulk_checkup(ticker_list=[self.short_symbol],quantity_list=[log["size"].sum()],price_list=[realtimequote(self.short_symbol).price.values[0]] )== "Trade Success!":
                log_trade(self.short_symbol,-log["size"].sum(), realtimequote(self.short_symbol).price.values[0], "vix_dayroll")
                send_email(body_html="",body_content="", title = "VIX Dayroll exit Signal")
        else:
            print ("no short trade signal")
        
        if vix_quote < buy_enter_signal:
            if self.robinhood.place_buy_bulk_checkup(ticker_list=[self.long_symbol],quantity_list=[long_size],price_list=[realtimequote(self.long_symbol).price.values[0]])== "Trade Success!":
                log_trade(self.long_symbol,long_size, realtimequote(self.long_symbol).price.values[0], "vix_dayroll")
                send_email(body_html="",body_content="", title = "VIX Dayroll buy enter Signal")
        
        
        elif vix_quote > buy_exit_signal and log_buy["size"].sum() != 0:
            if self.robinhood.place_sell_bulk_checkup(ticker_list=[self.long_symbol],quantity_list=[log_buy["size"].sum()],price_list=[realtimequote(self.long_symbol).price.values[0]] )== "Trade Success!":
                log_trade(self.long_symbol,-log_buy["size"].sum(), realtimequote(self.long_symbol).price.values[0], "vix_dayroll")
                send_email(body_html="",body_content="", title = "VIX Dayroll buy exit Signal")
        
        else:
            print ("no long trade signal")
            
        print(("\nDay roll is {:.4f}".format(vix_quote)))
        print(("\nDay roll enter signal is {:.4f}".format(enter_signal)))
        print(("\nDay roll exit signal is {:.4f}".format(exit_signal)))
        print(("\nDay roll buy enter signal is {:.4f}".format(buy_enter_signal)))
        print(("\nDay roll buy exit signal is {:.4f}".format(buy_exit_signal)))