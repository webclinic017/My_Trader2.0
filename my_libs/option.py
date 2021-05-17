from my_lib import *



def option_strategy_table(robinhood,ticker, pc,exp_pos = 0,list_len = 15):
    
    
    bs = 'buy'
    my_price=realtimequote(ticker).price.iloc[0];

    table = pd.DataFrame()

    get_record = []
    op = option_trading(robinhood,ticker,pc,bs,exp_pos)
    for i in range(0,list_len,1):

        if pc == "call":
            i = -i
        temp_strike_price = op.closest_strick_price(my_price*(1-i/100.0))
        if temp_strike_price in get_record:
            continue

        op = option_trading(robinhood,ticker,pc,bs,exp_pos,strike = temp_strike_price)
        op_table = op.current_Option()
        op_table_tick = op.get_option()["min_ticks"].iloc[0]

        op_table.set_value("Below_tick",op_table_tick["below_tick"])

        op_table.set_value("Experation",op.get_exp_date()[exp_pos])
        op_table.set_value("Strike",op.strike)
        op_table.set_value("Symbol",ticker)
        table = table.append(op_table,ignore_index=True)
        get_record.append(temp_strike_price)
        if int(i)%10 ==0:
            time.sleep(3)
    table = table[["Experation","Strike","Symbol","adjusted_mark_price","chance_of_profit_long","chance_of_profit_short","delta","gamma"]]
    table["PC"] = pc
    if pc == "put":
        table = table.sort_values("Strike",ascending = False)
    else:
        table = table.sort_values("Strike",ascending = True)
    table.loc[:,"adjusted_mark_price"] = table["adjusted_mark_price"].astype(float)
    table.loc[:,"Strike"] = table["Strike"].astype(float)
    table.loc[:,"chance_of_profit_short"] = table["chance_of_profit_short"].astype(float)
    table.loc[:,"chance_of_profit_long"] = table["chance_of_profit_long"].astype(float)

    table["Price_Diff"] = table["adjusted_mark_price"].shift(1) - table["adjusted_mark_price"]

    table["Strike_Diff"] = table["Strike"] -table["Strike"].shift(1)

    #######################


    for i in range(len(table)):
        if i != 0 and i != len(table)-1:
            table.loc[i,"Strategy_CF"] = str(table.loc[i-1,"Strike"]) + " & -" + str(table.loc[i,"Strike"])
            table.loc[i,"Sell_Strike"] = str(table.loc[i-1,"Strike"])
            table.loc[i,"Buy_Strike"] = str(table.loc[i,"Strike"])
            table.loc[i,"Strategy_Expected_Profit"] = table.loc[i,"Price_Diff"] * 100 * table.loc[i-1,"chance_of_profit_short"] - abs(table.loc[i,"Strike_Diff"])*100* table.loc[i-1,"chance_of_profit_long"]
    return table

class option_trading():
    
    def __init__(self,robinhood, symbol,pc, buy_sell, exp = None, strike = None ):
        self.trader = robinhood
        self.symbol = symbol
        self.pc=pc.lower()
        self.buy_sell = buy_sell.lower()
        self.my_price = 0        
        self.leg_list= []
        self.adjusted_mark_price = 0
        
        if exp == None:
            self.exp = self.get_exp_date()
            print((self.exp))
            self.exp= self.exp[eval(input("Which exp date"))]
            print((self.exp))
        elif type(exp) == int:
            self.exp = self.get_exp_date()[exp]
            print((self.exp))
          
        ################
        
        self.loaded_option_chain = self.__fetch_option_chain()
        
        
        ################ 
        
          
        if strike == None:
            self.strike = self.get_atp()  
            print ("Going ATP")
        else:
            self.strike = self.closest_strick_price(strike)  

        
        #####
        
        self.loaded_option = self.__fetch_option_info(self.get_p_oc().iloc[0]["id"])
        
        #####
        
        
        if buy_sell == 'sell':
            self.adjusted_mark_price -=  float(self.loaded_option["adjusted_mark_price"])
        elif buy_sell == 'buy':
            self.adjusted_mark_price +=  float(self.loaded_option["adjusted_mark_price"])
        
#         print ("Bid price is %s" % self.bid_price)
        
#         print ("The option information is: ")
#         print (self.get_option_price())
        print(("current option:\n Symbol:%s strike:%s, expiration:%s, type:%s"%(self.symbol,self.strike,self.exp,self.pc)))
        
    def change_option(self,pc, buy_sell, exp = None, strike = None ):
        
        self.pc=pc.lower()
        self.buy_sell = buy_sell.lower()
        
        
        if exp == None:
            self.exp = self.get_exp_date()
            print((self.exp))
            self.exp= self.exp[eval(input("Which exp date"))]
            print((self.exp))
        elif type(exp) == int:
            self.exp = self.get_exp_date()[exp]
            print((self.exp))
            
       ###
        
        self.loaded_option_chain = self.__fetch_option_chain()
        
        
        ###     
          
            
        if strike == None:
            self.strike = self.get_atp()  
            print ("Going ATP")
        else:
            self.strike = self.closest_strick_price(strike)  

        
        #####
        
        self.loaded_option = self.__fetch_option_info(self.get_p_oc().iloc[0]["id"])
        
        #####
        
        
        if buy_sell == 'sell':
             
            self.adjusted_mark_price -=  float(self.loaded_option["adjusted_mark_price"])
        elif buy_sell == 'buy':
            self.adjusted_mark_price +=  float(self.loaded_option["adjusted_mark_price"])
            
        print(("current option:\n Symbol:%s strike:%s, expiration:%s, type:%s"%(self.symbol,self.strike,self.exp,self.pc)))
    
    def __fetch_option_exp_date(self):
        """
        fetch option chain for instrument
        """
        url = "https://api.robinhood.com/options/chains/"
        params = {
            "equity_instrument_ids": self.trader.get_instrument(self.symbol)["id"].values[0],
            "state": "active",
            "tradability": "tradable"
        }
        data = self.trader.my_trader.session.get(url, params=params)
        return data.json()["results"][0]['expiration_dates']


    def __fetch_option_chain(self):
        
        return pd.DataFrame(self.trader.my_trader.get_options(self.symbol,self.exp, self.pc))


    def __fetch_option_info(self,option_id):
        return self.trader.my_trader.get_option_market_data(option_id)
    
    def gen_leg(self,position_effect ="open", ratio_quantity=1, direction = None):
        print(("current option strike:%s, expiration:%s, type:%s"%(self.strike,self.exp,self.pc)))
        
        option_chain= self.get_option()
        assert self.buy_sell in ["buy", "sell"]
        assert position_effect in ["open", "close"]
        self.leg_list.append({ "side": self.buy_sell,
        "option": option_chain["url"].values[0],
        "position_effect": position_effect,
        "ratio_quantity": ratio_quantity })
        self.my_price += self.adjusted_mark_price
        print(("My price is: %s"%self.my_price))
        print ("Current leg list:")
        
        return self.leg_list

    def place_order(self, quantity,price = None):
        
        legs=self.leg_list
        
        if price == None:
            #price = round(self.bid_price,2)
            price = round(self.my_price,2)
            
        
        if price < 0:
            direction = "credit"
            price = -price
        elif price >=0:
            direction = 'debit'
            
        print (price)

        return self.trader.my_trader.place_option_order(legs,quantity,price,direction)
    
    def get_exp_date(self):
        print ("Ascending")
       
        return pd.Series(self.__fetch_option_exp_date()).sort_values().to_list()
    
    def get_strike(self):

        print ("Ascending")
        return list(pd.DataFrame(self.loaded_option_chain).strike_price.astype(float).sort_values())
    
    
    def get_option(self):
        
        result =  pd.DataFrame(self.loaded_option_chain)
        result.strike_price = result.strike_price.astype(float)

        
        return result[result.strike_price == self.strike]
    
    def closest_strick_price_backup(self,target):
        data = self.get_strike()
        pointer = len(data)/2
        def recur(pointer):   
            if data[pointer] - target ==0:
                return pointer
            elif data[pointer] - target >0:
                return pointer/2
            elif data[pointer] - target <0:
                return (len(data)-pointer)/2
            
        while pointer != 0 or data[pointer] - target != 0:
            pointer = recur(pointer)
            
        return data[pointer]
        
    def closest_strick_price(self,target):
       
        
        data = self.get_strike()
        for i in range(len(data)):
            if data[i] - target < 0:
                continue
            elif data[i] - target == 0:
                return data[i]
            elif (target - data[i-1]) < (target - data[i]):
                
                return data[i-1]
            else:
                return data[i]
    def get_atp(self):
   
        
        return float(self.closest_strick_price(realtimequote(self.symbol).price.values[0]))
        
        
    def get_p_oc(self):
    
        cid = self.get_option()
        cid.strike_price = cid.strike_price.apply(lambda x: float(x))
        cid = cid[cid.strike_price == self.strike ]
        
        return cid
    
    def get_atp_oc(self):
        
        
        cid = op.get_option()
        cid.strike_price = cid.strike_price.apply(lambda x: float(x))
        cid = cid[cid.strike_price == float(self.get_atp())]
        
        return cid
    
    def get_option_price(self): 
        return pd.Series(self.loaded_option)

    

    def current_Option(self): 
        print(("current option:\n Symbol:%s strike:%s, expiration:%s, type:%s"%(self.symbol,self.strike,self.exp,self.pc)))
        get = pd.Series(self.loaded_option)
        get.set_value("break_even_pert",(float(get.break_even_price) - float(self.strike))/float(self.strike))
        return get.sort_index()
    