import click
from services.backtesting import trades_today


@click.command()
@click.argument('tickers')
@click.option('--today', help='mock today\'s date for testing in yyyy-mm-dd format (e.g. --today=2024-07-14')
def trade_today(tickers, today):
    """Advise on trades that should be made today. TICKERS provided as CSV. e.g.: AMZN,GOOG,MSFT)"""
    #TODO: Pass in today's date
    trades_today(tickers)


# Create a Click group to hold the commands
@click.group()
def cli():
    pass


# Add the commands to the group
cli.add_command(trade_today)

if __name__ == "__main__":
    cli()
