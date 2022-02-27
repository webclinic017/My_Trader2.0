# -*- coding: utf-8 -*-
"""
Created on Thu Mar 08 16:52:46 2018

@author: gli26
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 17:29:38 2018

@author: gli26
"""

from my_trader import *
import random
#from my_strategies import *

#robinhood = get_robinhood()
#
#
#stocks, quantity = robinhood.get_my_positions()
#
#plot_position(stocks,quantity)
#robinhood.logout()

#update_fundamentals()

def complete_line(pct):
    graph = "->"
    pct *=100
    line_pct = np.ceil(pct/5)
    for i in range(int(line_pct)):
        graph += "->"
#    print (graph + "  " + str(pct) + "%")
    print (graph + "{0:>100.2f}%".format(pct))
    

random.seed(time.time())

continue_point = 0        
skip_list=["BYLB"]
used = []

start = timeit.default_timer()
tradeable = pd.read_csv(directory + "cantrade.csv")
pair=[]
good_pair = []
signal_pair=[]
count = 0
res_total_return=[]
res_ave_return=[]
res_volatility=[]
res_sharp_ratio=[]
pairs=[]

header = [('pairs','ave_return','total_return','volatility',    'sharp_ratio')]
if continue_point >0:
    my_csv=write_my_csv("pair_ETF_0302.csv",header,False)
else:
    my_csv=write_my_csv("pair_ETF_0302.csv",header)
while True:
#     start_point+=1
    i = tradeable.Ticker.iloc[random.randrange(0,len(tradeable.Ticker))]
#    if i in used_i:
#         continue
#    used_i.append(i)
     
    j = tradeable.Ticker.iloc[random.randrange(0,len(tradeable.Ticker))]
#    if j in used_j:
#        continue
#    used_j.append(j)
    
    
    
#    if count <= continue_point:
#        continue
    if i==j or i in skip_list or j in skip_list or (i,j) in used :
        continue
    else:
        used.append((i,j))
#            if count %20 ==0:
#                time.sleep(60)
        count +=1
        print ("\n")
        print ("***************************")
        print ("Pair {} and {}".format(i,j))
        try:
            temp_price = pair_trade_short(i,j,1500,window=10,continuous=False)
        except KeyError:
            print ("price data not complete")
            continue
        try:
            total_return  = temp_price.p_L.sum()
            ave_return = temp_price.p_L.mean()
            volatility = temp_price.p_L.std()
            sharp_ratio = ave_return/volatility 
            
            if total_return >150 and sharp_ratio >0.5:
                good_pair.append((i,j))
                temp_price.to_csv("signal/" + str(datetime.now())[0:10] + "_good_pair.csv")
                
                
            if temp_price.iloc[-1].trade.sum() >0 and temp_price.p_L.sum() >100:    
                signal_pair.append(i,j)
            
            print ("Total return = {}".format(total_return))
            print ("Average return = {}".format(ave_return))
            print ("Volatility = {}".format(volatility))
            print ("Sharp_ratio = {}".format(sharp_ratio))
            my_csv.write_row([((i,j),total_return,ave_return,volatility,sharp_ratio)])
            '''
            if temp_price.iloc[-1].trade >0 and temp_price.p_L >100:
                print ("Pair {} and {}, signal raise!".format(i,j))
                print (temp_price.iloc[-1])
                temp_price.to_csv("signal/"+str(datetime.now())+"_trade_singal_pair.csv")
                input("press any key to continue")
            '''
            
#                res_total_return.append(total_return)
#                res_ave_return.append(ave_return)
#                res_volatility.append(volatility)
#                res_sharp_ratio.append(sharp_ratio)
#                pairs.append((i,j))
#                if total_return >100 and ave_return > 5:
#                    pair.append((i,j))
#                if sharp_ratio >1:
#                    good_pair.append((i,j))
#                if count %100 ==0:
#                    final = pd.DataFrame({"pairs":pairs,"total_return":res_total_return,\
#    "ave_return":res_ave_return,"volatility":res_volatility,\
#    "sharp_ratio":res_sharp_ratio})
#                    final.to_csv("pair_trade_BT.csv")
        except Exception as e:
            print e    
            continue
    complete_line(float(count)/(len(tradeable)*len(tradeable)))
#final = pd.DataFrame({"pairs":pairs,"total_return":res_total_return,\
#    "ave_return":res_ave_return,"volatility":res_volatility,\
#    "sharp_ratio":res_sharp_ratio})
final.to_csv("pair_trade_BT.csv")
stop = timeit.default_timer()
print ("total time {}".format(stop-start))