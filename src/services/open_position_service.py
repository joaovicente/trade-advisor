import os
from repositories.open_position_repository import OpenPositionRepository

class OpenPositionService:
    def __init__(self):
        pass
    
    def get_all(self):
        path = os.path.join("data", "open_position.csv")
        repo = OpenPositionRepository(path=path)
        positions = repo.get_all()
        # print(positions)
        return positions