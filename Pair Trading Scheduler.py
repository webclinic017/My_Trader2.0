# ========================HEADER=============================================
from my_trader import *

import time
import timeit
import talib as ta
import numpy as np
from Robinhood import Robinhood

import xlrd
from datetime import datetime
from pandas_datareader import data as da
import schedule

if datetime.now().weekday() == 0:
    last_trade_date_count = 3
elif datetime.now().weekday() == 6:
    last_trade_date_count = 2
else:
    last_trade_date_count = 1

# =============================================================================
#Template

# =============================================================================
# flag = False
# trail = 0
# while not flag and trail > 3:
#     try:
#
#         flag = True
#     except Exception as e:
#         print (e);
#         trail += 1
#         continue
# =============================================================================




#Parameters
# =============================================================================


directory = "file/"
working_suggestion = "Trade_suggestion_robinhood_1st"
stock_suggestion_path = directory + working_suggestion + str(datetime.now()-timedelta(days=last_trade_date_count))[0:10]+".csv"

stock1 = "VIXY"
stock2 = "SPY"

trade_window = 30

cutoff_rate= 1.5 #ratio of volatility

initial_capital = 1500

slippage = 0.02

continuous_adjust = True

intraday_cutoff = 0.15

flat = False  #default False

ready_trade = False #default  False

trade_on = True   #default  True
# =============================================================================











class bot:
    
    def __init__(self):
        self.problem = False
        self.login_status = False
        
        trail = 0 
        while not self.login_status and trail < 3:
            try:
                self.robinhood = get_robinhood()
                self.robinhood.logout()
                self.robinhood.my_trader.login_prompt()
                self.tickers , self.quantity = self.robinhood.get_my_positions()
                print "logined"
                self.login_status = True
            except Exception as e:
                print e
                self.robinhood.logout()
                trail += 1
                continue
        
        #run check
#        print self.get_trading_action()
#        price_table = pair_trade(stock1,stock2,initial_capital, window = trade_window, continuous=continuous_adjust)
#        price_table = price_table.iloc[-1]
#        if price_table[stock1 + "_suggest_shares"] or price_table[stock2 + "_suggest_shares"] == np.NaN:
#            self.can_trade = False
#            print ("pair trade function problem")
#            exit

        self.sell_and_buy()
        if not self.problem:
            print ("sell and buy OK!")
        self.intraday_trade()
        if not self.problem:
            print ("intraday trade OK!")
        time.sleep(2)
        self.robinhood.my_trader.cancel_open_orders()
        print "Order all canceled"
        print ""
        
        


        print "Can Trade ",not self.problem      
        
        if not self.problem:
            print "******************************************"
            print "***********Ready To Trade*****************"
            print "******************************************"
            ready_trade = True
        else:
            print ("##############################")
            print ("Please check the program")

    def __exit__(self):
        self.robinhood.logout
        print "logouted"
 



    def get_trading_action(self):
        get_success=False
        trial = 0
        while not get_success and trial < 3:
            try:
                positions = self.robinhood.get_my_positions()
                positions = pd.DataFrame(data=positions[1],index = positions[0],columns=["Quantity"])
                if stock1 and stock2 in positions.index:
                    print ("{}, {} in my position".format(stock1,stock2))
                    stock1_quant = positions.loc[stock1][0]
                    stock2_quant = positions.loc[stock2][0]
                    trade_on = True
                else:
                    stock1_quant = 0
                    stock2_quant = 0
                    trade_on = False
        
        
                price_table = pair_trade(stock1,stock2,initial_capital, method = "realtimeday" ,window = trade_window, continuous=continuous_adjust)
                price_table = price_table.iloc[-1]
                self.volatility1 = price_table[stock1 + "_volatility"]
                self.volatility2 = price_table[stock2 + "_volatility"]
                print ("Volatility of "+ stock1 +": ",self.volatility1)
                print ("Volatility of "+ stock1 +": ",self.volatility2)
                
                    
                if not continuous_adjust:
                    print ("Trade on signal")
                    if price_table["trade"]:
                        print ("Trade Day!\n")
                        stock1_trade = price_table[stock1 + "_shares"]
                        stock2_trade = price_table[stock2 + "_shares"]
                    else:
                        print ("No trade signal\n")
                else:
                    print ("Dynamic hedge!")
                    stock1_trade = price_table[stock1 + "_suggest_shares"]
                    stock2_trade = price_table[stock2 + "_suggest_shares"]
        
        
                stock1_trade = stock1_trade - stock1_quant
                stock2_trade = stock2_trade - stock2_quant
                if ( stock1_trade != stock1_trade ) or ( stock2_trade != stock2_trade ):
                    self.problem = True
                    print ("pair trade function problem")
                    
                    trial +=1
                    
                    continue
                
                else:
                    print ("{},{};{},{}".format(stock1,stock1_trade,stock2,stock2_trade)) 
                    get_success = True
                    self.problem = False
                    return stock1_trade, stock2_trade
            except Exception as e:
                print e
                print ("****************************")
                print ("      something wrong       ")
                print ("       restarting           ")
                print ("****************************")
                time.sleep(30)
                continue
    def intraday_trade(self):
        global flat
        
        if not flat and trade_on:
            now_price = float(self.robinhood.get_last_price(stock1))
            open_price = float(self.robinhood.my_trader.quote_data(stock1)['adjusted_previous_close'])
            positions = self.robinhood.get_my_positions()
            positions = pd.DataFrame(data=positions[1],index = positions[0],columns=["Quantity"])
            if log(now_price/open_price) > cutoff_rate*self.volatility1:
                try:
                    print ("meet cutoff, go flat!")
                    self.robinhood.place_sell(stock1,positions.loc[stock1])
                    self.robinhood.place_sell(stock2,positions.loc[stock2])
                except Exception as e:
                    print (e)
                    self.problem = True
                flat = True
            else:
                print (stock1 + "donesn't meet cutoff, keep!")
            ###################stock seperate#############
            now_price = float(self.robinhood.get_last_price(stock2))
            open_price = float(self.robinhood.my_trader.quote_data(stock2)['adjusted_previous_close'])
            positions = self.robinhood.get_my_positions()
            positions = pd.DataFrame(data=positions[1],index = positions[0],columns=["Quantity"])
            if log(now_price/open_price) > cutoff_rate*self.volatility2:
                try:
                    print ("meet cutoff, go flat!")
                    self.robinhood.place_sell(stock1,positions.loc[stock1])
                    self.robinhood.place_sell(stock2,positions.loc[stock2])
                except Exception as e:
                    print (e)
                    self.problem = True
                flat = True
            else:
                print (stock2 + "donesn't meet cutoff, keep!")

            
    def sell_and_buy(self):
        sell_flag = False
        if not flat and not self.problem:
            stock1_amount, stock2_amount = self.get_trading_action()
            print ("{},{};{},{}".format(stock1,stock1_amount,stock2,stock2_amount))
            
            if stock1_amount < 0:
                print ("Place {} short".format(stock1))
                self.robinhood.place_sell(stock1,abs(stock1_amount),slippage=slippage)
                stock1_amount, stock2_amount = self.get_trading_action()
                if ready_trade:
                    while not sell_flag:
                        stock1_amount, stock2_amount = self.get_trading_action()
                        if stock1_amount == 0:
                            sell_flag = True
                        else:
                            print("waiting for order to execute")
                            time.sleep(10)
            
            if stock2_amount < 0:
                print ("Place {} short".format(stock2))
                self.robinhood.place_sell(stock2,abs(stock2_amount),slippage=slippage)
                if ready_trade:
                    while not sell_flag:
                        stock1_amount, stock2_amount = self.get_trading_action()
                        if stock2_amount == 0:
                            sell_flag = True
                        else:
                            print("waiting for order to execute")
                            time.sleep(10)
            
            
            
            if stock1_amount > 0:
                print ("Place {} long".format(stock1))
                self.robinhood.place_buy(stock1,abs(stock1_amount),slippage=slippage)
            
            if stock2_amount > 0:
                print ("Place {} long".format(stock2))
                self.robinhood.place_buy(stock2,abs(stock2_amount),slippage=slippage)
            
# =============================================================================
#             elif stock1_amount < 0:
#                 print ("Place {} short".format(stock1))
#                 self.robinhood.place_sell(stock1,abs(stock1_amount),slippage=slippage)
#                 
#             if stock2_amount > 0:
#                 print ("Place {} long".format(stock2))
#                 self.robinhood.place_buy(stock2,abs(stock2_amount),slippage=slippage)
#                 
#             elif stock2_amount < 0:
#                 print ("Place {} short".format(stock2))
#                 self.robinhood.place_sell(stock2,abs(stock2_amount),slippage=slippage)
#                 
#             else:
#                 print ("nothing happened")
# =============================================================================
    # first, get can_trade universe

    def check_beta(self):
       # robinhood = get_robinhood()
  
        check= False
        trail =0
        while not check and trail <3:
            try:
                self.robinhood.get_my_position_beta_minute()
                check = True
       # robinhood.logout()
            except Exception as e:
                print e
                trail += 1
                continue

        #robinhood.logout()


    def mean_reversion_check(self):
       # robinhood = get_robinhood()
         flag = False
         trail = 0
         while not flag and trail < 3:
             try:
                self.robinhood.get_my_position_beta_minute()
                for i in self.tickers:
                    mean_reversion(self.tickers,"minute")
                flag = True
             except Exception as e:
                 print (e)
                 trail += 1
                 continue


    def plot(self):

         flag = False
         trail = 0
         while not flag and trail < 10:
             try:
                 my_positions, position_quantity= self.robinhood.get_my_positions()
                 print "###################################"
                 print "BETA IS: "
                 print self.robinhood.get_protfolio(my_positions, position_quantity,interval = "minute")[1]
                 print "###################################"
                 plot_position( my_positions, position_quantity )
                 flag = True
             except Exception as e:
                 print (e)
                 trail += 1
                 continue


def daily_update_db():
    mongodb = mongo()
    all_stock_data = mongodb.get_all_quote()
    mongodb.update_db(all_stock_data)
        


def hi():
    print (datetime.now())

def bye():
    print ("I am still here")


###########################################################################
#Debug Area:
#    
#bot = bot()
#bot.get_trading_action()
#price_table = pair_trade(stock1,stock2,initial_capital, window = trade_window, continuous=continuous_adjust)
#price_table = price_table.iloc[-1]
#print price_table

##########################################################################
bot = bot()
schedule.clear()
 ##schedule.every(4).weeks.do(update_fundamentals)
schedule.every(60).minutes.do(bot.get_trading_action)
schedule.every(20).minutes.do(bot.intraday_trade)
 ##schedule.every(25).minutes.do(mean_reversion_check)

 # schedule.every().monday.at("6:30").do(bot.update_price)
 # schedule.every().tuesday.at("6:30").do(bot.update_price)
 # schedule.every().wednesday.at("6:30").do(bot.update_price)
 # schedule.every().thursday.at("6:30").do(bot.update_price)
 # schedule.every().friday.at("6:30").do(bot.update_price)


schedule.every().monday.at("12:30").do(bot.sell_and_buy)
schedule.every().tuesday.at("12:30").do(bot.sell_and_buy)
schedule.every().wednesday.at("12:44").do(bot.sell_and_buy)
schedule.every().thursday.at("12:30").do(bot.sell_and_buy)
schedule.every().friday.at("12:58").do(bot.sell_and_buy)
#schedule.every().days.at("12:00").do(daily_update_db)
schedule.every().days.at("15:00").do(daily_update_db)
while True:
    schedule.run_pending()
    
    time.sleep(1)
###########################################################################

