from models.closed_position import ClosedPosition
from services.exchange_rate_service import ExchangeRateService
from services.tax_calculator_service import TaxCalculatorService
from test import utils

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
   
def exchange_rate_service_with_multi_date_stub():
    return ExchangeRateService(stub= {
                '2022-11-30': {'rates': {'USD': 1.04235}},
                '2022-12-31': {'rates': {'USD': 1.07265}},
                '2023-11-30': {'rates': {'USD': 1.08935}},
                '2023-12-31': {'rates': {'USD': 1.10376}}
        }
    )

def test_tax_year_creation():
    closed_positions_csv = [
        "2022-12-01,SPOT,1000,1,2022-12-31,0.5", # cost: 1000, loss: 500
        "2023-08-01,BRK-B,1000,1,2023-09-02,5",  # cost: 1000, gain: 4000
        "2023-12-30,AAPL,1000,1,2023-12-31,0.5", # cost: 1000, loss: 500
    ]
    closed_positions = [closed_position_builder(p) for p in closed_positions_csv]
    service = TaxCalculatorService(closed_positions=closed_positions, 
                                   exchange_rate_service = exchange_rate_service_with_multi_date_stub())
    
    tax_years = service.tax_years_dict
    assert len(tax_years) == 2
    assert 2022 in tax_years
    assert 2023 in tax_years
    assert len(tax_years[2022].closed_positions) == 1
    assert len(tax_years[2023].closed_positions) == 2
    
def test_tax_payment_window():
    closed_positions_csv = [
        "2022-12-01,SPOT,1000,1,2022-12-31,0.5", # cost: 1000, loss: 500
        "2023-08-01,BRK-B,1000,1,2023-09-02,5",  # cost: 1000, gain: 4000
        "2023-12-01,AAPL,1000,1,2023-12-15,0.5", # cost: 1000, loss: 500
    ]
    closed_positions = [closed_position_builder(p) for p in closed_positions_csv]
    service = TaxCalculatorService(closed_positions=closed_positions, 
                                   exchange_rate_service = exchange_rate_service_with_multi_date_stub())

    if True: 
        # Test tax payment window for December 2022
        dec_2022_tax_window = service.tax_year(year=2022).tax_payment_window(end_month=12)
        # SPOT trade gain item
        assert len(dec_2022_tax_window.trade_gain_items) == 1
        assert dec_2022_tax_window.trade_gain_items[0].ticker == "SPOT"
        assert dec_2022_tax_window.trade_gain_items[0].date_bought == utils.parse_date("2022-12-01")
        assert dec_2022_tax_window.trade_gain_items[0].quantity == 1000
        assert dec_2022_tax_window.trade_gain_items[0].price_bought == 1
        assert dec_2022_tax_window.trade_gain_items[0].date_sold == utils.parse_date("2022-12-31")
        assert dec_2022_tax_window.trade_gain_items[0].price_sold == 0.5
        assert dec_2022_tax_window.trade_gain_items[0].sale_price == 500
        assert dec_2022_tax_window.trade_gain_items[0].cost_of_shares_sold == 1000
        assert dec_2022_tax_window.trade_gain_items[0].chargeable_gain == 0
        assert dec_2022_tax_window.trade_gain_items[0].capital_loss == 500
        assert dec_2022_tax_window.exchange_rate == 1.07265
        assert dec_2022_tax_window.total_sale_price == 500
        assert dec_2022_tax_window.total_sale_price_in_euro == 466.14
        assert dec_2022_tax_window.total_cost_of_shares_sold == 1000
        assert dec_2022_tax_window.total_cost_of_shares_sold_in_euro == 932.27
        assert dec_2022_tax_window.total_chargeable_gain == 0
        assert dec_2022_tax_window.total_capital_loss == 500
        assert dec_2022_tax_window.total_chargeable_gain_in_euro == 0
        assert dec_2022_tax_window.total_capital_loss_in_euro == 466.14
        assert dec_2022_tax_window.taxable_gain == 0
        assert dec_2022_tax_window.tax_to_be_paid == 0
        assert dec_2022_tax_window.loss_to_carryover == 466.14
        assert dec_2022_tax_window.remaining_tax_exemption == 1270.00
        # CGT return
        cgt_return = service.tax_year(year=2022).cgt_return 
        assert cgt_return.quoted_shares == round(dec_2022_tax_window.total_sale_price_in_euro)
        assert cgt_return.total_consideration == round(dec_2022_tax_window.total_sale_price_in_euro)
        assert cgt_return.chargeable_gains == round(dec_2022_tax_window.total_chargeable_gain_in_euro)
        assert cgt_return.losses_in_year == round(dec_2022_tax_window.total_capital_loss_in_euro)
        assert cgt_return.chargeable_gains_net_of_losses == round(dec_2022_tax_window.total_chargeable_gain_in_euro \
            - dec_2022_tax_window.total_capital_loss_in_euro)
        assert cgt_return.losses_from_previous_years == 0 
        assert cgt_return.personal_exemption == 0
        assert cgt_return.net_chargeable_gain == 0
        assert cgt_return.unused_losses_to_carry_forward == round(dec_2022_tax_window.loss_to_carryover)
        assert cgt_return.net_chargeable_gains_jan_to_nov == 0
        assert cgt_return.net_chargeable_gains_dec == round(dec_2022_tax_window.taxable_gain)
    if True: 
        # Test tax payment window for November 2023
        nov_2023_tax_window = service.tax_year(year=2023).tax_payment_window(end_month=11)
        assert len(nov_2023_tax_window.trade_gain_items) == 1
        # BRK-B trade gain item
        assert nov_2023_tax_window.trade_gain_items[0].ticker == "BRK-B"
        assert nov_2023_tax_window.trade_gain_items[0].date_bought == utils.parse_date("2023-08-01")
        assert nov_2023_tax_window.trade_gain_items[0].quantity == 1000
        assert nov_2023_tax_window.trade_gain_items[0].price_bought == 1
        assert nov_2023_tax_window.trade_gain_items[0].date_sold == utils.parse_date("2023-09-02")
        assert nov_2023_tax_window.trade_gain_items[0].price_sold == 5
        assert nov_2023_tax_window.trade_gain_items[0].sale_price == 5000
        assert nov_2023_tax_window.trade_gain_items[0].cost_of_shares_sold == 1000
        assert nov_2023_tax_window.trade_gain_items[0].chargeable_gain == 4000
        assert nov_2023_tax_window.exchange_rate == 1.08935
        assert nov_2023_tax_window.total_sale_price == 5000
        assert nov_2023_tax_window.total_sale_price_in_euro == 4589.89
        assert nov_2023_tax_window.total_cost_of_shares_sold == 1000
        assert nov_2023_tax_window.total_cost_of_shares_sold_in_euro == 917.98
        assert nov_2023_tax_window.total_chargeable_gain == 4000
        assert nov_2023_tax_window.total_chargeable_gain_in_euro == 3671.91
        assert nov_2023_tax_window.taxable_gain == 1935.77 # 3671.91 - 1270.0 -466.14 (loss from previous year)
        assert nov_2023_tax_window.tax_to_be_paid == 638.80
        assert nov_2023_tax_window.loss_to_carryover == 0
        assert nov_2023_tax_window.remaining_tax_exemption == 0
        assert nov_2023_tax_window.total_chargeable_gain == 4000
    if True: 
        # Test tax payment window for December 2023
        dec_2023_tax_window = service.tax_year(year=2023).tax_payment_window(end_month=12)
        assert len(dec_2023_tax_window.trade_gain_items) == 1
        # AAPL trade gain item
        assert dec_2023_tax_window.trade_gain_items[0].ticker == "AAPL"
        assert dec_2023_tax_window.trade_gain_items[0].date_bought == utils.parse_date("2023-12-01")
        assert dec_2023_tax_window.trade_gain_items[0].quantity == 1000
        assert dec_2023_tax_window.trade_gain_items[0].price_bought == 1
        assert dec_2023_tax_window.trade_gain_items[0].date_sold == utils.parse_date("2023-12-15")
        assert dec_2023_tax_window.trade_gain_items[0].price_sold == 0.5
        assert dec_2023_tax_window.trade_gain_items[0].sale_price == 500
        assert dec_2023_tax_window.trade_gain_items[0].cost_of_shares_sold == 1000
        assert dec_2023_tax_window.trade_gain_items[0].chargeable_gain == 0
        assert dec_2023_tax_window.trade_gain_items[0].capital_loss == 500
        assert dec_2023_tax_window.exchange_rate == 1.10376
        assert dec_2023_tax_window.total_sale_price == 500
        assert dec_2023_tax_window.total_sale_price_in_euro == 453.00
        assert dec_2023_tax_window.total_cost_of_shares_sold == 1000
        assert dec_2023_tax_window.total_cost_of_shares_sold_in_euro == 905.99
        assert dec_2023_tax_window.total_chargeable_gain == 0
        assert dec_2023_tax_window.total_capital_loss == 500
        assert dec_2023_tax_window.total_chargeable_gain_in_euro == 0
        assert dec_2023_tax_window.total_capital_loss_in_euro == 453.00
        assert dec_2023_tax_window.taxable_gain == 0
        assert dec_2023_tax_window.tax_to_be_paid == 0
        assert dec_2023_tax_window.loss_to_carryover == 453.00
        assert dec_2023_tax_window.remaining_tax_exemption == 1270.00
        # CGT return
        cgt_return = service.tax_year(year=2023).cgt_return 
        assert cgt_return.quoted_shares == round(nov_2023_tax_window.total_sale_price_in_euro \
            + dec_2023_tax_window.total_sale_price_in_euro)
        assert cgt_return.total_consideration == round(nov_2023_tax_window.total_sale_price_in_euro \
            + dec_2023_tax_window.total_sale_price_in_euro)
        assert cgt_return.chargeable_gains == round(nov_2023_tax_window.total_chargeable_gain_in_euro \
            + dec_2023_tax_window.total_chargeable_gain_in_euro)
        assert cgt_return.losses_in_year == round(nov_2023_tax_window.total_capital_loss_in_euro \
            + dec_2023_tax_window.total_capital_loss_in_euro)
        assert cgt_return.chargeable_gains_net_of_losses == \
            round(nov_2023_tax_window.total_chargeable_gain_in_euro - nov_2023_tax_window.total_capital_loss_in_euro \
            + dec_2023_tax_window.total_chargeable_gain_in_euro - dec_2023_tax_window.total_capital_loss_in_euro)
        assert cgt_return.losses_from_previous_years == round(dec_2022_tax_window.loss_to_carryover)
        assert cgt_return.personal_exemption == round(nov_2023_tax_window.usable_tax_exemption + dec_2023_tax_window.usable_tax_exemption)
        assert cgt_return.net_chargeable_gain == round(cgt_return.chargeable_gains \
            - cgt_return.losses_from_previous_years - cgt_return.losses_in_year - cgt_return.personal_exemption)
        assert cgt_return.unused_losses_to_carry_forward == round(dec_2023_tax_window.loss_to_carryover)
        assert cgt_return.net_chargeable_gains_jan_to_nov == round(nov_2023_tax_window.taxable_gain)
        assert cgt_return.net_chargeable_gains_dec == round(dec_2023_tax_window.taxable_gain)
        
    with open('temp/test_tax_report.html', 'w') as file:
        output = "<html>"
        output += service.tax_activities_html_report()
        output += "</html>"
        file.write(output)