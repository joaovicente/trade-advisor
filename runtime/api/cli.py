import click
from services.backtesting import trades_today


@click.command()
@click.argument('tickers')
def trade_today(tickers):
    """Advise on trades that should be made today. Format tickers as CSV e.g.: AMZN,GOOG,MSFT"""
    click.echo("TODO: Advise on trades that should be made today")
    trades_today(tickers)


# Create a Click group to hold the commands
@click.group()
def cli():
    pass


# Add the commands to the group
cli.add_command(trade_today)

if __name__ == "__main__":
    cli()
