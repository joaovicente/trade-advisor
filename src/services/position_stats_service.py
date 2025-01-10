from typing import List

from models.closed_position import ClosedPosition
from models.open_position import OpenPosition
from services.utils_service import today_as_str, parse_date

class ClosedPositionsPerformance():
    def __init__(self, year=None, batting_average=0, pnl=0):
        self.year = year
        self.batting_average = batting_average
        self.pnl = pnl

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
    
    def get_batting_avg(self, closed_positions):
        num_hits = 0
        num_misses = 0
        for pos in closed_positions:
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
    
    def all_time_closed_positions_performance(self) -> ClosedPositionsPerformance:
        all_time_closed_positions_performance = ClosedPositionsPerformance(
            year = None,
            batting_average=self.get_batting_avg(self.closed_positions),
            pnl = self.get_pnl_from_closed_positions(self.closed_positions)
        )
        return all_time_closed_positions_performance
    
    def yearly_closed_positions_performance(self) -> List[ClosedPositionsPerformance]:
        yearly_closed_positions_performance = []
        years = list(set([pos.closed_date.year for pos in self.closed_positions]))
        for year in years:
            year_positions = [pos for pos in self.closed_positions if pos.closed_date.year == year]
            year_closed_positions_performance = ClosedPositionsPerformance(
                year = year,
                batting_average=self.get_batting_avg(year_positions),
                pnl = self.get_pnl_from_closed_positions(year_positions)
            )
            yearly_closed_positions_performance.append(year_closed_positions_performance)
        return yearly_closed_positions_performance
