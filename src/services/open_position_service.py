import os
from repositories.open_position_repository import OpenPositionRepository

class OpenPositionService:
    def __init__(self):
        pass
    
    def get_all(self):
        path = os.path.join("data", "open_position.csv")
        repo = OpenPositionRepository(path=path)
        positions = repo.get_all()
        return positions
    
    def get_distinct_tickers_list(self):
        postitions = self.get_all()
        return list(set([position.ticker for position in postitions]))
