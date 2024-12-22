
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
    report = TaxActivitiesReport(todays_date="2024-07-23", 
                                 closed_positions=closed_positions, 
                                 rapid=True,
                                 fixed_forex_pct=1
                                 )
    assert len(report.windows) == 1
    window = report.windows[0]
    assert window.year == 2024
    assert window.start_month == 1
    assert window.end_month == 11
    assert window.trade_gain_items[0].ticker == "AAPL"
    assert window.trade_gain_items[0].date_bought == datetime.date(2024, 1, 1)
    assert window.trade_gain_items[0].date_sold == datetime.date(2024, 1, 2)
    assert window.trade_gain_items[0].quantity == 2000
    assert window.trade_gain_items[0].price_bought == 1
    assert window.trade_gain_items[0].price_sold == 1.5
    assert window.trade_gain_items[0].sale_price == 3000
    assert window.trade_gain_items[0].cost_of_shares_sold == 2000
    assert window.trade_gain_items[0].chargeable_gain == 1000
    assert window.trade_gain_items[1].ticker == "AVGO"
    assert window.trade_gain_items[1].date_bought == datetime.date(2024, 2, 1)
    assert window.trade_gain_items[1].date_sold == datetime.date(2024, 2, 2)
    assert window.trade_gain_items[1].quantity == 1000
    assert window.trade_gain_items[1].price_bought == 1.5
    assert window.trade_gain_items[1].price_sold == 2
    assert window.trade_gain_items[1].sale_price == 2000
    assert window.trade_gain_items[1].cost_of_shares_sold == 1500
    assert window.trade_gain_items[1].chargeable_gain == 500
    assert window.trade_gain_total.cost_of_shares_sold == 3500
    assert window.trade_gain_total.chargeable_gain == 1500
    # This example assumes dolar/euro exchange rate is 
    assert window.aggregated_tax.sale_price == 5000
    assert window.aggregated_tax.cost_of_shares_sold == 3500
    assert window.aggregated_tax.chargeable_gain == 1500
    assert window.aggregated_tax.personal_exemption == 1270
    assert window.aggregated_tax.taxable_gain == 230
    assert window.aggregated_tax.cgt_to_be_paid == 75.90
    output = "<html>" + report.get_tax_activities_html_report() + "</html>"
    with open('temp/test_tax_activities_report.html', 'w') as file:
        file.write(output)
        

def test_tax_activities_report_temp():
    # example from https://www.revenue.ie/en/gains-gifts-and-inheritance/transfering-an-asset/selling-or-disposing-of-shares.aspx
    closed_positions_csv = [
        "2024-01-01,AAPL,2000,1,2024-01-02,1.5", # cost: 2000, gain: 1000
        "2024-02-01,AVGO,1000,1.5,2024-02-02,2", # cost: 1500, gain: 500
    ]
    closed_positions = [closed_position_builder(p) for p in closed_positions_csv]
    report = TaxActivitiesReport(todays_date="2024-09-25", 
                                 closed_positions=closed_positions)
    assert len(report.windows) == 1
    window = report.windows[0]
    assert window.year == 2024
    assert window.start_month == 1
    assert window.end_month == 11
    assert window.trade_gain_items[0].ticker == "AAPL"
    assert window.trade_gain_items[0].date_bought == datetime.date(2024, 1, 1)
    assert window.trade_gain_items[0].date_sold == datetime.date(2024, 1, 2)
    assert window.trade_gain_items[0].quantity == 2000
    assert window.trade_gain_items[0].price_bought == 1
    assert window.trade_gain_items[0].price_sold == 1.5
    assert window.trade_gain_items[0].sale_price == 3000
    assert window.trade_gain_items[0].cost_of_shares_sold == 2000
    assert window.trade_gain_items[0].chargeable_gain == 1000
    assert window.trade_gain_items[1].ticker == "AVGO"
    assert window.trade_gain_items[1].date_bought == datetime.date(2024, 2, 1)
    assert window.trade_gain_items[1].date_sold == datetime.date(2024, 2, 2)
    assert window.trade_gain_items[1].quantity == 1000
    assert window.trade_gain_items[1].price_bought == 1.5
    assert window.trade_gain_items[1].price_sold == 2
    assert window.trade_gain_items[1].sale_price == 2000
    assert window.trade_gain_items[1].cost_of_shares_sold == 1500
    assert window.trade_gain_items[1].chargeable_gain == 500
    assert window.trade_gain_total.cost_of_shares_sold == 3500
    assert window.trade_gain_total.chargeable_gain == 1500
    # This example assumes dolar/euro exchange rate is 1
    #assert window.aggregated_tax.sale_price == 5000
    #assert window.aggregated_tax.cost_of_shares_sold == 3500
    #assert window.aggregated_tax.chargeable_gain == 1500
    #assert window.aggregated_tax.personal_exemption == 1270
    #assert window.aggregated_tax.taxable_gain == 230
    #assert window.aggregated_tax.cgt_to_be_paid == 75.90
    output = "<html>" + report.get_tax_activities_html_report() + "</html>"
    with open('temp/test_tax_activities_report.html', 'w') as file:
        file.write(output)
        
        
        
def test_tax_activities_report_carried_losses():
    # example from https://youtu.be/YorwaTXEPYI?t=330&si=9NycM_LC7AYKFZid
    closed_positions_csv = [
        #date,ticker,size,price,close_date,close_price
        #"2023-12-01,SPOT,1000,1,2024-01-02,0.5", # cost: 1000, loss:  500
        "2024-08-01,BRK-B,1000,1,2024-02-02,5",  # cost: 1000, gain: 4000
        "2024-12-30,AAPL,1000,1,2024-01-02,0.5", # cost: 1000, loss:  500
    ]
    closed_positions = [closed_position_builder(p) for p in closed_positions_csv]
    fixed_forex_pct_values = [2, 1]
    for fixed_forex_pct in fixed_forex_pct_values:
        report = TaxActivitiesReport(todays_date="2024-12-31", 
                                    closed_positions=closed_positions, rapid=True, fixed_forex_pct=fixed_forex_pct)
        assert len(report.windows) == 1
        window = report.windows[0]
        assert window.year == 2024
        assert window.start_month == 1
        assert window.end_month == 11
        assert window.trade_gain_items[0].ticker == "BRK-B"
        assert window.trade_gain_items[0].cost_of_shares_sold == 1000
        assert window.trade_gain_items[0].chargeable_gain == 4000
        assert window.trade_gain_items[1].ticker == "AAPL"
        assert window.trade_gain_items[1].cost_of_shares_sold == 1000
        assert window.trade_gain_items[1].chargeable_gain == -500
        assert window.trade_gain_total.cost_of_shares_sold == 2000
        assert window.trade_gain_total.chargeable_gain == 3500
        # Tax calculation (considers Dollar to Euro exchange)
        assert window.aggregated_tax.cost_of_shares_sold == 2000 / fixed_forex_pct
        assert window.aggregated_tax.chargeable_gain == 3500 / fixed_forex_pct
        assert window.aggregated_tax.personal_exemption == 1270 
        assert window.aggregated_tax.taxable_gain == 3500/fixed_forex_pct - 1270
        assert window.aggregated_tax.cgt_to_be_paid == round((3500/fixed_forex_pct - 1270)*0.33, 2)
    
    # TODO: Learn where figures go in GC1 (see https://youtu.be/YorwaTXEPYI?si=2FUa-ulGvOt02xin)
    output = "<html>" + report.get_tax_activities_html_report() + "</html>" 
    #+ "<p>How to fill CG1 from</p>" \
    #+ f"<p>section 1(a): Sale Price: {window.aggregated_tax.chargeable_gain} </p>" \
    #+ f"<p>section 1(l): Sale Price: {window.aggregated_tax.chargeable_gain} </p>" \
    #+ f"<p>section 7(self): Chargeable gain before relief: {window.aggregated_tax.chargeable_gain} </p>" \
    
    with open('temp/test_tax_activities_report.html', 'w') as file:
        file.write(output)
        
    # TODO: Test model and output for 3 windows: 1) Jan-Nov 2) Nov-Dec 3) Oct
    # TODO: Test model and output for 4 windows: 0) Previous year losses 1) Jan-Nov 2) Nov-Dec 3) Oct