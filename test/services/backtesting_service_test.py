from api.models.open_position import OpenPosition
from api.services.backtesting_service import trades_today
from datetime import datetime

def parse_date(date_string):
    return (datetime.strptime(date_string, "%Y-%m-%d")).date()

def test_trade_today_sell_open_position():
    ticker = "SNOW"
    open_positions = [
        OpenPosition(date=parse_date("2024-06-18"), ticker=ticker, size=24.304851, price=130.49)
    ]   
    # FIXME: Find the date when it would be sold and then test SELL action is returned
    expected_sell_date = "2024-07-20"
    actions = trades_today(ticker, expected_sell_date, open_positions)
    # Expect sell action is returned
    assert len(actions) == 1
    assert actions[0].date == expected_sell_date
    assert actions[0].action == "SELL"
    assert actions[0].ticker == ticker
    
    
def test_trade_today_without_open_positions():
    date = "2024-05-06"
    ticker = "META"
    actions = trades_today(ticker, date)
    assert len(actions) == 1
    assert actions[0].date == date
    assert actions[0].action == "BUY"
    assert actions[0].ticker == ticker