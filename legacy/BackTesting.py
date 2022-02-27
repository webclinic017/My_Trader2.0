
def moving_cross_backtest(ticker, period):

    #---------------------------------------------------------------
    period = period.lower()
    if period == "day":
        stock =  get_price_data([i], method = "realtimeday",back_day = 10)
        try:

            reversion_test = mean_reversion(ticker,"day")
            short_ma = np.linspace(10,10+5*reversion_test[2],20,dtype=int)
            long_ma = np.linspace(60,60+5*reversion_test[2],20,dtype=int)
            results_cum_ret = np.zeros((len(short_ma),len(long_ma)))
            results_sharpe = np.zeros((len(short_ma),len(long_ma)))
        except:

            short_ma = np.linspace(10,10+5*20,20,dtype=int)
            long_ma = np.linspace(60,60+20,20,dtype=int)
            results_cum_ret = np.zeros((len(short_ma),len(long_ma)))
            results_sharpe = np.zeros((len(short_ma),len(long_ma)))
            raise "except used, probably cannot convert"
            exit()

        for i, shortma in enumerate(short_ma):
            for j, longma in enumerate(long_ma):
                results = moving_cross_backtest_day(stock,shortma,longma)
                results_cum_ret[i,j] = results[0]
                results_sharpe[i,j] = results[1]
        #plt.figure(figsize=(8,8))
        plt.pcolor(short_ma,long_ma,results_cum_ret)
        plt.colorbar()
        plt.show()
