import pandas as pd
import yfinance as yf


def fetch_data(ticker_list, start_date, end_date, fast, med, slow):
    """
    Fetches historical data for the given tickers and calculates moving averages.
    """
    data = {}
    for ticker in ticker_list:
        df = yf.download(ticker, start=start_date, end=end_date).fillna(method='ffill')
        df['fast_sma'] = df['Close'].rolling(window=fast).mean()
        df['med_sma'] = df['Close'].rolling(window=med).mean()
        df['slow_sma'] = df['Close'].rolling(window=slow).mean()
        data[ticker] = df
    return data


def backtest_portfolio(start_date, end_date, ticker_list, initial_value, shift, hurdle, fast, med, slow, trade_frequency):
    """
    Simulates a trading strategy, running the logic every X days.
    """
    portfolio_value = initial_value
    cash_balance = initial_value
    positions = {}  # Tracks positions {ticker: quantity}
    portfolio_history = []
    trade_log = []

    # Fetch data
    data = fetch_data(ticker_list, start_date, end_date, fast, med, slow)

    # Align all dates across tickers
    dates = data[ticker_list[0]].index
    for ticker in ticker_list[1:]:
        dates = dates.intersection(data[ticker].index)

    # Simulate trading logic every X days
    for current_date in dates[::trade_frequency]:
        # Sell all current positions
        for ticker, quantity in positions.items():
            if ticker in data and current_date in data[ticker].index:
                current_price = data[ticker].loc[current_date, 'Close']
                cash_balance += quantity * current_price
                trade_log.append({
                    "Date": current_date,
                    "Ticker": ticker,
                    "Action": "SELL",
                    "Quantity": quantity,
                    "Price": current_price
                })
        positions.clear()

        # Execute new trades
        for ticker in ticker_list:
            if ticker in data and current_date in data[ticker].index:
                current_price = data[ticker].loc[current_date, 'Close']
                predicted_date = current_date - pd.Timedelta(days=shift)

                # Ensure the predicted date exists
                if predicted_date in data[ticker].index:
                    predicted_price = data[ticker].loc[predicted_date, 'fast_sma']
                else:
                    continue  # Skip if no data for the predicted date

                # Buy condition
                if predicted_price > current_price * (1 + hurdle):
                    shares_to_buy = int(cash_balance // current_price)
                    if shares_to_buy > 0:
                        positions[ticker] = shares_to_buy
                        cash_balance -= shares_to_buy * current_price
                        trade_log.append({
                            "Date": current_date,
                            "Ticker": ticker,
                            "Action": "BUY",
                            "Quantity": shares_to_buy,
                            "Price": current_price
                        })

        # Calculate portfolio value
        portfolio_value = cash_balance + sum(
            positions[ticker] * data[ticker].loc[current_date, 'Close'] for ticker in positions if current_date in data[ticker].index
        )
        portfolio_history.append({"Date": current_date, "Portfolio Value": portfolio_value})

    # Convert logs to DataFrames
    portfolio_history = pd.DataFrame(portfolio_history)
    trade_log = pd.DataFrame(trade_log)

    return portfolio_history, trade_log
