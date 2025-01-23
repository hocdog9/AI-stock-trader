import pandas as pd
import matplotlib.pyplot as plt


def plot_portfolio_history(portfolio_history):
    """
    Plots the portfolio value over time.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(portfolio_history['Date'], portfolio_history['Portfolio Value'], label="Portfolio Value", color="blue")
    plt.title("Portfolio Value Over Time")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.legend(loc="upper left")
    plt.grid(True)
    plt.show()


def print_trade_log(trade_log):
    """
    Prints the trade log to the console.
    """
    print("\nTrade Log:")
    print(trade_log.to_string(index=False))


def export_to_csv(dataframe, filename):
    """
    Exports a DataFrame to a CSV file.
    """
    dataframe.to_csv(filename, index=False)
    print(f"Data successfully exported to {filename}")


def calculate_metrics(trade_df):
    """
    Calculates and plots portfolio performance metrics.
    """
    trade_df['PnL'] = trade_df.apply(lambda row: row['Quantity'] * row['Price'] if row['Action'] == 'SELL' else -row['Quantity'] * row['Price'], axis=1)
    trade_df['Cumulative_PnL'] = trade_df['PnL'].cumsum()

    total_return = trade_df['Cumulative_PnL'].iloc[-1]
    daily_returns = trade_df['PnL'].diff().fillna(0)
    sharpe_ratio = daily_returns.mean() / daily_returns.std() * (252 ** 0.5)
    max_drawdown = (trade_df['Cumulative_PnL'] / trade_df['Cumulative_PnL'].cummax() - 1).min()

    print(f"Total Return: ${total_return:.2f}")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"Max Drawdown: {max_drawdown:.2%}")

    # Plot cumulative PnL
    plt.figure(figsize=(10, 6))
    plt.plot(trade_df['Cumulative_PnL'], label="Cumulative PnL")
    plt.title("Backtest Performance")
    plt.xlabel("Trades")
    plt.ylabel("PnL")
    plt.legend()
    plt.grid(True)
    plt.show()
