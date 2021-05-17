from my_libs import *


# Defining datafeed object



# def backtest_pair(i,j, strategy, capital = 2000, method = "day",back_day = 80,window = 3 ):

# #     try:
#     robinhood = robingateway()
    
#     price1 = get_price_data([i], method=method,robinhood=robinhood,back_day=back_day )
#     price1 = price1.set_index("TimeStamp")
#     price1.loc[price1.Open == 0,"Open"] = np.NaN
    

#     price2 = get_price_data([j], method=method,robinhood=robinhood,back_day=back_day )
#     price2 = price2.set_index("TimeStamp")
#     price_table = pd.DataFrame()
#     #--------------------------------------------------------------
# #     return price1, price2
    


#     price1.loc[:,"log_ret"] = log(price1.Close / price1.Close.shift(1))
#     price2.loc[:,"log_ret"] = log(price1.Close / price2.Close.shift(1))


#     price1.loc[:, "log_ret_mv"] = price1.log_ret.rolling(window).mean()
#     price2.loc[:, "log_ret_mv"] = price2.log_ret.rolling(window).mean()

#     price1 = price1.fillna(method="bfill")
#     price2 = price2.fillna(method="bfill")
    
#     price_table.loc[:,"relative"] = price1.log_ret_mv / price2.log_ret_mv

#     price_table.loc[:,"relative_mv"] = price_table["relative"].rolling(window, min_periods=window).mean()
#     price_table["relative_mv"] = abs(price_table["relative_mv"])
   

#     for i in range(1,len(price1)):
#         j = i- window
#         if j < 0 :
#             j = 0 
#         price_table.loc[price_table.iloc[i].name,"slope"] = stats.linregress(price1.log_ret.iloc[j:i],price2.log_ret.iloc[j:i])[0] 
#         price_table.loc[price_table.iloc[i].name,"hedge_ratio"]= \
#         sm.OLS(price1.Close.iloc[j:i],price2.Close.iloc[j:i]).fit().params[0]

  





#     price1.loc[:,"volatility"] = price1.log_ret.rolling(window,min_periods=window-5).std()
#     price2.loc[:,"volatility"] = price2.log_ret.rolling(window,min_periods=window-5).std()


#     price_table["z_score"] =( price_table["relative"]-price_table["relative_mv"])/price_table.relative.std()
#     up, mid , low = ta.BBANDS(price_table.z_score)

#     bb = pd.DataFrame({"up":up,"mid":mid,"low":low})

#     price_table = price_table.join(bb)
#     price_table = price_table.fillna(method="bfill")




#     cerebro = bt.Cerebro()
#     cerebro.addstrategy(strategy)
#     cerebro.broker.setcommission(commission=0.0)



#     # Create a Data Feed
#     data1 = datapairtrade(dataname=price1)
#     data2 = datapairtrade(dataname=price2)
#     data3 = datapairtrade_table_bb(dataname=price_table)


#     cerebro.adddata(data1)
#     cerebro.adddata(data2)
#     cerebro.adddata(data3)
#     cerebro.broker.setcash(capital)
#     #cerebro.addanalyzer(bt.analyzers.PyFolio)
#     init = cerebro.broker.getvalue()
#     #print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
#     cerebro.run()
#     post = cerebro.broker.getvalue()
    
#     print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
#     if post > init + init*0.1:
#         print ("Good Trade")
#         return ["Good Trade", post]


# #     cerebro.plot()
            
# #     except Exception as e:
# #         print (e)
# #         return

# class pair_trade(bt.Strategy):
    
#     def notify_order(self, order):
#         if order.status in [order.Submitted, order.Accepted]:
#             # Buy/Sell order submitted/accepted to/by broker - Nothing to do
#             return

#         # Check if an order has been completed
#         # Attention: broker could reject order if not enough cash
#         if order.status in [order.Completed]:
#             if order.isbuy():
#                 self.log('BUY EXECUTED, price: %.2f, size: %d' % (order.executed.price, order.executed.size))
#             elif order.issell():
#                 self.log('SELL EXECUTED, %.2f, size: %d' % (order.executed.price,order.executed.size))

#             self.bar_executed = len(self)

#         elif order.status in [order.Canceled, order.Margin, order.Rejected]:
#             self.log('Order Canceled/Margin/Rejected')

#         # Write down: no pending order
#         self.order = None

    
#     def log(self, txt, dt=None):
#         ''' Logging function for this strategy'''
#         dt = dt or self.data.datetime.date(0)
#         print('%s, %s' % (dt, txt))
    
    
#     def buy_line(self,data_frame):
#         data_frame = data_frame.slope
#         if data_frame>0.5:
#             return -1.25
#         elif data_frame>0.75:
#             return -1.75
#         elif data_frame:
#             return -2.25
#         elif data_frame<-0.75:
#             return -2.75
#         else:
#             return -2
#     def sell_line(self,data_frame):
#         data_frame = data_frame.slope
#         if data_frame>0.5:
#             return 1.25
#         elif data_frame>0.75:
#             return 1.75
#         elif data_frame:
#             return 2.25
#         elif data_frame<-0.75:
#             return 2.75
#         else:
#             return 2


#     def __init__(self):
#         self.buy_lines = None
#         self.sell_lines = None
#         self.currentsell = 0
#         self.currentbuy = 0
       
        

#     def next(self):
# #         self.buy_lines = self.buy_line(self.datas[2])
# #         self.sell_lines = self.sell_line(self.datas[2])
#         self.buy_lines = self.datas[2].low
#         self.sell_lines = self.datas[2].up
# #         print self.datas[2].hedge_ratio[0]
    
    
#         if self.datas[2].z_score < self.buy_lines:
#             # control the size to be long only if wish
#             size1 = 1
#             size2 = -size1 * self.datas[2].hedge_ratio
            
# #             size1 = np.ceil(((self.broker.getcash()/2)/(1+self.datas[2].relative_mv[0])/self.datas[0].close[0]))
# #             size2 = np.ceil(((self.broker.getcash()/2) \
# #                                 /(1+self.datas[2].relative_mv)*self.datas[2].relative_mv[0]/self.datas[1].close[0]))
#             if self.getposition(self.datas[0]).size != size1:
#                 self.log("Close buy position: %d" % (self.getposition(self.datas[0]).size))
#                 self.close(data=self.datas[0])
#                 self.buy(size = size1,data = self.datas[0])
         
                
                
#             if self.getposition(self.datas[1]).size != size2:
#                 self.log("Close sell position: %d" % (self.getposition(self.datas[1]).size))
#                 self.close(data=self.datas[1])
                
                
#                 if size2 < 0:
#                     self.sell(size = -size2 ,data = self.datas[1])
#                 else:
#                     self.buy(size = size2 ,data = self.datas[1]) 
                
                
                
            
#             self.log("Buy signal, Cash left:  %.2f , buy stock1: %d sell stock2:  %d"  % (self.broker.getcash(),size1,size2 ))
                
#         if self.datas[2].z_score > self.sell_lines:
#             # control the size to be long only if wish
#             size1 = -1
#             size2 = -size1 * self.datas[2].hedge_ratio
                
# #             size1 = np.ceil(((self.broker.getcash()/2)/(1+self.datas[2].relative_mv[0])/self.datas[0].close[0]))
# #             size2 = np.ceil(((self.broker.getcash()/2)\
# #                                /(1+self.datas[2].relative_mv)*self.datas[2].relative_mv[0]/self.datas[1].close[0])) 
            
#             if self.getposition(self.datas[0]).size != size1:
#                 self.log("Close sell position: %d" % (self.getposition(self.datas[0]).size))
#                 self.close(data=self.datas[0])
                
#                 if size1 < 0:
                
#                     self.sell(size = -size1 ,data = self.datas[0]) 
#                 else:
#                     self.buy(size = size1 ,data = self.datas[0])
          
#             if self.getposition(self.datas[1]).size != size2:
#                 self.log("Close buy position: %d" % (self.getposition(self.datas[1]).size))
#                 self.close(data=self.datas[1])
                
                
#                 if size2 < 0:
#                     self.sell(size = -size2 ,data = self.datas[1])
#                 else:
#                     self.buy(size = size2 ,data = self.datas[1])
                
            
#             self.log("sell signal, Cash left:  %.2f , sell stock1: %d buy stock2:  %d "  % (self.broker.getcash(),size1,size2 ))
        
                    
                    

def remember_spot(x):
    with open("meanreversion_pair.txt","w") as p:
        p.writelines(x)

def write_result(x):
    with open("meanreversion_result_pair.txt","a") as p:
        p.writelines(x)

method = 'self_minute'
robinhood  = robingateway()
back_day = 90
test = False
start_over = True
H = []
adf = []
bband = []

tradeable = pd.DataFrame()
price = pd.DataFrame()
my_list = pd.read_csv("/home/ken/notebook/My_Trader2.0/file/cantrade.csv")


if test:
    print "Test mode is on!!"
    my_list =  my_list[0:5]

elif start_over:
    done = [0,0]
    print "Starting over"

else:
    try:
        with open("meanreversion_pair.txt", "r") as p:
            done = p.readlines()
            done = done[0].split(",")
    except:
        remember_spot("")
        done = [0,0]
        

for i in range(len(my_list.Ticker)):
    for j in range(len(my_list.Ticker[i:])):    
        if i < int(done[0]):
            continue
            if j <= int(done[1]):
                continue
        try:
            

            print ("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            print 'Pair:' + my_list.Ticker[i] +", " + my_list.Ticker[j]
            price1 = get_price_data([my_list.Ticker[i]],method = 'day', robinhood = robingateway())
            price2 = get_price_data([my_list.Ticker[j]],method = 'day', robinhood = robingateway())
            hr = cadf(price1.Close,price2.Close)
            port = price1.Close + hr*price2.Close
            temp = mean_reversion(0,method,port)
            if  temp[0] == "Hurst Exponent:mean reverting":
                H.append((my_list.Ticker[i],my_list.Ticker[j]))
                send_email(temp +" : "+ str(H), title="Mean Reversion Found")
                write_result(temp +" : "+ str(H))
            if "Augmented Dickey Fuller: significant" in temp[0]:
                adf.append((my_list.Ticker[i],my_list.Ticker[j]))
                send_email(temp +" : "+ str(adf), title="Mean Reversion Found")
                write_result(temp +" : "+ str(adf))
                
                
            temp2 = backtest_pair(my_list.Ticker[i],my_list.Ticker[j],pair_trade_strategy_single,back_day = int(temp[1]),method = method)
            if temp2[0] == "Good Trade":
                bband.append((my_list.Ticker[i],my_list.Ticker[j],int(temp2[1]),int(temp[1])))
                write_result(temp2[0] +" : "+ str(bband))
                send_email("Good Trade" +" : "+ str(bband), title="BBand Good Trade")
                
                


            

            
            
        except Exception as e:
            print e
            print "ERROR"

        if j%200 ==0: 
                remember_spot(str(i)+","+str(j))
                


result = "Hurst Exponential <= 0.5: " + str(H) + '<br>' + "ADF TEST Significant: " + str(adf)
     
send_email(result, title="Mean Reversion Check")