import duckdb

from models.open_position import OpenPosition
from repositories.base_repository import BaseRepository

class OpenPositionRepository(BaseRepository):
    def __init__(self, path):
        BaseRepository.__init__(self, path)

    def get_all(self):
        query_result = self.conn.execute(f"SELECT * FROM read_csv_auto('{self.path}')").fetchall()
        result = [OpenPosition(
            date=row[0], 
            ticker=row[1], 
            size=row[2], 
            price=row[3], 
            currency=row[4]
            ) for row in query_result]
        return result
    