import datetime
from services.stock_compute_service import StockComputeService
import matplotlib.ticker as ticker
import matplotlib.ticker as ticker


class TradeTodayReportingService():
    def __init__(self, today, tickers, open_positions, context, user="unknown"):
        self.cli_command = ""
        self.trades_today = []
        self.stock_stats_today = []
        self.context = context
        self.open_positions = open_positions
        self.user = user
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
            output += f"No trades today ({str(datetime.datetime.today().date())})\n"
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
        output += f"<h1>Trades today</h1>"
        if self.trades_today:
            output += "<ul>"
            for trade in self.trades_today:
                output += f"<li>{trade.as_text(context=False, include_date=False)}</li>"
            output += "</ul>"
        else:
            output += f"<p>No trades today ({str(datetime.datetime.today().date())})</p>"
        # Stock stats
        output += f"<h1>Selected tickers statistics</h1>"
        output += '<table border="1">'
        output += """<tr>
                        <th>Ticker</th>
                        <th>Close</th>
                        <th>RSI</th>
                        <th>Growth Range</th>
                        <th>BB-Bot</th>
                        <th>BB-Mid</th>
                        <th>BB-Top</th>
                    <tr>"""
        for stock in self.stock_stats_today:
            # exclude stocks with open positions
            if self.position_from_ticker(stock.ticker) is None:
                growth_potential = round((stock.bb_top - stock.bb_bot) / stock.bb_bot * 100, 1)
                if stock.rsi < StockComputeService.LOWER_RSI:
                    rsi_style =' style="background-color: Orange;"' 
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
                    if growth_potential > 10:
                        growth_potential_style =' style="background-color: Green;"'
                else:
                    rsi_style =''
                    close_style =''
                    growth_potential_style =' style="background-color: Gray;"'
                output += "<tr>"
                output += f"<td>{stock.ticker}</td>"
                output += f"<td{close_style}>{round(stock.close, 2):.2f}</td>"
                output += f'<td{rsi_style}>{round(stock.rsi, 2):.2f}</td>'
                output += f'<td{growth_potential_style}>{growth_potential:.1f}%</td>'
                output += f"<td>{round(stock.bb_bot, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_mid, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_top, 2):.2f}</td>"
                output += "</tr>"
        output += "</table>"
        rsi = '<a href="https://www.investopedia.com/terms/r/rsi.asp">RSI</a>'
        bb = '<a href="https://www.investopedia.com/terms/b/bollingerbands.asp">BB</a>'
        output += f'<p style="font-size=12px; line-height: 0.8;"><i>{rsi}</i> shows orange when it goes below {StockComputeService.LOWER_RSI}</p>'
        output += f'<p style="font-size=12px; line-height: 0.8;"><i>Close</i> shows orange when approaching <i>{bb}-Bot</i>, and green when it goes below <i>{bb}-Bot</i></p>'
        output += f'<p style="font-size=12px; line-height: 0.8;"><i>Close</i> going green is a sign of likely reversal of downwards trend. Excplicit recommendation to buy will only occur when Close crosses above {bb}-Bot but this also means some potential gains may be lost if the price increases rapidly once reversal occurs</p>'
        output += f'<p style="font-size=12px; line-height: 0.8;"><i>Growth Range</i> Indicates how high stock price might go in the short term (applicable only when <i>Close</i> near or below <i>{bb}-Bot</i>)</p>'
        output += f'<p style="font-size=12px; line-height: 0.8;"><i>Growth Range</i> will show orange if above 5% and green if above 10%</p>'
        output += f'<p style="font-size=12px; line-height: 0.8;"><i>Growth Range</i> will show gray if <i>Close</i> not near <i>{bb}-Bot</i> as price is not at the bottom of the growth band</p>'
        return output
        
    def position_performance_html_section(self):
        output = ""
        total_pnl = 0.0
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
        pnl_span = f'<span style="color: {pnl_color};">{total_pnl:.0f}</span>'
        output += f"<h1>Position performance: PNL$ = {pnl_span}</h1>"
        output += '<table border="1">'
        output += """<tr>
                        <th>Ticker</th>
                        <th>Position date</th>
                        <th>Investment</th>
                        <th>Position size</th>
                        <th>Position price</th>
                        <th>Close</th>
                        <th>RSI</th>
                        <th>BB-Bot</th>
                        <th>BB-Mid</th>
                        <th>BB-Top</th>
                        <th>PNL %</th>
                        <th>PNL</th>
                    <tr>"""
        # exclude stocks with open positions
        for stock in stock_stats_sorted_by_pnl:
            position = self.position_from_ticker(stock.ticker)
            if position is not None:
                pnl = round((stock.close*position.size)-(position.price*position.size), 2)
                if pnl > 0:
                    pnl_style =' style="background-color: Green;"' 
                else:
                    pnl_style =' style="background-color: Red;"' 
                output += "<tr>"
                output += f"<td>{stock.ticker}</td>"
                output += f"<td>{position.date}</td>"
                output += f"<td>{round(position.size*position.price, 2):.2f}</td>"
                output += f"<td>{round(position.size, 2):.2f}</td>"
                output += f"<td>{round(position.price, 2):.2f}</td>"
                output += f"<td>{round(stock.close, 2):.2f}</td>"
                output += f'<td>{round(stock.rsi, 2):.2f}</td>'
                output += f"<td>{round(stock.bb_bot, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_mid, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_top, 2):.2f}</td>"
                output += f"<td>{round((stock.close - position.price) / stock.close * 100, 2):.2f}</td>"
                output += f"<td{pnl_style}>{pnl:.2f}</td>"
                output += "</tr>"
        output += "</table>"
        return output
    
    def email_html_report(self):
        output = ""
        output += f"<p>Report for {self.user.capitalize()}</p>"
        # CLI command
        output += f"<h1>Execution Command</h1>"
        output += f"<p>{self.cli_command}</p>"
        # Trades today
        output += self.trades_today_html_section()
        # Add open positions performance
        # Ticker, Position Date, Position price, Position size, Close, RSI, BB-Top, BB-Mid, BB-Low, PNL %, PNL
        if self.open_positions:
            output += self.position_performance_html_section()
        # TODO: Remove when dev complete
        #with open('temp/trade_advisor_report.html', 'w') as file:
        #    file.write(output)
        return(f"{len(self.trades_today)} trades today", output)
    
    def whatsapp_report(self):
        return self.console_report(include_stats=False)
    
    