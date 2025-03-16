import datetime
from services.exchange_rate_service import ExchangeRateService

def test_exchange_rate_service_with_wildcard_date():
    stub = {
        '*': {'rates': {'USD': 1.01, 'CHF': 1.02}}
    }
    svc = ExchangeRateService(base_currency='EUR', stub=stub)
    assert svc.get_rate('USD', datetime.date(2025, 1, 13)) == 1.01
    assert svc.get_rate('CHF', datetime.date(2025, 1, 14)) == 1.02
    
def test_exchange_rate_service_with_specific_dates():
    stub = {
        '2025-01-01': {'rates': {'USD': 1.01, 'CHF': 1.02}},
        '2025-01-02': {'rates': {'USD': 1.03, 'CHF': 1.04}}
    }
    svc = ExchangeRateService(base_currency='EUR', stub=stub)
    assert svc.get_rate('USD', datetime.date(2025, 1, 1)) == 1.01
    assert svc.get_rate('CHF', datetime.date(2025, 1, 1)) == 1.02
    assert svc.get_rate('USD', datetime.date(2025, 1, 2)) == 1.03
    assert svc.get_rate('CHF', datetime.date(2025, 1, 2)) == 1.04