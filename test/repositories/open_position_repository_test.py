import os
import datetime
from runtime.api.repositories.open_position_repository import OpenPositionRepository

def test_open_position_repository():
    path = os.path.join("test","data", "open_position.csv")
    repo = OpenPositionRepository(path=path)
    positions = repo.get_all()
    assert positions[0].date == datetime.date(2024, 6, 18)
    assert positions[0].ticker == "SNOW"
    assert positions[0].size == 24.304851
    assert positions[0].price == 130.49