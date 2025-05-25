import datetime
import os
from time import sleep
from dotenv import load_dotenv
import pytest
from repositories.file_repository import FileRepository
from services.yfinance_data_service import YfinanceDataService
from services.utils_service import parse_date

TEST_PATH = './test/data/twelve_data_sample_response.json'

def test_transform_api_data_format_to_csv_map():
    """ Verify currency conversions using EUR as base currency, when API default base currency is USD """
    load_dotenv()
    svc = YfinanceDataService()
    api_data = FileRepository(TEST_PATH).load()
    csv_data = svc._transform_api_data_format_to_csv_map(api_data)
    # AAPL stock data (earliest date)
    # "datetime": "2024-08-05",
    # "open": "199.089996",
    # "high": "213.5",
    # "low": "196",
    # "close": "209.27000",
    # "volume": "119548600"
    # expected cvs sequence: open,high,low,close,volume
    assert csv_data['yfinance_data_AAPL.csv'].split('\n')[0] == "2024-08-05,199.089996,213.5,196,209.27000,119548600"
    assert csv_data['yfinance_data_AAPL.csv'].split('\n')[1] == "2024-08-06,205.30000,209.99001,201.070007,207.23000,69660500"
    assert csv_data['yfinance_data_ABBV.csv'].split('\n')[0] == "2024-08-05,187.45000,189.28999,183.039993,184.36000,6459300"
    assert csv_data['yfinance_data_ABBV.csv'].split('\n')[1] == "2024-08-06,185.42999,187.82001,183.080002,185.71001,4273200"
    
@pytest.mark.skip(reason="Uses TwelveData API quota")
def test_download_batch_of_data_from_api():
    load_dotenv()
    svc = YfinanceDataService()
    svc.download_data_from_api("2024-08-05", "2025-05-18")
    
@pytest.mark.skip(reason="Uses TwelveData API quota")
def test_download_batch_of_data_from_api_explicit_tickers():
    load_dotenv()
    svc = YfinanceDataService()
    tickers = "AAPL,ABBV,ADBE,AMD,AMZN,AVGO,BAC,BRK-B,COST,CRM,CVX,GOOG,HD,JNJ,JPM,KO,LLY,MA,META,MRK,MSFT,NFLX,NVDA,ORCL,PEP,PFE,PG,TMO,TSLA,UNH,V,WMT,XOM,AACT,TRGP,THC,AMPY,PCG,BCAB,DIS,FLUT,WCC,SBUX,CVS,LPLA,CRH,SCHW,DG,UBER,FDX,TWLO"
    svc.download_data_from_api("2024-08-05", "2025-05-18", 
                               tickers=tickers,
                               batch_size=7)
    
@pytest.mark.skip(reason="Requires data to have been downloaded from TwelveData API")
def test_check_all_yfinance_data_is_in_s3():
    load_dotenv()
    svc = YfinanceDataService()
    svc._check_all_yfinance_data_is_in_s3("AAPL,ABBV")
    
@pytest.mark.skip(reason="Requires data to have been downloaded from TwelveData API")
def test_download_required_yfinance_data_to_filesystem():
    load_dotenv()
    svc = YfinanceDataService()
    svc.download_required_yfinance_data_to_filesystem("AAPL,ABBV", "/home/joao/code/trade-advisor/temp/deleteme")


   
