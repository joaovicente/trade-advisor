from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import backtrader as bt
import yfinance as yf
from api.models.trade_action import TradeAction

rsi_warmup_in_weeks = 6
rsi_warmup_in_days = rsi_warmup_in_weeks * 5 # 5 market-active days per week

# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('printlog', False),
        ('upper_rsi', 60),
        ('lower_rsi', 50),
        ('loss_pct_threshold', 5),
        ('fixed_investment_amount', 3000),
        ('single_date_to_trade', None), # date string expected (e.g. 2023-12-31)
        ('custom_callback', None)
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
        
        # To keep track of pending orders and buy price/commission
        self.order = {data._name: None for data in self.datas}
        self.buyprice = {data._name: None for data in self.datas}
        self.buycomm = {data._name: None for data in self.datas}
            
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
            else:  # Sell
                if not self.trade_today_mode():                
                    self.log('%s SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                            (order.data._name,
                            order.executed.price,
                            order.executed.value,
                            order.executed.comm))

            #self.bar_executed = len(self)
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

    def buy_condition(self, name):
        # Buy when RSI crosses over RSI-based-MA comming up below RSI lower_rsi
        rsi_below_lower_threshold = self.rsi[name][0] < self.params.lower_rsi
        rsi_crossed_above_rsi_ma = self.rsi[name][-1] < self.rsi_ma[name][-1] and self.rsi[name][0] > self.rsi_ma[name][0]
        is_todays_date = self.single_date_to_trade == self.datas[0].datetime.date(0)
        if not self.trade_today_mode():
            buy = rsi_below_lower_threshold and rsi_crossed_above_rsi_ma    
        else:
            buy = rsi_below_lower_threshold and rsi_crossed_above_rsi_ma and is_todays_date
        return buy
        
    def sell_condition(self, name):
        # Sell when RSI crosses over RSI-based-MA coming down above RSI 60, or when position showing 10% loss
        data = self.getdatabyname(name)
        if not self.getposition(data) or \
            (self.trade_today_mode() and self.single_date_to_trade != self.datas[0].datetime.date(0)):
            return False
        else:
            rsi_above_upper_threshold = self.rsi[name][0] > self.params.upper_rsi
            rsi_crossed_below_rsi_ma = self.rsi[name][-1] > self.rsi_ma[name][-1] and self.rsi[name][0] < self.rsi_ma[name][0]
            rsi_stayed_below_rsi_ma = self.rsi[name][0] < self.rsi_ma[name][0] and self.rsi[name][-1] < self.rsi_ma[name][-1] and self.rsi[name][-2] < self.rsi_ma[name][-2]
            percent = self.params.loss_pct_threshold
            pnl_perc = 1 - (self.getposition(data).price / data.close[0])
            reached_maximum_tolerated_loss = pnl_perc < -1 * (percent/100)
            if reached_maximum_tolerated_loss:
                self.log('%s Maximum tolerated loss reached (%.2f%%) Selling with %.2f%% loss.' 
                         % (name, percent, pnl_perc * 100 * -1))
            elif pnl_perc < 0:
                pass
                #self.log('%s Position loss of %.2f%% - above tolerated level %.2f' % (name, pnl_perc * 100, percent))
        return (rsi_above_upper_threshold and rsi_stayed_below_rsi_ma) or reached_maximum_tolerated_loss
    
    def next(self):
        # Warm-up RSI for rsi_warmup_in_days
        if len(self) < rsi_warmup_in_days:
            return
        for data in self.datas:
            # Simply log the closing price of the series from the reference
            pnl_perc = 0
            if self.getposition(data):
                pnl_perc = 1 - (self.getposition(data).price / data.close[0]) 
            if True or not self.trade_today_mode() or self.datas[0].datetime.date(0) == self.single_date_to_trade:
                self.log('%s Close: %.2f, RSI: %.2f, RSI-MA: %.2f, Position: %.2f, PNL: %.2f%%' 
                        % (data._name, data.close[0], self.rsi[data._name][0], self.rsi_ma[data._name][0], self.getposition(data).price, pnl_perc*100))

            # Check if an order is pending ... if yes, we cannot send a 2nd one
            if self.order[data._name]:
                return

            # Check if we are in the market
            if not self.getposition(data):
                # Buy conditionaly
                if self.buy_condition(data._name):
                    # BUY, BUY, BUY!!! (with all possible default parameters)
                    self.log(f'{data._name} BUY CREATE, {data.close[0]:.2f}')
                    # Buy dollar ammount
                    self.order[data._name] = self.buy(data=data, size=float(self.params.fixed_investment_amount / data.close[0]))
                    self.trade_actions.append(TradeAction(date=str(self.datas[0].datetime.date(0)), action="BUY", ticker=data._name))
            else:
                # TODO: Sell when RSI crosses over RSI-based-MA comming down above RSI 60, or when position showing 10% loss

                if self.sell_condition(data._name):
                    # SELL, SELL, SELL!!! (with all possible default parameters)
                    self.log('%s SELL CREATE, %.2f' % (data._name, data.close[0]))
                    # Sell position
                    self.order[data._name] = self.sell(data = data, size = self.getposition(data).size)

    def stop(self):
        if not self.trade_today_mode():
            self.log(f'RSI: {self.params.upper_rsi}/{self.params.lower_rsi}, ' +
                    f'loss_pct: {self.params.loss_pct_threshold}, '
                    f'investment: {self.params.fixed_investment_amount}, '
                    f'End portfolio value: {round(self.broker.getvalue())}')
        if self.params.custom_callback is not None:
            self.params.custom_callback(self)
            
            
def trades_today(tickers, todays_date_str, open_positions=None):
    initial_cash = 30000
    
    # end_date is the supplied date in today_data_str
    end_date = (datetime.datetime.strptime(todays_date_str, "%Y-%m-%d") + datetime.timedelta(days=1)).date()
    number_of_weeks_to_observe = 2
    if open_positions:
        start_date = open_positions[0].date - datetime.timedelta(weeks = rsi_warmup_in_weeks + number_of_weeks_to_observe)
    else:
        start_date = end_date - datetime.timedelta(weeks = rsi_warmup_in_weeks + number_of_weeks_to_observe)
        
    if start_date > end_date:
        print(f"ERROR start_date={start_date} < end_date={end_date}")
        return []
    tickers_list = tickers.split(',')
    # Create a cerebro entity
    cerebro = bt.Cerebro()

     # Add a strategy
    cerebro.addstrategy(TestStrategy,
                        printlog=True,
                        upper_rsi=60,
                        lower_rsi=50,
                        loss_pct_threshold = 9,
                        fixed_investment_amount=5000,
                        single_date_to_trade=todays_date_str)

    # Add the Data Feed to Cerebro
    for ticker in tickers_list:
        yahoo_data = yf.download(ticker, start_date, end_date)
        data = bt.feeds.PandasData(dataname=yahoo_data)
        cerebro.adddata(data=data, name=ticker)

    # Set our desired cash start
    cerebro.broker.setcash(initial_cash)
    start_portfolio_value = cerebro.broker.getvalue()

    # Run over everything
    results = cerebro.run()
    
    # TODO: test this will return actions for 2 tickers in the same day
    return cerebro.runstrats[0][0].trade_actions
    