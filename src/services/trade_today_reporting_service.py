import datetime
from services.exchange_rate_service import ExchangeRateService
from services.tax_calculator_service import TaxCalculatorService
from services.position_stats_service import PositionStatsService
from services.runtime_stock_stats_service import RuntimeStockStatsService
from services.stock_compute_service import StockComputeService
from services.dataroma_service import DataromaService

class TradeTodayReportingService():
    def __init__(self, today: str, tickers, open_positions, closed_positions, context, user="unknown", rapid=False, 
                 exchange_rate_service: ExchangeRateService = None):
        self.cli_command = ""
        self.trades_today = []
        self.stock_stats_today = []
        self.context = context
        self.open_positions = open_positions
        self.closed_positions = closed_positions
        self.user = user
        self.today_str = today
        self.rapid = rapid
        self.position_stats_service = PositionStatsService(open_positions, closed_positions)
        self.dataroma_service = DataromaService()
        self.tax_calculator_service = TaxCalculatorService(closed_positions=closed_positions, exchange_rate_service=exchange_rate_service)
        svc = StockComputeService(tickers, today, open_positions)
        trades = svc.trades_today()
        # Command line expanded
        self.cli_command = f"trade-today --tickers {tickers}"
        for open_position in open_positions:
            self.cli_command += f" -p {open_position.as_csv()}"
        # Trades today
        if trades:
            for trade in trades:
                self.trades_today.append(trade)
        # stock stats today
        for ticker in tickers.split(','):
            self.stock_stats_today.append(svc.get_stock_daily_stats_list(ticker, 1)[0])
        self.stock_stats_today.sort(key=lambda stock: stock.rsi)
    
    def console_report(self, include_stats=True):
        output = ""
        # CLI command
        output += self.cli_command + "\n"
        output += "\n"
        # Trades today
        if self.trades_today:
            for trade in self.trades_today:
                output += trade.as_text(context=False) + "\n"
        else:
            output += f"No trades today ({self.today_str})\n"
        output += "\n"
        # Stock stats
        if include_stats:
            for stock in self.stock_stats_today:
                output += stock.as_text() + "\n"
        return output
   
    def position_from_ticker(self, ticker):
        for open_position in self.open_positions:
            if open_position.ticker == ticker:
                return open_position
        return None
   
    def trades_today_html_section(self):
        oversold_hedge_fund_bought_tickers = []
        output = ""
        output += f"<h1>Trades today ({self.today_str})</h1>"
        if self.trades_today:
            output += "<ul>"
            for trade in self.trades_today:
                output += f"<li>{trade.as_text(context=False, include_date=False)}</li>"
            output += "</ul>"
        else:
            output += f"<p>No trades today ({self.today_str})</p>"
        # Stock stats
        output += f"<h1>Selected tickers statistics</h1>"
        output += '<table border="1">'
        output += "<tr>"
        output += "<th>Ticker</th>"
        output += "<th>Close</th>"
        output += "<th>RSI</th>"
        output += '<th>HF <a href="https://www.dataroma.com/m/g/portfolio_b.php?q=h&o=c">H</a>,<a href="https://www.dataroma.com/m/g/portfolio_b.php?q=q&o=c">Q</a>,<a href="https://www.dataroma.com/m/g/portfolio.php?pct=0&o=c">O</a></th>'
        if not self.rapid:
            output += "<th>P/E ratio</th>"
        output += "<th>Growth Range</th>"
        output += "<th>BB-Bot</th>"
        output += "<th>BB-Mid</th>"
        output += "<th>BB-Top</th>"
        if not self.rapid:
            output += "<th>Earnings in</th>"
        output += "</tr>"
        ticker_list = [stock.ticker for stock in self.stock_stats_today]
        runtime_stock_stats_service = RuntimeStockStatsService(ticker_list, self.rapid)
        for stock in self.stock_stats_today:
            # exclude stocks with open positions
            if self.position_from_ticker(stock.ticker) is None:
                growth_potential = round((stock.bb_top - stock.bb_bot) / stock.bb_bot * 100, 1)
                pe_ratio = runtime_stock_stats_service.pe_ratio(stock.ticker)
                days_till_earnings = runtime_stock_stats_service.next_earnings_call_in_days(stock.ticker)
                hedge_fund_buys_quarter= self.dataroma_service.num_quarter_buys_by_ticker(stock.ticker)
                hedge_fund_buys_last_6months = self.dataroma_service.num_6month_buys_by_ticker(stock.ticker)
                if stock.rsi < StockComputeService.LOWER_RSI:
                    rsi_style =' style="background-color: Green;"' 
                    # Close styling
                    if stock.close < stock.bb_bot:
                        close_style =' style="background-color: Green;"'
                    elif stock.close < stock.bb_mid - ((stock.bb_mid-stock.bb_bot)/2): # close nearing bb-bot
                        close_style =' style="background-color: Orange;"' 
                    else:
                        close_style =''
                    # Growth Potential styling
                    if growth_potential > 5 and growth_potential < 10:
                        growth_potential_style =' style="background-color: Orange;"'
                    elif growth_potential > 10:
                        growth_potential_style =' style="background-color: Green;"'
                    else:
                        growth_potential_style =''
                    # PE ratio styling
                    if pe_ratio > 0 and pe_ratio < 15:
                        pe_ratio_style =' style="background-color: Green;"'
                    elif pe_ratio >= 15 and pe_ratio < 50:
                        pe_ratio_style =''
                    else:
                        pe_ratio_style =' style="background-color: Red;"'
                    if days_till_earnings < 6:
                        days_till_earnings_style =' style="background-color: Green;"' 
                    else:
                        days_till_earnings_style ='' 
                    # Hedge fund buys styling
                    if hedge_fund_buys_last_6months >= 6:
                        hedge_fund_buys_style =' style="background-color: Green;"'
                    elif hedge_fund_buys_last_6months > 0 and hedge_fund_buys_last_6months < 6:
                        hedge_fund_buys_style =' style="background-color: Orange;"'
                    else:
                        hedge_fund_buys_style =''
                else:
                    rsi_style =''
                    close_style =''
                    growth_potential_style =' style="background-color: Gray;"'
                    pe_ratio_style =''
                    days_till_earnings_style ='' 
                    hedge_fund_buys_style =''
                if close_style != "" and rsi_style != "" and hedge_fund_buys_last_6months >= 5:
                    oversold_hedge_fund_bought_tickers.append(stock.ticker)
                    
                dotted_stock = stock.ticker.replace("-",".")
                output += "<tr>"
                output += f'<td><a href="https://finviz.com/quote.ashx?t={stock.ticker}">{stock.ticker}</a>   <a href="https://www.tradingview.com/symbols/{dotted_stock}"><span style="font-size: 0.5em;">TV</span></a></td>'
                output += f"<td{close_style}>{round(stock.close, 2):.2f}</td>"
                output += f'<td{rsi_style}>{round(stock.rsi, 2):.2f}</td>'
                output += f'<td{hedge_fund_buys_style}>{hedge_fund_buys_last_6months},{hedge_fund_buys_quarter},<a href="https://www.dataroma.com/m/stock.php?sym={stock.ticker}">{self.dataroma_service.num_owners_by_ticker(stock.ticker)}</a></td>'
                if not self.rapid:
                    output += f'<td{pe_ratio_style}>{pe_ratio:.2f}</td>'
                output += f'<td{growth_potential_style}>{growth_potential:.1f}%</td>'
                output += f"<td>{round(stock.bb_bot, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_mid, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_top, 2):.2f}</td>"
                if not self.rapid:
                    output += f"<td {days_till_earnings_style}>{days_till_earnings}d</td>"
                output += "</tr>"
        output += "</table>"
        p_open = '<p style="font-size=12px; line-height: 0.8;">'
        output += f'{p_open}Screen in <a href="https://finviz.com/screener.ashx?v=311&ft=3&t=AAPL,ABBV,ADBE,AMD,AMZN,AVGO,BAC,BRK-B,COST,CRM,CVX,GOOG,HD,JNJ,JPM,KO,LLY,MA,META,MRK,MSFT,NFLX,NVDA,ORCL,PEP,PFE,PG,TMO,TSLA,UNH,V,WMT,XOM&o=rsi">Finviz</a></p>'
        output += f'{p_open}HF shortlist in <a href="https://finviz.com/screener.ashx?v=311&ft=3&t={",".join(oversold_hedge_fund_bought_tickers)}&o=forwardpe">Finviz</a></p>'
        output += f'{p_open}Observe hedge fund movements in <a href="https://whalewisdom.com">Whalewisdom</a> and <a href="https://www.dataroma.com">Dataroma</a></p>'
        output += f'{p_open}<b>RSI:</b><a href="https://www.investopedia.com/terms/r/rsi.asp"> Relative Strength Index</a></p>'
        output += f'{p_open}<b>BB:</b><a href="https://www.investopedia.com/terms/b/bollingerbands.asp"> Bollinger Band</a></p>'
        output += f'{p_open}<i>Close</i> shows green as a sign of likely reversal of downwards trend (<i>Close</i> < <i>BB-Bot</i>). Explicit recommendation to buy will only occur when <i>Close</i> crosses above <i>BB-Bot</i> but this also means some potential gains may be lost if the price increases rapidly once reversal occurs. There is however no guarantee price will go up at this point. It could always keep going down. Do further research on the stock before opening a position on it.</p>'
        output += f'{p_open}<i>Close</i> shows orange when approaching <i>BB-Bot</i>, more specifically <i>Close</i> is in the lower half of [<i>BB-Bot</i>..<i>BB-Mid</i>] range. Meaning start researching this stock</p>'
        output += f'{p_open}<i>RSI</i> shows green when it goes below {StockComputeService.LOWER_RSI}, meaning it is oversold</p>'
        output += f'{p_open}<i>HF Buys</i> shows the number of Hedge Funds that bought stock in last 6 months (H), quarter (Q), followed by the number of Hedge Funds that own stock (O)</p>'
        output += f'{p_open}<i>Growth Range</i> Indicates how high stock price might go in the short term (applicable only when <i>Close</i> near or below <i>BB-Bot</i>)</p>'
        output += f'{p_open}<i>Growth Range</i> will show orange if above 5% and green if above 10%</p>'
        output += f'{p_open}<i>Growth Range</i> will show gray if <i>Close</i> not near <i>BB-Bot</i> as price is not at the bottom of the growth band</p>'
        return output
        
    def open_position_performance_html_section(self):
        output = ""
        total_pnl = 0.0
        ticker_list = [stock.ticker for stock in self.stock_stats_today]
        runtime_stock_stats_service = RuntimeStockStatsService(ticker_list, self.rapid)
        stock_stats_sorted_by_pnl = sorted(self.stock_stats_today, key=lambda stats: stats.pnl_pct, reverse=True)
        for stock in stock_stats_sorted_by_pnl:
            position = self.position_from_ticker(stock.ticker)
            if position is not None:
                total_pnl += ((stock.close*position.size)-(position.price*position.size))
        if total_pnl > 0:
            pnl_color = 'green'
        elif total_pnl < 0:
            pnl_color = 'red'
        else:
            pnl_color = 'black'
        pnl_span = f'<span style="color: {pnl_color};">${total_pnl:.0f}</span>'
        output += f"<h1>Open position performance (PNL={pnl_span}):</h1>"
        output += '<table border="1">'
        # replace with line by line increment
        output += "<tr>"
        output += "<th>Ticker</th>"
        output += "<th>Position date</th>"
        output += "<th>Investment</th>"
        output += "<th>Position size</th>"
        output += "<th>Position price</th>"
        output += "<th>Close</th>"
        output += "<th>RSI</th>"
        if not self.rapid:
            output += "<th>P/E Ratio</th>"
        output += "<th>BB-Bot</th>"
        output += "<th>BB-Mid</th>"
        output += "<th>BB-Top</th>"
        output += "<th>PNL %</th>"
        output += "<th>PNL</th>"
        output += '<th>HF <a href="https://www.dataroma.com/m/g/portfolio_b.php?q=h&o=c">H</a>,<a href="https://www.dataroma.com/m/g/portfolio_b.php?q=q&o=c">Q</a>,<a href="https://www.dataroma.com/m/g/portfolio.php?pct=0&o=c">O</a></th>'
        if not self.rapid:
            output += "<th>Earnings in</th>"
        output += "</tr>"
        # exclude stocks with open positions
        open_positions_tickers_csv = None
        for stock in stock_stats_sorted_by_pnl:
            pe_ratio = runtime_stock_stats_service.pe_ratio(stock.ticker)
            position = self.position_from_ticker(stock.ticker)
            if position is not None:
                #TODO: Add PNL function to PositionStatsService
                pnl = round((stock.close*position.size)-(position.price*position.size), 2)
                days_till_earnings = runtime_stock_stats_service.next_earnings_call_in_days(stock.ticker)
                if pnl > 0:
                    pnl_style =' style="background-color: Green;"' 
                else:
                    pnl_style =' style="background-color: Red;"' 
                # Hedge fund buys styling
                hedge_fund_buys_quarter= self.dataroma_service.num_quarter_buys_by_ticker(stock.ticker)
                hedge_fund_buys_last_6months = self.dataroma_service.num_6month_buys_by_ticker(stock.ticker)
                if hedge_fund_buys_last_6months >= 6:
                    hedge_fund_buys_style =' style="color: Green;"'
                elif hedge_fund_buys_last_6months > 0 and hedge_fund_buys_last_6months < 6:
                    hedge_fund_buys_style =' style="color: Orange;"'
                else:
                    hedge_fund_buys_style =''
                    
                dotted_stock = stock.ticker.replace("-",".")
                output += "<tr>"
                output += f'<td><a href="https://finviz.com/quote.ashx?t={stock.ticker}">{stock.ticker}</a>   <a href="https://www.tradingview.com/symbols/{dotted_stock}"><span style="font-size: 0.5em;">TV</span></a></td>'
                output += f"<td>{position.date}</td>"
                output += f"<td>{round(position.size*position.price, 2):.2f}</td>"
                output += f"<td>{round(position.size, 2):.2f}</td>"
                output += f"<td>{round(position.price, 2):.2f}</td>"
                output += f"<td>{round(stock.close, 2):.2f}</td>"
                output += f'<td>{round(stock.rsi, 2):.2f}</td>'
                if not self.rapid:
                    output += f'<td>{pe_ratio:.2f}</td>'
                output += f"<td>{round(stock.bb_bot, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_mid, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_top, 2):.2f}</td>"
                output += f"<td>{round((stock.close - position.price) / stock.close * 100, 2):.2f}</td>"
                output += f"<td{pnl_style}>{pnl:.2f}</td>"
                output += f'<td{hedge_fund_buys_style}>{hedge_fund_buys_last_6months},{hedge_fund_buys_quarter},<a href="https://www.dataroma.com/m/stock.php?sym={stock.ticker}">{self.dataroma_service.num_owners_by_ticker(stock.ticker)}</a></td>'
                if not self.rapid:
                    output += f"<td>{days_till_earnings}d</td>"
                output += "</tr>"
                if open_positions_tickers_csv is None:
                    open_positions_tickers_csv = stock.ticker
                else:
                    open_positions_tickers_csv += ',' + stock.ticker
        output += "</table>"
        p_open = '<p style="font-size=12px; line-height: 0.8;">'
        if open_positions_tickers_csv is not None:
            output += f'{p_open}<a href="https://finviz.com/screener.ashx?v=311&ft=3&t={open_positions_tickers_csv}&o=-perf1w">Finviz open position analysis</a></p>'
        return output
    
    def closed_position_performance_html_section(self):
        output = ""
        output += f"<h1>Closed position performance</h1>"
        output += '<table border="1">'
        output += """<tr>
                        <th>Period</th>
                        <th>Batting average</th>
                        <th>PNL</th>
                    <tr>"""
        # years
        years = self.position_stats_service.yearly_closed_positions_performance()
        for year in years:
            output += "<tr>"
            output += f"<td>{year.year}</td>"
            output += f"<td>{year.batting_average}</td>"
            output += f"<td>{year.pnl:.0f}</td>"
            output += "</tr>"
        output += "<tr>"
        all_time = self.position_stats_service.all_time_closed_positions_performance()
        output += f"<td>All time</td>"
        output += f"<td>{all_time.batting_average}</td>"
        output += f"<td>{all_time.pnl:.0f}</td>"
        output += "</tr>"
        output += "</table>"
        return output
    
    def email_html_report(self, simulation=False):
        output = ""
        output += f"<p>Report for {self.user.capitalize()}</p>"
        output += f"<p><i>Created on {str(datetime.datetime.now()).split('.')[0]}</i></p>"
        # Trades today
        print("Building trade today report ...")
        output += self.trades_today_html_section()
        # Add open positions performance
        # Ticker, Position Date, Position price, Position size, Close, RSI, BB-Top, BB-Mid, BB-Low, PNL %, PNL
        if self.open_positions:
            print("Building open positions performance report ...")
            output += self.open_position_performance_html_section()
        if self.closed_positions:
            print("Building closed positions performance report ...")
            output += self.closed_position_performance_html_section()
            print("Building tax activities report ...")
            output += self.tax_calculator_service.tax_activities_html_report()
        # CLI command
        output += f"<h1>Execution Command</h1>"
        output += f"<p>{self.cli_command}</p>"
        if simulation:
            with open('temp/trade_advisor_report.html', 'w') as file:
                file.write(output)
        return(f"{len(self.trades_today)} trades today {str(datetime.datetime.now()).split('.')[0]}", output)
    
    def whatsapp_report(self):
        return self.console_report(include_stats=False)
    
    