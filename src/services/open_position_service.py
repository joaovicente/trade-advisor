import os
from models.open_position import OpenPosition
from repositories.open_position_repository import OpenPositionRepository
from datetime import datetime

class OpenPositionService:
    def __init__(self):
        self.cli_supplied_positions = []
    
    def get_all(self):
        if len(self.cli_supplied_positions) > 0:
            return self.cli_supplied_positions
        else:
            path = os.path.join("data", "open_position.csv")
            repo = OpenPositionRepository(path=path)
            positions = repo.get_all()
            return positions
    
    def get_distinct_tickers_list(self):
        postitions = self.get_all()
        return list(set([position.ticker for position in postitions]))

    def add_position(self, position_csv: str):
        position_part = position_csv.split(",")
        #TODO: Error handling
        self.cli_supplied_positions.append(
            OpenPosition(datetime.strptime(position_part[0], "%Y-%m-%d").date(), 
                         position_part[1], 
                         float(position_part[2]), 
                         float(position_part[3])))