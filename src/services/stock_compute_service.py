from typing import List
from schemas.portfolio_stats import AssetStats, PortfolioStats, PositionStats
from schemas.stock_daily_stats import StockDailyStats
from strategies.base_strategy import BaseStrategy
from strategies.rsi_strategy import RsiStrategy

import backtrader as bt
import yfinance as yf

import datetime

class StockComputeService:
    DEFAULT_DAILY_STATS_RETURNED = BaseStrategy.TRADE_ACTION_CONTEXT_SIZE
    def __init__(self, tickers, todays_date_str, open_positions=None):
        self.todays_date_str = todays_date_str
        self.open_positions = open_positions

        self.initial_cash = 30000
        # end_date is the supplied date in today_data_str
        self.end_date = (datetime.datetime.strptime(todays_date_str, "%Y-%m-%d") + datetime.timedelta(days=1)).date()
        number_of_weeks_to_observe = 2
        if open_positions:
            self.warmup_date = open_positions[0].date - datetime.timedelta(weeks = BaseStrategy.INDICATOR_WARMUP_IN_WEEKS + number_of_weeks_to_observe)
            self.start_date = open_positions[0].date - datetime.timedelta(weeks = number_of_weeks_to_observe)
        else:
            self.warmup_date = self.end_date - datetime.timedelta(weeks = BaseStrategy.INDICATOR_WARMUP_IN_WEEKS + number_of_weeks_to_observe)
            self.start_date = self.end_date - datetime.timedelta(weeks = number_of_weeks_to_observe)
        if self.warmup_date > self.end_date:
            print(f"ERROR start_date={self.start_date} < end_date={self.end_date}")
        self.tickers_list = tickers.split(',')
        # Create a cerebro entity
        self.cerebro = bt.Cerebro()
        # Add a strategy
        self.cerebro.addstrategy(RsiStrategy,
                            start_date = self.start_date,
                            printlog=False,
                            upper_rsi=60,
                            lower_rsi=50,
                            loss_pct_threshold = 9,
                            fixed_investment_amount=5000,
                            single_date_to_trade=self.todays_date_str,
                            open_positions=self.open_positions)

        # Add the Data Feed to Cerebro
        for ticker in self.tickers_list:
            yahoo_data = yf.download(ticker, self.warmup_date, self.end_date)
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

    def get_stock_daily_stats_list(self, ticker, num_lines=DEFAULT_DAILY_STATS_RETURNED) -> List[StockDailyStats]:
        return self.strategy.stock_daily_stats_list[ticker][-num_lines:]

    def get_stock_daily_stats_list_as_text(self, ticker, num_lines=DEFAULT_DAILY_STATS_RETURNED):
        return [s.as_text() for s in self.get_stock_daily_stats_list(ticker, num_lines)]

    def get_strategy(self):
        return self.strategy
    
    def portfolio_stats(self) -> PortfolioStats:
        # compute portfolio statistics
        position_stats_list = []
        asset_stats_list = []
        portfolio_stats = None
        total_invested = 0
        for open_position in self.open_positions:
            # compute PositionStats from open_position and StockDailyStats
            stock_daily_stats = self.get_stock_daily_stats_list(open_position.ticker, 1)[-1]
            amount = open_position.size * open_position.price
            value = open_position.size * stock_daily_stats.close
            total_invested += amount
            position_stats = PositionStats(
                ticker = stock_daily_stats.ticker,
                date = stock_daily_stats.date,
                units = open_position.size,
                open = open_position.price,
                amount = amount,
                value = value,
                pnl = amount - value,
                pnl_pct = (value - amount) / amount * 100
            )
            position_stats_list.append(position_stats)
            # compute AssetStats (same as PositionStats if only one position per ticker)
            asset_stats = AssetStats(
                ticker = stock_daily_stats.ticker,
                price = stock_daily_stats.close,
                units = open_position.size,
                num_positions = 1, # TODO: P2 Support multiple positions per ticker
                amount = amount,
                value = value,
                pnl = value - amount,
                pnl_pct =  (value - amount) / amount * 100
            )
            asset_stats_list.append(asset_stats)
            
        # calculate portfolio stats
        portfolio_value = 0
        for asset_stats in asset_stats_list:
            portfolio_value += asset_stats.value
        portfolio_stats = PortfolioStats(
            total_invested = total_invested, 
            pnl = portfolio_value - total_invested,
            pnl_pct = (portfolio_value - total_invested) / total_invested * 100,
            portfolio_value = portfolio_value,
            asset_stats_list = asset_stats_list, 
            position_stats_list  = position_stats_list)
        return portfolio_stats