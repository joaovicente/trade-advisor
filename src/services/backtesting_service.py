from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import backtrader as bt
from schemas.stock_daily_stats import StockDailyStats
from schemas.trade_action import TradeAction


# Create a Strategy
class BacktraderStrategy(bt.Strategy):
    TRADE_ACTION_CONTEXT_SIZE = 5
    RSI_WARMUP_IN_WEEKS = 24
    RSI_WARMUP_IN_DAYS = RSI_WARMUP_IN_WEEKS * 5 # 5 market-active days per week
    params = (
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

    def log(self, txt, dt=None, do_print=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or do_print:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def trade_today_mode(self):
        return self.single_date_to_trade is not None

    def __init__(self):
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
            
        # Add the RSI indicator
        self.rsi = {data._name: bt.indicators.RSI(data,plot=True) for data in self.datas}
        self.rsi_ma = {data._name: bt.indicators.SmoothedMovingAverage(self.rsi[data._name], period=14,plot=True) for data in self.datas}
        
        # Trade action list
        self.trade_actions = []
        
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
        self.log('%s OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.data._name, trade.pnl, trade.pnlcomm))

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
   
    def days_in_buffer(self):
        # FIXME: This function does not work consistently for single and multiple tickers - see optimise.ipynb
        return len(self)
    
    def next(self):
        for data in self.datas:
            # Warm-up RSI for rsi_warmup_in_days
            if self.days_in_buffer() < BacktraderStrategy.RSI_WARMUP_IN_DAYS:
                return
            # Simply log the closing price of the series from the reference
            pnl_perc = 0
            if self.getposition(data):
                pnl_perc = 1 - (self.getposition(data).price / data.close[0]) 
            rsi_crossover_signal = self.rsi[data._name][0] > self.rsi_ma[data._name][0] and self.rsi[data._name][-1] < self.rsi_ma[data._name][-1]
            stock_stats = StockDailyStats(date=str(self.datas[0].datetime.date(0)), 
                                          ticker = data._name, 
                                          close = round(data.close[0], 2), 
                                          rsi = round(self.rsi[data._name][0], 2), 
                                          rsi_ma = round(self.rsi_ma[data._name][0], 2),
                                          rsi_crossover_signal = rsi_crossover_signal,
                                          position = round(self.getposition(data).price, 2), 
                                          pnl_pct = round(pnl_perc * 100,2))
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
                    buy_action.context = [s.as_text() for s in self.stock_daily_stats_list[data._name][-BacktraderStrategy.TRADE_ACTION_CONTEXT_SIZE:]]
                    self.trade_actions.append(buy_action)
            else:
                # TODO: Sell when RSI crosses over RSI-based-MA comming down above RSI 60, or when position showing 10% loss
                sell_action = self.sell_action(data._name)
                if sell_action:
                    # SELL, SELL, SELL!!! (with all possible default parameters)
                    self.log('%s SELL CREATE, %.2f' % (data._name, data.close[0]))
                    # Sell position
                    self.order[data._name] = self.sell(data = data, size = self.getposition(data).size)
                    sell_action.context = [s.as_text() for s in self.stock_daily_stats_list[data._name][-BacktraderStrategy.TRADE_ACTION_CONTEXT_SIZE:]]
                    self.trade_actions.append(sell_action)

    def stop(self):
        if not self.trade_today_mode():
            self.log(f'RSI: {self.params.upper_rsi}/{self.params.lower_rsi}, ' +
                    f'loss_pct: {self.params.loss_pct_threshold}, '
                    f'investment: {self.params.fixed_investment_amount}, '
                    f'End portfolio value: {round(self.broker.getvalue())}')
        if self.params.custom_callback is not None:
            self.params.custom_callback(self)

            
        
        