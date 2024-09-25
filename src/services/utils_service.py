
from datetime import datetime

def parse_date(date_string):
    return (datetime.strptime(date_string, "%Y-%m-%d")).date()

def date_as_str(date):
    return str(date)

def today_as_str():
    return str(datetime.today().date())

def todays_date():
    return datetime.today().date()