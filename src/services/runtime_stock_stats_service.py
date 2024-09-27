import yfinance as yf
from services.utils_service import todays_date
from datetime import datetime

class RuntimeStockStatsService():
    # see https://pypi.org/project/yfinance/ 
    def __init__(self, ticker_list: list, rapid=False):
        space_separated_tickers = ' '.join(ticker_list)
        self.tickers = yf.Tickers(space_separated_tickers)
        self.ticker_list = ticker_list
        self.rapid = rapid
        
    def pe_ratio(self, ticker):
        if ticker not in self.ticker_list:
            raise Exception(f"{ticker} not in ticker list")
        stock = self.tickers.tickers[ticker]
        stock_price = stock.history(period='1d')['Close'].iloc[0]
        eps_ttm = stock.info['trailingEps']
        if eps_ttm:
            pe_ratio = round(stock_price / eps_ttm, 2)
        else:
            raise Exception(f"EPS data not available for {ticker}")
        return(pe_ratio)
    
    def next_earnings_call_in_days(self, ticker):
        if not self.rapid:
            stock = self.tickers.tickers[ticker]
            #print(stock.get_earnings_dates())
            earnings_dates = [d.astype('M8[ms]').astype(datetime).date() for d in list(stock.get_earnings_dates().index.values)]
            future_earnings_dates = [d for d in earnings_dates if d > todays_date()]
            next_earnings_date = min(future_earnings_dates)
            days_to_earning = (next_earnings_date - todays_date()).days
        else:
            days_to_earning = 99
        #print(f"{ticker}: {days_to_earning}d {next_earnings_date}")
        return days_to_earning
        
        