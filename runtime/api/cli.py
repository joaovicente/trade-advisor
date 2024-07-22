import click
import datetime
from api.services.backtesting_service import TradesToday
from api.services.open_position_service import OpenPositionService


@click.command()
@click.argument('tickers')
@click.option('--today', 
              help='mock today\'s date for testing in yyyy-mm-dd format (e.g. --today=2024-07-14',
              default=str(datetime.datetime.today().date()))
@click.option('--no-pos',
              help='do not use open positions for testing', 
              is_flag=True)
@click.option('--context',
              help='Show the context for each ticker', 
              is_flag=True)
def trade_today(tickers, today, no_pos, context):
    """Advise on trades that should be made today. TICKERS provided as CSV. e.g.: AMZN,GOOG,MSFT)"""
    if no_pos:
        open_positions = []
    else:
        open_positions = OpenPositionService().get_all()
    trades_today = TradesToday(tickers, today, open_positions)
    trades = trades_today.calculate()
    print(f"start_date={trades_today.start_date}, end_date={trades_today.end_date}")
    if trades:
        for trade in trades:
            print(trade.as_text())
    else:
        print("No trades today")
        if context:
            for ticker in tickers.split(','):
                print('\n'.join(trades_today.get_context(ticker)))
            


# Create a Click group to hold the commands
@click.group()
def cli():
    pass


# Add the commands to the group
cli.add_command(trade_today)

if __name__ == "__main__":
    cli()
