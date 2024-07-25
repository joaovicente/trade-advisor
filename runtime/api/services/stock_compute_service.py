from api.services.backtesting_service import BacktraderStrategy

import backtrader as bt
import yfinance as yf

import datetime

class StockComputeService:
    DEFAULT_DAILY_STATS_RETURNED = BacktraderStrategy.TRADE_ACTION_CONTEXT_SIZE
    def __init__(self, tickers, todays_date_str, open_positions=None):
        self.todays_date_str = todays_date_str
        self.open_positions = open_positions

        self.initial_cash = 30000
        # end_date is the supplied date in today_data_str
        self.end_date = (datetime.datetime.strptime(todays_date_str, "%Y-%m-%d") + datetime.timedelta(days=1)).date()
        number_of_weeks_to_observe = 2
        if open_positions:
            self.start_date = open_positions[0].date - datetime.timedelta(weeks = BacktraderStrategy.RSI_WARMUP_IN_WEEKS + number_of_weeks_to_observe)
        else:
            self.start_date = self.end_date - datetime.timedelta(weeks = BacktraderStrategy.RSI_WARMUP_IN_WEEKS + number_of_weeks_to_observe)
        if self.start_date > self.end_date:
            print(f"ERROR start_date={self.start_date} < end_date={self.end_date}")
        self.tickers_list = tickers.split(',')
        # Create a cerebro entity
        self.cerebro = bt.Cerebro()
        # Add a strategy
        self.cerebro.addstrategy(BacktraderStrategy,
                            printlog=False,
                            upper_rsi=60,
                            lower_rsi=50,
                            loss_pct_threshold = 9,
                            fixed_investment_amount=5000,
                            single_date_to_trade=self.todays_date_str,
                            open_positions=self.open_positions)

        # Add the Data Feed to Cerebro
        for ticker in self.tickers_list:
            yahoo_data = yf.download(ticker, self.start_date, self.end_date)
            data = bt.feeds.PandasData(dataname=yahoo_data)
            self.cerebro.adddata(data=data, name=ticker)
        # Set our desired cash start
        self.cerebro.broker.setcash(self.initial_cash)
        # Run over everything
        self.cerebro.run()
        # TODO: test this will return actions for 2 tickers in the same day
        self.strategy = self.cerebro.runstrats[0][0]

    def trades_today(self):
        return self.strategy.trade_actions

    def get_stock_daily_stats_list(self, ticker, num_lines=DEFAULT_DAILY_STATS_RETURNED):
        return self.strategy.stock_daily_stats_list[ticker][-num_lines:]

    def get_stock_daily_stats_list_as_text(self, ticker, num_lines=DEFAULT_DAILY_STATS_RETURNED):
        return [s.as_text() for s in self.get_stock_daily_stats_list(ticker, num_lines)]

    def get_strategy(self):
        return self.strategy