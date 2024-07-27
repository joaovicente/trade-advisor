import click
import datetime
from services.stock_compute_service import StockComputeService
from services.open_position_service import OpenPositionService


@click.command()
@click.option('--tickers','-t',
              help='TICKERS provided as CSV. e.g.: AMZN,GOOG,MSFT)',
              default=','.join(OpenPositionService().get_distinct_tickers_list()))
@click.option('--today',
              help='mock today\'s date for testing in yyyy-mm-dd format (e.g. --today=2024-07-14',
              default=str(datetime.datetime.today().date()))
@click.option('--no-pos', '-n',
              help='do not use open positions for testing', 
              is_flag=True)
@click.option('--context', '--ctx', '-c',
              help='Show provided number of days context for each ticker', 
              show_default=True,
              default=0)
def trade_today(tickers, today, no_pos, context):
    """Advise on trades that should be made today. """
    if no_pos:
        open_positions = []
    else:
        open_positions = OpenPositionService().get_all()
    scmp = StockComputeService(tickers, today, open_positions)
    trades = scmp.trades_today()
    #print(f"start_date={trades_today.start_date}, end_date={trades_today.end_date}")
    if trades:
        for trade in trades:
            print(trade.as_text())
    else:
        print(f"No trades today ({str(datetime.datetime.today().date())})")
        if context:
            for ticker in tickers.split(','):
                print('\n'.join(scmp.get_stock_daily_stats_list_as_text(ticker, context)))
            


# Create a Click group to hold the commands
@click.group()
def cli():
    pass


# Add the commands to the group
cli.add_command(trade_today)

if __name__ == "__main__":
    cli()
