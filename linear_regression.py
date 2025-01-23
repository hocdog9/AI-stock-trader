import yfinance as yf
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd

def linear_regression(dataset, ticker, hurdle, shift):
    count = 0
    # Prepare the feature matrix X and target vector y
    X = dataset[['Decimal_Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'Close_VIX', 'Close_TNX', 'fast_sma', 'med_sma', 'slow_sma']]
    y = dataset['Expected_Open']

    # Split the dataset into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=100)

    # Initialize and train the model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Predict the open price for the next 'shift' days using the last row of data
    last_row = dataset.iloc[-1]
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
        print("Buying ",ticker)
        count += 1
    return count