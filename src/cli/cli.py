import click
import datetime
from services.stock_compute_service import StockComputeService
from services.open_position_service import OpenPositionService
from services.whatsup_notification_service import WhatsappNotificationService


@click.command()
@click.option('--tickers','-t',
              help='TICKERS provided as CSV. e.g.: AMZN,GOOG,MSFT)',
              default=None)
@click.option('--today',
              help='mock today\'s date for testing in yyyy-mm-dd format (e.g. --today=2024-07-14)',
              default=str(datetime.datetime.today().date()))
@click.option('--no-pos', '-n',
              help='do not use open positions for testing', 
              is_flag=True)
@click.option('--context', '--ctx', '-c',
              help='Show provided number of days context for each ticker', 
              show_default=True,
              default=0)
@click.option('--position', '-p',
              help='Provide open positions explicitly as follows -p {date},{ticker},{size},{price} (e.g. -p 2024-07-18,META,2.09692,476.89). Call this multiple times for multiple positions',
              multiple=True) 
@click.option('--output', '-o',
              help='Output to either `console` (default) or whatsapp (e.g. --output=whatsapp)',
              default='console') 
def trade_today(tickers, today, no_pos, context, position, output):
    """Advise on trades that should be made today"""
    response = ""
    open_position_service = OpenPositionService()
    open_positions = []
    if no_pos:
        # use only supplied tickers
        if tickers is None:
            raise click.UsageError("tickers must be supplied when not using open positions")
    else:
        if position: # explicitly supplied open positions
            for p in list(position):
                open_position_service.add_position(p)
        open_positions = open_position_service.get_all()
        # add open positions to any supplied tickers
        position_ticker_list = open_position_service.get_distinct_tickers_list()
        # add supplied tickers
        if tickers is None:
           tickers = ','.join(position_ticker_list)
        else:
           supplied_ticker_list = tickers.split(',')
           tickers = ','.join(list(set(position_ticker_list + supplied_ticker_list)))
    scmp = StockComputeService(tickers, today, open_positions)
    trades = scmp.trades_today()
    #print(f"start_date={trades_today.start_date}, end_date={trades_today.end_date}")
    response += f"trade-today --tickers {tickers}"
    for open_position in open_positions:
        response += f" -p {open_position.as_csv()}"
    response += "\n\n"
    if trades:
        for trade in trades:
            response += trade.as_text() + "\n"
    else:
        response += f"No trades today ({str(datetime.datetime.today().date())})\n"
        if context:
            for ticker in tickers.split(','):
                response += '\n'.join(scmp.get_stock_daily_stats_list_as_text(ticker, context))
                response += f"\n"
    print(response)
    if output=='whatsapp':
        WhatsappNotificationService().send_message(response)
            
@click.command()
@click.option('--today',
              help='mock today\'s date for testing in yyyy-mm-dd format (e.g. --today=2024-07-14)',
              default=str(datetime.datetime.today().date()))
def portfolio_stats(today):
    """Show portfolio statistics"""
    open_positions = OpenPositionService().get_all()
    # add open positions to any supplied tickers
    position_ticker_list = OpenPositionService().get_distinct_tickers_list()
    # add supplied tickers
    tickers = ','.join(position_ticker_list)
    scmp = StockComputeService(tickers, today, open_positions)
    portfolio_stats = scmp.portfolio_stats()
    
    print(f"Portfolio on {str(datetime.datetime.today().date())}: {portfolio_stats.portfolio_as_text()}")
    print(portfolio_stats.assets_as_text())
    
    


# Create a Click group to hold the commands
@click.group()
def cli():
    pass


# Add the commands to the group
cli.add_command(trade_today)
cli.add_command(portfolio_stats)

if __name__ == "__main__":
    cli()
