import datetime
import os

import requests
from services.utils_service import date_as_str, todays_date, parse_date

class ExchangeRateService:
    def __init__(self,  base_currency='EUR', stub=None):
        #// self returns a dictionary of exchange rates for provided date to a base currency, e.g.
        #   {
        #     'date': '2022-11-30',
        #     'base': 'EUR',
        #     'rates': {'USD': 1.01, 'CHF': 1.02"}
        #   }
        #   similar to https://docs.openexchangerates.org/reference/set-base-currency#basic-request--response
        # 
        # One can supply a stub providing fixed rate stub
        # 1) stub rates regardless of input date:
        #   { 
        #       '*': {'rates': {'USD': 1.01, 'CHF': 1.02"}}
        #   }
        # 2) stub rates per date:
        #   { 
        #       '2022-11-30': {'rates': {'USD': 1.01, 'CHF': 1.02"}},
        #       '2022-12-31': {'rates': {'USD': 1.00, 'CHF': 1.03"}}
        #   }
        self.base = base_currency
        if stub is None:
            # store APP_ID
            self.app_id = os.environ.get('OPEN_EXCHANGE_APP_ID', None)
            if self.app_id is None:
                raise Exception(f"Missing environment variable OPEN_EXCHANGE_APP_ID") 
        else:
            # Check for wildcard date stub 
            self.stub_has_wildcard_date = '*' in stub
            if self.stub_has_wildcard_date:
                if 'rates' not in stub['*']:
                    raise Exception(f"Missing 'rates' key in wildcard date stub")
                self.validate_rates(stub['*']['rates'])
            else:
                # Check non wildcard_date have 'rates' key
                for date in stub:
                    if 'rates' not in stub[date]:
                        raise Exception(f"Missing 'rates' key in stub for date {date}")
                    self.validate_rates(stub[date]['rates'])
            self.stub = stub

    def validate_rates(self, rates):
        for currency in rates:
            if not isinstance(currency, str):
                raise Exception(f"Currency {currency} is not a string")
            if not isinstance(rates[currency], float):
                raise Exception(f"Rate {rates[currency]} is not a float")
        
    def get_rate(self, currency: str, date: datetime.date):
        if date > todays_date():
            date = todays_date()
        date_str = date_as_str(date)
        if self.stub is None:
            url = f"https://openexchangerates.org/api/historical/{date_str}.json?app_id={self.app_id}"
            response = requests.get(url)
            # TODO: Convert historical base='USD' response to supplied base_currency
            if response.status_code == 200:
                data = response.json()
                exchange_rate = round(1 / data['rates']['EUR'], 5)
            else:
                exchange_rate = 1
                print(f"ERROR: ({response.status_code}) fetching data from openexchangerates.org")
            return exchange_rate
        else: # supplied exchange rate(s)
            if self.stub_has_wildcard_date:
                return self.stub['*']['rates'][currency]
            elif date_str in self.stub:
                return self.stub[date_str]['rates'][currency]
            else:
                raise Exception(f"Date {date_str} not found in found for in stub: {self.stub}")
