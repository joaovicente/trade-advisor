import click
import datetime
from api.services.backtesting_service import trades_today
from api.services.open_position_service import OpenPositionService


@click.command()
@click.argument('tickers')
@click.option('--today', 
              help='mock today\'s date for testing in yyyy-mm-dd format (e.g. --today=2024-07-14',
              default=str(datetime.datetime.today().date()))
def trade_today(tickers, today):
    """Advise on trades that should be made today. TICKERS provided as CSV. e.g.: AMZN,GOOG,MSFT)"""
    trades = trades_today(tickers, today, OpenPositionService().get_all())
    for trade in trades:
        print(trade)


# Create a Click group to hold the commands
@click.group()
def cli():
    pass


# Add the commands to the group
cli.add_command(trade_today)

if __name__ == "__main__":
    cli()
