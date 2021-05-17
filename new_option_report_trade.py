from my_libs_py3 import *
# import cudf

mongod = mongo()
sql = '''

SELECT * FROM all_symbol.`Screener_TOS`

'''

price = mongod.conn.get_data(sql)

# ticker = price[((price.Change >= price.Change.quantile(0.8)) | (price.Change <= price.Change.quantile(0.2)))& (price.Price > 20)& (price["Volatility (Month)"]<price["Volatility (Month)"].quantile(0.5))].Ticker

put_ticker = price[(price.Change >= price.Change.quantile(0.8)) & (price.Price > 50) & (price["Volatility (Month)"]<price["Volatility (Month)"].quantile(0.5))].Ticker

call_ticker = price[(price.Change <= price.Change.quantile(0.2)) & (price.Price > 50) & (price["Volatility (Month)"]<price["Volatility (Month)"].quantile(0.5))].Ticker


# initialization

put_now = put_ticker.iloc[0]
call_now = call_ticker.iloc[0]
put_traded = 0
call_traded = 0
call_result=pd.DataFrame()
put_result=pd.DataFrame()
##################

# Screen Put

#################
start_time = time.time()
start = False
for i in put_ticker:
    if i == put_now:
        start = True
    if start and put_traded <=3:
        try:
            table = option_strategy_table(robingateway(),i,"put")
            table = table[(table.chance_of_profit_short > 0.8) & (table.Strategy_Expected_Profit == table.Strategy_Expected_Profit.max()) & (table.Strategy_Expected_Profit >0) & (abs(table.Price_Diff )< abs(table.Strike_Diff))]
            table = table[table.Strategy_Expected_Profit > 50]

            if len(table) > 0:

                op = option_trading(robingateway(),table.iloc[0]["Symbol"],'put','buy',0,strike = float(table.iloc[0]["Buy_Strike"]))
                op.gen_leg()

                op.change_option('put','sell',0,strike = float(table.iloc[0]["Sell_Strike"]))
                op.gen_leg()

                trade_price = -float(table.iloc[0]["Price_Diff"]) if abs(float(table.iloc[0]["Price_Diff"])) < abs(float(table.iloc[0]["Strike_Diff"])) else -abs(float(table.iloc[0]["Strike_Diff"]))
                trade_price = round(trade_price,2)

                try:

                    put_code = op.place_order(1,trade_price)
                    put_code["cancel_url"]
                    send_email(title = "Option Traded", body_html= put_code)
                    put_traded += 1
                except:
                    print ("Trade Fail")
                    print (put_code)

                    continue

                put_traded = table.iloc[i]["Symbol"]

            put_result= put_result.append(table)
        except Exception as e:
            print (e)
            time.sleep(1)
            continue
end_time = time.time()
print (end_time - start_time)


##################

# Screen Call

#################
start_time = time.time()
start = False
for i in put_ticker:
    if i == put_now:
        start = True
    if start and call_traded <=3:
        try:
            table = option_strategy_table(robingateway(),i,"call")
            table = table[(table.chance_of_profit_short > 0.8) & (table.Strategy_Expected_Profit == table.Strategy_Expected_Profit.max()) & (table.Strategy_Expected_Profit >0) & (abs(table.Price_Diff )< abs(table.Strike_Diff))]
            table = table[table.Strategy_Expected_Profit > 50]

            if len(table) > 0:

                op = option_trading(robingateway(),table.iloc[0]["Symbol"],'call','buy',0,strike = float(table.iloc[0]["Buy_Strike"]))
                op.gen_leg()

                op.change_option('call','sell',0,strike = float(table.iloc[0]["Sell_Strike"]))
                op.gen_leg()

                trade_price = -float(table.iloc[0]["Price_Diff"]) if abs(float(table.iloc[0]["Price_Diff"])) < abs(float(table.iloc[0]["Strike_Diff"])) else -abs(float(table.iloc[0]["Strike_Diff"]))
                trade_price = round(trade_price,2)

                try:

                    put_code = op.place_order(1,trade_price)
                    put_code["cancel_url"]
                    send_email(title = "Option Traded", body_html= put_code)
                    call_traded += 1
                except:
                    print ("Trade Fail")
                    print (put_code)

                    continue

                call_traded = table.iloc[i]["Symbol"]

            call_result= call_result.append(table)
        except Exception as e:
            print (e)
            time.sleep(1)
            continue
end_time = time.time()
print (end_time - start_time)
