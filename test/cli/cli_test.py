
from models.open_position import OpenPosition
from services.open_position_service import OpenPositionService
from services.stock_compute_service import StockComputeService
from test.utils import *
from click.testing import CliRunner
from cli.cli import trade_today
import pytest
import pytest
import pytest

def test_trade_today_with_open_position():
    # TODO: Actually call the CLI method rather than replicating its logic 
    ticker = "SNOW"
    today = "2024-05-31"
    open_positions = [
        OpenPosition(date=parse_date("2024-04-09"), ticker=ticker, size=32.1377968, price=155.58, currency='USD'),
    ]   
    scmp = StockComputeService(ticker, today, open_positions)
    trades = scmp.trades_today()
    print('\n'.join(scmp.get_stock_daily_stats_list_as_text(ticker)))
    assert len(trades) == 1
    for trade in trades:
        print(trade)
        
def test_trade_today_without_open_positions():
    # TODO: Actually call the CLI method rather than replicating its logic 
    tickers = "JNJ"
    today = "2024-09-27"
    scmp = StockComputeService(tickers, today, None)
    trades = scmp.trades_today()
    assert len(trades) == 1
    assert trades[0].action == "BUY"
    assert trades[0].ticker == tickers
    for trade in trades:
        print(trade)
        
@pytest.mark.skip(reason="Requires environment variables - use settings_test.json")
def test_my_command():
    runner = CliRunner()
    result = runner.invoke(trade_today, ['-u', 'bugfix', '-o', 'file', '-r', '--skip-currency-conversion'])
    assert result.exit_code == 0