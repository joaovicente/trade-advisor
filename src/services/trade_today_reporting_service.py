import datetime
from reports.tax_activities_report import TaxActivitiesReport
from services.position_stats_service import PositionStatsService
from services.runtime_stock_stats_service import RuntimeStockStatsService
from services.stock_compute_service import StockComputeService

class TradeTodayReportingService():
    def __init__(self, today: str, tickers, open_positions, closed_positions, context, user="unknown", rapid=False):
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
        self.tax_activities_report = TaxActivitiesReport(todays_date=today, closed_positions=closed_positions, rapid=rapid)
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
        output += """<tr>
                        <th>Ticker</th>
                        <th>Close</th>
                        <th>RSI</th>
                        <th>P/E ratio</th>
                        <th>Growth Range</th>
                        <th>BB-Bot</th>
                        <th>BB-Mid</th>
                        <th>BB-Top</th>
                        <th>Earnings in</th>
                    <tr>"""
        ticker_list = [stock.ticker for stock in self.stock_stats_today]
        runtime_stock_stats_service = RuntimeStockStatsService(ticker_list, self.rapid)
        for stock in self.stock_stats_today:
            # exclude stocks with open positions
            if self.position_from_ticker(stock.ticker) is None:
                growth_potential = round((stock.bb_top - stock.bb_bot) / stock.bb_bot * 100, 1)
                pe_ratio = runtime_stock_stats_service.pe_ratio(stock.ticker)
                days_till_earnings = runtime_stock_stats_service.next_earnings_call_in_days(stock.ticker)
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
                else:
                    rsi_style =''
                    close_style =''
                    growth_potential_style =' style="background-color: Gray;"'
                    pe_ratio_style =''
                    days_till_earnings_style ='' 
                        
                output += "<tr>"
                output += f'<td><a href="https://finviz.com/quote.ashx?t={stock.ticker}">{stock.ticker}</a></td>'
                output += f"<td{close_style}>{round(stock.close, 2):.2f}</td>"
                output += f'<td{rsi_style}>{round(stock.rsi, 2):.2f}</td>'
                output += f'<td{pe_ratio_style}>{pe_ratio:.2f}</td>'
                output += f'<td{growth_potential_style}>{growth_potential:.1f}%</td>'
                output += f"<td>{round(stock.bb_bot, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_mid, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_top, 2):.2f}</td>"
                output += f"<td {days_till_earnings_style}>{days_till_earnings}d</td>"
                output += "</tr>"
        output += "</table>"
        p_open = '<p style="font-size=12px; line-height: 0.8;">'
        output += f'{p_open}screen in <a href="https://finviz.com/screener.ashx?v=111&ft=3&t=AAPL,ABBV,ADBE,AMD,AMZN,AVGO,BAC,BRK-B,COST,CRM,CVX,GOOG,HD,JNJ,JPM,KO,LLY,MA,META,MRK,MSFT,NFLX,NVDA,ORCL,PEP,PFE,PG,TMO,TSLA,UNH,V,WMT,XOM&o=rsi">Finviz</a></p>'
        output += f'{p_open}<b>rsi:</b><a href="https://www.investopedia.com/terms/r/rsi.asp"> Relative Strength Index</a></p>'
        output += f'{p_open}<b>BB:</b><a href="https://www.investopedia.com/terms/b/bollingerbands.asp"> Bollinger Band</a></p>'
        output += f'{p_open}<i>Close</i> shows green as a sign of likely reversal of downwards trend (<i>Close</i> < <i>BB-Bot</i>). Explicit recommendation to buy will only occur when <i>Close</i> crosses above <i>BB-Bot</i> but this also means some potential gains may be lost if the price increases rapidly once reversal occurs. There is however no guarantee price will go up at this point. It could always keep going down. Do further research on the stock before opening a position on it.</p>'
        output += f'{p_open}<i>Close</i> shows orange when approaching <i>BB-Bot</i>, more specifically <i>Close</i> is in the lower half of [<i>BB-Bot</i>..<i>BB-Mid</i>] range. Meaning start researching this stock</p>'
        output += f'{p_open}<i>RSI</i> shows green when it goes below {StockComputeService.LOWER_RSI}, meaning it is oversold</p>'
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
        output += """<tr>
                        <th>Ticker</th>
                        <th>Position date</th>
                        <th>Investment</th>
                        <th>Position size</th>
                        <th>Position price</th>
                        <th>Close</th>
                        <th>RSI</th>
                        <th>P/E Ratio</th>
                        <th>BB-Bot</th>
                        <th>BB-Mid</th>
                        <th>BB-Top</th>
                        <th>PNL %</th>
                        <th>PNL</th>
                        <th>Earnings in</th>
                    <tr>"""
        # exclude stocks with open positions
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
                output += "<tr>"
                output += f'<td><a href="https://finviz.com/quote.ashx?t={stock.ticker}">{stock.ticker}</a></td>'
                output += f"<td>{position.date}</td>"
                output += f"<td>{round(position.size*position.price, 2):.2f}</td>"
                output += f"<td>{round(position.size, 2):.2f}</td>"
                output += f"<td>{round(position.price, 2):.2f}</td>"
                output += f"<td>{round(stock.close, 2):.2f}</td>"
                output += f'<td>{round(stock.rsi, 2):.2f}</td>'
                output += f'<td>{pe_ratio:.2f}</td>'
                output += f"<td>{round(stock.bb_bot, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_mid, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_top, 2):.2f}</td>"
                output += f"<td>{round((stock.close - position.price) / stock.close * 100, 2):.2f}</td>"
                output += f"<td{pnl_style}>{pnl:.2f}</td>"
                output += f"<td>{days_till_earnings:.0f}d</td>"
                output += "</tr>"
        output += "</table>"
        return output
    
    def closed_position_performance_html_section(self):
        output = ""
        output += f"<h1>Closed position performance</h1>"
        output += '<table border="1">'
        output += """<tr>
                        <th>PNL all time</th>
                        <th>Batting average</th>
                        <th>PNL year to date</th>
                        <th>PNL Jan - Nov</th>
                        <th>PNL Nov - Dec</th>
                    <tr>"""
        pnl_all_time = self.position_stats_service.get_pnl_all_time()
        pnl_year_to_date = self.position_stats_service.get_pnl_year_to_date()
        pnl_jan_to_nov = self.position_stats_service.get_pnl_jan_to_nov()
        pnl_nov_to_dec = self.position_stats_service.get_pnl_nov_to_dec()
        batting_average = self.position_stats_service.get_batting_avg()
        output += "<tr>"
        output += f"<td>{pnl_all_time:.0f}</td>"
        output += f"<td>{batting_average}</td>"
        output += f"<td>{pnl_year_to_date:.0f}</td>"
        output += f"<td>{pnl_jan_to_nov:.0f}</td>"
        output += f"<td>{pnl_nov_to_dec:.0f}</td>"
        output += "</table>"
        return output
    
    def email_html_report(self, simulation=False):
        output = ""
        output += f"<p>Report for {self.user.capitalize()}</p>"
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
            output += self.tax_activities_report.get_tax_activities_html_report()
        # CLI command
        output += f"<h1>Execution Command</h1>"
        output += f"<p>{self.cli_command}</p>"
        if simulation:
            with open('temp/trade_advisor_report.html', 'w') as file:
                file.write(output)
        return(f"{len(self.trades_today)} trades today {str(datetime.datetime.now()).split('.')[0]}", output)
    
    def whatsapp_report(self):
        return self.console_report(include_stats=False)
    
    