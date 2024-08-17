from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import backtrader as bt
from schemas.stock_daily_stats import StockDailyStats
from schemas.trade_action import TradeAction
import matplotlib.pyplot as plt

class BaseStrategy(bt.Strategy):
    INDICATOR_WARMUP_IN_WEEKS = 24
    INDICATOR_WARMUP_IN_DAYS = INDICATOR_WARMUP_IN_WEEKS * 5 # 5 market-active days per week
    TRADE_ACTION_CONTEXT_SIZE = 5
    def __init__(self):
        super().__init__() 
        if self.params.single_date_to_trade is not None:
            self.single_date_to_trade = datetime.datetime.strptime(self.params.single_date_to_trade, "%Y-%m-%d").date()
        else:
            self.single_date_to_trade = None    
        # The attributes below are stored as dictionaries keyed by ticker name (e.g. AMZN)
        self.order = {data._name: None for data in self.datas}
        self.buyprice = {data._name: None for data in self.datas}
        self.buycomm = {data._name: None for data in self.datas}
        self.last_bought_order_date = {data._name: None for data in self.datas}
        self.stock_daily_stats_list = {data._name: [] for data in self.datas}
        self.stock_pnl = {data._name: 0 for data in self.datas}
        # Add the RSI indicator
        self.rsi = {
            data._name: bt.indicators.RSI(data, 
                                          plot=True, 
                                          plothlines=[self.params.lower_rsi,self.params.upper_rsi]) 
            for data in self.datas}
        self.rsi_ma = {
            data._name: bt.indicators.SmoothedMovingAverage(self.rsi[data._name], 
                                                            period=14,plot=True) 
            for data in self.datas}
        self.b_band = {
            data._name: bt.indicators.BollingerBands(data, 
                                                     period=20, 
                                                     devfactor=2,
                                                     plot=True) 
            for data in self.datas }
        for data in self.datas:
            self.stock_daily_stats_list[data._name] = []
        # Trade action list
        self.trade_actions = []
        
    def log(self, txt, dt=None, do_print=False):
        ''' Logging function for strategy'''
        if self.params.printlog or do_print:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def trade_today_mode(self):
        return self.single_date_to_trade is not None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                if not self.trade_today_mode():
                    self.log(
                        '%s BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.data._name,
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm))

                self.buyprice[order.data._name] = order.executed.price
                self.buycomm[order.data._name] = order.executed.comm
                self.last_bought_order_date[order.data._name] = self.datas[0].datetime.date(0)
            else:  # Sell
                if not self.trade_today_mode():                
                    self.log('%s SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                            (order.data._name,
                            order.executed.price,
                            order.executed.value,
                            order.executed.comm))

        elif order.status in [order.Canceled]:
            self.log('%s Order Canceled' % order.data._name)
        elif order.status in [order.Margin]:
            self.log('%s Order Margin' % order.data._name)
        elif order.status in [order.Rejected]:
            self.log('%s Order Rejected' % order.data._name)
        # Write down: no pending order
        self.order[order.data._name] = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.stock_pnl[trade.data._name] += trade.pnl
        self.log('%s OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.data._name, trade.pnl, trade.pnlcomm))

    def warmup_buffer(self):
        # processing date within warmup buffer
        return self.datas[0].datetime.date(0) < self.params.start_date
   
    def days_in_buffer(self):
        return len(self)
    
    def buy_position_recorded(self, name):
        open_position_recorded = None
        if self.params.open_positions is not None:
            for position in self.params.open_positions:
                if position.ticker == name and position.date == self.datas[0].datetime.date(0):
                    open_position_recorded = position
        return open_position_recorded
    
    def peak_price_since_bought(self, data):
        # Walk back until position date (negative) index is found
        index = 0
        j = 0
        peak_price = self.getposition(data).price
        
        order_date = self.last_bought_order_date[data._name]
        while order_date != data.datetime.date(index) and j < self.days_in_buffer():
            index -= 1
            j += 1
        # Now calculate max from than index forward
        for k in range(index, 1):
            peak_price = max(peak_price, data.close[k])
        return peak_price
   
    def pnl_perc(self, data):
        return round((1 - (self.getposition(data).price / data.close[0])) * 100, 2)
    
    def next(self):
        for data in self.datas:
            # Warm-up RSI for rsi_warmup_in_days
            if self.warmup_buffer():
                return
            # Simply log the closing price of the series from the reference
            pnl_perc = 0
            if self.getposition(data):
                pnl_perc = self.pnl_perc(data)
            rsi_crossover_signal = self.rsi[data._name][0] > self.rsi_ma[data._name][0] and self.rsi[data._name][-1] < self.rsi_ma[data._name][-1]
            stock_stats = StockDailyStats(date=str(self.datas[0].datetime.date(0)), 
                                          ticker = data._name, 
                                          close = round(data.close[0], 2), 
                                          rsi = round(self.rsi[data._name][0], 2), 
                                          rsi_ma = round(self.rsi_ma[data._name][0], 2),
                                          rsi_crossover_signal = rsi_crossover_signal,
                                          bb_top = self.b_band[data._name].lines.top[0],
                                          bb_mid = self.b_band[data._name].lines.mid[0],
                                          bb_bot = self.b_band[data._name].lines.bot[0],
                                          position = round(self.getposition(data).price, 2), 
                                          pnl_pct = pnl_perc)
            self.stock_daily_stats_list[data._name].append(stock_stats)
            self.log(stock_stats.as_text(include_date=False))

            # Check if an order is pending ... if yes, we cannot send a 2nd one
            if self.order[data._name]:
                return

            # Check if we are in the market
            if not self.getposition(data):
                # Recorded position from repository
                position_recorded = self.buy_position_recorded(data._name)
                buy_action = self.buy_action(data._name)
                if position_recorded:
                    self.log(f'{data._name} BUY RECORDED, {position_recorded.price:.2f}')
                    self.order[data._name] = self.buy(data=data, size=position_recorded.size, price=position_recorded.price)
                elif buy_action is not None:
                    # BUY, BUY, BUY!!! (with all possible default parameters)
                    self.log(f'{data._name} BUY CREATE, {data.close[0]:.2f}')
                    # Buy dollar ammount
                    self.order[data._name] = self.buy(data=data, size=float(self.params.fixed_investment_amount / data.close[0]))
                    buy_action.context = [s.as_text() for s in self.stock_daily_stats_list[data._name][-BaseStrategy.TRADE_ACTION_CONTEXT_SIZE:]]
                    self.trade_actions.append(buy_action)
                    if self.params.print_trade_actions:
                        print(buy_action.as_text(context=False)) 
            else:
                # TODO: Sell when RSI crosses over RSI-based-MA comming down above RSI 60, or when position showing 10% loss
                sell_action = self.sell_action(data._name)
                if sell_action:
                    # SELL, SELL, SELL!!! (with all possible default parameters)
                    self.log('%s SELL CREATE, %.2f' % (data._name, data.close[0]))
                    # Sell position
                    self.order[data._name] = self.sell(data = data, size = self.getposition(data).size)
                    sell_action.context = [s.as_text() for s in self.stock_daily_stats_list[data._name][-BaseStrategy.TRADE_ACTION_CONTEXT_SIZE:]]
                    self.trade_actions.append(sell_action)
                    if self.params.print_trade_actions:
                        print(sell_action.as_text(context=False))
                    
