from .tdameritrade import *
from .my_lib import *

account_id = 277216702
client  = TDClient(client_id="QV4XBB76GOYNVORVOBPMN3PKZFURM0VZ",refresh_token=readgateway(7),account_ids=[str(account_id)])


def get_order_by_id(_id):
    orders = client.orders()
    orders = list(filter(lambda x: x["orderId"]==_id,orders))
    return orders[0]


def get_td_last_order():
    order = client.orders()
    order = list(sorted(filter(lambda x: x["orderLegCollection"][0]["orderLegType"]=="EQUITY",order),key=lambda x: x["enteredTime"]))
    return order[-1]

def cancel_order(orderid):
    code = client.cancelOrder(account_id,orderid).status_code
    if code == 200:
        return True
    else:
        time.sleep(3)
        code = client.cancelOrder(account_id,orderid).status_code
        time.sleep(1)
        code = client.cancelOrder(account_id,orderid).status_code
    if code == 200:
        return True
    else:
        return False


def search_strike(x, thelist):
    thelist = [float(x) for x in thelist]
    thelist.sort()
    pointer = int(len(thelist)/2)
    up = 0
    down = len(thelist) -1
    while not(x == thelist[pointer]) and down - up >1:
        # print("%s,%s,%s"%(up,down,pointer))
        if x > thelist[pointer]:
            up = pointer
            pointer = up + int((down-up)/2)
        elif x< thelist[pointer]:
            down = pointer
            pointer = down - int((down-up)/2)
    return thelist[pointer]


def option_strategy_table_TD(ticker, pc,exp_pos = 0,list_len = 15):
    
    pc = pc.upper()
    
    my_price=realtimequote(ticker).price.iloc[0];

    table = pd.DataFrame()

    get_record = []
    op = client.optionsDF(ticker,pc)
    for i in range(0,list_len,1):

        if pc == "PUT":
            i = -i
            
        exp_date = list(set(op["expirationDate"]))
        myexpdate = exp_date[exp_pos]
        op2 = op[op.expirationDate == myexpdate]
        # strike selector
        strike = op2.strikePrice
         
        strike_start_index = strike[strike == search_strike(my_price,strike)].index
        temp_strike_price = strike.loc[strike_start_index+i].iloc[0] 

        if temp_strike_price in get_record:
            continue

        op3 = op2[op2.strikePrice ==temp_strike_price]
        
        op3 = op3[["putCall","symbol","strikePrice","expirationDate","daysToExpiration","bid","ask","last","mark","closePrice","volatility",\
                 "delta","gamma","theta","vega","theoreticalVolatility"]]

        op_table = op3    
        
        ######### Got a option and calculate chance of profit ###############

        val_num_steps = 100
        val_num_paths = 100

        val_random_seed = int(time.time())
        np.random.seed(val_random_seed)


        riskless_rate = 0
        yield_ = 0

        cont_yield = 0 if hasattr(yield_, '__call__') else yield_
        mat = op.iloc[i]["daysToExpiration"]
        vol = float(op.iloc[i]["volatility"])/100


        dt = mat / val_num_steps
        sqrt_dt = dt ** 0.5
        cont_yield = 0 if hasattr(yield_, '__call__') else yield_
        drift = (riskless_rate - cont_yield - (vol ** 2) / 2) * dt

        spot = float(realtimequote(ticker).price.iloc[0])
        target = float(op.iloc[i]["strikePrice"])


        ##### Modeling
        def cast_spot_paths(spot):
            result = np.empty([val_num_paths, val_num_steps])
            for path_num in range(val_num_paths):
                result1 = np.empty([val_num_steps])
                result1[0] = spot
                temp = spot

                for step_num in range(1, val_num_steps):
                    temp *= np.exp(drift + vol * np.random.normal() * sqrt_dt)
                    if hasattr(yield_, '__call__'):
                        div_t1, div_t2 = dt * step_num, dt * (step_num + 1)
                        div = yield_(div_t1, div_t2)
                        if is_number(div): spot -= div
                    result1[step_num] = temp

                result[path_num] = result1
            return result


        path = cast_spot_paths(spot)

        end_point = []
        for item in path:
            end_point.append(item[4])

        end_point=np.array(end_point)

        prob = len(end_point[end_point>=target])/len(end_point)

            
        op_table["chance_of_profit_long"] = prob
        op_table["chance_of_profit_short"] = 1-prob
        
        
#         op_table["Below_tick"] = op_table_tick["below_tick"]
#         op_table["Experation"] = op.get_exp_date()[exp_pos]
#         op_table["Strike"] = op.strike
#         op_table["Symbol"] = ticker

#         op_table.set_value("Below_tick",op_table_tick["below_tick"])

#         op_table.set_value("Experation",op.get_exp_date()[exp_pos])
#         op_table.set_value("Strike",op.strike)
#         op_table.set_value("Symbol",ticker)
        table = table.append(op_table,ignore_index=True)
        get_record.append(temp_strike_price)
        if int(i)%15 ==0:
            time.sleep(5)
#     table = table[["Experation","Strike","Symbol","adjusted_mark_price","chance_of_profit_long","chance_of_profit_short","delta","gamma","high_fill_rate_buy_price","high_fill_rate_sell_price","ask_price","bid_price"]]
#     table["PC"] = pc
    if pc == "PUT":
        table = table.sort_values("strikePrice",ascending = False)
    else:
        table = table.sort_values("strikePrice",ascending = True)
#     table.loc[:,"adjusted_mark_price"] = table["adjusted_mark_price"].astype(float)
#     table.loc[:,"high_fill_rate_sell_price"] = table["high_fill_rate_sell_price"].astype(float)
#     table.loc[:,"high_fill_rate_buy_price"] = table["high_fill_rate_buy_price"].astype(float)
#     table.loc[:,"ask_price"] = table["ask_price"].astype(float)
#     table.loc[:,"bid_price"] = table["bid_price"].astype(float)
#     table.loc[:,"Strike"] = table["Strike"].astype(float)
#     table.loc[:,"chance_of_profit_short"] = table["chance_of_profit_short"].astype(float)
#     table.loc[:,"chance_of_profit_long"] = table["chance_of_profit_long"].astype(float)

    table.loc[:,"ask"] = table["ask"].astype(float)
    table.loc[:,"bid"] = table["bid"].astype(float)
    table.loc[:,"mark"] = table["mark"].astype(float)
    table.loc[:,"closePrice"] = table["closePrice"].astype(float)
    
    ## Get the price difference
    table["Price_Diff"] = table["mark"].shift(1) - table["mark"]
    # table["Price_Diff"] -= table["Price_Diff"]*0.1
#     print (table["Price_Diff"] )

    table["Strike_Diff"] = table["strikePrice"] -table["strikePrice"].shift(1)

    #######################


    for i in range(len(table)):
        if i != 0 and i != len(table)-1:
            table.loc[i,"Strategy_CF"] = str(table.loc[i-1,"strikePrice"]) + " & -" + str(table.loc[i,"strikePrice"])
            table.loc[i,"Sell_Symbol"] = str(table.loc[i-1,"symbol"])
            table.loc[i,"Buy_Symbol"] = str(table.loc[i,"symbol"])
            table.loc[i,"Strategy_Expected_Profit"] = table.loc[i,"Price_Diff"] * 100 *\
                    table.loc[i-1,"chance_of_profit_short"] - abs(table.loc[i,"Strike_Diff"])*100* \
                    table.loc[i-1,"chance_of_profit_long"]
#             print (table.loc[i,"Strategy_Expected_Profit"])
    return table

class instruction_type(enumerate):
    SELL = "SELL"
    BUY = "BUY"
    BUY_TO_COVER = "BUY_TO_COVER"
    BUY_TO_OPEN = "BUY_TO_OPEN"
    BUY_TO_CLOSE = "BUY_TO_CLOSE"
    SELL_TO_OPEN = "SELL_TO_OPEN"
    SELL_TO_CLOSE = "SELL_TO_CLOSE"
    EXCHANGE = "EXCHANGE"
    SELL_SHORT = "SELL_SHORT"


class order_type(enumerate):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    NET_CREDIT = "NET_CREDIT"
    NET_DEBIT = "NET_DEBIT"
    NET_ZERO = "NET_ZERO"

class option_type(enumerate):
    CALL = "CALL"
    PUT = "PUT"

    
class order_equity():

    def __init__(self, this_order_type:order_type):
        self.ordertype = this_order_type
        self.leg = []


    def place (self,ticker:str,quantity:int ,price=None, quantity_type = 'SHARES', instruction:instruction_type = None):
        
        price = price or round(float(client.quoteDF(ticker).lastPrice),2)

        if instruction is None:
            if quantity < 0:
                instruction = instruction_type.SELL
                quantity=-quantity
            elif quantity > 0:
                instruction = instruction_type.BUY
            else:
                print ("Quantity should not be zero")
                raise
        else:
            if quantity <= 0:
                print ("When you feed instruction, Quantity should not be zero or less")
                raise

        order_dic = {
            "session": "NORMAL",
            "duration": 'DAY',
            "orderType":self.ordertype,
            "price": price,
            "orderStrategyType": "SINGLE",
            "orderLegCollection":  
                [{
                    "orderLegType": "EQUITY",
                    "instrument": { 'symbol': ticker,'assetType': 'EQUITY'},
                    "instruction": instruction,
                    # "positionEffect": 'OPENING',
                    "quantity": quantity,
                    "quantityType":  quantity_type
                }]

        }
        client.placeOrder(client.accountIds[0],order_dic)
        time.sleep(0.8)
        ## Check order status
        last_status = get_td_last_order()["status"]
        last_id = get_td_last_order()["orderId"]
        return last_id
#         if last_status == "REJECTED":
#             return "REJECTED"
#         else:
#             return "Not REJECTED"
        
    def pair_trade_place(self,ticker1:str,ticker2:str, quantity1:int ,quantity2:int ,price1=None, price2=None, quantity_type = 'SHARES'):
        price1 = price1 or float(client.quoteDF(ticker1).lastPrice)
        price2 = price2 or float(client.quoteDF(ticker2).lastPrice)

        def get_instruction(quantity):
            if quantity < 0:
                instruction = instruction_type.SELL
                quantity=-quantity
            elif quantity > 0:
                instruction = instruction_type.BUY
            else:
                print ("Quantity should not be zero")
                raise
            return instruction, abs(quantity)
        
        instruction1, quantity1 = get_instruction(quantity1)
        instruction2, quantity2 = get_instruction(quantity2)
   

        order_dic = {
            "session": "NORMAL",
            "duration": 'DAY',
            "orderType":self.ordertype,
            "price": price1,
            "orderStrategyType": "TRIGGER",
            "orderLegCollection":  
                [{
                    "orderLegType": "EQUITY",
                    "instrument": { 'symbol': ticker1,'assetType': 'EQUITY'},
                    "instruction": instruction1,
                    # "positionEffect": 'OPENING',
                    "quantity": quantity1,
                    "quantityType":  quantity_type
                }],
            "childOrderStrategies": [
                                        {
                                          "orderType": "MARKET",
                                          "session": "NORMAL",
                                          "price": price2,
                                          "duration": "DAY",
                                          "orderStrategyType": "SINGLE",
                                          "orderLegCollection": [
                                            {
                                              "instruction": instruction2,
                                              "quantity": quantity2,
                                              "instrument": {"symbol": ticker2,"assetType": "EQUITY"},
                                              "quantityType":  quantity_type 
                                           }
                                              ]

                                            }
                                    ]
                 }
        client.placeOrder(client.accountIds[0],order_dic)


class order_option():

    def __init__(self,ordertype):
#         self.option_type = option_type
        self.ordertype = ordertype
#         self.price = price
        self.leg = []




    def gen_leg(self,ticker:str,quantity:int, option_type, instruction:instruction_type = None ):


        if instruction is None:
            if quantity < 0:
                instruction = instruction_type.SELL_TO_OPEN
                quantity = -quantity
            elif quantity > 0:
                instruction = instruction_type.BUY_TO_OPEN
                
            else:
                print ("Quantity should not be zero")
                raise
        else:
            if quantity <= 0:
                print ("When you feed instruction, Quantity should not be zero or less")
                raise

        



        self.leg.append(
                {
                    "orderLegType": "OPTION",

                    "instrument": {
                                  "assetType": "OPTION",
                                  "symbol": ticker,
                                  "putCall": option_type,

                                  # "optionMultiplier":  self.quantity
                                  # "underlyingSymbol": "string",

                                },
                    "instruction": instruction,
                    # "positionEffect": 'OPENING',
                    "quantity": quantity,
                    # "quantityType":  'SHARES'
                }
            )

        print("Current legs:/n")
        print(self.leg)


    def place (self,price):



        order_dic = {
            "session": "NORMAL",
            "duration": 'DAY',
            "orderType":self.ordertype,
            # "quantity": 0,
            "price": price,
            "orderStrategyType": "SINGLE",
            "orderLegCollection": self.leg

        }
        client.placeOrder(client.accountIds[0],order_dic)
