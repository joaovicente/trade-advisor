from api.models.open_position import OpenPosition
from api.services.backtesting_service import trades_today
from datetime import datetime

def parse_date(date_string):
    return (datetime.strptime(date_string, "%Y-%m-%d")).date()

def test_trade_today_sell_open_position():
    ticker = "SNOW"
    #2024-04-05, SNOW Close: 153.86, RSI: 32.61, RSI-MA: 35.01, Position: 0.00, PNL: 0.00%
    #2024-04-08, SNOW Close: 154.86, RSI: 34.22, RSI-MA: 34.96, Position: 0.00, PNL: 0.00%
    #2024-04-09, SNOW Close: 155.58, RSI: 35.42, RSI-MA: 34.99, Position: 0.00, PNL: 0.00%
    #2024-04-09, SNOW BUY CREATE, 155.58
    open_positions = [
        OpenPosition(date=parse_date("2024-04-09"), ticker=ticker, size=32.1377968, price=155.58)
    ]   
    # Find the date when it would be sold (at loss) and then test SELL action is returned
    # TODO: Adjust test when strategy improves to sell when position peak profit halves
    #2024-05-29, SNOW Close: 148.19, RSI: 36.72, RSI-MA: 47.28, Position: 151.60, PNL: -2.30%
    #2024-05-30, SNOW Close: 140.95, RSI: 30.74, RSI-MA: 46.10, Position: 151.60, PNL: -7.56%
    #2024-05-31, SNOW Close: 136.18, RSI: 27.56, RSI-MA: 44.78, Position: 151.60, PNL: -11.32%
    #2024-05-31, SNOW Maximum tolerated loss reached (9.00%) Selling with 11.32% loss.
    #2024-05-31, SNOW SELL CREATE, 136.18
    expected_sell_date = "2024-05-31"
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