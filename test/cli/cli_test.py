
from models.open_position import OpenPosition
from services.open_position_service import OpenPositionService
from services.stock_compute_service import StockComputeService
from test.utils import *

def test_trade_today_with_open_position():
    # TODO: Actually call the CLI method rather than replicating its logic 
    ticker = "SNOW"
    today = "2024-05-31"
    open_positions = [
        OpenPosition(date=parse_date("2024-04-09"), ticker=ticker, size=32.1377968, price=155.58)
    ]   
    scmp = StockComputeService(ticker, today, open_positions)
    trades = scmp.trades_today()
    print('\n'.join(scmp.get_stock_daily_stats_list_as_text(ticker)))
    assert len(trades) == 1
    for trade in trades:
        print(trade)
        
def test_trade_today_without_open_positions():
    # TODO: Actually call the CLI method rather than replicating its logic 
    tickers = "AMD"
    today = "2023-08-18"
    scmp = StockComputeService(tickers, today, None)
    trades = scmp.trades_today()
    assert len(trades) == 1
    for trade in trades:
        print(trade)
        
def test_portfolio_value():
    today = today_as_str()
    open_positions = OpenPositionService().get_all()
    # add open positions to any supplied tickers
    position_ticker_list = OpenPositionService().get_distinct_tickers_list()
    # add supplied tickers
    tickers = ','.join(position_ticker_list)
    scmp = StockComputeService(tickers, today, open_positions)
    portfolio_stats = scmp.portfolio_stats()
    print("Portfolio stats:")
    print(portfolio_stats.portfolio_as_text())
    