from ib_api import IBApi
import threading
import time
import yfinance as yf
import math
from backtest import backtest_portfolio
from trade_logger import plot_portfolio_history, print_trade_log, export_to_csv
from get_data import get_data

def main():
    app = IBApi()
    app.connect("127.0.0.1", 7497, 0)

    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()

    while app.nextOrderId is None or app.buying_power is None:
        print("Waiting for connection and account summary...")
        time.sleep(1)

    # Ensure positions are sold before proceeding
    time.sleep(5)

    good_stocks = []
    # only variables that change is the following 7 lines
    trade = 1 # 0 to trade, 1 to backtest, else just predictions
    ticker_list = ["GOOG", "AMZN", "AAPL", "META", "MSFT", "NVDA", "TSLA", "INTC", "WMT", "COST", "JPM", "BAC", "CB","GE"] # any stocks you want to predict 
    shift = 5 # shift = 5 would be predicting the open in 5 days time, 1 would be predicting tmr's open
    hurdle = 0.02 # requirement to buy 
    fast_sma = 5 # of periods
    med_sma = 15
    slow_sma = 50

    

    if trade == 0:
        # Sell all open positions
        app.sell_all_positions()

        for ticker in ticker_list:
            get_data(good_stocks, ticker, shift, hurdle, fast_sma, med_sma, slow_sma)

        buying_power_per_security = min(app.buying_power / (len(good_stocks) + 1), app.buying_power/4) # position shouldn't ever be more than 25% of portfolio

        for ticker in good_stocks:
            if app.nextOrderId:
                current_price = yf.Ticker(ticker).history(period=(str(shift)+'d'))['Close'].iloc[-1*shift]
                app.trade_security(ticker, math.floor(buying_power_per_security/current_price), "BUY")

        print("number of stocks still in list: ",len(good_stocks))

    elif trade == 1:
        start_date = "2023-01-01"
        end_date = "2023-12-31"
        portfolio_history, trade_log = backtest_portfolio(
        start_date, end_date, ticker_list, 100000, shift, hurdle, fast_sma, med_sma, slow_sma, shift
    )
        plot_portfolio_history(portfolio_history)
        print_trade_log(trade_log)
        export_to_csv(portfolio_history, "portfolio_history.csv")
        export_to_csv(trade_log, "trade_log.csv")

    else:
         for ticker in ticker_list:
            get_data(good_stocks, ticker, shift, hurdle, fast_sma, med_sma, slow_sma)

    # Give some time for all operations to complete
    time.sleep(5)

    # Disconnect from TWS
    app.disconnect()

if __name__ == "__main__":
    main()