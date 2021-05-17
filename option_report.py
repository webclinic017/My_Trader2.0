from my_libs_py3 import *
import cudf

mongod = mongo()
sql = '''

SELECT * FROM all_symbol.`Screener_TOS`b

'''

price = mongod.conn.get_data(sql)

# ticker = price[((price.Change >= price.Change.quantile(0.8)) | (price.Change <= price.Change.quantile(0.2)))& (price.Price > 20)& (price["Volatility (Month)"]<price["Volatility (Month)"].quantile(0.5))].Ticker

put_ticker = price[(price.Change >= price.Change.quantile(0.8)) & (price.Price > 50) & (price["Volatility (Month)"]<price["Volatility (Month)"].quantile(0.5))].Ticker

call_ticker = price[(price.Change <= price.Change.quantile(0.2)) & (price.Price > 50) & (price["Volatility (Month)"]<price["Volatility (Month)"].quantile(0.5))].Ticker


# initialization
put_result = pd.DataFrame()
call_result = pd.DataFrame()
put_now = put_ticker.iloc[0]
call_now = call_ticker.iloc[0]

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
            table = option_strategy_table(robingateway(),i,"put")
            table = table[(table.chance_of_profit_short > 0.8) & (table.Strategy_Expected_Profit == table.Strategy_Expected_Profit.max()) & (table.Strategy_Expected_Profit >0) & (abs(table.Price_Diff )< abs(table.Strike_Diff))]
            put_result= put_result.append(table)
        except Exception as e:
            print (e)
            time.sleep(1)
            continue 
end_time = time.time()
print (end_time - start_time)





##################
# Put Trade action
#################

time.sleep(30)
put_code = ''
put_traded = ''


trade_flag = 0
if datetime.now().hour >=7 and datetime.now().hour <10:
    put_result = put_result.sort_values("Strategy_Expected_Profit",ascending=False)
    put_result=put_result[abs(put_result.Strike_Diff) <=5]

    if len(put_result)>0:

        for i in range(1,len(put_result.Symbol)):
            if  trade_flag < 3:
#                 try:
                row = i

                ## Trade put stategy
                op = option_trading(robingateway(),put_result.iloc[row]["Symbol"],'put','buy',0,strike = float(put_result.iloc[row]["Buy_Strike"]))
                op.gen_leg()

                op.change_option('put','sell',0,strike = float(put_result.iloc[row]["Sell_Strike"]))
                op.gen_leg()

                trade_price = -float(put_result.iloc[row]["Price_Diff"]) if abs(float(put_result.iloc[row]["Price_Diff"])) < abs(float(put_result.iloc[row]["Strike_Diff"])) else -abs(float(put_result.iloc[row]["Strike_Diff"]))
                trade_price = round(trade_price,2)

                try:

                    put_code = op.place_order(1,trade_price)
                    put_code["cancel_url"]
                except:
                    print ("Trade Fail")
                    print (put_code)

                    continue

                trade_flag += 1
                put_traded = put_result.iloc[i]["Symbol"]
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
            table = option_strategy_table(robingateway(),i,"call")
            table = table[(table.chance_of_profit_short > 0.8) & (table.Strategy_Expected_Profit == table.Strategy_Expected_Profit.max()) & (table.Strategy_Expected_Profit >0) & (abs(table.Price_Diff )< abs(table.Strike_Diff))]
            call_result= call_result.append(table)
        except Exception as e:
            print (e)
            time.sleep(1)
            continue 



##################
# Call Trade action
#################

time.sleep(30)
call_code = ''
call_traded = ''


trade_flag = 0            
if datetime.now().hour >=7 and datetime.now().hour <10:
    call_result = call_result.sort_values("Strategy_Expected_Profit",ascending=False)
    call_result=call_result[abs(call_result.Strike_Diff) <=5]
    
    if len(call_result)>0:
    
        for i in range(1,len(call_result.Symbol)):
            if  trade_flag < 3:
#                 try:    
                row = i

                ## Trade put stategy
                op = option_trading(robingateway(),call_result.iloc[row]["Symbol"],'call','buy',0,strike = float(call_result.iloc[row]["Buy_Strike"]))
                op.gen_leg()

                op.change_option('call','sell',0,strike = float(call_result.iloc[row]["Sell_Strike"]))
                op.gen_leg()

                trade_price = -float(call_result.iloc[row]["Price_Diff"]) if abs(float(call_result.iloc[row]["Price_Diff"])) < abs(float(call_result.iloc[row]["Strike_Diff"])) else -abs(float(call_result.iloc[row]["Strike_Diff"]))
                trade_price = round(trade_price,2)

                try:

                    call_code = op.place_order(1,trade_price)
                    call_code["cancel_url"]
                except:
                    print ("Trade Fail")
                    print (call_code)
                    
                    continue

                trade_flag += 1
                call_traded = call_result.iloc[i]["Symbol"]
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
<b>Code:</b>
%s


<br><br>
<b>Call Traded:</b>
%s
<br><br>
<b>Code:</b>
%s

'''%(put_result.to_html(), call_result.to_html(),put_traded,put_code, call_traded, call_code)





send_email(title = "Option Report", body_html= html)
