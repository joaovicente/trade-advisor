import duckdb

from models.user import User
from repositories.base_repository import BaseRepository

class UserRepository(BaseRepository):
    def __init__(self, path):
        BaseRepository.__init__(self, path)

    def get_all(self):
        query_result = self.conn.execute(f"SELECT * FROM read_csv_auto('{self.path}')").fetchall()
        result = [User(id=row[0], email=row[1], mobile=row[2]) for row in query_result]
        return result
    
    def get_by_id(self, id):
        query_result = self.conn.execute(f"SELECT * FROM read_csv_auto('{self.path}') WHERE id = '{id}'").fetchone()
        if query_result:
            return User(id=query_result[0], email=query_result[1], mobile=query_result[2])
    