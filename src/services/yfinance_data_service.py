import datetime
import json
import os
import boto3
import requests

from repositories.file_repository import FileRepository
from time import sleep

from repositories.selected_tickers_repository import SelectedTickersRepository
from repositories.user_repository import UserRepository

class YfinanceDataService:
    def __init__(self):
        self.s3_prefix = os.environ.get('TRADE_ADVISOR_S3_BUCKET', None)
        if self.s3_prefix is None:
            raise Exception("TRADE_ADVISOR_S3_BUCKET environment variable not set")
        self.path_to_yfinance_data_in_s3 = f"{self.s3_prefix}/services/yfinance"

    def _transform_api_data_format_to_csv_map(self, api_data: str) -> dict:
        # Returns a dictionary with the key as file name and the value as the csv data
        input_data = json.loads(api_data)
        output = {}
        for ticker, data in input_data.items():
            values = sorted(data["values"], key=lambda x: x["datetime"])
            rows = [f'{v["datetime"]},{v["open"]},{v["high"]},{v["low"]},{v["close"]},{v["volume"]}' for v in values]
            output[f"yfinance_data_{ticker.replace('.','-')}.csv"] = "\n".join(rows)
        return output

    def _download_next_batch_of_data_from_api(self, start_date, end_date, tickers) -> str:
        reformatted_tickers = tickers.replace("-", ".")
        url = "https://api.twelvedata.com/time_series"
        params = {
            "symbol": reformatted_tickers,
            "interval": "1day",
            "start_date": start_date,
            "end_date": end_date,
            "apikey": self.api_key
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to download data from TwelveData API ({response.status_code}): {response.text}")
        return response.text

    def download_data_from_api(self, start_date, end_date, tickers=None, batch_size=7) -> str:
        """
        Transforms API data from the TwelveData time_series endpoint into a yfinance compatible csv files
        Retrieves data from the TwelveData API in batches spaced in 1 minute intervals to avoid rate limits.
        Args:
            start_date (str): Start date for the data retrieval in 'YYYY-MM-DD' format.
            end_date (str): End date for the data retrieval in 'YYYY-MM-DD' format.
            tickers (list, optional): List of ticker symbols to retrieve data for. If None, will use user selected tickers.
        """    
        # get list of selected_stock (for all users) unless provided (provided means caller is managing the list)
        self.api_key = os.environ.get('TWELVEDATA_API_KEY', None)
        if self.api_key is None:
            raise Exception("TWELVEDATA_API_KEY environment variable not set")
        # Get list of selected tickers from user repository
        self.selected_tickers = []
        users = [user.id for user in UserRepository(f"{self.s3_prefix}/users/users.csv").get_all() if user.id not in ['test', 'utest', 'blank', 'bugfix']]
        for user in users:
            self.selected_tickers += SelectedTickersRepository(f"{self.s3_prefix}/users/{user}/selected_tickers.csv").get_all_as_list()
        self.selected_list = list(set(self.selected_tickers)) 
        if tickers is None:
            tickers_remaining = self.selected_tickers
        else:
            tickers_remaining = tickers.split(',')
        while len(tickers_remaining) > 0:
            tickers_to_retrieve = tickers_remaining[:batch_size]
            tickers_remaining = tickers_remaining[batch_size:]
            api_data = self._download_next_batch_of_data_from_api(start_date, end_date, ",".join(tickers_to_retrieve))
            csv_map = self._transform_api_data_format_to_csv_map(api_data)
            for file_name, csv_data in csv_map.items():
                FileRepository(f"{self.path_to_yfinance_data_in_s3}/{file_name}").save(csv_data)
            print(f"Downloaded {len(csv_map)} tickers {tickers_to_retrieve} from TwelveData and uploaded yfinance files to S3 ({len(tickers_remaining)} remaining).")
            if len(tickers_remaining) > 0:
                print("Pausing next for 60 seconds to avoid rate limits")
                sleep(60)
                
    def _check_all_yfinance_data_is_in_s3(self, tickers):
        """
        Checks if all expected yfinance data files for the given tickers are present and up-to-date in the specified S3 bucket.
        Args:
            tickers (str): A comma-separated string of ticker symbols (e.g., "AAPL,GOOG,MSFT").
        Raises:
            Exception: If no yfinance data is found in S3.
            Exception: If any expected yfinance data files are missing in S3.
            Exception: If any yfinance data files in S3 are not up to date (i.e., last modified date is before today).
        Returns:
            list: A list of S3 object entries corresponding to the required yfinance data files.
            {'Key': 'services/yfinance/yfinance_data_AAPL.csv', 'LastModified': datetime.datetime(2025, 5, 25, 9, 33, 42, tzinfo=tzutc()), 'ETag': '"45aac209401d91d6d1a5edb72949c58a"', 'ChecksumAlgorithm': ['CRC64NVME'], 'Size': 590, 'StorageClass': 'STANDARD'}
        """
        s3 = boto3.client('s3')
        today = datetime.datetime.today().date()
        path_to_files = "services/yfinance/"
        tickers = tickers.split(",")
        expected_ticker_files = [f"{path_to_files}yfinance_data_{ticker}.csv" for ticker in tickers]
        response = s3.list_objects_v2(Bucket=self.s3_prefix.replace('s3://',''), Prefix=path_to_files)
        if 'Contents' not in response:
            raise Exception("No yfinance data found in S3")
        entries_in_s3 = [entry for entry in response['Contents']]
        
        # Check all required files are present in S3
        missing_files = [file for file in expected_ticker_files if file not in [entry['Key'] for entry in entries_in_s3]]
        if len(missing_files) > 0:
            raise Exception(f"Missing yfinance data files in S3: {missing_files}")
        required_s3_files_entries = [entry for entry in response['Contents'] if entry['Key'] in expected_ticker_files]
        # Check all files are up to date
        for entry in required_s3_files_entries:
            if entry['LastModified'].date() < today:
                raise Exception(f"yfinance data file {entry['Key']} is not up to date in S3, last modified on {entry['LastModified'].date()} (today is {today})")
        return required_s3_files_entries
    
    def _download_yfinance_data_from_s3(self, s3_files_entries, temp_directory=None):   
        """
        Downloads the yfinance data files from the specified S3 bucket and saves them to the local file system.
        Args:
            s3_files_entries (list): A list of S3 object entries corresponding to the yfinance data files to download.
        """
        s3 = boto3.client('s3')
        # Create temp directory using tempfile.TemporaryDirectory()
        for entry in s3_files_entries:
            file_name = entry['Key'].split('/')[-1]
            response = s3.get_object(Bucket=self.s3_prefix.replace('s3://', ''), Key=entry['Key'])
            content = response['Body'].read().decode('utf-8')
            FileRepository(f"{temp_directory}/{file_name}").save(content)

    def download_required_yfinance_data_to_filesystem(self, tickers, temp_directory) -> str:
        # Ensure yfinance files in s3 are up to date (refreshed today)
        s3_files_entries = self._check_all_yfinance_data_is_in_s3(tickers)
        # Download yfinance-data-store data files to tempfile.TemporaryDirectory()
        self._download_yfinance_data_from_s3(s3_files_entries, temp_directory)