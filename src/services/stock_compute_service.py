import random
import tempfile
from typing import List
from schemas.portfolio_stats import AssetStats, PortfolioStats, PositionStats
from schemas.stock_daily_stats import StockDailyStats
from services.yfinance_data_service import YfinanceDataService
from services.utils_service import date_as_str, parse_date
from strategies.base_strategy import BaseStrategy
from strategies.rsi_strategy import RsiStrategy
from strategies.bbrsi_strategy import BbRsiStrategy

import backtrader as bt
import yfinance as yf

import datetime
import os

class StockComputeService:
    DEFAULT_DAILY_STATS_RETURNED = BaseStrategy.TRADE_ACTION_CONTEXT_SIZE
    LOWER_RSI = 50
    def __init__(self, tickers, todays_date_str, open_positions=None, strategy=BbRsiStrategy, calculate_dates_only=False):
        self.todays_date_str = date_as_str(parse_date(todays_date_str) - datetime.timedelta(days=1))
        self.open_positions = open_positions

        self.initial_cash = 30000
        # end_date is the supplied date in today_data_str
        self.end_date = parse_date(self.todays_date_str) + datetime.timedelta(days=1)
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
        self.cerebro.addstrategy(strategy,
                            start_date = self.start_date,
                            printlog=False,
                            upper_rsi=60,
                            lower_rsi=StockComputeService.LOWER_RSI,
                            loss_pct_threshold = 9,
                            fixed_investment_amount=5000,
                            single_date_to_trade=self.todays_date_str,
                            open_positions=self.open_positions)

        print(f'StockComputeService warmup_date:{self.warmup_date}, end_date: {self.end_date}')
        if calculate_dates_only == True:
            return
        # TODO: If yfinance-data-store contains all ticker data for the required date range, use that instead of yfinance (see yfinance-data-download)
        with tempfile.TemporaryDirectory() as temp_yfinance_download_folder:
            print(f"Temporary yfinance download folder: {temp_yfinance_download_folder}")
            skip_yfinance_download_due_to_rate_limiting_issues = True
            if skip_yfinance_download_due_to_rate_limiting_issues:
                YfinanceDataService().download_required_yfinance_data_to_filesystem(tickers, temp_yfinance_download_folder)
            else:
                # There are persistent issues with yfinance rate limiting, so this code will be disabled, and replaced by TwelveData API above
                #see https://github.com/ranaroussi/yfinance/issues/2422
                # Downloading yfinance CSV to file and loading to backtrader from csv to keep Backtrader decoupled from YFinance
                #yf.enable_debug_mode() # Uncomment to debug download
                multi_ticker_data = yf.download(self.tickers_list, start=self.warmup_date, end=self.end_date)  # Custom date range
                if multi_ticker_data.empty:
                    raise Exception(f"Unable to retrieve data from yfinance. Likely rate limited")
                # Store downloded data to CSV files  
                for ticker in self.tickers_list:
                    # Extract data for a single ticker (like yf.Ticker().history() format)
                    single_ticker_data = multi_ticker_data.xs(ticker, level=1, axis=1)
                    # Save as CSV
                    filename = os.path.join(temp_yfinance_download_folder, f'yfinance_data_{ticker}.csv')
                    single_ticker_data.to_csv(filename)
            # Add the Data Feed to Cerebro
            for ticker in self.tickers_list:
                filename = os.path.join(temp_yfinance_download_folder, f'yfinance_data_{ticker}.csv')
                # Load data from CSV
                # Using GenericCSVData instead of YahooFinanceCSVData as there are issues with YahooFinanceCSVData
                # see https://www.backtrader.com/docu/datafeed/#genericcsvdata
                data = bt.feeds.GenericCSVData(
                    dataname=filename,
                    fromdate=datetime.datetime.combine(self.warmup_date, datetime.datetime.min.time()),
                    todate=datetime.datetime.combine(self.end_date, datetime.datetime.min.time()),
                    nullvalue=0.0,
                    dtformat=('%Y-%m-%d'),
                    datetime=0,
                    close=1,
                    high=2,
                    low=3,
                    open=4,
                    volume=5,
                    openinterest=None
                )
                self.cerebro.adddata(data=data, name=ticker)
            # Set our desired cash start
            self.cerebro.broker.setcash(self.initial_cash)
            # Run over everything
            self.cerebro.run()
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