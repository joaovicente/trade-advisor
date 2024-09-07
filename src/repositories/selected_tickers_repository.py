import duckdb

from models.selected_tickers import SelectedTickers
from repositories.base_repository import BaseRepository

class SelectedTickersRepository(BaseRepository):
    def __init__(self, path):
        BaseRepository.__init__(self, path)

    def get_all(self):
        query_result = self.conn.execute(f"SELECT * FROM read_csv_auto('{self.path}')").fetchall()
        result = [SelectedTickers(ticker=row[0]) for row in query_result]
        return result
    
    def get_all_as_list(self):
        ticker_list = [ ticker.ticker for ticker in self.get_all()]
        return ticker_list
        
    