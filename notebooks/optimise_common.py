import datetime 
import backtrader as bt
from strategies.base_strategy import BaseStrategy
import yfinance as yf

tech_stock = [ 'AMZN', 'MSFT', 'AAPL', 'GOOG', 'NVDA', 'META', 'ORCL', 'NFLX', 'ADBE', 'AVGO', 'CRM']
non_tech_stock = [ 'JNJ', 'LLY', 'PFE', 'UNH', 'V', 'MA', 'BRK-B', 'JPM', 'COST', 'PG']
interesting_stock = tech_stock + non_tech_stock

# Target stock: US Mega (>200B market cap) with positive growth (from finviz screener)
high_performance_stock = ['AAPL', 'ABBV', 'ADBE', 'AMD', 'AMZN', 'AVGO', 'BAC', 'BRK-B', 'COST', 'CRM', 'CVX', 'GOOG', 'HD', 'JNJ', 'JPM', 'KO', 'LLY', 'MA', 'META', 'MRK', 'MSFT', 'NFLX', 'NVDA', 'ORCL', 'PEP', 'PFE', 'PG', 'TMO', 'TSLA', 'UNH', 'V', 'WMT', 'XOM']

def optimisation_dates(start_date, end_date):
    warmup_date = start_date - datetime.timedelta(BaseStrategy.INDICATOR_WARMUP_IN_DAYS)
    return warmup_date, start_date, end_date

def optimisation_date_offsets(num_years, year_offset):
    number_of_days_to_simulate = 365 * num_years
    time_travel_days = 365 * year_offset
    end_date=datetime.datetime.today().date() - datetime.timedelta(time_travel_days)
    warmup_date = end_date - datetime.timedelta(number_of_days_to_simulate + BaseStrategy.INDICATOR_WARMUP_IN_DAYS)
    start_date = end_date - datetime.timedelta(number_of_days_to_simulate)
    return warmup_date, start_date, end_date

def create_cerebro():
    return bt.Cerebro(optreturn=False)

def add_data_feed(cerebro, tickers, warmup_date, start_date, end_date):
    print(f"tickers: {tickers}")
    print(f"time window = warmup-date: {warmup_date}, start-date: {start_date}, end-data: {end_date}")
    for ticker in tickers:
        data = bt.feeds.PandasData(dataname=yf.download(ticker, warmup_date, end_date))
        cerebro.adddata(data=data, name=ticker)
        
def set_cash(cerebro, initial_cash):
    cerebro.broker.setcash(initial_cash)
    
def execute_cerebro(cerebro, optimise, stats):
    # Print out the starting conditions
    start_portfolio_value = cerebro.broker.getvalue()

    # Run over everything
    opt_runs = cerebro.run(maxcpus=1)
   
    if optimise: 
        print('Optimised runs by Final Value:')
        sorted_results = sorted(stats, key=lambda x: x['final_portolio_value'], reverse=True)
        for result in sorted_results[:5]:
            print(result)
    else:
        # Print out the final result
        print(f'Portfolio Value Starting: {start_portfolio_value:.0f}, End: {cerebro.broker.getvalue():.0f}')
    
    
