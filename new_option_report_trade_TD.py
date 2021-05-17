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
put_traded = None
call_traded = None
call_result=pd.DataFrame()
put_result=pd.DataFrame()
##################

# Screen Call

#################
start_time = time.time()
start = False
for i in put_ticker:
    if i == put_now:
        start = True
    if start and put_traded <=3:
        try:
            table = option_strategy_table_TD(i,"call")
            table = table[(table.chance_of_profit_short > 0.8) \
                          & (table.Strategy_Expected_Profit == table.Strategy_Expected_Profit.max()) \
                          & (table.Strategy_Expected_Profit >0) \
                          & (abs(table.Price_Diff )< abs(table.Strike_Diff))]
            table = table[table.Strategy_Expected_Profit > 50]

            if len(table) > 0:
                try:

                    myordertype = order_type.NET_CREDIT if table.iloc[0]["Price_Diff"] >0 else order_type.NET_DEBIT
                    my_option_order = order_option(myordertype)
                    my_option_order.gen_leg(table.iloc[0]["Buy_Symbol"],1,table.iloc[0]["putCall"],instruction=instruction_type.BUY_TO_OPEN)
                    my_option_order.gen_leg(table.iloc[0]["Sell_Symbol"],1,table.iloc[0]["putCall"],instruction=instruction_type.SELL_TO_OPEN)
                    my_option_order.place(round(table.iloc[0]["Price_Diff"],2))
            
                except:
                    print ("Trade Fail")


                    continue

                call_traded = table.iloc[i]["Symbol"]

            call_result= call_result.append(table)
        except Exception as e:
            print (e)
            time.sleep(2)
            continue
end_time = time.time()
print (end_time - start_time)


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
            table = option_strategy_table_TD(i,"put")
            table = table[(table.chance_of_profit_short > 0.8) \
                          & (table.Strategy_Expected_Profit == table.Strategy_Expected_Profit.max()) \
                          & (table.Strategy_Expected_Profit >0) \
                          & (abs(table.Price_Diff )< abs(table.Strike_Diff))]
            table = table[table.Strategy_Expected_Profit > 50]

            if len(table) > 0:
                try:

                    myordertype = order_type.NET_CREDIT if table.iloc[0]["Price_Diff"] >0 else order_type.NET_DEBIT
                    my_option_order = order_option(myordertype)
                    my_option_order.gen_leg(table.iloc[0]["Buy_Symbol"],1,table.iloc[0]["putCall"],instruction=instruction_type.BUY_TO_OPEN)
                    my_option_order.gen_leg(table.iloc[0]["Sell_Symbol"],1,table.iloc[0]["putCall"],instruction=instruction_type.SELL_TO_OPEN)
                    my_option_order.place(round(table.iloc[0]["Price_Diff"],2))
            
                except:
                    print ("Trade Fail")
                    continue

                put_traded = table.iloc[i]["Symbol"]

            put_result= put_result.append(table)
        except Exception as e:
            print (e)
            time.sleep(2)
            continue
end_time = time.time()
print (end_time - start_time)