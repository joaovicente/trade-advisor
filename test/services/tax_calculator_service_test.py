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
        currency=csv[4],
        closed_date=utils.parse_date(csv[5]),
        closed_price=float(csv[6]),
        commission=float(csv[7]) if len(csv) > 7 else 0,
    )

   
def exchange_rate_service_with_multi_date_stub():
    return ExchangeRateService(stub= {
                '2022-11-30': {'rates': {'USD': 1.04235}},
                '2022-12-31': {'rates': {'USD': 1.07265}},
                '2023-11-30': {'rates': {'USD': 1.08935}},
                '2023-12-31': {'rates': {'USD': 1.10376}}
        }
    )
    
def exchange_rate_service_with_single_date_no_forex_stub():
    return ExchangeRateService(stub= {
                '*': {'rates': {'USD': 1.0}},
        }
    )

# TODO: 1. Test using utest user with added EURO abnd CHF stock 
# TODO: 2. Add new test that uses stock in EU and CHF currency

def test_tax_year_creation():
    closed_positions_csv = [
        # date, ticker, size, price, currency, closed_date, closed_price, commission
        "2022-12-01,SPOT,1000,1,USD,2022-12-31,0.5,0", # cost: 1000, loss: 500
        "2023-08-01,BRK-B,1000,1,USD,2023-09-02,5,0",  # cost: 1000, gain: 4000
        "2023-12-30,AAPL,1000,1,USD,2023-12-31,0.5,0", # cost: 1000, loss: 500
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
        "2022-12-01,SPOT,1000,1,USD,2022-12-31,0.5", # cost: 1000, loss: 500
        "2023-08-01,BRK-B,1000,1,USD,2023-09-02,5",  # cost: 1000, gain: 4000
        "2023-12-01,AAPL,1000,1,USD,2023-12-15,0.5", # cost: 1000, loss: 500
    ]
    closed_positions = [closed_position_builder(p) for p in closed_positions_csv]
    service = TaxCalculatorService(closed_positions=closed_positions, 
                                  exchange_rate_service = exchange_rate_service_with_multi_date_stub())
                                #  exchange_rate_service = exchange_rate_service_with_single_date_no_forex_stub())

    if True: 
        # Test tax payment window for December 2022
        dec_2022_tax_window = service.tax_year(year=2022).tax_payment_window(end_month=12)
        # SPOT trade gain item
        assert len(dec_2022_tax_window.trade_gain_items) == 1
        assert dec_2022_tax_window.trade_gain_items[0].ticker == "SPOT"
        assert dec_2022_tax_window.trade_gain_items[0].date_sold == utils.parse_date("2022-12-31")
        assert dec_2022_tax_window.trade_gain_items[0].date_bought == utils.parse_date("2022-12-01")
        assert dec_2022_tax_window.trade_gain_items[0].quantity == 1000
        assert dec_2022_tax_window.trade_gain_items[0].price_sold == 0.5
        assert dec_2022_tax_window.trade_gain_items[0].price_bought == 1
        assert dec_2022_tax_window.trade_gain_items[0].sale_price == 500
        assert dec_2022_tax_window.trade_gain_items[0].cost_of_shares_sold == 1000
        assert dec_2022_tax_window.trade_gain_items[0].chargeable_gain == 0
        assert dec_2022_tax_window.trade_gain_items[0].capital_loss == 500
        assert dec_2022_tax_window.trade_gain_items[0].forex == 1.07265
        assert dec_2022_tax_window.trade_gain_items[0].sale_price_in_euro == 466.14
        assert dec_2022_tax_window.trade_gain_items[0].cost_of_shares_sold_in_euro == 932.27
        assert dec_2022_tax_window.trade_gain_items[0].chargeable_gain_in_euro == 0
        assert dec_2022_tax_window.trade_gain_items[0].capital_loss_in_euro == 466.14
        # Total row
        assert dec_2022_tax_window.total_sale_price == 466.14 
        assert dec_2022_tax_window.total_cost_of_shares_sold == 932.27
        assert dec_2022_tax_window.total_chargeable_gain == 0
        assert dec_2022_tax_window.total_capital_loss == 466.14
        # CGT payment table
        assert dec_2022_tax_window.total_sale_price == 466.14 # Sale price
        assert dec_2022_tax_window.total_cost_of_shares_sold == 932.27 # Cost of shares sold
        assert dec_2022_tax_window.total_chargeable_gain == 0 # Chargeable gain
        assert dec_2022_tax_window.total_capital_loss == 466.14 # Capital loss
        assert dec_2022_tax_window.loss_from_previous_window == 0 # Carried loss to offset
        assert dec_2022_tax_window.usable_tax_exemption == 0 # Deduct personal exemption
        assert dec_2022_tax_window.taxable_gain == 0 # Taxable gain
        assert dec_2022_tax_window.tax_to_be_paid == 0 # Tax to be paid
        # CGT return
        cgt_return = service.tax_year(year=2022).cgt_return 
        assert cgt_return.quoted_shares == round(dec_2022_tax_window.total_sale_price)
        assert cgt_return.total_consideration == round(dec_2022_tax_window.total_sale_price)
        assert cgt_return.chargeable_gains == round(dec_2022_tax_window.total_chargeable_gain)
        assert cgt_return.losses_in_year == round(dec_2022_tax_window.total_capital_loss)
        assert cgt_return.chargeable_gains_net_of_losses == round(dec_2022_tax_window.total_chargeable_gain\
            - dec_2022_tax_window.total_capital_loss)
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
        assert nov_2023_tax_window.trade_gain_items[0].date_sold == utils.parse_date("2023-09-02")
        assert nov_2023_tax_window.trade_gain_items[0].date_bought == utils.parse_date("2023-08-01")
        assert nov_2023_tax_window.trade_gain_items[0].quantity == 1000
        assert nov_2023_tax_window.trade_gain_items[0].price_bought == 1
        assert nov_2023_tax_window.trade_gain_items[0].price_sold == 5
        assert nov_2023_tax_window.trade_gain_items[0].sale_price == 5000
        assert nov_2023_tax_window.trade_gain_items[0].cost_of_shares_sold == 1000
        assert nov_2023_tax_window.trade_gain_items[0].chargeable_gain == 4000
        assert nov_2023_tax_window.trade_gain_items[0].capital_loss == 0
        assert nov_2023_tax_window.trade_gain_items[0].forex == 1.08935
        assert nov_2023_tax_window.trade_gain_items[0].sale_price_in_euro == 4589.89
        assert nov_2023_tax_window.trade_gain_items[0].cost_of_shares_sold_in_euro == 917.98
        assert nov_2023_tax_window.trade_gain_items[0].chargeable_gain_in_euro == 3671.91
        assert nov_2023_tax_window.trade_gain_items[0].capital_loss_in_euro == 0
        # Total row
        assert nov_2023_tax_window.total_sale_price == 4589.89
        assert nov_2023_tax_window.total_cost_of_shares_sold == 917.98
        assert nov_2023_tax_window.total_chargeable_gain == 3671.91
        assert nov_2023_tax_window.total_capital_loss == 0
        # CGT payment table
        assert nov_2023_tax_window.total_sale_price == 4589.89 # Sale price
        assert nov_2023_tax_window.total_cost_of_shares_sold == 917.98 # Cost of shares sold
        assert nov_2023_tax_window.total_chargeable_gain == 3671.91 # Chargeable gain
        assert nov_2023_tax_window.total_capital_loss == 0 # Capital loss
        assert nov_2023_tax_window.loss_from_previous_window == 466.14 # Carried loss to offset
        assert nov_2023_tax_window.usable_tax_exemption == 1270.0 # Deduct personal exemption
        assert nov_2023_tax_window.taxable_gain == 1935.77 # Taxable gain
        assert nov_2023_tax_window.tax_to_be_paid == 638.80 # Tax to be paid
    if True: 
        # Test tax payment window for December 2023
        dec_2023_tax_window = service.tax_year(year=2023).tax_payment_window(end_month=12)
        assert len(dec_2023_tax_window.trade_gain_items) == 1
        # AAPL trade gain item
        assert dec_2023_tax_window.trade_gain_items[0].ticker == "AAPL"
        assert dec_2023_tax_window.trade_gain_items[0].date_sold == utils.parse_date("2023-12-15")
        assert dec_2023_tax_window.trade_gain_items[0].date_bought == utils.parse_date("2023-12-01")
        assert dec_2023_tax_window.trade_gain_items[0].quantity == 1000
        assert dec_2023_tax_window.trade_gain_items[0].price_sold == 0.5
        assert dec_2023_tax_window.trade_gain_items[0].price_bought == 1
        assert dec_2023_tax_window.trade_gain_items[0].sale_price == 500
        assert dec_2023_tax_window.trade_gain_items[0].cost_of_shares_sold == 1000
        assert dec_2023_tax_window.trade_gain_items[0].chargeable_gain == 0
        assert dec_2023_tax_window.trade_gain_items[0].capital_loss == 500
        assert dec_2023_tax_window.trade_gain_items[0].forex == 1.10376
        assert dec_2023_tax_window.trade_gain_items[0].sale_price_in_euro == 453.00
        assert dec_2023_tax_window.trade_gain_items[0].cost_of_shares_sold_in_euro == 905.99
        assert dec_2023_tax_window.trade_gain_items[0].chargeable_gain_in_euro == 0
        assert dec_2023_tax_window.trade_gain_items[0].capital_loss_in_euro == 453.00
        # Total row
        assert dec_2023_tax_window.total_sale_price == 453.00
        assert dec_2023_tax_window.total_cost_of_shares_sold == 905.99
        assert dec_2023_tax_window.total_chargeable_gain == 0
        assert dec_2023_tax_window.total_capital_loss == 453.00
        # CGT payment table
        assert dec_2023_tax_window.total_sale_price == 453.00 # Sale price
        assert dec_2023_tax_window.total_cost_of_shares_sold == 905.99 # Cost of shares sold
        assert dec_2023_tax_window.total_chargeable_gain == 0 # Chargeable gain
        assert dec_2023_tax_window.total_capital_loss == 453.00 # Capital loss
        assert dec_2023_tax_window.loss_from_previous_window == 0 # Carried loss to offset
        assert dec_2023_tax_window.usable_tax_exemption == 0 # Deduct personal exemption
        assert dec_2023_tax_window.taxable_gain == 0 # Taxable gain
        assert dec_2023_tax_window.tax_to_be_paid == 0 # Tax to be paid
        # CGT return
        cgt_return = service.tax_year(year=2023).cgt_return 
        assert cgt_return.quoted_shares == round(nov_2023_tax_window.total_sale_price \
            + dec_2023_tax_window.total_sale_price)
        assert cgt_return.total_consideration == round(nov_2023_tax_window.total_sale_price \
            + dec_2023_tax_window.total_sale_price)
        assert cgt_return.chargeable_gains == round(nov_2023_tax_window.total_chargeable_gain \
            + dec_2023_tax_window.total_chargeable_gain)
        assert cgt_return.losses_in_year == round(nov_2023_tax_window.total_capital_loss \
            + dec_2023_tax_window.total_capital_loss)
        assert cgt_return.chargeable_gains_net_of_losses == \
            round(nov_2023_tax_window.total_chargeable_gain - nov_2023_tax_window.total_capital_loss \
            + dec_2023_tax_window.total_chargeable_gain - dec_2023_tax_window.total_capital_loss)
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