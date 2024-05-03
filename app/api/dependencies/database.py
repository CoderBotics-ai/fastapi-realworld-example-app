from typing import AsyncGenerator, Callable, Type

from asyncpg.connection import Connection
from asyncpg.pool import Pool
from fastapi import Depends
from starlette.requests import Request

from app.db.repositories.base import BaseRepository
from pymongo.collection import Collection
from pymongo.database import Database


def _get_db_pool(request: Request) -> Pool:
    return request.app.state.pool


async def _get_connection_from_pool(
    db: Database = Depends(_get_db_pool),
) -> AsyncGenerator[Collection, None]:
    yield db.get_collection('users')


def get_repository(
    repo_type: Type[BaseRepository],
) -> Callable[[Connection], BaseRepository]:
    def _get_repo(
        conn: Connection = Depends(_get_connection_from_pool),
    ) -> BaseRepository:
        return repo_type(conn)

    return _get_repo
