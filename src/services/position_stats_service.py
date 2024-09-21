from typing import List

from models.closed_position import ClosedPosition
from models.open_position import OpenPosition
from services.utils_service import today_as_str, parse_date

class PositionStatsService():
    def __init__(self, 
                 open_positions: List[OpenPosition] = [],
                 closed_positions: List[ClosedPosition] = [],
                 todays_date_str=today_as_str()
                 ):
        
        # filter earlier positions if performing simulations
        todays_date = parse_date(todays_date_str)
        self.open_positions = [pos for pos in open_positions if pos.date <= todays_date]
        self.closed_positions = closed_positions = [pos for pos in closed_positions if pos.closed_date <= todays_date]
        self.todays_date_str = todays_date_str
        self.todays_date = parse_date(todays_date_str)

    def get_batting_avg(self):
        num_hits = 0
        num_misses = 0
        for pos in self.closed_positions:
            if pos.closed_price > pos.price:
                num_hits += 1
            else:
                num_misses += 1
        pct = round(num_hits / (num_hits + num_misses) * 100, 0)
        return f"{pct:.0f}% ({num_hits}/{(num_hits + num_misses)})"
    
    def get_pnl_from_closed_positions(self, closed_positions=[]):
        pnl = 0
        for pos in closed_positions:
            pnl += (pos.closed_price * pos.size) - (pos.price * pos.size) 
        return pnl

    def get_pnl_all_time(self):
        pnl = self.get_pnl_from_closed_positions(self.closed_positions)
        return pnl
    
    def get_pnl_year_to_date(self):
        positions_this_year = [pos for pos in self.closed_positions if pos.closed_date.year == self.todays_date.year]
        pnl = self.get_pnl_from_closed_positions(positions_this_year)
        return pnl
    
    def get_pnl_jan_to_nov(self):
        positions = \
            [pos for pos in self.closed_positions \
                if pos.closed_date.year == self.todays_date.year \
                    and pos.closed_date.month < 12
                ]
        pnl = self.get_pnl_from_closed_positions(positions)
        return pnl
        
    def get_pnl_nov_to_dec(self):
        positions = \
            [pos for pos in self.closed_positions \
                if pos.closed_date.year == self.todays_date.year \
                    and pos.closed_date.month == 12
                ]
        pnl = self.get_pnl_from_closed_positions(positions)
        return pnl
        