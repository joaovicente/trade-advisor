from typing import List
from pydantic import BaseModel
from datetime import date

from models.closed_position import ClosedPosition

class TradeGain(BaseModel):
    ticker: str # will hold Total in last row
    date_bought: date
    date_sold: date
    quantity: float
    price_bought: float
    price_sold: float
    cost_of_shares_sold: float
    chargeable_gain: float
    
class TradeGainTotal(BaseModel):
    cost_of_shares_sold: float
    chargeable_gain: float

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
    year: date
    start_month: date
    end_month: date
    trade_gain: list[TradeGain]
    trade_gain_total: TradeGainTotal
    aggregated_tax: AggregatedTax

class TaxActivitiesReport():
    def __init__(self, 
                 todays_date: str, 
                 closed_positions: List[ClosedPosition] = [], 
                 rapid=False):
        self.windows = []
        # TODO: Calculate TradeGainWindow from earlier tax activities applicable time
        # TODO: Previous year Jan-Nov
        # TODO: Previous year Nov-Dec
        # TODO: This year Jan-Nov
        # TODO: This year Nov-Dec
        pass
    
    def get_tax_activities_html_report(self) -> str:
        # TODO: calculations for previous year TradeGainPeriodInfo
        # TODO: calculations for this year TradeGainPeriodInfo
        # TODO: determine next set of actitities based on current date
        # TODO: render html report
        pass
    
    