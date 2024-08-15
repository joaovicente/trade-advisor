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

basic_materials_stock = ['SNES', 'CRKN', 'AUMN', 'INHD', 'JCTCF', 'LODE', 'PZG', 'WWR', 'GORO', 'EVA']
communication_services_stock = ['GOOG', 'GOOGL', 'META', 'NFLX', 'TMUS', 'VZ', 'DIS', 'CMCSA', 'T', 'DASH']
consumer_cyclical_stock = ['AMZN', 'TSLA', 'HD', 'MCD', 'LOW', 'TJX', 'BKNG', 'NKE', 'SBUX', 'MELI']
consumer_defensive_stock = ['WMT', 'PG', 'COST', 'KO', 'PEP', 'PM', 'MDLZ', 'MO', 'CL', 'TGT']
energy_stock = ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'EPD', 'MPC', 'PSX', 'ET', 'WMB']
financial_stock = ['BRK-A', 'BRK-B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'AXP', 'BX', 'MS']
healthcare_stock = ['LLY', 'UNH', 'JNJ', 'ABBV', 'MRK', 'TMO', 'DHR', 'ABT', 'AMGN', 'ISRG']
industrial_stock = ['GE', 'CAT', 'RTX', 'UNP', 'LMT', 'HON', 'UPS', 'ADP', 'BA', 'DE']
real_estate_stock = ['PLD', 'AMT', 'EQIX', 'WELL', 'PSA', 'O', 'SPG', 'DLR', 'CCI', 'EXR']
technology_stock = ['AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'ADBE', 'AMD', 'QCOM', 'CSCO']
utilities_stock = ['NEE', 'SO', 'DUK', 'CEG', 'AEP', 'GEV', 'SRE', 'D', 'PEG', 'PCG']
diversified_stock = basic_materials_stock \
    + communication_services_stock \
    + consumer_cyclical_stock \
    + consumer_defensive_stock \
    + energy_stock \
    + financial_stock \
    + healthcare_stock \
    + industrial_stock \
    + real_estate_stock \
    + utilities_stock \
    + technology_stock 


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
    
    
