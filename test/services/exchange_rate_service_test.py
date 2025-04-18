import datetime
import os
from dotenv import load_dotenv
import pytest
from services.exchange_rate_service import ExchangeRateService
from services.utils_service import parse_date

TEST_PATH = './test/data/exchange_rate_cache.json'
TEST_TMP_PATH = './test/data/tmp/exchange_rate_cache.json'

def test_exchange_rate_service_stub_with_wildcard_date():
    stub = ExchangeRateService.WILCARD_DATE_STUB_EXAMPLE
    svc = ExchangeRateService(base_currency='EUR', stub=stub)
    assert svc.get_rate('USD', datetime.date(2025, 1, 13)) == 1.01
    assert svc.get_rate('CHF', datetime.date(2025, 1, 14)) == 1.02
    
def test_exchange_rate_service_stub_with_specific_dates():
    stub = ExchangeRateService.MULTI_DATE_STUB_EXAMPLE
    svc = ExchangeRateService(base_currency='EUR', stub=stub)
    assert svc.get_rate('USD', datetime.date(2025, 1, 1)) == 1.01
    assert svc.get_rate('CHF', datetime.date(2025, 1, 1)) == 1.02
    assert svc.get_rate('USD', datetime.date(2025, 1, 2)) == 1.03
    assert svc.get_rate('CHF', datetime.date(2025, 1, 2)) == 1.04
    
def test_exchange_rate_service_stub_with_no_path():
    with pytest.raises(Exception, match="Missing path for exchange rate cache"):
        ExchangeRateService(base_currency='EUR')
    
    
def test_filesystem_cache_reading():
    load_dotenv()
    svc = ExchangeRateService(path=TEST_PATH)
    assert svc.cache['2025-01-01'].read_count == 1
    assert svc.cache['2025-01-01'].last_read_date == "2025-01-01"
    assert svc.cache['2025-01-01'].rates['EUR'] == 0.966096
    assert svc.cache['2025-01-01'].rates['CHF'] == 0.907733
    assert svc.cache['2025-01-02'].read_count == 20
    assert svc.cache['2025-01-02'].last_read_date == "2025-01-11"
    assert svc.cache['2025-01-02'].rates['EUR'] == 0.973909
    assert svc.cache['2025-01-02'].rates['CHF'] == 0.912095
    
def test_cache_update_on_filesystem():
    load_dotenv()
    svc = ExchangeRateService(
        path=TEST_PATH,
        today_date_str='2025-01-12'
        )
    # Given a Stale cache entry
    assert svc.cache['2025-01-01'].last_read_date == "2025-01-01"
    # And Recently accessed cache entry
    assert svc.cache['2025-01-02'].last_read_date == "2025-01-11"
    assert svc.cache['2025-01-02'].read_count == 20
    # When Recently accessed entry is accessed '2025-01-02' one more time
    svc.get_rate('USD', parse_date('2025-01-02'))
    # And the cache is updated
    svc.set_path('./test/data/tmp/exchange_rate_cache.json')
    svc.save_exchange_rate_cache()
    # And reloaded
    svc = ExchangeRateService(
        path='./test/data/tmp/exchange_rate_cache.json', 
        today_date_str='2025-01-13'
        )
    # Then Stale entry will have been flushed
    assert '2025-01-01' not in svc.cache
    # And Recent entry to stay in cache
    assert '2025-01-02' in svc.cache
    # And Recent entry last_read_date to be updated to '2025-01-12'
    assert svc.cache['2025-01-02'].last_read_date == "2025-01-12"
    # And Recent entry read_count to be incremented by 1
    assert svc.cache['2025-01-02'].read_count == 21
    
@pytest.mark.skip(reason="Uses S3 API")
def test_s3_read_and_write():
    load_dotenv()
    s3_bucket_path = os.environ.get('TRADE_ADVISOR_S3_BUCKET', None)
    path = s3_bucket_path + '/tmp/exchange_rate_cache.json' 
    svc = ExchangeRateService(path = path, today_date_str='2025-01-12')
    svc.get_rate('USD', parse_date('2025-01-02'))
    svc.save_exchange_rate_cache()
    svc = ExchangeRateService(path = path, today_date_str='2025-01-12')
    assert '2025-01-02' in svc.cache
    
@pytest.mark.skip(reason="Uses quota from API")
def test_cache_miss():
    load_dotenv()
    svc = ExchangeRateService(
        path=TEST_PATH,
        today_date_str='2025-01-12'
        )
    svc.get_rate('USD', parse_date('2025-01-03'))
    svc.set_path(TEST_TMP_PATH)
    assert '2025-01-03' in svc.cache
    assert svc.cache['2025-01-03'].rates['EUR'] == 0.969697
     
def test_get_rate_using_eur_base():
    """ Verify currency conversions using EUR as base currency, when API default base currency is USD """
    load_dotenv()
    svc = ExchangeRateService(base_currency='EUR', path=TEST_PATH)
    E_EUR = 0.966096
    E_CHF = 0.907733
    us_to_eur = round(1 / E_EUR, 5)
    chf_to_eur = round(E_CHF * (1 / E_EUR), 5)
    assert svc.get_rate(from_currency='USD', date=datetime.date(2025, 1, 1)) == us_to_eur
    assert svc.get_rate(from_currency='CHF', date=datetime.date(2025, 1, 1)) == chf_to_eur
    assert svc.get_rate(from_currency='EUR', date=datetime.date(2025, 1, 1)) == 1.0