from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt
import backtrader.analyzers as btanalyzers
import yfinance as yf


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('printlog', False),
        ('upper_rsi', 60),
        ('lower_rsi', 50),
        ('loss_pct_threshold', 5),
        ('fixed_investment_ammount', 3000)
    )

    def log(self, txt, dt=None, do_print=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or do_print:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def add_custom_stats(self, stats):
        self.custom_stats.append(stats)
        
    def __init__(self):
        self.custom_stats = []
        # To keep track of pending orders and buy price/commission
        self.order = {data._name: None for data in self.datas}
        self.buyprice = {data._name: None for data in self.datas}
        self.buycomm = {data._name: None for data in self.datas}
            
        # Add the RSI indicator
        self.rsi = {data._name: bt.indicators.RSI(data,plot=True) for data in self.datas}
        self.rsi_ma = {data._name: bt.indicators.SmoothedMovingAverage(self.rsi[data._name], period=14,plot=True) for data in self.datas}
        
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    '%s BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.data._name,
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice[order.data._name] = order.executed.price
                self.buycomm[order.data._name] = order.executed.comm
            else:  # Sell
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
        return rsi_below_lower_threshold and rsi_crossed_above_rsi_ma
        
    def sell_condition(self, name):
        # Sell when RSI crosses over RSI-based-MA coming down above RSI 60, or when position showing 10% loss
        data = self.getdatabyname(name)
        if not self.getposition(data):
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
        for data in self.datas:
            # Simply log the closing price of the series from the reference
            pnl_perc = 0
            if self.getposition(data):
                pnl_perc = 1 - (self.getposition(data).price / data.close[0]) 
            
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
                    self.log('%s BUY CREATE, %.2f' % (data._name, data.close[0]))

                    # Buy dollar ammount
                    self.order[data._name] = self.buy(data=data, size=float(self.params.fixed_investment_ammount / data.close[0]))

            else:
                # TODO: Sell when RSI crosses over RSI-based-MA comming down above RSI 60, or when position showing 10% loss

                if self.sell_condition(data._name):
                    # SELL, SELL, SELL!!! (with all possible default parameters)
                    self.log('%s SELL CREATE, %.2f' % (data._name, data.close[0]))
                    # Sell position
                    self.order[data._name] = self.sell(data = data, size = self.getposition(data).size)

    def stop(self):
        self.add_custom_stats({'rsi_lower': self.params.lower_rsi, 
                      'rsi_upper': self.params.upper_rsi, 
                      'loss_pct': self.params.loss_pct_threshold,
                      'final_value': round(self.broker.getvalue())}) 
        self.log(f'RSI: {self.params.upper_rsi}/{self.params.lower_rsi}, ' +
                 f'loss_pct: {self.params.loss_pct_threshold}, '
                 f'investment: {self.params.fixed_investment_ammount}, '
                 f'End portfolio value: {round(self.broker.getvalue())}', do_print=True)

def trades_today(tickers_csv):
    tickers = tickers_csv.split(",")
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    optimise = False
    
    if not optimise:
        # Add a strategy
        cerebro.addstrategy(TestStrategy,
                            printlog=True,
                            upper_rsi=60,
                            lower_rsi=50,
                            loss_pct_threshold = 9,
                            fixed_investment_ammount=5000)
    else:
        strats = cerebro.optstrategy(
            TestStrategy,
            upper_rsi=range(55, 70, 5),
            lower_rsi=range(30, 55, 5),
            loss_pct_threshold = 9,
            fixed_investment_ammount=5000
            )
        cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe')

    # Add the Data Feed to Cerebro
    end_date=datetime.datetime.today().date()
    start_date = end_date - datetime.timedelta(days=356)
    
    #tickers = ['SNOW']
    #tickers = [ 'AMZN', 'SNOW', 'MSFT', 'AAPL', 'GOOG', 'NVDA', 'META']
    #tickers = [ 'AMZN', 'SNOW', 'MSFT', 'AAPL', 'GOOG', 'NVDA', 'META', 'JNJ', 'JPM', 'PFE', 'PG', 'UNH', 'V']
    for ticker in tickers:
        data = bt.feeds.PandasData(dataname=yf.download(ticker, start_date, end_date))
        cerebro.adddata(data=data, name=ticker)

    # Set our desired cash start
    cerebro.broker.setcash(30000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    opt_return = cerebro.run(maxcpus=1)

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
  
    #stats = cerebro.strategies[0].stats
    #sorted_results = sorted(stats, key=lambda x: x['final_value'], reverse=True)
    #for result in sorted_results[:5]:
    #    print(result)
    