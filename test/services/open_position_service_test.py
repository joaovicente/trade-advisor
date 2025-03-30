from models.open_position import OpenPosition
from services.open_position_service import OpenPositionService
from test.utils import *

def test_set_position():
    svc = OpenPositionService()
    svc.add_position(position_csv="2024-07-18,META,2.09692,476.89,USD")
    svc.add_position(position_csv="2024-07-18,GOOG,5.56917,179.56,USD")
    positions = svc.get_all()
    assert len(positions) == 2
    assert positions[0].date == parse_date("2024-07-18")
    assert positions[0].ticker == "META"
    assert positions[0].size == 2.09692
    assert positions[0].price == 476.89
    assert positions[0].currency == "USD"
    assert positions[0].date == parse_date("2024-07-18")
    assert positions[1].ticker == "GOOG"
    assert positions[1].size == 5.56917
    assert positions[1].price == 179.56
    assert positions[1].currency == "USD"
