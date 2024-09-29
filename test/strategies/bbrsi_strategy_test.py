from models.open_position import OpenPosition
from services.stock_compute_service import StockComputeService
from strategies.base_strategy import BaseStrategy
from strategies.bbrsi_strategy import BbRsiStrategy
from test.utils import *

trade_action_context_size = BaseStrategy.TRADE_ACTION_CONTEXT_SIZE

def test_buy_above_bollinger_bottom():
    # 2023-08-18 BUY AMD because AMD Close (104.44,105.45) above Bollinger bottom (104.51) while RSI (40.88) below 44.00
    closing_date = "2023-08-18"
    buy_date = "2023-08-19"
    ticker = "AMD"
    actions = StockComputeService(ticker, buy_date, strategy=BbRsiStrategy).trades_today()
    assert len(actions) == 1
    assert actions[0].date == parse_date(closing_date)
    assert actions[0].action == "BUY"
    assert actions[0].ticker == ticker
    assert 'above Bollinger bottom' in actions[0].reason
    
def test_sell_below_bollinger_bottom():
    # 2023-08-18 BUY AMD because AMD Close (104.44,105.45) above Bollinger bottom (104.51) while RSI (40.88) below 44.00
    ticker = "AMD"
    open_positions = [
        OpenPosition(date=parse_date("2023-08-18"), ticker='AMD', size=38.30, price=104.45),
    ]   
    # 2023-09-21 SELL AMD because AMD Close (100.34, 96.11) below Bollinger bottom (97.73) and loss above 5% - pnl-pct: -10.5%
    closing_date = "2023-09-21"
    buy_date = "2023-09-22"
    actions = StockComputeService(ticker, buy_date, open_positions=open_positions, strategy=BbRsiStrategy).trades_today()
    assert len(actions) == 1
    assert actions[0].date == parse_date(closing_date)
    assert actions[0].action == "SELL"
    assert actions[0].ticker == ticker
    assert 'below Bollinger bottom' in actions[0].reason
    
def test_sell_upon_bb_middle_inflection():
    # 2023-09-25 BUY AMD because AMD Close (96.20,97.38) crossover Bollinger bottom (95.83) while RSI (36.04) below 44.00
    ticker = "AMD"
    open_positions = [
        OpenPosition(date=parse_date("2023-09-25"), ticker='AMD', size=41.08, price=97.38),
    ]   
    # 2024-02-20 SELL AMD because AMD Bollinger mid inflection sustained (172.61, 173.31, 173.29, 173.17) - pnl-pct: 41.76%
    closing_date = "2024-02-20"
    buy_date = "2024-02-21"
    actions = StockComputeService(ticker, buy_date, open_positions=open_positions, strategy=BbRsiStrategy).trades_today()
    assert len(actions) == 1
    assert actions[0].date == parse_date(closing_date)
    assert actions[0].action == "SELL"
    assert actions[0].ticker == ticker
    assert 'Bollinger mid inflection sustained' in actions[0].reason
