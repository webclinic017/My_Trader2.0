from .my_lib import *
from .my_trader import *
import pyfolio as pf

# rsi_buy = 30
# rsi_sell= 70

# cci_buy = -100
# cci_sell = 90

class DrawDownLength(bt.observers.DrawDown):

    lines = ('length', 'maxlength')
    plotinfo = dict(plotinfo=True, subplot=True)

    plotlines = dict(drawdown=dict(_plotskip='True',))
    plotlines = dict(maxlength=dict(_plotskip='True',))

    def __init__(self):

        super(DrawDownLength, self).__init__()
        self.length = 0

    def __next__(self):

        next(super(DrawDownLength, self))

        if self.lines.drawdown[0] != 0:
            self.length += 1
        else:
            self.length = 0

        self.lines.length[0] = self.length
        self.lines.maxlength[0] = max(self.length, self.lines.maxlength[-1])

class datapairtrade_table_bb(bt.feeds.PandasData):
    lines = ('datetime','relative','relative_mv','z_score',"hedge_ratio","slope","up","mid","low")
    params = (
        ('datetime', None),
            ('relative', -1),
        ('relative_mv', -1),
        ('z_score', -1),
        ('slope', -1),
        ('hedge_ratio',-1),
        ('up',-1),
        ('mid',-1),
        ('low',-1)
    
        )




class datapairtrade(bt.feeds.PandasData):
    lines = ('datetime','open','high','low','close','volume','openinterest','log_ret','log_ret_mv','volatility')
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
        
        
        )
    
class datapairtrade_table(bt.feeds.PandasData):
    lines = ('datetime','relative','relative_mv','z_score',"slope")
    params = (
        ('datetime', None),
            ('relative', -1),
        ('relative_mv', -1),
        ('z_score', -1),
        ('slope', -1)
    
        )
                
def backtest(i, strategy, method = "day",back_day = 80 ):

    try:
        robinhood = robingateway()
        price = get_price_data([i], method=method,robinhood=robinhood,back_day=back_day )
        price = price.set_index("TimeStamp")
    
        
        cerebro = bt.Cerebro()
        cerebro.addstrategy(strategy)
        cerebro.broker.setcommission(commission=0.001)



        # Create a Data Feed
        data = bt.feeds.PandasData(dataname=price)

        cerebro.adddata(data)
        cerebro.broker.setcash(2000.0)
        init = cerebro.broker.getvalue()
        #print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
        cerebro.run()
        post = cerebro.broker.getvalue()
        if post > init:
            print ("Good Trade")

        print(('Final Portfolio Value: %.2f' % cerebro.broker.getvalue()))
        cerebro.plot()
            
    except Exception as e:
        print (e)
        return

    
def backtest_pair(i,j, capital = 2000, method = "day",back_day = 80,window = 7 ):


    returns = []

    class pair_trade_strategy(bt.Strategy):

        def notify_order(self, order):
            if order.status in [order.Submitted, order.Accepted]:
                # Buy/Sell order submitted/accepted to/by broker - Nothing to do
                return

            # Check if an order has been completed
            # Attention: broker could reject order if not enough cash
            if order.status in [order.Completed]:
                if order.isbuy():
                    self.log('BUY EXECUTED, price: %.2f, size: %d' % (order.executed.price, order.executed.size))
                elif order.issell():
                    self.log('SELL EXECUTED, %.2f, size: %d' % (order.executed.price,order.executed.size))

                self.bar_executed = len(self)

            elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                self.log('Order Canceled/Margin/Rejected')

            # Write down: no pending order
            self.order = None


        def log(self, txt, dt=None):
            ''' Logging function for this strategy'''
            dt = dt or self.data.datetime.date(0)
            print(('%s, %s' % (dt, txt)))


        def buy_line(self,data_frame):
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
        def sell_line(self,data_frame):
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


        def __init__(self):


            self.buy_lines = None
            self.sell_lines = None

            self.lastcash = None
            self.buytradeopen = False
            self.selltradeopen = False
            self.lastvalue = self.broker.getvalue()
            self.lastcash  = self.broker.getcash()
            self.holddays = 0





        def next(self):
            ############################
            ### Order filled at the next bar
            ############################
            
            #get return for one day
            returns.append(np.log(self.broker.getvalue()/self.lastvalue))
            
            self.lastvalue = self.broker.getvalue()
            self.lastcash  = self.broker.getcash()
            
            self.buy_lines = self.buy_line(self.datas[2])
            self.sell_lines = self.sell_line(self.datas[2])
#             self.buy_lines = self.datas[2].low
#             self.sell_lines = self.datas[2].up

            money = capital if self.lastcash > capital else self.lastcash
    #         print self.datas[2].hedge_ratio[0]

            if self.buytradeopen or self.selltradeopen:
                self.holddays += 1
        
        
            if self.datas[2].z_score < self.buy_lines and not self.buytradeopen:
                
                self.selltradeopen = False
                self.holddays = 0
            
                # control the size to be long only if wish

                size1 = money/(self.datas[0].close + self.datas[0].close* self.datas[2].hedge_ratio)
                size2 = -size1 * self.datas[2].hedge_ratio

    #             size1 = np.ceil(((self.broker.getcash()/2)/(1+self.datas[2].relative_mv[0])/self.datas[0].close[0]))
    #             size2 = np.ceil(((self.broker.getcash()/2) \
    #                                 /(1+self.datas[2].relative_mv)*self.datas[2].relative_mv[0]/self.datas[1].close[0]))
                if self.getposition(self.datas[0]).size != size1:
                    self.log("Close buy position: %d" % (self.getposition(self.datas[0]).size))
                    self.close(data=self.datas[0])

                    self.buy(size = size1,data = self.datas[0])



                if self.getposition(self.datas[1]).size != size2:
                    self.log("Close sell position: %d" % (self.getposition(self.datas[1]).size))
                    self.close(data=self.datas[1])
                    if size2 < 0:
                        self.sell(size = -size2 ,data = self.datas[1])
                    else:
                        self.buy(size = size2 ,data = self.datas[1])


                self.log("Buy signal, Cash left:  %.2f , buy stock1: %d sell stock2:  %d, Portfolio value: %.2f"  % (self.broker.getcash(),size1,size2,self.broker.getvalue() ))
                
                self.buytradeopen = True
                
                

            elif self.datas[2].z_score > self.sell_lines and not self.selltradeopen:
                
                self.buytradeopen = False
                self.holddays = 0
                
                # control the size to be long only if wish
                size1 = - money/(self.datas[0].close + self.datas[0].close* self.datas[2].hedge_ratio)
                size2 = -size1 * self.datas[2].hedge_ratio

    #             size1 = np.ceil(((self.broker.getcash()/2)/(1+self.datas[2].relative_mv[0])/self.datas[0].close[0]))
    #             size2 = np.ceil(((self.broker.getcash()/2)\
    #                                /(1+self.datas[2].relative_mv)*self.datas[2].relative_mv[0]/self.datas[1].close[0]))

                if self.getposition(self.datas[0]).size != size1:
                    self.log("Close sell position: %d" % (self.getposition(self.datas[0]).size))
                    self.close(data=self.datas[0])

                    if size1 < 0:

                        self.sell(size = -size1 ,data = self.datas[0])
                    else:
                        self.buy(size = size1 ,data = self.datas[0])

                if self.getposition(self.datas[1]).size != size2:
                    self.log("Close buy position: %d" % (self.getposition(self.datas[1]).size))
                    self.close(data=self.datas[1])


                    if size2 < 0:
                        self.sell(size = -size2 ,data = self.datas[1])
                    else:
                        self.buy(size = size2 ,data = self.datas[1])


                self.log("sell signal, Cash left:  %.2f , sell stock1: %d buy stock2:  %d, portfolio value:%.2f" % (self.broker.getcash(),size1,size2, self.broker.getvalue() ))
                
                self.selltradeopen = True
            
            elif self.holddays > 5 and (self.getposition(self.datas[0]).size > 0 or self.getposition(self.datas[1]).size > 0 )  :
                self.close(data=self.datas[0])
                self.close(data=self.datas[1])
                self.log("Hold days > 5, Close all positions. CLose Stock1: %d, Stock2: %d" % (self.getposition(self.datas[0]).size,self.getposition(self.datas[0]).size))
            
            else:
                
                self.log("No Trade: Cash left:  %.2f , stock1: %d stock2:  %d, portfolio value:%.2f"\
                         %(self.broker.getcash(),self.getposition(self.datas[0]).size,self.getposition(self.datas[1]).size, self.broker.getvalue() ))

            


#     try:
    robinhood = robingateway()
    
    price1 = get_price_data([i], method=method,robinhood=robinhood,back_day=back_day )
    price1 = price1.set_index("TimeStamp")
    # price1.loc[price1.Open == 0,"Open"] = np.NaN
    

    price2 = get_price_data([j], method=method,robinhood=robinhood,back_day=back_day )
    price2 = price2.set_index("TimeStamp")


    # set to the same length
    if len(price2) != len(price1):
        price1 = get_price_data([i], method="realtimeday",robinhood=robinhood,back_day=back_day )
        price1 = price1.set_index("TimeStamp")
        # price1.loc[price1.Open == 0,"Open"] = np.NaN


        price2 = get_price_data([j], method="realtimeday",robinhood=robinhood,back_day=back_day )
        price2 = price2.set_index("TimeStamp")


    price_table = pd.DataFrame()
    #--------------------------------------------------------------
#     return price1, price2
    

    price1.loc[:,"log_ret"] = log(price1.Close / price1.Close.shift(1))
    price2.loc[:,"log_ret"] = log(price1.Close / price2.Close.shift(1))


    price1.loc[:, "log_ret_mv"] = price1.log_ret.rolling(window).mean()
    price2.loc[:, "log_ret_mv"] = price2.log_ret.rolling(window).mean()

    price1 = price1.fillna(method="bfill")
    price2 = price2.fillna(method="bfill")
    
    price_table.loc[:,"relative"] = price1.log_ret_mv / price2.log_ret_mv

    price_table.loc[:,"relative_mv"] = price_table["relative"].rolling(window, min_periods=window).mean()
    price_table["relative_mv"] = abs(price_table["relative_mv"])
   

    for i in range(1,len(price1)):
        j = i- window
        if j < 0 :
            j = 0 
        price_table.loc[price_table.iloc[i].name,"slope"] = stats.linregress(price1.log_ret.iloc[j:i],price2.log_ret.iloc[j:i])[0] 
        price_table.loc[price_table.iloc[i].name,"hedge_ratio"]= \
        sm.OLS(price2.Close.iloc[j:i],price1.Close.iloc[j:i]).fit().params[0]

    price1.loc[:,"volatility"] = price1.log_ret.rolling(window).std()
    price2.loc[:,"volatility"] = price2.log_ret.rolling(window).std()

    price_table["z_score"] =( price_table["relative"]-price_table["relative_mv"])/price_table.relative.std()
    up, mid , low = ta.BBANDS(price1.Close*price_table.hedge_ratio)

    bb = pd.DataFrame({"up":up,"mid":mid,"low":low})

    price_table = price_table.join(bb)
    price_table = price_table.fillna(method="bfill")
    

    cerebro = bt.Cerebro()
    cerebro.addstrategy(pair_trade_strategy)
    cerebro.broker.setcommission(commission=0.005)

    # Create a Data Feed
    data1 = datapairtrade(dataname=price1)
    data2 = datapairtrade(dataname=price2)
    data3 = datapairtrade_table_bb(dataname=price_table)

    cerebro.adddata(data1)
    cerebro.adddata(data2)
    cerebro.adddata(data3)
    cerebro.broker.setcash(capital)
    # cerebro.addanalyzer(bt.analyzers.PyFolio)
    #print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run()
    post = cerebro.broker.getvalue()
    # strat = results[0]
    # pyfoliozer = strat.analyzers.getbyname('pyfolio')
    # returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()

    returns = [x for x in returns if x == x]
    return post,np.mean(returns),np.mean(returns)/np.std(returns), np.min(returns),np.max(returns)
    
#     return returns



 
class pair_trade_strategy_backup(bt.Strategy):

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, price: %.2f, size: %d' % (order.executed.price, order.executed.size))
            elif order.issell():
                self.log('SELL EXECUTED, %.2f, size: %d' % (order.executed.price,order.executed.size))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None


    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.data.datetime.date(0)
        print(('%s, %s' % (dt, txt)))


    def buy_line(self,data_frame):
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
    def sell_line(self,data_frame):
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


    def __init__(self):


        self.buy_lines = None
        self.sell_lines = None

        self.lastcash = None
        self.buytradeopen = False
        self.selltradeopen = False
        self.lastvalue = self.broker.getvalue()
        self.lastcash  = self.broker.getcash()





    def next(self):
        ############################
        ### Order filled at the next bar
        ############################

        #get return for one day
        returns.append(np.log(self.broker.getvalue()/self.lastvalue))

        self.lastvalue = self.broker.getvalue()
        self.lastcash  = self.broker.getcash()
#         self.buy_lines = self.buy_line(self.datas[2])
#         self.sell_lines = self.sell_line(self.datas[2])
        self.buy_lines = self.datas[2].low
        self.sell_lines = self.datas[2].up

        money = capital if self.lastcash > capital else self.lastcash
#         print self.datas[2].hedge_ratio[0]

        # print(self.buy_lines[0])
        # print(self.broker.getcash())
        # print(self.sell_lines)
        # print(self.datas[2].z_score)

        if self.datas[2].z_score < self.buy_lines:
            # control the size to be long only if wish


            size1 = money/(self.datas[0].close + self.datas[0].close* self.datas[2].hedge_ratio)
            size2 = -size1 * self.datas[2].hedge_ratio

#             size1 = np.ceil(((self.broker.getcash()/2)/(1+self.datas[2].relative_mv[0])/self.datas[0].close[0]))
#             size2 = np.ceil(((self.broker.getcash()/2) \
#                                 /(1+self.datas[2].relative_mv)*self.datas[2].relative_mv[0]/self.datas[1].close[0]))
            if self.getposition(self.datas[0]).size != size1:
                self.log("Close buy position: %d" % (self.getposition(self.datas[0]).size))
                self.close(data=self.datas[0])

                self.buy(size = size1,data = self.datas[0])




            if self.getposition(self.datas[1]).size != size2:
                self.log("Close sell position: %d" % (self.getposition(self.datas[1]).size))
                self.close(data=self.datas[1])
                if size2 < 0:
                    self.sell(size = -size2 ,data = self.datas[1])
                else:
                    self.buy(size = size2 ,data = self.datas[1])


            self.log("Buy signal, Cash left:  %.2f , buy stock1: %d sell stock2:  %d, Portfolio value: %.2f"  % (self.broker.getcash(),size1,size2,self.broker.getvalue() ))

        if self.datas[2].z_score > self.sell_lines:
            # control the size to be long only if wish
            size1 = - money/(self.datas[0].close + self.datas[0].close* self.datas[2].hedge_ratio)
            size2 = -size1 * self.datas[2].hedge_ratio

#             size1 = np.ceil(((self.broker.getcash()/2)/(1+self.datas[2].relative_mv[0])/self.datas[0].close[0]))
#             size2 = np.ceil(((self.broker.getcash()/2)\
#                                /(1+self.datas[2].relative_mv)*self.datas[2].relative_mv[0]/self.datas[1].close[0]))

            if self.getposition(self.datas[0]).size != size1:
                self.log("Close sell position: %d" % (self.getposition(self.datas[0]).size))
                self.close(data=self.datas[0])

                if size1 < 0:

                    self.sell(size = -size1 ,data = self.datas[0])
                else:
                    self.buy(size = size1 ,data = self.datas[0])

            if self.getposition(self.datas[1]).size != size2:
                self.log("Close buy position: %d" % (self.getposition(self.datas[1]).size))
                self.close(data=self.datas[1])


                if size2 < 0:
                    self.sell(size = -size2 ,data = self.datas[1])
                else:
                    self.buy(size = size2 ,data = self.datas[1])


            self.log("sell signal, Cash left:  %.2f , sell stock1: %d buy stock2:  %d, portfolio value:%.2f" % (self.broker.getcash(),size1,size2, self.broker.getvalue() ))
    
            
            
class pair_trade_strategy_single(bt.Strategy):
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, price: %.2f, size: %d' % (order.executed.price, order.executed.size))
            elif order.issell():
                self.log('SELL EXECUTED, %.2f, size: %d' % (order.executed.price,order.executed.size))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.data.datetime.date(0)
        print(('%s, %s' % (dt, txt)))
    
    
    def buy_line(self,data_frame):
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
    def sell_line(self,data_frame):
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


    def __init__(self):
        self.buy_lines = None
        self.sell_lines = None
        self.currentsell = 0
        self.currentbuy = 0
       
        

    def __next__(self):
        self.buy_lines = self.buy_line(self.datas[2])
        self.sell_lines = self.sell_line(self.datas[2])
#         self.buy_lines = self.datas[2].low
#         self.sell_lines = self.datas[2].up
#         print self.datas[2].hedge_ratio[0]
    
    
        if self.datas[2].z_score < self.buy_lines:
            # control the size to be long only if wish
            size1 = 1
            size2 = -size1 * self.datas[2].hedge_ratio
            
#             size1 = np.ceil(((self.broker.getcash()/2)/(1+self.datas[2].relative_mv[0])/self.datas[0].close[0]))
#             size2 = np.ceil(((self.broker.getcash()/2) \
#                                 /(1+self.datas[2].relative_mv)*self.datas[2].relative_mv[0]/self.datas[1].close[0]))
            if self.getposition(self.datas[0]).size != size1:
                self.log("Close buy position: %d" % (self.getposition(self.datas[0]).size))
                self.close(data=self.datas[0])
                self.buy(size = size1,data = self.datas[0])
         
                
                
#             if self.getposition(self.datas[1]).size != size2:
#                 self.log("Close sell position: %d" % (self.getposition(self.datas[1]).size))
#                 self.close(data=self.datas[1])
                
                
#                 if size2 < 0:
#                     self.sell(size = -size2 ,data = self.datas[1])
#                 else:
#                     self.buy(size = size2 ,data = self.datas[1]) 
                
                
                
            
            self.log("Buy signal, Cash left:  %.2f , buy stock1: %d sell stock2:  %d, Portfolio value: %.2f"  % (self.broker.getcash(),size1,size2,self.broker.getvalue() ))
                
        if self.datas[2].z_score > self.sell_lines:
            # control the size to be long only if wish
            size1 = -1
            size2 = -size1 * self.datas[2].hedge_ratio
                
#             size1 = np.ceil(((self.broker.getcash()/2)/(1+self.datas[2].relative_mv[0])/self.datas[0].close[0]))
#             size2 = np.ceil(((self.broker.getcash()/2)\
#                                /(1+self.datas[2].relative_mv)*self.datas[2].relative_mv[0]/self.datas[1].close[0])) 
            
            if self.getposition(self.datas[0]).size != size1:
                self.log("Close sell position: %d" % (self.getposition(self.datas[0]).size))
                self.close(data=self.datas[0])
                
                if size1 < 0:
                
                    self.sell(size = -size1 ,data = self.datas[0]) 
                else:
                    self.buy(size = size1 ,data = self.datas[0])
          
#             if self.getposition(self.datas[1]).size != size2:
#                 self.log("Close buy position: %d" % (self.getposition(self.datas[1]).size))
#                 self.close(data=self.datas[1])
                
                
#                 if size2 < 0:
#                     self.sell(size = -size2 ,data = self.datas[1])
#                 else:
#                     self.buy(size = size2 ,data = self.datas[1])
                
            
            self.log("sell signal, Cash left:  %.2f , sell stock1: %d buy stock2:  %d, portfolio value:%.2f" % (self.broker.getcash(),size1,size2, self.broker.getvalue() ))

    
    
    
    
    
    
    
class rsiStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(('%s, %s' % (dt.isoformat(), txt)))

    def __init__(self):
        
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.point = 0

        self.rsi = bt.indicators.RelativeStrengthIndex()
        #self.adxr = bt.indicators.ADXR()
        #self.cci = bt.indicators.CCI()
        #self.macd = bt.talib.MACD(self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        #self.mfi = bt.talib.MFI(self.data.High, self.data.Low, self.data.Close, self.data.Volume,timeperiod=14)
        #self.rocp = bt.talib.ROCP(self.data.Close, timeperiod=10)
        


    def __next__(self):
        

        if not self.position:
            if (self.rsi < trading_param["rsi_buy"]):
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy(size=int(300/self.dataclose))

        elif self.position:
            if (self.rsi > trading_param["rsi_sell"]):
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell(size = self.position.size)
                
                
class cciStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(('%s, %s' % (dt.isoformat(), txt)))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.point = 0

        #self.rsi = bt.indicators.RelativeStrengthIndex()
        #self.adxr = bt.indicators.ADXR()
        self.cci = bt.indicators.CCI()
        #self.macd = bt.talib.MACD(self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        #self.mfi = bt.talib.MFI(self.data.High, self.data.Low, self.data.Close, self.data.Volume,timeperiod=14)
        #self.rocp = bt.talib.ROCP(self.data.Close, timeperiod=10)
        


    def __next__(self):
        
        if self.order:
            return

        if not self.position:
            if (self.cci < trading_param["cci_buy"]):
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy(size=int(300/self.dataclose))

        elif self.position:
            if (self.cci > trading_param["cci_sell"]):
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell(size = self.position.size)               
                
                
class adxrStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(('%s, %s' % (dt.isoformat(), txt)))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.point = 0

        #self.rsi = bt.indicators.RelativeStrengthIndex()
        self.adxr = bt.indicators.ADXR()
        #self.cci = bt.indicators.CCI()
        #self.macd = bt.talib.MACD(self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        #self.mfi = bt.talib.MFI(self.data.High, self.data.Low, self.data.Close, self.data.Volume,timeperiod=14)
        #self.rocp = bt.talib.ROCP(self.data.Close, timeperiod=10)
        


    def __next__(self):
        
        if self.order:
            return

     
        
        if not self.position:
            if (self.cci < rsi_buy):
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy(size=int(300/self.dataclose))

        elif self.position:
            if (self.cci > rsi_sell):
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell(size = self.position.size)  
                
                
