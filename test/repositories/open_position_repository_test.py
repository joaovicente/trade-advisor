import os
import datetime
import warnings
from test.conftest import abspath

from repositories.open_position_repository import OpenPositionRepository

def test_open_position_repository_filesystem():
    path = os.path.join(abspath, "data", "open_positions.csv")
    repo = OpenPositionRepository(path=path)
    positions = repo.get_all()
    assert positions[0].date == datetime.date(2000, 1, 1)
    assert positions[0].ticker == "FAKE"
    assert positions[0].size == 20.0
    assert positions[0].price == 30.0
    
def test_open_position_repository_s3():
    if os.environ.get('AWS_ACCESS_KEY_ID') is None or os.environ.get('AWS_SECRET_ACCESS_KEY') is None or os.environ.get('TRADE_ADVISOR_S3_BUCKET') is None:
        warnings.warn(UserWarning("AWS tests skipped as no credentials in environment"))
        return
    s3_bucket = os.environ.get('TRADE_ADVISOR_S3_BUCKET', None)
    path = f"{s3_bucket}/users/utest/open_positions.csv"
    repo = OpenPositionRepository(path=path)
    positions = repo.get_all()
    assert positions[0].date == datetime.date(2024, 7, 18)
    assert positions[0].ticker == "AMZN"
    assert positions[0].size == 2.68962
    assert positions[0].price == 185.90