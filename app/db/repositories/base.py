from asyncpg.connection import Connection
from pymongo.database import Database




class BaseRepository:

    def __init__(self, db: Database) -> None:
        self._db = db

    @property
    def connection(self) -> Connection:
        return self._conn
