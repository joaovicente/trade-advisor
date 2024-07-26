from models.open_position import OpenPosition
from services.stock_compute_service import StockComputeService
from services.backtesting_service import BacktraderStrategy
from datetime import datetime
from test.utils import *

trade_action_context_size = BacktraderStrategy.TRADE_ACTION_CONTEXT_SIZE

def test_trade_today_sell_single_open_position():
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
    actions = StockComputeService(ticker, expected_sell_date, open_positions).trades_today()
    # Expect sell action is returned
    assert len(actions) == 1
    assert actions[0].date == expected_sell_date
    assert actions[0].action == "SELL"
    assert actions[0].ticker == ticker
    assert actions[0].reason == 'SNOW Maximum tolerated loss reached 9.00% Selling with 11.32% loss'
    assert len(actions[0].context) == trade_action_context_size
    
def test_trade_today_sell_multiple_open_positions():
    ticker = "SNOW"
    open_positions = [
        OpenPosition(date=parse_date("2023-10-30"), ticker='AMZN', size=38.5445575, price=129.72),
        OpenPosition(date=parse_date("2024-04-09"), ticker='SNOW', size=32.1377968, price=155.58)
    ]   
    expected_sell_date = "2024-05-31"
    actions = StockComputeService(ticker, expected_sell_date, open_positions).trades_today()
    # Expect sell action is returned
    assert len(actions) == 1
    assert actions[0].date == expected_sell_date
    assert actions[0].action == "SELL"
    assert actions[0].ticker == 'SNOW'
    assert len(actions[0].context) == trade_action_context_size
    
def test_trade_today_buy_without_open_positions():
    date = "2024-05-06"
    ticker = "META"
    actions = StockComputeService(ticker, date).trades_today()
    assert len(actions) == 1
    assert actions[0].date == date
    assert actions[0].action == "BUY"
    assert actions[0].ticker == ticker
    #'META RSI: 46.91 (yesterday=40.79) above RSI-MA 46.69 under RSI < 50.00 threshold'
    assert 'above RSI-MA' in actions[0].reason
    assert len(actions[0].context) == trade_action_context_size
    # '*RSI' is shown when RSI crosses RSI-MA threshold
    assert '*rsi' in actions[0].context[-1]
    
    
def test_trade_today_rsi_calculation_bug():
    ticker = "SNOW"
    open_positions = [
        OpenPosition(date=parse_date("2024-04-09"), ticker='SNOW', size=32.1377968, price=155.58)
    ]   
    date_today = "2024-07-16"
   
    scenarios = {'pos': None, 'no_pos': None}
     
    scenarios['pos'] = StockComputeService(ticker, date_today, open_positions)
    scenarios['no_pos'] = StockComputeService(ticker, date_today)
   
    for scenario in list(scenarios.keys()):
        print(f'{scenario}:')
        print(f"start_date={scenarios[scenario].start_date}, end_date={scenarios[scenario].end_date}")
        print('\n'.join(scenarios[scenario].get_stock_daily_stats_list_as_text(ticker)))
        print('\n')
        last_line = scenarios[scenario].get_stock_daily_stats_list(ticker)[-1]
        assert last_line.rsi_crossover_signal == True, "RSI crossover should be consistent regardless of start and end dates"
        
    pos_rsi_rounded = round(scenarios['pos'].get_stock_daily_stats_list(ticker)[-1].rsi,0)
    pos_rsi_ma_rounded = round(scenarios['pos'].get_stock_daily_stats_list(ticker)[-1].rsi_ma,0)
    no_pos_rsi_rounded = round(scenarios['no_pos'].get_stock_daily_stats_list(ticker)[-1].rsi,0)
    no_pos_rsi_ma_rounded = round(scenarios['no_pos'].get_stock_daily_stats_list(ticker)[-1].rsi_ma,0)
    assert pos_rsi_rounded == no_pos_rsi_rounded, "RSI rounded number should be consistent regardless of start and end dates"
    # FIXME: RSI-MA is not the same as seen in TradingView (while RSI is close enough). Need to investigate further
    assert pos_rsi_ma_rounded == no_pos_rsi_ma_rounded, "RSI-MA rounded number should be consistent regardless of start and end dates"