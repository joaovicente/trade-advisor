import pytest
from test.utils import *                
import yfinance as yf
import backtrader as bt
from services.stock_compute_service import StockComputeService
import datetime

# Using GenericCSVData instead of YahooFinanceCSVData as a workaround to YahooFinanceCSVData 
# see https://www.backtrader.com/docu/datafeed/#genericcsvdata and https://www.backtrader.com/docu/datayahoo/

def test_genericcsv_bug():
    from collections import namedtuple
    Svc = namedtuple("Svc", ['tickers_list', 'warmup_date', 'end_date', 'cerebro'])
    self = Svc(
        tickers_list=["AAPL"], 
        warmup_date=datetime.datetime.strptime("2024-05-31", "%Y-%m-%d").date(), 
        end_date= datetime.datetime.strptime("2025-03-09", "%Y-%m-%d").date(),
        cerebro=bt.Cerebro()
        )
    strategy = bt.Strategy
    self.cerebro.addstrategy(strategy)
    multi_ticker_data = yf.download(self.tickers_list, start=self.warmup_date, end=self.end_date)  # Custom date range
    for ticker in self.tickers_list:
        # Extract data for a single ticker (like yf.Ticker().history() format)
        single_ticker_data = multi_ticker_data.xs(ticker, level=1, axis=1)
        # Save as CSV
        filename = f"yfinance_data_{ticker}.csv"
        single_ticker_data.to_csv(filename)
        print(f"Saved {filename}")
        # Load data from CSV
        data = bt.feeds.GenericCSVData(
            dataname=filename,
            fromdate=datetime.datetime.combine(self.warmup_date, datetime.datetime.min.time()),
            todate=datetime.datetime.combine(self.end_date, datetime.datetime.min.time()),
            nullvalue=0.0,
            dtformat=('%Y-%m-%d'),
            datetime=0,
            close=1,
            high=2,
            low=3,
            open=4,
            volume=5,
            openinterest=None
        )
        self.cerebro.adddata(data=data, name=ticker)
    self.cerebro.run()
   
 
@pytest.mark.skip(reason="yfinance rate limiting issues https://github.com/ranaroussi/yfinance/issues/2422")
def test_download_single_ticker_yahoo_finance_csv_data():
    # Define the stock ticker symbol (e.g., Apple)
    ticker_symbol = "AAPL"

    # Fetch historical data
    ticker = yf.Ticker(ticker_symbol)
    data = ticker.history(period="1y")  # Get 1 year of data

    # Save to CSV
    csv_filename = f"yfinance_data_{ticker_symbol}.csv"
    data.to_csv(csv_filename)

    print(f"Data saved as {csv_filename}")
    
@pytest.mark.skip(reason="yfinance rate limiting issues https://github.com/ranaroussi/yfinance/issues/2422")
def test_download_multi_ticker_yahoo_finance_csv_data():
    # Define the stock ticker symbol (e.g., Apple)
    tickers = ["AAPL", "META"]

    # Fetch historical data
    data = yf.download(tickers, start='2024-07-02', end='2024-12-31')  # Custom date range
    
    assert data.empty == False
    # Loop through each ticker and save separately
    for ticker in tickers:
        # Extract data for a single ticker (like yf.Ticker().history() format)
        single_ticker_data = data.xs(ticker, level=1, axis=1)
        
        # Save as CSV
        filename = f"yfinance_data_{ticker}.csv"
        single_ticker_data.to_csv(filename, header=False)
        print(f"Saved {filename}")
    
    
    