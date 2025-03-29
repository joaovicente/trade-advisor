import os
import datetime
import warnings

import pytest
from test.conftest import abspath

from repositories.closed_position_repository import ClosedPositionRepository

def test_open_position_repository_filesystem():
    path = os.path.join(abspath, "data", "closed_positions.csv")
    repo = ClosedPositionRepository(path=path)
    positions = repo.get_all()
    assert positions[0].date == datetime.date(2000, 1, 1)
    assert positions[0].ticker == "AMZN"
    assert positions[0].size == 20.0
    assert positions[0].price == 30.0
    assert positions[0].currency == "USD"
    assert positions[0].closed_date == datetime.date(2001, 1, 1)
    assert positions[0].closed_price == 31.0
    assert positions[1].date == datetime.date(2000, 1, 1)
    assert positions[1].ticker == "NOVN"
    assert positions[1].size == 20.0
    assert positions[1].price == 30.0
    assert positions[1].currency == "CHF"
    assert positions[1].closed_date == datetime.date(2001, 1, 1)
    assert positions[1].closed_price == 31.0

    
def test_open_position_repository_filesystem_fail_invalid_currency():
    path = os.path.join(abspath, "data", "closed_positions_invalid_currency.csv")
    repo = ClosedPositionRepository(path=path)
    # This file contains an invalid currency code "AAA"
    with pytest.raises(ValueError, match="Invalid currency: AAA"):
        positions = repo.get_all()
    
def test_open_position_repository_s3():
    if os.environ.get('AWS_ACCESS_KEY_ID') is None or os.environ.get('AWS_SECRET_ACCESS_KEY') is None or os.environ.get('TRADE_ADVISOR_S3_BUCKET') is None:
        warnings.warn(UserWarning("AWS tests skipped as no credentials in environment"))
        return
    s3_bucket = os.environ.get('TRADE_ADVISOR_S3_BUCKET', None)
    path = f"{s3_bucket}/users/utest/open_positions.csv"
    repo = ClosedPositionRepository(path=path)
    positions = repo.get_all()
    assert positions[0].date == datetime.date(2024, 7, 18)
    assert positions[0].ticker == "AMZN"
    assert positions[0].size == 2.68962
    assert positions[0].price == 185.90