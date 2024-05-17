from asyncpg.connection import Connection
from pymongo.collection import Collection
from pymongo.database import Database
from typing import Any


class BaseRepository:

    def __init__(self, client: MongoClient) -> None:
        """Initializes the BaseRepository with a MongoDB client."""
        self._client = client

    @property
    def connection(self) -> Database:
        return self._db

    @property
    def collection(self) -> Collection[Any]:
        return self._collection
