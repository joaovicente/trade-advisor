from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import backtrader as bt
from schemas.stock_daily_stats import StockDailyStats
from schemas.trade_action import TradeAction
import matplotlib.pyplot as plt

from strategies.base_strategy import BaseStrategy

class RsiStrategy(BaseStrategy):
    params = (
        ('start_date', None),
        ('printlog', False),
        ('upper_rsi', 60),
        ('lower_rsi', 50),
        ('loss_pct_threshold', 5),
        ('profit_protection_pct_threshold', 0), # 0 = allow profit to come down to 0%
        ('fixed_investment_amount', 3000),
        ('single_date_to_trade', None), # date string expected (e.g. 2023-12-31)
        ('custom_callback', None),
        ('open_positions', None)
    )

    def __init__(self):
        super().__init__() 

    def buy_action(self, name):
        buy_action = None
        # Buy when RSI goes over RSI-MA while under lower_rsi
        rsi_below_lower_threshold = self.rsi[name][0] < self.params.lower_rsi
        rsi_crossed_above_rsi_ma = self.rsi[name][-1] < self.rsi_ma[name][-1] and self.rsi[name][0] > self.rsi_ma[name][0]
        is_todays_date = self.single_date_to_trade == self.datas[0].datetime.date(0)
        if not self.trade_today_mode():
            buy = rsi_below_lower_threshold and rsi_crossed_above_rsi_ma
        else:
            buy = rsi_below_lower_threshold and rsi_crossed_above_rsi_ma and is_todays_date
        if buy:
            buy_action = TradeAction(date=self.datas[0].datetime.date(0), action="BUY", ticker=name)
            buy_action.reason = f"{name} RSI: {self.rsi[name][0]:.2f} (yesterday={self.rsi[name][-1]:.2f}) above RSI-MA {self.rsi_ma[name][0]:.2f} under RSI < {self.params.lower_rsi:.2f} threshold"
        return buy_action
       
    def sell_action(self, name):
        sell_action = TradeAction(date=self.datas[0].datetime.date(0), action="SELL", ticker=name)
        # Sell when RSI crosses over RSI-based-MA coming down above RSI 60, or when position showing 10% loss
        data = self.getdatabyname(name)
        reached_maximum_tolerated_loss = False
        reached_maximum_profit_loss_tolerance = False
        # Nothing to sell or not current-trade-day
        if not self.getposition(data) or \
            (self.trade_today_mode() and self.single_date_to_trade != self.datas[0].datetime.date(0)):
            return False
        else:
            # Profitable position
            if data.close[0] > self.getposition(data).price:
                # Check if we want to protect profit when price is comming down
                # profit_protection_pct_threshold (0 = all loss of all profit made)
                share_price_peak = self.peak_price_since_bought(data) 
                peak_share_profit = share_price_peak - self.getposition(data).price
                current_per_share_profit = data.close[0] - self.getposition(data).price 
                profit_pct =  current_per_share_profit / peak_share_profit * 100
                if profit_pct < self.params.profit_protection_pct_threshold:
                    reached_maximum_profit_loss_tolerance = True
                    sell_action.reason = f"{name} Maximum profit loss tolerance reached {self.params.profit_protection_pct_threshold}% Selling with {profit_pct:.2f}% profit"
                    self.log(sell_action.reason)
            else:
                # Check if maximum tolerated loss
                percent = self.params.loss_pct_threshold
                pnl_perc = 1 - (self.getposition(data).price / data.close[0])
                if pnl_perc < -1 * (percent/100):
                    sell_action.reason = f"{name} Maximum tolerated loss reached {percent:.2f}% Selling with {pnl_perc*100*-1:.2f}% loss"
                    self.log(sell_action.reason)
                    reached_maximum_tolerated_loss = True
        if reached_maximum_profit_loss_tolerance or reached_maximum_tolerated_loss:
            return sell_action
        else:
            return None

    def stop(self):
        if not self.trade_today_mode():
            #TODO: Make log statment more generic and push to parent class
            self.log(f'RSI: {self.params.upper_rsi}/{self.params.lower_rsi}, ' +
                    f'loss_pct: {self.params.loss_pct_threshold}, '
                    f'investment: {self.params.fixed_investment_amount}, '
                    f'End portfolio value: {round(self.broker.getvalue())}')
        if self.params.custom_callback is not None:
            self.params.custom_callback(self)

            
        
        