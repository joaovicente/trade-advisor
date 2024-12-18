from typing import List
from pydantic import BaseModel
from datetime import date
import requests

from models.closed_position import ClosedPosition
from services.utils_service import date_as_str, todays_date, parse_date

class TradeGainItem(BaseModel):
    ticker: str # will hold Total in last row
    date_bought: date
    date_sold: date
    quantity: float
    price_bought: float
    price_sold: float
    sale_price: float # price_sold * quantity
    cost_of_shares_sold: float # how much shares sold were bought for originally
    chargeable_gain: float
    
class TradeGainTotal(BaseModel):
    sale_price: float 
    cost_of_shares_sold: float
    chargeable_gain: float # sale price - cost of shares sold

class AggregatedTax(BaseModel):
    #Aggregate tax calculation table (euro):
    #- Description,Calculation,Value (as per https://www.revenue.ie/en/gains-gifts-and-inheritance/transfering-an-asset/selling-or-disposing-of-shares.aspx)
    sale_price: float
    cost_of_shares_sold: float
    chargeable_gain: float
    personal_exemption: float
    taxable_gain: float
    cgt_to_be_paid: float
    
class TradeGainWindow(BaseModel):
    #Jan-Nov or Nov-Dec
    year: int
    start_month: int
    end_month: int
    end_date: date
    trade_gain_items: list[TradeGainItem]
    trade_gain_total: TradeGainTotal
    aggregated_tax: AggregatedTax

class TaxActivitiesReport():
    def cross_window_boundary(previous_position, this_position):
        if previous_position is None:
            return True
            #TODO: return True also if year is crossed or if same year, but this closed position in December
        else:
            return False
        
    def personal_exemption(self):
        return 1270
    
    def cgp_tax_percentage(self):
        return 33
    
    def us_to_euro_rate(self, date):
        # Get exhange date for provided date
        # Unless date is in the future. In that case return today's exchange rate
        todays_date = parse_date(self.todays_date)
        if date > todays_date:
            date = todays_date
        # API call if not fixed or rapid
        if self.fixed_forex_pct is not None:
            exchange_rate = self.fixed_forex_pct
        else:
            # API call 
            date_str = date_as_str(date)
            open_exchange_rates_app_id = '7df731da502f49f480a9b3e44e3c3d4c'
            url = f"https://openexchangerates.org/api/historical/{date_str}.json?app_id={open_exchange_rates_app_id}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                exchange_rate = 1 / data['rates']['EUR']
                #print(f"1 US = {exchange_rate} EUR - for {date_str}")
            else:
                raise Exception(f"Error ({response.status_code}) fetching data from openexchangerates.org")
        return exchange_rate
    
    def __init__(self, 
                 todays_date: str = todays_date(), 
                 closed_positions: List[ClosedPosition] = [], 
                 rapid=False,
                 fixed_forex_pct=None):
        self.windows = []
        self.fixed_forex_pct = fixed_forex_pct
        self.todays_date = todays_date
        self.rapid = rapid
        last_position = None
        window = None
        if not closed_positions:
            return 
        for position in closed_positions:
            if TaxActivitiesReport.cross_window_boundary(last_position, position):
                # New window
                trade_gain = []
                trade_gain_total = TradeGainTotal(sale_price=0, cost_of_shares_sold=0, chargeable_gain=0)
                window_year = position.closed_date.year
                if position.closed_date.month < 12:
                    window_start_month = 1
                    window_end_month = 11
                    window_end_date = parse_date(f"{window_year}-{window_end_month:02d}-30")
                else:
                    window_start_month = 12
                    window_end_month = 12
                    window_end_date = parse_date(f"{window_year}-{window_end_month:02d}-31")
                window = TradeGainWindow(
                    year=window_year,
                    start_month=window_start_month,
                    end_month=window_end_month,
                    end_date=window_end_date,
                    trade_gain_items=trade_gain,
                    trade_gain_total=trade_gain_total,
                    aggregated_tax=AggregatedTax(sale_price=0, cost_of_shares_sold=0, chargeable_gain=0, personal_exemption=0, taxable_gain=0, cgt_to_be_paid=0)
                )
                self.windows.append(window)
            # Update window with new closed position
            chargeable_gain = position.size * (position.closed_price - position.price)
            cost_of_shares_sold=position.size * position.price
            sale_price = position.size * position.closed_price
            window.trade_gain_items.append(
                TradeGainItem(
                    ticker=position.ticker,
                    date_bought=position.date,
                    date_sold=position.closed_date,
                    quantity=position.size,
                    price_bought=position.price,
                    price_sold=position.closed_price,
                    sale_price=sale_price,
                    cost_of_shares_sold=cost_of_shares_sold,
                    chargeable_gain=chargeable_gain
                )
            )
            # Update trade gain total
            window.trade_gain_total.sale_price += sale_price
            window.trade_gain_total.cost_of_shares_sold += cost_of_shares_sold
            window.trade_gain_total.chargeable_gain += chargeable_gain
            last_position = position
        # Aggregated tax calculations
        window.aggregated_tax.sale_price = window.trade_gain_total.sale_price / self.us_to_euro_rate(window.end_date)
        window.aggregated_tax.cost_of_shares_sold = window.trade_gain_total.cost_of_shares_sold / self.us_to_euro_rate(window.end_date)
        window.aggregated_tax.chargeable_gain = window.trade_gain_total.chargeable_gain / self.us_to_euro_rate(window.end_date)
        window.aggregated_tax.personal_exemption = self.personal_exemption()
        #TODO: Deal with 
        window.aggregated_tax.taxable_gain = window.aggregated_tax.chargeable_gain - window.aggregated_tax.personal_exemption
        if window.aggregated_tax.taxable_gain < 0:
            window.aggregated_tax.taxable_gain = 0
        window.aggregated_tax.cgt_to_be_paid = window.aggregated_tax.taxable_gain * (self.cgp_tax_percentage() / 100)
    
    
    def get_tax_activities_html_report(self) -> str:
        window = self.windows[0]
        # Next Tax Activities
        output = "<h1>Tax Activities</h1>"
        # TODO: Identify next tax actitity and associated window(s)
        output += f"<h2>By 15-Dec: Pay (€{window.aggregated_tax.cgt_to_be_paid:.2f}) CGT for Jan-Nov gains </h2>"
        # TODO: Trade Gains Table
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
                    </tr>"""
        for item in window.trade_gain_items:
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
            output += "</tr>"
        # Total row
        output += "<tr>"
        output += f'<td>Total</td>'
        output += f"<td></td>"
        output += f"<td></td>"
        output += f"<td></td>"
        output += f"<td></td>"
        output += f"<td></td>"
        output += f"<td>{window.trade_gain_total.sale_price:.2f}</td>"
        output += f"<td>{window.trade_gain_total.cost_of_shares_sold:.2f}</td>"
        output += f"<td>{window.trade_gain_total.chargeable_gain:.2f}</td>"
        output += "</tr>"
        output += "</table>"
        # TODO: Aggregate Tax calculations
        output += "<br>"
        output += '<table border="1">'
        output += """<tr>
                        <th>Description</th>
                        <th>Calculation</th>
                        <th>Value €</th>
                    </tr>"""
        output += f"<tr><td>Sale Price</td><td>{window.trade_gain_total.sale_price:.2f} / {self.us_to_euro_rate(window.end_date):.5f} <i>(forex rate)</i></td><td>{window.aggregated_tax.sale_price:.2f}</td></tr>"
        output += f"<tr><td>Cost of shares sold</td><td>{window.trade_gain_total.cost_of_shares_sold:.2f} / {self.us_to_euro_rate(window.end_date):.5f} <i>(forex rate)</i></td><td>{window.aggregated_tax.cost_of_shares_sold:.2f}</td></tr>"
        output += f"<tr><td>Chargeable gain</td><td>{window.trade_gain_total.chargeable_gain:.2f} / {self.us_to_euro_rate(window.end_date):.5f} <i>(forex rate)</i></td><td>{window.aggregated_tax.chargeable_gain:.2f}</td></tr>"
        output += f"<tr><td>Deduct personal exemption</td><td></td><td>{window.aggregated_tax.personal_exemption:.2f}</td></tr>"
        output += f"<tr><td>Taxable gain</td><td></td><td>{window.aggregated_tax.taxable_gain:.2f}</td></tr>"
        output += f"<tr><td>CGT to be paid</td><td>({self.cgp_tax_percentage()}% of {window.aggregated_tax.taxable_gain:.2f})</td><td>{window.aggregated_tax.cgt_to_be_paid:.2f}</td></tr>"
        output += "</tr>"
        output += "</table>"
        p_open = '<p style="font-size=12px; line-height: 0.8;">'
        output += f'<p><a href="https://www.revenue.ie/en/gains-gifts-and-inheritance/transfering-an-asset/when-and-how-do-you-pay-and-file-cgt.aspx"> How to pay for for Capital Gain Tax</a></p>'
        return output
        
        
        
    
    