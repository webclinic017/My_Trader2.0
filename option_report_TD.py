from my_libs_py3 import *
# import cudf

mongod = mongo("all_symbol","screener")

tos = pd.DataFrame(mongod.conn.table.find({},{"Refresh_Date":1}).sort("Refresh_Date",-1).limit(1))["Refresh_Date"].iloc[0]
price = pd.DataFrame(mongod.conn.table.find({"Refresh_Date":tos}))



# ticker = price[((price.Change >= price.Change.quantile(0.8)) | (price.Change <= price.Change.quantile(0.2)))& (price.Price > 20)& (price["Volatility (Month)"]<price["Volatility (Month)"].quantile(0.5))].Ticker

put_ticker = price[(price.Change >= price.Change.quantile(0.8)) & (price.Price > 50) & (price["Volatility (Month)"]<price["Volatility (Month)"].quantile(0.5))].Ticker

call_ticker = price[(price.Change <= price.Change.quantile(0.2)) & (price.Price > 50) & (price["Volatility (Month)"]<price["Volatility (Month)"].quantile(0.5))].Ticker


# initialization
put_result = pd.DataFrame()
call_result = pd.DataFrame()
put_now = put_ticker.iloc[0]
call_now = call_ticker.iloc[0]
put_traded = []
call_traded = []
##################

# Screen Put

#################
start_time = time.time()
start = False
for i in put_ticker:
    if i == put_now:
        start = True
    if start:
        try:
            table = option_strategy_table_TD(i,"put")
            table = table[(table.chance_of_profit_short > 0.8) \
                          & (table.Strategy_Expected_Profit == table.Strategy_Expected_Profit.max()) \
                          & (table.Strategy_Expected_Profit >0) \
                          & (abs(table.Price_Diff )< abs(table.Strike_Diff))]
            table = table[table.Strategy_Expected_Profit > 50]
            put_result= put_result.append(table)
        except Exception as e:
            print (e)
            time.sleep(5)
            continue 
put_result = put_result.sort_values("Strategy_Expected_Profit",ascending=False)
end_time = time.time()
print (end_time - start_time)





##################
# Put Trade action
#################

time.sleep(10)



trade_flag = 0
if datetime.now().hour >=7 and datetime.now().hour <20:
    put_result = put_result.sort_values("Strategy_Expected_Profit",ascending=False)
    put_result=put_result[abs(put_result.Strike_Diff) <=5]

    if len(put_result)>0:

        for i in range(1,len(put_result.symbol)):
            if trade_flag < 1:
                try:


                    ## Trade put stategy
                    myordertype = order_type.NET_CREDIT if put_result.iloc[i]["Price_Diff"] >0 else order_type.NET_DEBIT
                    my_option_order = order_option(myordertype)
                    my_option_order.gen_leg(put_result.iloc[i]["Buy_Symbol"],1,put_result.iloc[i]["putCall"],instruction=instruction_type.BUY_TO_OPEN)
                    my_option_order.gen_leg(put_result.iloc[i]["Sell_Symbol"],1,put_result.iloc[i]["putCall"],instruction=instruction_type.SELL_TO_OPEN)
                    my_option_order.place(round(put_result.iloc[i]["Price_Diff"],2))
                    trade_flag += 1
                    put_traded.append(put_result.iloc[i]["symbol"])

             
                except:
                    print ("Trade Fail")


                    continue


#                 except Exception as e:
#                     print (e)
#                     continue




##################

# Screen Call

#################
start = False
for i in call_ticker:
    if i == call_now:
        start = True
    if start:
        try:
            table = option_strategy_table_TD(i,"call")
            table = table[(table.chance_of_profit_short > 0.8) \
                          & (table.Strategy_Expected_Profit == table.Strategy_Expected_Profit.max()) \
                          & (table.Strategy_Expected_Profit >0) \
                          & (abs(table.Price_Diff )< abs(table.Strike_Diff))]
            table = table[table.Strategy_Expected_Profit > 50]
            call_result= call_result.append(table)
        except Exception as e:
            print (e)
            time.sleep(1)
            continue
call_result = call_result.sort_values("Strategy_Expected_Profit", ascending=False)


##################
# Call Trade action
#################

time.sleep(10)



trade_flag = 0            
if datetime.now().hour >=7 and datetime.now().hour <20:
    call_result = call_result.sort_values("Strategy_Expected_Profit",ascending=False)
    call_result=call_result[abs(call_result.Strike_Diff) <=5]
    
    if len(call_result)>0:
    
        for i in range(1,len(call_result.symbol)):
            if  trade_flag < 1:
                try:


                ## Trade put stategy
                    myordertype = order_type.NET_CREDIT if call_result.iloc[i]["Price_Diff"] >0 else order_type.NET_DEBIT
                    my_option_order = order_option(myordertype)
                    my_option_order.gen_leg(call_result.iloc[i]["Buy_Symbol"],1,call_result.iloc[i]["putCall"],instruction=instruction_type.BUY_TO_OPEN)
                    my_option_order.gen_leg(call_result.iloc[i]["Sell_Symbol"],1,call_result.iloc[i]["putCall"],instruction=instruction_type.SELL_TO_OPEN)
                    my_option_order.place(round(call_result.iloc[i]["Price_Diff"],2))
                    trade_flag += 1
                    call_traded.append(call_result.iloc[i]["symbol"])

             

                except:
                    print ("Trade Fail")
                    continue


#                 except Exception as e:
#                     print (e)
#                     continue


html = '''

Here's the report: 
<br><br>

<b>Put Report</b>:<br>
%s

<br><br>

<b>Call Report</b>:<br>
%s
<br><br>
<b>Put Traded:</b>
%s



<br><br>
<b>Call Traded:</b>
%s


'''%(put_result.to_html(), call_result.to_html(),put_traded, call_traded)





send_email(title = "Option Report", body_html= html)
