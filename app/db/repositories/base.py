from asyncpg.connection import Connection
from pymongo.collection import Collection
from pymongo.database import Database


class BaseRepository:

    def __init__(self, db: Database) -> None:
        self._db = db


    @property
    def connection(self) -> Database:
        return self._conn
