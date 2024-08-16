from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import backtrader as bt
from schemas.stock_daily_stats import StockDailyStats
from schemas.trade_action import TradeAction
import matplotlib.pyplot as plt

from strategies.base_strategy import BaseStrategy

class BbRsiStrategy(BaseStrategy):
    params = (
        ('start_date', None),
        ('printlog', False),
        ('upper_rsi', 60), # Not in use in this strategy
        ('lower_rsi', 40),
        ('bb_low_crossover_loss_tolerance', 5), # allow loss above this pct when bb-low is crossed
        ('loss_pct_threshold', 100), # 100 is full loss tolerance. using values such as 10-11% made little difference. bb-bot cathes loss better
        ('profit_protection_pct_threshold', 0), # Not in use
        ('inflection_profit_percentage_target', 4), # Don't sell on inflection unless profit is above this value
        ('fixed_investment_amount', 3000),
        ('single_date_to_trade', None), # date string expected (e.g. 2023-12-31)
        ('custom_callback', None),
        ('open_positions', None)
    )
    def __init__(self):
        super().__init__() 
        # References:
        # https://blackwellglobal.com/the-bollinger-bands-rsi-trading-strategy/
        # https://github.com/Worlddatascience/DataScienceCohort/blob/refs/heads/master/8_How_to_Backtest_a_Bollinger_Bands_Strategy.ipynb

    def buy_upon_bb_bot_upwards_crossover_with_rsi_reenforcement(self, name, data):
        buy_action = None
        if data.close[-1] < self.b_band[name].lines.bot[-1] \
            and data.close[0] > self.b_band[name].lines.bot[0]\
            and self.rsi[name][0] < self.params.lower_rsi: # rsi below threshold
            buy_action = TradeAction(date=self.datas[0].datetime.date(0), action="BUY", ticker=name)
            buy_action.reason = f"{name} Close ({data.close[-1]:.2f},{data.close[0]:.2f}) crossover Bollinger bottom ({self.b_band[name].lines.bot[0]:.2f}) while RSI ({self.rsi[name][0]:.2f}) below {self.params.lower_rsi:.2f}"
        return buy_action

    def buy_action(self, name):
        ret_buy_action = None
        # TODO: Buy when lower bb is crossed and 
        data = self.getdatabyname(name)
        is_todays_date = self.single_date_to_trade == self.datas[0].datetime.date(0)
        # Bollinger bottom band upwards crossover
        buy_action = self.buy_upon_bb_bot_upwards_crossover_with_rsi_reenforcement(name, data)
        if not self.trade_today_mode():
            buy = buy_action is not None
        else:
            buy = buy_action is not None and is_todays_date
        if buy:
            ret_buy_action = buy_action
        return ret_buy_action
      
    def sell_upon_bb_mid_hat_inflection(self, name, data):
        sell_action = None
        # In bull mode
        condition = data.close[0] > self.getposition(data).price\
            and self.b_band[name].lines.mid[-3] < self.b_band[name].lines.mid[-2]\
            and self.b_band[name].lines.mid[-2] > self.b_band[name].lines.mid[-1]\
            and self.b_band[name].lines.mid[-1] > self.b_band[name].lines.mid[0]\
            and self.pnl_perc(data) > self.params.inflection_profit_percentage_target\
            and data.close[0] < data.close[-2] # close recovery seen in last close compared to hat peak
        if condition:
            sell_action = TradeAction(date=self.datas[0].datetime.date(0), action="SELL", ticker=name)
            sell_action.reason = f"{name} Bollinger mid inflection sustained ({self.b_band[name].lines.mid[-3]:.2f}, {self.b_band[name].lines.mid[-2]:.2f}, {self.b_band[name].lines.mid[-1]:.2f}, {self.b_band[name].lines.mid[0]:.2f}) - pnl-pct: {self.pnl_perc(data)}%"

        return sell_action
       
    def sell_upon_bb_low_crossover(self, name, data):
        sell_action = None
        condition = data.close[0] < self.b_band[name].lines.bot[0] \
            and ((1-(data.close[0] / self.getposition(data).price))*100) > self.params.bb_low_crossover_loss_tolerance
        if condition:
            sell_action  = TradeAction(date=self.datas[0].datetime.date(0), action="SELL", ticker=name)
            sell_action.reason = f"{name} Close ({data.close[-1]:.2f}, {data.close[0]:.2f}) below Bollinger bottom ({self.b_band[name].lines.bot[0]:.2f}) and loss above {self.params.bb_low_crossover_loss_tolerance}% - pnl-pct: {self.pnl_perc(data)}%"
        return sell_action
   
    def sell_if_percent_loss(self, name, data):
        sell_action = None
        condition = data.close[0] < self.getposition(data).price * (1-(self.params.loss_pct_threshold / 100))
        if condition:
            sell_action  = TradeAction(date=self.datas[0].datetime.date(0), action="SELL", ticker=name)
            sell_action.reason = f"{name} Close ({data.close[-1]:.2f}, {data.close[0]:.2f}) loss {self.pnl_perc(data)} above {self.params.loss_pct_threshold}%"
        return sell_action
    
    def sell_action(self, name):
        sell_action = None
        # TODO: Sell when bb-mid falls below its recent peak, at a magnitude of n multiplier of ATR (optimise using different multiplier values on stocks that are not so bullish)
        data = self.getdatabyname(name)
        # Nothing to sell or not current-trade-day
        if not self.getposition(data) or \
            (self.trade_today_mode() and self.single_date_to_trade != self.datas[0].datetime.date(0)):
            return False
        else:
            sell_action = self.sell_upon_bb_mid_hat_inflection(name, data)
            if sell_action is None:
                sell_action = self.sell_upon_bb_low_crossover(name, data)
                if sell_action is None:
                    sell_action = self.sell_if_percent_loss(name, data)
        return sell_action
    
    def stop(self):
        if self.params.custom_callback is not None:
            self.params.custom_callback(self)

        