from asyncpg.connection import Connection
from pymongo.collection import Collection


class BaseRepository:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn


    @property
    def connection(self) -> Collection:
        return self._conn
