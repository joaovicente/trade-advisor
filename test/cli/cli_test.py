
from api.cli import trade_today
from api.services.open_position_service import OpenPositionService
from api.services.backtesting_service import TradesToday

def test_trade_today_with_open_position():
    # TODO: Actually call the CLI method rather than replicating its logic 
    tickers = "SNOW"
    today = "2024-05-31"
    trades = TradesToday(tickers, today, OpenPositionService().get_all()).calculate()
    assert len(trades) == 1
    for trade in trades:
        print(trade)
        
def test_trade_today_without_open_positions():
    # TODO: Actually call the CLI method rather than replicating its logic 
    tickers = "META"
    today = "2024-05-06"
    trades = TradesToday(tickers, today).calculate()
    assert len(trades) == 1
    for trade in trades:
        print(trade)