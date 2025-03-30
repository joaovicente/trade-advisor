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
    WILCARD_DATE_STUB_EXAMPLE = { '*': {'rates': {'USD': 1.01, 'CHF': 1.02}} }
    MULTI_DATE_STUB_EXAMPLE = {
        '2025-01-01': {'rates': {'USD': 1.01, 'CHF': 1.02}},
        '2025-01-02': {'rates': {'USD': 1.03, 'CHF': 1.04}}
    }
    def __init__(self,  
                 base_currency='EUR', 
                 stub=None,
                 path=None, 
                 today_date_str=None # for testing only
                 ):
        """
        ExchangeRateService uses Open Exchange Rates API to fetch exchange rates.
        
        Initializes the ExchangeRateService with the given parameters.
        
        Args:
            base_currency (str): The base currency for conversion (default is 'EUR').
            stub (dict): Supplies data for testing. see `WILCARD_DATE_STUB_EXAMPLE` and `MULTI_DATE_STUB_EXAMPLE`
            path (str): The path to the cache file for exchange rates. (s3://.../myfile.json or ./.../myfile.json)
            today_date_str (str): The date string for today (for testing only).
           
        ExchangeRateService uses the https://docs.openexchangerates.org/reference/latest-json endpoint to get the latest exchange rates.\n
        Given changing base currency (default is USD) requires additional licensing, this class uses USD base currency.\n
        It caches the results in a local file to avoid repeated API calls.\n
        Cache structure is as follows:\n
        .. code-block:: json
            {
                "2025-01-01": {
                    "last_read_date": "2025-01-01",
                    "read_count": 1,
                    "rates": {
                        "USD": 1.01,
                        "CHF": 1.02
                    }
                },
                "2025-01-02": {
                    "last_read_date": "2025-01-11",
                    "read_count": 20,
                    "rates": {
                        "USD": 1.03,
                        "CHF": 1.04
                    }
                }
            }
        """
        self.base = base_currency
        self.today_date_str = today_as_str() if today_date_str is None else today_date_str
        self.stub = stub
        if stub is None:
            # Ensure path is provided
            if path is None:
                raise Exception(f"Missing path for exchange rate cache")
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

    def get_rate(self, from_currency: str, date: datetime.date) -> float:
        """
        Gets the exchange rate for the given currency for a given date.

        Args:
            from_currency (str): The currency to convert from.
            date (datetime.date): The date for which to get the exchange rate.

        Returns:
            float: The exchange rate.
        """
        exchange_rate = None
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
            
    def set_path(self, path):
        """
        Used for testing only. Sets the path for the file repository.
        """
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
        """
        Saves the exchange rate cache to the file.\n
        Updates the cache file with the current state of the cache.\n
        Removes stale cache entries (not used in the last 10 days).\n
        Should be called after when application have completed all its currency conversion tasks and is about to exit.\n
        """
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
        