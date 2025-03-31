import duckdb

from models.closed_position import ClosedPosition
from repositories.base_repository import BaseRepository

class ClosedPositionRepository(BaseRepository):
    def __init__(self, path):
        BaseRepository.__init__(self, path)

    def get_all(self):
        query_result = self.conn.execute(f"SELECT * FROM read_csv_auto('{self.path}')").fetchall()
        result = [ClosedPosition(
            date=row[0], 
            ticker=row[1], 
            size=row[2], 
            price=row[3], 
            currency=row[4], 
            closed_date=row[5], 
            closed_price=row[6],
            commission=row[7]
            ) for row in query_result]
        return result
    