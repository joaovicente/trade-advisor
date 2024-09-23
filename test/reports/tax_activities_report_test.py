
import datetime
from models.closed_position import ClosedPosition
from reports.tax_activities_report import TaxActivitiesReport
from test import utils
from test.conftest import abspath

def closed_position_builder(csv):
    csv = csv.split(",")
    return ClosedPosition(
        date=utils.parse_date(csv[0]),
        ticker=csv[1],
        size=float(csv[2]),
        price=float(csv[3]),
        closed_date=utils.parse_date(csv[4]),
        closed_price=float(csv[5])
    )

def test_tax_activities_report_single_window_above_exemption():
    # example from https://www.revenue.ie/en/gains-gifts-and-inheritance/transfering-an-asset/selling-or-disposing-of-shares.aspx
    closed_positions_csv = [
        "2024-01-01,AAPL,2000,1,2024-01-02,1.5", # cost: 2000, gain: 1000
        "2024-02-01,AVGO,1000,1.5,2024-02-02,2", # cost: 1500, gain: 500
    ]
    closed_positions = [closed_position_builder(p) for p in closed_positions_csv]
    report = TaxActivitiesReport(todays_date="2024-07-23", closed_positions=closed_positions, rapid=True)
    assert len(report.windows) == 1
    window = report.windows[0]
    assert window.year == 2024
    assert window.start_month == 1
    assert window.end_month == 11
    assert window.trade_gain[0].ticker == "AAPL"
    assert window.trade_gain[0].date_bought == datetime.date(2024, 1, 1)
    assert window.trade_gain[0].date_sold == datetime.date(2024, 1, 2)
    assert window.trade_gain[0].quantity == 2000
    assert window.trade_gain[0].price_bought == 1
    assert window.trade_gain[0].price_sold == 1.5
    assert window.trade_gain[0].cost_of_shares_sold == 2000
    assert window.trade_gain[0].chargeable_gain == 1000
    assert window.trade_gain[0].ticker == "AVGO"
    assert window.trade_gain[0].date_bought == datetime.date(2024, 2, 1)
    assert window.trade_gain[0].date_sold == datetime.date(2024, 2, 2)
    assert window.trade_gain[0].quantity == 1000
    assert window.trade_gain[0].price_bought == 1.5
    assert window.trade_gain[0].price_sold == 2
    assert window.trade_gain[0].cost_of_shares_sold == 1500
    assert window.trade_gain[0].chargeable_gain == 500
    assert window.trade_gain_total.cost_of_shares_sold == 3500
    assert window.trade_gain_total.chargeable_gain == 1500
    # This example assumes dolar/euro exchange rate is 
    assert window.aggregated_tax.sale_price == 5000
    assert window.aggregated_tax.cost_of_shares_sold == 3500
    assert window.aggregated_tax.chargeable_gain == 230
    assert window.aggregated_tax.personal_exemption == 1270
    assert window.aggregated_tax.taxable_gain == 230
    assert window.aggregated_tax.cgt_to_be_paid == 75.90