

from my_trader import *


def complete_line(pct):
    graph = "->"
    pct *=100
    line_pct = np.ceil(pct/5)
    for i in range(int(line_pct)):
        graph += "->"
#    print (graph + "  " + str(pct) + "%")
    print (graph + "{0:>100.2f}%".format(pct))


continue_point = 0
skip_list=["BYLB"]


start = timeit.default_timer()
tradeable = pd.read_csv(directory + "ETFList.csv")
pair=[]
good_pair = []
count = 0
res_total_return=[]
res_ave_return=[]
res_volatility=[]
res_sharp_ratio=[]
pairs=[]

header = [('pairs','ave_return','total_return','volatility',	'sharp_ratio')]
if continue_point >0:
    my_csv=write_my_csv("pair_ETF_0302.csv",header,False)
else:
    my_csv=write_my_csv("pair_ETF_0302.csv",header)
for i in tradeable.Ticker:
#     start_point+=1
     for j in tradeable.Ticker:

        count +=1
        if count <= continue_point:
            continue
        if i==j or i in skip_list or j in skip_list :
            continue
        else:
#            if count %20 ==0:
#                time.sleep(60)

            print ("\n")
            print ("***************************")
            print ("Pair {} and {}".format(i,j))
            try:
                temp_price = pair_trade(i,j,1500,continuous=True)
            except KeyError:
                print ("price data not complete")
                continue
            try:
                total_return  = temp_price.p_L.sum()
                ave_return = temp_price.p_L.mean()
                volatility = temp_price.p_L.std()
                sharp_ratio = ave_return/volatility

                print ("Total return = {}".format(total_return))
                print ("Average return = {}".format(ave_return))
                print ("Volatility = {}".format(volatility))
                print ("Sharp_ratio = {}".format(sharp_ratio))
                my_csv.write_row([((i,j),total_return,ave_return,volatility,sharp_ratio)])


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
