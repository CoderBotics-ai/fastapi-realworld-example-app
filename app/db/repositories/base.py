from asyncpg.connection import Connection
from bson.objectid import ObjectId
from pymongo import MongoClient




class BaseRepository:

    def __init__(self, client: MongoClient) -> None:
        self._client = client
        self._db = client.get_database()

    @property
    def connection(self) -> Connection:
        return self._conn

    def get_collection(self, collection_name: str):
        return self._db[collection_name]
