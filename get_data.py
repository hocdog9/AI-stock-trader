import yfinance as yf
import pandas as pd
from linear_regression import linear_regression

# def linear_regression(x, y, )
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

    lin_reg = linear_regression(merged_data, ticker, hurdle, shift)

    if lin_reg == 1:
        stock_list.append(ticker) 