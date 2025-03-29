from dataclasses import dataclass
import datetime
import json
import os
from typing import Dict

import requests
from repositories.file_repository import FileRepository
from services.utils_service import date_as_str, date_str_diff_in_days, todays_date, today_as_str

@dataclass
class ExchangeRateCacheEntry:
    last_read_date: str
    read_count: int
    rates: Dict[str, float]

class ExchangeRateService:
    def __init__(self,  
                 base_currency='EUR', 
                 stub=None,
                 path='./test/data/exchange_rate_cache.json', 
                 today_date_str=None # for testing only
                 ):
        # TODO: Update with updated description of the class behavior
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
        self.today_date_str = today_as_str() if today_date_str is None else today_date_str
        self.stub = stub
        if stub is None:
            # store APP_ID
            self.app_id = os.environ.get('OPEN_EXCHANGE_APP_ID', None)
            if self.app_id is None:
                raise Exception(f"Missing environment variable OPEN_EXCHANGE_APP_ID") 
            self.file_repository = FileRepository(path)
            self.cache = self.load_exchange_rate_cache()
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

    def set_path(self, path):
        self.file_repository.set_path(path)
            
    def load_exchange_rate_cache(self) -> Dict[str, ExchangeRateCacheEntry]:
        data_as_str = self.file_repository.load()
        if data_as_str is None:
            data_as_str = "{}"
        data = json.loads(data_as_str)
        # Convert dictionary values to ExchangeRateCacheEntry instances
        return {
            date: ExchangeRateCacheEntry(
                last_read_date=entry["last_read_date"],
                read_count=entry["read_count"],
                rates=entry["rates"]
            )
            for date, entry in data.items()
        }
        
    def save_exchange_rate_cache(self):
        # Convert dataclass instances back to dictionaries for JSON serialization
        # Removing stale cache entries (not used in the last 10 days)
        cache_data = {
            date: entry.__dict__ 
            for date, entry in self.cache.items() 
            if date_str_diff_in_days(self.today_date_str, entry.last_read_date) < 10
        }
        # Convert the data to a JSON string
        json_string = json.dumps(cache_data, indent=4)        
        self.file_repository.save(json_string)

    def validate_rates(self, rates):
        for currency in rates:
            if not isinstance(currency, str):
                raise Exception(f"Currency {currency} is not a string")
            if not isinstance(rates[currency], float):
                raise Exception(f"Rate {rates[currency]} is not a float")
        
    def get_rate(self, from_currency: str, date: datetime.date):
        if date > todays_date():
            date = todays_date()
        date_str = date_as_str(date)
        if self.stub is None:
            if date_str not in self.cache:
                url = f"https://openexchangerates.org/api/historical/{date_str}.json?app_id={self.app_id}"
                response = requests.get(url)
                if response.status_code == 200:
                    rates = response.json().get('rates', None)
                    self.cache[date_str] = ExchangeRateCacheEntry(
                        last_read_date=self.today_date_str,
                        read_count=1,
                        rates=rates
                    )
                else:
                    raise Exception(f"ERROR: ({response.status_code}) fetching data from openexchangerates.org")
            else:
                self.cache[date_str].read_count += 1
                self.cache[date_str].last_read_date = self.today_date_str
            # Supports only EUR as base currency
            if self.base == 'EUR':
                if from_currency == 'USD':
                    exchange_rate = round(1 / self.cache[date_str].rates['EUR'], 5)
                else:
                    # Multi step conversion to EUR from other currencies via USD, as openechangerates.org uses USD as default currency
                    exchange_rate = round( self.cache[date_str].rates[from_currency] * 1 / self.cache[date_str].rates['EUR'], 5)
                return exchange_rate
            else:
                raise Exception(f"Base currency {self.base} is not supported yet")
            return exchange_rate
        else: # supplied exchange rate(s)
            if self.stub_has_wildcard_date:
                return self.stub['*']['rates'][from_currency]
            elif date_str in self.stub:
                return self.stub[date_str]['rates'][from_currency]
            else:
                raise Exception(f"Date {date_str} not found in found for in stub: {self.stub}")
