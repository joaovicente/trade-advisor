import os
import datetime
from test.conftest import abspath

from repositories.open_position_repository import OpenPositionRepository

def test_open_position_repository():
    path = os.path.join(abspath, "data", "open_position.csv")
    repo = OpenPositionRepository(path=path)
    positions = repo.get_all()
    assert positions[0].date == datetime.date(2000, 1, 1)
    assert positions[0].ticker == "FAKE"
    assert positions[0].size == 20.0
    assert positions[0].price == 30.0