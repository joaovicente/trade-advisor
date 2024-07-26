import duckdb

from models.open_position import OpenPosition

# TODO: make the following class generic to support other models
class OpenPositionRepository:
    def __init__(self, path):
        # Connect to an in-memory DuckDB database
        self.conn = duckdb.connect(database=':memory:')
        self.entity = "open_position"
        self.path = path

    def get_all(self):
        query_result = self.conn.execute(f"SELECT * FROM read_csv_auto('{self.path}')").fetchall()
        result = [OpenPosition(date=row[0], ticker=row[1], size=row[2], price=row[3]) for row in query_result]
        return result