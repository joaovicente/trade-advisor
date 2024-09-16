import yfinance as yf

class RuntimeStockStatsService():
    # see https://pypi.org/project/yfinance/ 
    def __init__(self, ticker_list: list):
        space_separated_tickers = ' '.join(ticker_list)
        self.tickers = yf.Tickers(space_separated_tickers)
        self.ticker_list = ticker_list
        
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