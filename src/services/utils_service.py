
from datetime import datetime

date_format = "%Y-%m-%d"

def parse_date(date_string):
    return (datetime.strptime(date_string, date_format)).date()

def date_as_str(date):
    return str(date)

def today_as_str():
    return str(datetime.today().date())

def todays_date():
    return datetime.today().date()

def date_str_diff_in_days(date1, date2):
    return (datetime.strptime(date1, date_format) - datetime.strptime(date2, date_format)).days