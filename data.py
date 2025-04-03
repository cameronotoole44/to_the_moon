import pandas as pd
import requests
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import time
from datetime import datetime

# load API key from .env
load_dotenv()
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
if not API_KEY:
    raise ValueError('API key not found')

# stock tickers
tickers = ['NVDA', 'TSLA', 'GOOGL', 'AMD', 'MSFT']

# timestamp for unique file names (no overwrites)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# fetch stock data for a single ticker
def get_stock_data(ticker): 
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={API_KEY}'
    response = requests.get(url)
    data = response.json()

    # error check | rate limits or invalid key
    if 'Time Series (Daily)' not in data:
        print(f'Error fetching {ticker}: {data.get("Note", "Unknown issue")}')
        return None

    # convert to dataframe
    df = pd.DataFrame(data['Time Series (Daily)']).T 
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    df['Ticker'] = ticker
    return df

# fetch all stock data (handles rate limit)
all_data = pd.DataFrame()
for ticker in tickers:
    stock_data = get_stock_data(ticker)
    if stock_data is not None:
        all_data = pd.concat([all_data, stock_data])
    time.sleep(12)  # pause for 12 seconds | 5 calls/minute = 60/5
    # script should take ~1 min total

# 1. broad overview: compare returns
summary = all_data.groupby("Ticker")["Close"].agg(["first", "last"])
summary["Return"] = (summary["last"] - summary["first"]) / summary["first"] * 100
print("Broad Overview - Returns (%):")
print(summary.sort_values("Return", ascending=False))

# plot trends and save
for ticker in tickers:
    stock_data = all_data[all_data["Ticker"] == ticker]
    plt.plot(stock_data.index, stock_data["Close"], label=ticker)
plt.legend()
plt.title("Stock Price Trends")
plt.savefig(f"broad_trends_{timestamp}.png", dpi=300)
plt.show()
plt.close()

# 2. drill-down snapshot for each stock
def drill_down_analysis(df, ticker, timestamp):
    stock_df = df[df["Ticker"] == ticker].copy()
    stock_df["MA20"] = stock_df["Close"].rolling(window=20).mean()
    stock_df["Daily_Change"] = stock_df["Close"].pct_change() * 100

    # snapshot stats
    print(f"\n{ticker} Snapshot:")
    print(f"Latest Price: ${stock_df['Close'].iloc[-1]:.2f}")
    print(f"Biggest Daily Drop: {stock_df['Daily_Change'].min():.2f}%")
    print(f"Average Daily Swing: {stock_df['Daily_Change'].std():.2f}%")
    print(f"Trending Up? {'Yes' if stock_df['Close'].iloc[-1] > stock_df['MA20'].iloc[-1] else 'No'}")

    # plot and save drill-down
    plt.plot(stock_df.index, stock_df["Close"], label="Price")
    plt.plot(stock_df.index, stock_df["MA20"], label="20-Day MA")
    plt.legend()
    plt.title(f"{ticker} Price and Moving Average")
    plt.savefig(f"{ticker.lower()}_drilldown_{timestamp}.png", dpi=300)
    plt.show()
    plt.close()

# call drill-down for each ticker
for ticker in tickers:
    drill_down_analysis(all_data, ticker, timestamp)

# save all data to CSV
all_data.to_csv("stock_data.csv")