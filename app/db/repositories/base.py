from asyncpg.connection import Connection
from pymongo.collection import Collection
from pymongo.database import Database
from typing import Optional


class BaseRepository:

    def __init__(self, db: Optional[Database], collection: Optional[str]) -> None:
        """Initializes the BaseRepository with a MongoDB database and collection."""
        self._db = db
        self._collection: Collection = db[collection]

    @property
    def connection(self) -> Database:
        return self._conn
