from asyncpg.connection import Connection
from pymongo.collection import Collection
from pymongo.database import Database
from typing import Any


class BaseRepository:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    @property
    def connection(self) -> Database:
        return self._db

    def get_collection(self) -> Collection:
        """Gets the MongoDB collection."""
        return self._collection
