import duckdb
import boto3

from models.open_position import OpenPosition
import os

class BaseRepository():
    def __init__(self, path):
        if path.startswith("s3://"):
            s3 = boto3.client('s3')
            s3.download_file(path.split('/')[2], '/'.join(path.split('/')[3:]), 'temp.csv')
            self.conn = duckdb.connect()
            self.path = 'temp.csv'
        else:
            # Local path
            self.conn = duckdb.connect(database=':memory:')
            self.path = path
            