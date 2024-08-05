import datetime 
import backtrader as bt
from services.backtesting_service import BaseBacktraderStrategy
import yfinance as yf

tech_stock = [ 'AMZN', 'SNOW', 'MSFT', 'AAPL', 'GOOG', 'NVDA', 'META', 'ORCL', 'NFLX', 'ADBE', 'TWLO', 'AVGO', 'CRM', ]
tech_stock_without_snow = [s for s in tech_stock if s != 'SNOW']
tech_stock_without_nvidia = [s for s in tech_stock if s != 'NVDA']
non_tech_stock = [ 'JNJ', 'LLY', 'PFE', 'UNH', 'V', 'MA', 'BRK-B', 'JPM', 'COST', 'PG'] # FIXME: default strategy causes losses in non-tech stock
interesting_stock = tech_stock_without_snow + non_tech_stock
interesting_stock_without_nvda = interesting_stock.remove('NVDA')

def optimisation_dates(num_years, year_offset):
    number_of_days_to_simulate = 365 * num_years
    time_travel_days = 365 * year_offset
    end_date=datetime.datetime.today().date() - datetime.timedelta(time_travel_days)
    warmup_date = end_date - datetime.timedelta(number_of_days_to_simulate + BaseBacktraderStrategy.INDICATOR_WARMUP_IN_DAYS)
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
        sorted_results = sorted(stats, key=lambda x: x['final_value'], reverse=True)
        for result in sorted_results[:5]:
            print(result)
    else:
        # Print out the final result
        print(f'Portfolio Value Starting: {start_portfolio_value:.0f}, End: {cerebro.broker.getvalue():.0f}')
    
    
