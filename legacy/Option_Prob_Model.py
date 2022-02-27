from my_libs_py3 import *
import urllib.parse as up

client.accounts()

# get account
pos = client.accountsDF().transpose()


### Functions #############
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



################################## Get Option for Prob Calculation #########################
ticker = "AAPL"
#get options DF
op = client.optionsDF(ticker,"CALL")



# there should be a loop or use the selected option
i = 0
exp_date = list(set(op["expirationDate"]))
myexpdate = exp_date[i]
op2 = op[op.expirationDate == myexpdate]
# strike selector
strike = op2.strikePrice
mystrike = search_strike(130.28,strike)

op3 = op2[op2.strikePrice ==mystrike]
op3 = op3[["putCall","symbol","strikePrice","expirationDate","daysToExpiration","bid","ask","last","mark","closePrice","volatility",\
         "delta","gamma","theta","vega","theoreticalVolatility"]]

op = op3

######### Got a option ###############

val_num_steps = 5
val_num_paths = 10
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
        for step_num in range(1, val_num_steps):
            spot *= exp(drift + vol * np.random.normal() * sqrt_dt)
            if hasattr(yield_, '__call__'):
                div_t1, div_t2 = dt * step_num, dt * (step_num + 1)
                div = yield_(div_t1, div_t2)
                if is_number(div): spot -= div
            result1[step_num] = spot

        result[path_num] = result1
    return result


path = cast_spot_paths(spot)

path[0]

