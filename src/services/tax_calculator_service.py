from typing import Dict, List
from models.closed_position import ClosedPosition
from services.exchange_rate_service import ExchangeRateService
from services.utils_service import date_as_str, todays_date, parse_date
import os

class TradeGainItem:
    def __init__(self, position: ClosedPosition, exchange_rate_service: ExchangeRateService, exchange_rate_date: str):
        self.ticker = position.ticker
        self.date_bought = position.date
        self.price_bought = position.price
        self.quantity = position.size
        self.date_sold = position.closed_date
        self.price_sold = position.closed_price
        self.sale_price = position.size * position.closed_price
        self.cost_of_shares_sold = position.size * position.price
        self.chargeable_gain = 0
        self.capital_loss = 0
        if self.sale_price > self.cost_of_shares_sold:
            # gain
            self.chargeable_gain = self.sale_price - self.cost_of_shares_sold
            self.capital_loss = 0
        else:
            # loss
            self.chargeable_gain = 0
            self.capital_loss = self.cost_of_shares_sold - self.sale_price
        # currency convert attributes below to closed position currency
        self.forex =  exchange_rate_service.get_rate(from_currency=position.currency, date=exchange_rate_date)
        self.currency = position.currency
        self.sale_price_in_euro = round(self.sale_price / self.forex , 2)
        self.cost_of_shares_sold_in_euro = round(self.cost_of_shares_sold / self.forex, 2)
        self.chargeable_gain_in_euro = round(self.chargeable_gain / self.forex, 2)
        self.capital_loss_in_euro = round(self.capital_loss / self.forex, 2)
        
class TaxPaymentWindow:
    def __init__(self, start_month, end_month: int, year: int, closed_positions: List[ClosedPosition], exchange_rate_service):
        self.start_month = start_month
        self.end_month = end_month
        self.year = year
        self.trade_gain_items = []
        self.total_sale_price = 0
        self.total_cost_of_shares_sold = 0 # How much shares were bought for
        self.total_chargeable_gain = 0
        self.total_capital_loss = 0
        self.month_name = "Nov" if end_month == 11 else "Dec"
        self.exchange_rate_service = exchange_rate_service
        #: Get exchange rate for the last day of the end_month, or today's if in future
        # It will either be 30 of November or 31 of December
        if end_month == 11:
            end_date = parse_date(f"{year}-11-30")
            self.tax_due_date = "December 15"
        else:
            end_date = parse_date(f"{year}-12-31")
            self.tax_due_date = "January 31"
        self.cgt_tax_rate = 0.33
        self.yearly_tax_exemption = 1270.00
        for position in closed_positions:
            if position.closed_date.month <= end_month and position.closed_date.month >= start_month:
                self.trade_gain_items.append(TradeGainItem(position, self.exchange_rate_service, end_date))
                
    def calculate(self, carried_over_loss_in_euro = 0, remaining_tax_exemption_in_euro = 1270.00):
        # use chargeable gain and capital loss in euro
        for item in self.trade_gain_items:
            self.total_sale_price += item.sale_price_in_euro
            self.total_cost_of_shares_sold += item.cost_of_shares_sold_in_euro
            self.total_chargeable_gain += item.chargeable_gain_in_euro
            self.total_capital_loss += item.capital_loss_in_euro
        self.loss_from_previous_window = carried_over_loss_in_euro
       
        chargeable_gain_with_loss_offset = self.total_chargeable_gain - self.total_capital_loss 
        if chargeable_gain_with_loss_offset < 0:
            # loss in this window is greater than gains
            self.taxable_gain = 0
            self.tax_to_be_paid = 0
            self.loss_to_carryover = chargeable_gain_with_loss_offset * -1 + carried_over_loss_in_euro
            self.remaining_tax_exemption = self.yearly_tax_exemption
            self.usable_tax_exemption = 0
        else:
            usable_carried_over_loss_in_euro = min(carried_over_loss_in_euro, chargeable_gain_with_loss_offset)
            remaining_gain_after_loss_offset = chargeable_gain_with_loss_offset - usable_carried_over_loss_in_euro
            self.usable_tax_exemption = min(remaining_tax_exemption_in_euro, remaining_gain_after_loss_offset)
            self.taxable_gain = round(chargeable_gain_with_loss_offset - usable_carried_over_loss_in_euro - self.usable_tax_exemption, 2)
            self.tax_to_be_paid = round(self.taxable_gain * self.cgt_tax_rate, 2)
            self.loss_to_carryover = carried_over_loss_in_euro - usable_carried_over_loss_in_euro
            self.remaining_tax_exemption = remaining_tax_exemption_in_euro - self.usable_tax_exemption
        
    def as_html(self) -> str:
        output = f"<h2> {self.month_name} {self.year} tax (€{self.tax_to_be_paid:.2f}) to be paid by {self.tax_due_date}</h2>"
        output += '<table border="1">'
        output += """<tr>
                        <th>Ticker</th>
                        <th>Date Sold</th>
                        <th>Date Bought</th>
                        <th>Quantity</th>
                        <th>Price sold</th>
                        <th>Price bought</th>
                        <th>Sale price</th>
                        <th>Cost of shares sold</th>
                        <th>Chargeable gain</th>
                        <th>Capital loss</th>
                        <th>Currency (forex)</th>
                        <th>Sale price (EUR)</th>
                        <th>Cost of shares sold (EUR)</th>
                        <th>Chargeable gain (EUR)</th>
                        <th>Capital loss (EUR)</th>
                    </tr>"""
        for item in self.trade_gain_items:
            output += "<tr>"
            output += f'<td><a href="https://finviz.com/quote.ashx?t={item.ticker}">{item.ticker}</a></td>'
            output += f"<td>{date_as_str(item.date_sold)}</td>"
            output += f"<td>{date_as_str(item.date_bought)}</td>"
            output += f"<td>{item.quantity}</td>"
            output += f"<td>{item.price_sold:.2f}</td>"
            output += f"<td>{item.price_bought:.2f}</td>"
            output += f"<td>{item.sale_price:.2f}</td>"
            output += f"<td>{item.cost_of_shares_sold:.2f}</td>"
            output += f"<td>{item.chargeable_gain:.2f}</td>"
            output += f"<td>{item.capital_loss:.2f}</td>"
            output += f"<td>{item.currency} <small>({item.forex})</small></td>"
            output += f"<td>{item.sale_price_in_euro:.2f}</td>"
            output += f"<td>{item.cost_of_shares_sold_in_euro:.2f}</td>"
            output += f"<td>{item.chargeable_gain_in_euro:.2f}</td>"
            output += f"<td>{item.capital_loss_in_euro:.2f}</td>"
            output += "</tr>"
        # Total row
        output += "<tr>"
        output += f'<td>Total</td>'
        output += f"<td></td>"
        output += f"<td></td>"
        output += f"<td></td>"
        output += f"<td></td>"
        output += f"<td></td>"
        output += f"<td></td>"
        output += f"<td></td>"
        output += f"<td></td>"
        output += f"<td></td>"
        output += f"<td></td>"
        output += f"<td>{self.total_sale_price:.2f}</td>"
        output += f"<td>{self.total_cost_of_shares_sold:.2f}</td>"
        output += f"<td>{self.total_chargeable_gain:.2f}</td>"
        output += f"<td>{self.total_capital_loss:.2f}</td>"
        output += "</tr>"
        output += "</table>"
        # Aggregate Tax calculations
        output += "<br>"
        output += '<table border="1">'
        output += """<tr>
                        <th>Description</th>
                        <th>Calculation</th>
                        <th>Value €</th>
                    </tr>"""
        output += f"<tr><td>Sale Price</td><td></td><td>{self.total_sale_price:.2f}</td></tr>"
        output += f"<tr><td>Cost of shares sold</td><td></td><td>{self.total_cost_of_shares_sold:.2f}</td></tr>"
        output += f"<tr><td>Chargeable gain</td><td></td><td>{self.total_chargeable_gain:.2f}</td></tr>"
        output += f"<tr><td>Capital loss</td><td></td><td>{self.total_capital_loss:.2f}</td></tr>"
        output += f"<tr><td>Carried loss to offset </td><td></td><td>{self.loss_from_previous_window:.2f}</td></tr>"
        output += f"<tr><td>Deduct personal exemption</td><td></td><td>{self.usable_tax_exemption:.2f}</td></tr>"
        output += f"<tr><td>Taxable gain</td><td></td><td>{self.taxable_gain:.2f}</td></tr>"
        output += f"<tr><td>CGT to be paid</td><td>({self.cgt_tax_rate*100}% of {self.taxable_gain:.2f})</td><td>{self.tax_to_be_paid:.2f}</td></tr>"
        output += "</tr>"
        output += "</table>"
        output += f'<p><a href="https://www.revenue.ie/en/gains-gifts-and-inheritance/transfering-an-asset/when-and-how-do-you-pay-and-file-cgt.aspx"> How to pay for for Capital Gain Tax</a></p>'
        return output

class TaxYear:
    def __init__(self, 
                 year: int, 
                 closed_positions: List[ClosedPosition],
                 exchange_rate_service
                 ):
        self.year = year
        self.closed_positions = [position for position in closed_positions if position.closed_date.year == year]
        self.tax_payment_windows_dict: Dict[int, TaxPaymentWindow] = {
            11: TaxPaymentWindow(1, 11, year, closed_positions=self.closed_positions, exchange_rate_service=exchange_rate_service),
            12: TaxPaymentWindow(12, 12, year, closed_positions=self.closed_positions, exchange_rate_service=exchange_rate_service)
        }
    
    def tax_payment_window(self, end_month: int) -> TaxPaymentWindow:
        return self.tax_payment_windows_dict.get(end_month)

class CapitalGainTaxReturn:
    def __init__(self, tax_year: TaxYear):
        self.tax_year = tax_year
        # attributes below refer to to CG1 tax form 2023
        self.quoted_shares = 0                      # Section 1(a) Shares / Securities - Quoted (total amount received from selling)
        self.total_consideration = 0                # Section 1(l) Total consideration (total amount received from selling)
        self.chargeable_gains = 0                   # Section 7 Gains / Losses / Net Chargeable gains - Chargeable gains in the year before relief (self)
        self.losses_in_year = 0                     # Section 8 Gains / Losses / Net Chargeable gains - Losses in the year before relief (self)
        self.chargeable_gains_net_of_losses = 0     # Section 11 Chargeable Gain(s) net of allowable current year losses and relief
        self.losses_from_previous_years = 0         # Section 14: previous year losses
        self.personal_exemption = 0                 # Section 15 Personal Exemption (maximun used exemption min=0 max=1270)
        self.net_chargeable_gain = 0                # Section 16 Chargeable Gain
        self.unused_losses_to_carry_forward = 0     # Section 19 Unused losses to carry forward
        self.net_chargeable_gains_jan_to_nov = 0    # Section 21 net chargeable gains that arose in the Jan-Nov period
        self.net_chargeable_gains_dec = 0           # Section 22 net chargeable gains that arose in the month of Dec
        self.calculate()
        
    def as_html(self) -> str:
        output = f"<h2> {self.tax_year.year} Tax returns (CG1 form) to be submitted by end of October {self.tax_year.year+1}</h2>"
        # CG1 form figures
        output += '<table border="1">'
        output += """<tr>
                        <th>Item</th>
                        <th><a href="https://www.revenue.ie/en/gains-gifts-and-inheritance/documents/formcg1.pdf">CG1 form</a> section</th>
                        <th>Value</th>
                    </tr>"""
        output += f"<tr><td>Quoted shares</td><td>1(a)</td><td>{self.quoted_shares:.2f}</td></tr>"
        output += f"<tr><td>Total consideration</td><td>1(l)</td><td>{self.total_consideration:.2f}</td></tr>"
        output += f"<tr><td>Chargeable gains</td><td>7</td><td>{self.chargeable_gains:.2f}</td></tr>"
        output += f"<tr><td>Losses in year</td><td>8</td><td>{self.losses_in_year:.2f}</td></tr>"
        output += f"<tr><td>Chargeable gains net of losses</td><td>11</td><td>{self.chargeable_gains_net_of_losses:.2f}</td></tr>"
        output += f"<tr><td>Losses from previous years</td><td>14</td><td>{self.losses_from_previous_years:.2f}</td></tr>"
        output += f"<tr><td>Personal exemption</td><td>15</td><td>{self.personal_exemption:.2f}</td></tr>"
        output += f"<tr><td>Net chargeable gain</td><td>16</td><td>{self.net_chargeable_gain:.2f}</td></tr>"
        output += f"<tr><td>Unused losses to carry forward</td><td>19</td><td>{self.unused_losses_to_carry_forward:.2f}</td></tr>"
        output += f"<tr><td>Net chargeable gains Jan to Nov</td><td>21</td><td>{self.net_chargeable_gains_jan_to_nov:.2f}</td></tr>"
        output += f"<tr><td>Net chargeable gains Dec</td><td>22</td><td>{self.net_chargeable_gains_dec:.2f}</td></tr>"
        output += "</tr>"
        output += "</table>"
        output += f'<p><a href="https://www.youtube.com/watch?v=YorwaTXEPYI&t=540s"> Filling a CG1 form step by step video</a></p>'
        return output
       
    def calculate(self):
        for tax_payment_window in self.tax_year.tax_payment_windows_dict.values():
            self.quoted_shares += tax_payment_window.total_sale_price
            self.total_consideration += tax_payment_window.total_sale_price
            self.chargeable_gains += tax_payment_window.total_chargeable_gain
            self.losses_in_year += tax_payment_window.total_capital_loss
            self.chargeable_gains_net_of_losses += tax_payment_window.total_chargeable_gain\
                - tax_payment_window.total_capital_loss
            self.personal_exemption += tax_payment_window.usable_tax_exemption
        self.losses_from_previous_years = self.tax_year.tax_payment_window(11).loss_from_previous_window
        self.net_chargeable_gain = self.chargeable_gains \
            - self.losses_from_previous_years - self.losses_in_year - self.personal_exemption
        if self.net_chargeable_gain < 0:
            self.net_chargeable_gain = 0
        self.unused_losses_to_carry_forward = self.tax_year.tax_payment_window(12).loss_to_carryover
        self.net_chargeable_gains_jan_to_nov = self.tax_year.tax_payment_window(11).taxable_gain
        self.net_chargeable_gains_dec = self.tax_year.tax_payment_window(12).taxable_gain
        # round up 
        self.quoted_shares = round(self.quoted_shares, 0)
        self.total_consideration = round(self.total_consideration, 0)
        self.chargeable_gains = round(self.chargeable_gains, 0)
        self.losses_in_year = round(self.losses_in_year, 0)
        self.chargeable_gains_net_of_losses = round(self.chargeable_gains_net_of_losses, 0)
        self.personal_exemption = round(self.personal_exemption, 0)
        self.losses_from_previous_years = round(self.losses_from_previous_years, 0)
        self.net_chargeable_gain = round(self.net_chargeable_gain, 0)
        self.unused_losses_to_carry_forward = round(self.unused_losses_to_carry_forward, 0)
        self.net_chargeable_gains_jan_to_nov = round(self.net_chargeable_gains_jan_to_nov, 0)
        self.net_chargeable_gains_dec = round(self.net_chargeable_gains_dec, 0)
        

    
class TaxCalculatorService:
    def __init__(self, closed_positions: List[ClosedPosition] = [], exchange_rate_service: ExchangeRateService = None):
        self.closed_positions = closed_positions
        if exchange_rate_service is None:
            raise Exception("ExchangeRateService not provided")
        self.exchange_rate_service = exchange_rate_service
        self.tax_years_dict: Dict[int, TaxYear] = {}
        self.load_tax_years()
        remaining_tax_exemption_in_euro = 0
        carried_over_loss_in_euro = 0
        for tax_year_int in sorted(self.tax_years_dict.keys()):
            tax_year = self.tax_years_dict[tax_year_int]
            for month in sorted(tax_year.tax_payment_windows_dict.keys()):
                if month == 11:
                    tax_year.tax_payment_window(month).calculate(
                        carried_over_loss_in_euro=carried_over_loss_in_euro)
                    remaining_tax_exemption_in_euro = tax_year.tax_payment_window(month).remaining_tax_exemption
                    carried_over_loss_in_euro = tax_year.tax_payment_window(month).loss_to_carryover
                else:
                    tax_year.tax_payment_window(month).calculate(
                        carried_over_loss_in_euro=carried_over_loss_in_euro,
                        remaining_tax_exemption_in_euro=remaining_tax_exemption_in_euro)
                    carried_over_loss_in_euro = tax_year.tax_payment_window(month).loss_to_carryover
                    tax_year.cgt_return = CapitalGainTaxReturn(tax_year)
        
    def load_tax_years(self):
        # Create TaxYear objects for each year that has open positions
        years = set(position.closed_date.year for position in self.closed_positions)
        self.tax_years_dict = {year: TaxYear(year, self.closed_positions, self.exchange_rate_service) for year in years}
        
    def tax_year(self, year: int) -> TaxYear:
        return self.tax_years_dict.get(year)
    
    def tax_activities_html_report(self) -> str:
        output = ""
        for tax_year_int in sorted(self.tax_years_dict.keys()):
            tax_year = self.tax_years_dict[tax_year_int]
            output += f"<h1>{tax_year_int} Tax</h1>"
            for month in sorted(tax_year.tax_payment_windows_dict.keys()):
                output += tax_year.tax_payment_window(month).as_html()
                if month == 12:
                    output += tax_year.cgt_return.as_html()
        return output

