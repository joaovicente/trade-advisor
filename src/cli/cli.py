import click
import datetime
from repositories.closed_position_repository import ClosedPositionRepository
from repositories.open_position_repository import OpenPositionRepository
from repositories.selected_tickers_repository import SelectedTickersRepository
from repositories.user_repository import UserRepository
from services.exchange_rate_service import ExchangeRateService
from services.stock_compute_service import StockComputeService
from services.open_position_service import OpenPositionService
from services.trade_today_reporting_service import TradeTodayReportingService
from services.whatsup_notification_service import WhatsappNotificationService
from services.email_notification_service import EmailNotificationService
import os

from services.yfinance_data_service import YfinanceDataService


@click.command()
@click.option('--user', '-u',
              help='Get information for this user storage (e.g. email, selected_stock, open_positions, etc)',
              default=None) 
@click.option('--output', '-o',
              help='Output to either `console` (default),  `email`, `file` or `whatsapp` (e.g. --output=email)',
              default='console') 
@click.option('--rapid', '-r',
              help='skip long operations (e.g. retrieve extra information from external apis)', 
              is_flag=True)
@click.option('--skip-currency-conversion',
              help='skip currency conversions (Will assume 1 US is worth 1 EURO)', 
              is_flag=True)
@click.option('--tickers','-t',
              help='selected TICKERS provided as CSV. e.g.: AMZN,GOOG,MSFT)',
              default=None)
@click.option('--today',
              help='mock today\'s date for testing in yyyy-mm-dd format (e.g. --today=2024-07-14)',
              default=str(datetime.datetime.today().date()))
@click.option('--no-pos', '-n',
              help='do not use open positions for testing', 
              is_flag=True)
@click.option('--context', '--ctx', '-c',
              help='Show provided number of days context for each ticker (deprecating)', 
              show_default=True,
              default=0)
@click.option('--position', '-p',
              help='Provide open positions explicitly as follows -p {date},{ticker},{size},{price} (e.g. -p 2024-07-18,META,2.09692,476.89). Call this multiple times for multiple positions',
              multiple=True) 
def trade_today(tickers, today, no_pos, context, position, output, user, rapid, skip_currency_conversion):
    """Advise on trades that should be made today"""
    email_receiver = None
    open_positions = []
    response = ""
    if user is not None:
        s3_bucket = os.environ.get('TRADE_ADVISOR_S3_BUCKET', None)
        if s3_bucket is None:
            raise click.UsageError("TRADE_ADVISOR_S3_BUCKET environment variable not set")
        if os.environ.get('AWS_ACCESS_KEY_ID') is None:
            raise click.UsageError("AWS_ACCESS_KEY_ID environment variable not set")
        if os.environ.get('AWS_SECRET_ACCESS_KEY') is None:
            raise click.UsageError("AWS_ACCESS_KEY_ID environment variable not set")
        pass
        # Get user info
        users_s3_path = f'{s3_bucket}/users/users.csv'
        user_info = UserRepository(users_s3_path).get_by_id(user)
        #print(user_info)
        if user_info is not None:
            email_receiver = user_info.email
            # Get open_positions
            if no_pos:
                open_positions = []
            else:
                open_positions_s3_path = f'{s3_bucket}/users/{user}/open_positions.csv'
                open_positions = OpenPositionRepository(open_positions_s3_path).get_all()
            # Get selected_tickers
            selected_tickers_s3_path = f'{s3_bucket}/users/{user}/selected_tickers.csv'
            tickers = ",".join(SelectedTickersRepository(selected_tickers_s3_path).get_all_as_list())
            # Get closed_positions
            closed_positions_s3_path = f'{s3_bucket}/users/{user}/closed_positions.csv'
            closed_positions = ClosedPositionRepository(closed_positions_s3_path).get_all()
        else:
            raise click.UsageError(f"user {user} not found")
    else: 
        open_position_service = OpenPositionService()
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
    if skip_currency_conversion:
        # Initialize ExchangeRateService with a stub for testing if skip_currency_conversion is True
        exchange_rate_service = ExchangeRateService(stub={'*': {'rates': {'USD': 1.00, 'CHF': 1.00}}})
    else:
        # Initialize ExchangeRateService
        s3_prefix = get_s3_prefix()
        exchange_rate_service = ExchangeRateService(path=f"{s3_prefix}/services/exchange_rate_service/exchange_rate_cache.json")
    rep_svc = TradeTodayReportingService(today, tickers, open_positions, closed_positions, context, user, rapid=rapid, 
                                         exchange_rate_service=exchange_rate_service)
    # Update ExchangeRateCache with retrived dates (to avoid uneccessary API calls)
    if not skip_currency_conversion:
        exchange_rate_service.save_exchange_rate_cache()
    print(rep_svc.console_report())
    if 'whatsapp' in output:
        WhatsappNotificationService().send_message(rep_svc.whatsapp_report())
        print("Whatsapp report sent")
    elif 'email' in output:
        subject, body = rep_svc.email_html_report()
        EmailNotificationService(email_receiver=email_receiver).send_email(subject, body)
        print("Email report sent")
    elif 'file' in output:
        subject, body = rep_svc.email_html_report(simulation=True)
        print("Email report written to file")
    
            
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

def validate_download_upload_requirements():
    if os.environ.get('AWS_ACCESS_KEY_ID', None) is None:
        raise click.UsageError("AWS_ACCESS_KEY_ID must be set")
    if os.environ.get('AWS_SECRET_ACCESS_KEY', None) is None:
        raise click.UsageError("AWS_SECRET_ACCESS_KEY must be set")

def get_s3_prefix():
    s3_prefix = os.environ.get('TRADE_ADVISOR_S3_BUCKET', None)
    if s3_prefix is None:
        raise click.UsageError("TRADE_ADVISOR_S3_BUCKET environment variable not set")
    return s3_prefix

def check_aws_cli_installed():
    if os.system(f"which aws > /dev/null 2>&1") != 0:
        raise click.UsageError("You must install awscli as per https://docs.aws.amazon.com/cli/v1/userguide/install-macos.html#install-macosos-bundled-no-sudo")
        

@click.command()
@click.option('--user', '-u', 
              required=True,
              help='Download data for a given user into ./local_storage')
def download(user):
    """download data for a given user"""
    s3_prefix = get_s3_prefix()
    check_aws_cli_installed()
    validate_download_upload_requirements()
    command = f"aws s3 sync {s3_prefix}/users/{user} ./local_storage/users/{user}"
    print(command)
    os.system(command)
    
@click.command()
@click.option('--user', '-u', 
              required=True,
              help='Upload data for a given user from ./local_storage. Files in local storage must be structured as follows ./local_storage/users/username/file, where username is your trade-advisor username and files supported are selected_tickers.csv, open_positions.csv and closed_positions.csv')
def upload(user):
    """upload data for a given user"""
    s3_prefix = get_s3_prefix()
    check_aws_cli_installed()
    validate_download_upload_requirements()
    command = f"aws s3 sync ./local_storage/users/{user} {s3_prefix}/users/{user}"
    print(command)
    os.system(command)
   
@click.command()
def download_yfinance_data():
    """Download yfinance data for all users"""
    scmp = StockComputeService(tickers="", todays_date_str=str(datetime.datetime.today().date()), calculate_dates_only=True)
    YfinanceDataService().download_data_from_api(scmp.warmup_date, scmp.end_date)
    
@click.command()
@click.option('--user', '-u', 
              required=True,
              help='Test email')
def test_email(user):
    """test email for a given user"""
    if user is not None:
        s3_bucket = os.environ.get('TRADE_ADVISOR_S3_BUCKET', None)
        if s3_bucket is None:
            raise click.UsageError("TRADE_ADVISOR_S3_BUCKET environment variable not set")
    # Get user info
    users_s3_path = f'{s3_bucket}/users/users.csv'
    user_info = UserRepository(users_s3_path).get_by_id(user)
    if user_info is not None:
        email_receiver = user_info.email
        generated_time = str(datetime.datetime.now()).split('.')[0]
        subject = f"Trade Advisor test email {generated_time}"
        body = f"<p><i>Test email sent on {generated_time}</i></p>"
        EmailNotificationService(email_receiver=email_receiver).send_email(subject, body)
        print(f"Test email sent to {user_info.email}")
    else:
        raise click.UsageError(f"user information for {user} not found")
    
# Create a Click group to hold the commands
@click.group()
def cli():
    pass

# Add the commands to the group
cli.add_command(trade_today)
cli.add_command(portfolio_stats)
cli.add_command(download)
cli.add_command(upload)
cli.add_command(download_yfinance_data)
cli.add_command(test_email)

if __name__ == "__main__":
    cli()
