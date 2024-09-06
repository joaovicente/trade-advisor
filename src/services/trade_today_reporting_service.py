import datetime
from services.stock_compute_service import StockComputeService
import matplotlib.ticker as ticker
import matplotlib.ticker as ticker


class TradeTodayReportingService():
    def __init__(self, today, tickers, open_positions, context):
        self.cli_command = ""
        self.trades_today = []
        self.stock_stats_today = []
        self.context = context
        self.open_positions = open_positions
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
    
    def email_html_report(self):
        output = ""
        # CLI command
        output += f"<h1>Execution Command</h1>"
        output += f"<p>{self.cli_command}</p>"
        # Trades today
        output += f"<h1>Trades today</h1>"
        if self.trades_today:
            output += "<ul>"
            for trade in self.trades_today:
                output += f"<li>{trade.as_text(context=False, include_date=False)}</li>"
            output += "</ul>"
        else:
            output += f"<p>No trades today ({str(datetime.datetime.today().date())})</p>"
        # Stock stats
        output += f"<h1>Watched stock statistics</h1>"
        output += '<table border="1">'
        output += """<tr>
                        <th>Ticker</th>
                        <th>Close</th>
                        <th>RSI</th>
                        <th>BB-Bot</th>
                        <th>BB-Mid</th>
                        <th>BB-Top</th>
                    <tr>"""
        for stock in self.stock_stats_today:
            # exclude stocks with open positions
            if self.position_from_ticker(stock.ticker) is None:
                if stock.rsi < StockComputeService.LOWER_RSI:
                    rsi_style =' style="background-color: Orange;"' 
                    if stock.close < stock.bb_bot:
                        close_style =' style="background-color: Green;"' 
                    elif stock.close < stock.bb_mid - ((stock.bb_mid-stock.bb_bot)/2): # close nearing bb-bot
                        close_style =' style="background-color: Orange;"' 
                    else:
                        close_style =''
                else:
                    rsi_style =''
                    close_style =''
                output += "<tr>"
                output += f"<td>{stock.ticker}</td>"
                output += f"<td{close_style}>{round(stock.close, 2):.2f}</td>"
                output += f'<td{rsi_style}>{round(stock.rsi, 2):.2f}</td>'
                output += f"<td>{round(stock.bb_bot, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_mid, 2):.2f}</td>"
                output += f"<td>{round(stock.bb_top, 2):.2f}</td>"
                output += "</tr>"
        output += "</table>"
        # Add open positions performance
        # Ticker, Position Date, Position price, Position size, Close, RSI, BB-Top, BB-Mid, BB-Low, PNL %, PNL
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
                if stock.pnl_pct > 0:
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
                output += f"<td{pnl_style}>{round((stock.close*position.size)-(position.price*position.size), 2):.2f}</td>"
                output += "</tr>"
        output += "</table>"
        # TODO: Remove when dev complete
        #with open('temp/trade_advisor_report.html', 'w') as file:
        #    file.write(output)
        return(f"{len(self.trades_today)} trades today", output)
    
    def whatsapp_report(self):
        return self.console_report(include_stats=False)
    
    