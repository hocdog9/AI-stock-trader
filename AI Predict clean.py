import pandas as pd
import yfinance as yf
import threading
import time
import math
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import numpy as np
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.utils import iswrapper

class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.nextOrderId = None
        self.buying_power = None
        self.positions = []

    @iswrapper
    def nextValidId(self, orderId):
        self.nextOrderId = orderId
        print(f"Next Valid Order ID: {self.nextOrderId}")
        self.reqAccountSummary(9001, "All", "BuyingPower")  # Request the buying power
        self.reqPositions()  # Request all open positions

    @iswrapper
    def accountSummary(self, reqId, account, tag, value, currency):
        if tag == "BuyingPower":
            self.buying_power = float(value)
            # print(f"Buying Power for account {account} in {currency}: {value}")

    # @iswrapper
    # def accountSummaryEnd(self, reqId):
    #     # print(f"AccountSummaryEnd. ReqId: {reqId}")

    @iswrapper
    def position(self, account, contract, position, avgCost):
        if position > 0:  # Only add positions that have positive quantity
            self.positions.append((contract, position))
            # print(f"Position: {contract.symbol}, Quantity: {position}, Avg Cost: {avgCost}")

    @iswrapper
    def positionEnd(self):
        print("All positions retrieved")

    def sell_all_positions(self):
        for contract, position in self.positions:
            sell_order = Order()
            sell_order.action = "SELL"
            sell_order.orderType = "MKT"  # Market order
            sell_order.totalQuantity = position
            sell_order.eTradeOnly = ''
            sell_order.firmQuoteOnly =''

            self.placeOrder(self.nextOrderId, contract, sell_order)
            print(f"Placed SELL order for {contract.symbol}: {position} shares")
            self.nextOrderId += 1

    def trade_security(self, ticker, order_size, action):
        # Create the contract for the security
        contract = Contract()
        contract.symbol = ticker
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        # Create the order
        order = Order()
        order.action = action
        order.orderType = "MKT"  # Market Order
        order.totalQuantity = order_size
        order.eTradeOnly = ''
        order.firmQuoteOnly =''

        # Place the order
        self.placeOrder(self.nextOrderId, contract, order)
        print(f"Placed {action} order for {ticker}: {order_size} shares")
        self.nextOrderId += 1  # Increment the order ID for the next order

# def get_data(list, ticker, shift)) first consolidates the data from yfinance for the ticker, vix and tnx
# and makes a new column for the expected value by setting the next "shift" days close/open as the expected
# value for the test case and trains the model on this dataset. If predicted price is above a certain hurdle
# rate, then it appends it to a list. The function returns null. 
def get_data(stock_list, ticker, shift, hurdle, fast, med, slow):
    stock_data = yf.download(ticker)
    stock_data.reset_index(inplace=True)
    stock_data['fast_sma'] = stock_data['Close'].rolling(window=fast).mean()
    stock_data['med_sma'] = stock_data['Close'].rolling(window=med).mean()
    stock_data['slow_sma'] = stock_data['Close'].rolling(window=slow).mean()

    vix_data = yf.download("^VIX")
    vix_data.reset_index(inplace=True)

    tnx_data = yf.download("^TNX")
    tnx_data.reset_index(inplace=True)

    stock_data['Date'] = pd.to_datetime(stock_data['Date'])
    vix_data['Date'] = pd.to_datetime(vix_data['Date'])
    tnx_data['Date'] = pd.to_datetime(tnx_data['Date'])

    # Merge stock data with VIX and TNX data
    merged_data = pd.merge(stock_data, vix_data[['Date', 'Close']], on='Date', how='left', suffixes=('', '_VIX'))
    merged_data = pd.merge(merged_data, tnx_data[['Date', 'Close']], on='Date', how='left', suffixes=('', '_TNX'))

    # Calculate the Decimal_Date
    reference_date = pd.to_datetime('1900-01-01')
    merged_data['Decimal_Date'] = (merged_data['Date'] - reference_date).dt.days
    merged_data.dropna(inplace=True)

    # Create the target variable y, which is the Open price shifted by -shift days
    merged_data['Expected_Open'] = merged_data['Open'].shift(-shift)

    # Drop the last 'shift' rows as they won't have valid expected values
    merged_data = merged_data.iloc[:-shift]

    # print(merged_data.head())

    # Prepare the feature matrix X and target vector y
    X = merged_data[['Decimal_Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'Close_VIX', 'Close_TNX', 'fast_sma', 'med_sma', 'slow_sma']]
    y = merged_data['Expected_Open']

    # Split the dataset into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=100)

    # Initialize and train the model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Predict the open price for the next 'shift' days using the last row of data
    last_row = merged_data.iloc[-1]
    new_data = pd.DataFrame([[
        last_row['Decimal_Date'],
        last_row['Open'],
        last_row['High'],
        last_row['Low'],
        last_row['Close'],
        last_row['Adj Close'],
        last_row['Volume'],
        last_row['Close_VIX'],
        last_row['Close_TNX'],
        last_row['fast_sma'],
        last_row['med_sma'],
        last_row['slow_sma']
    ]], columns=['Decimal_Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'Close_VIX', 'Close_TNX', 'fast_sma', 'med_sma', 'slow_sma'])

    predicted_price = model.predict(new_data)
    current_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
    print(f'Predicted {ticker} Open in ', shift, f'days: {predicted_price[0]} ~', np.round(predicted_price, 2))
    print(f"The current price of {ticker} is: {current_price} ~", np.round(current_price, 2))
    if predicted_price > ((1 + hurdle) * current_price):
        stock_list.append(ticker)
        print("Buying ", ticker)

def main():
    app = IBApi()
    app.connect("127.0.0.1", 7497, 0)

    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()

    while app.nextOrderId is None or app.buying_power is None:
        print("Waiting for connection and account summary...")
        time.sleep(1)

    # Sell all open positions
    app.sell_all_positions()

    # Ensure positions are sold before proceeding
    time.sleep(5)

    good_stocks = []
    # only variables that change is the following 6 lines
    ticker_list = ["GOOG", "AMZN", "AAPL", "META", "MSFT", "NVDA", "TSLA", "INTC", "WMT", "COST"] # any stocks you want to track 
    shift = 1 # shift = 5 would be predicting the open in 5 days time, 1 would be predicting tmr's open
    hurdle = 0.02 # requirement to buy 
    fast_sma = 5 # of periods
    med_sma = 15
    slow_sma = 50

    for ticker in ticker_list:
        get_data(good_stocks, ticker, shift, hurdle, fast_sma, med_sma, slow_sma)

    buying_power_per_security = app.buying_power / (len(good_stocks) + 1)


    for ticker in good_stocks:
        if app.nextOrderId:
            current_price = yf.Ticker(ticker).history(period=(str(shift)+'d'))['Close'].iloc[-1*shift]
            app.trade_security(ticker, math.floor(buying_power_per_security/current_price), "BUY")

    # Give some time for all operations to complete
    time.sleep(5)

    # Disconnect from TWS
    app.disconnect()

if __name__ == "__main__":
    main()
