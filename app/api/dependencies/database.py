from typing import AsyncGenerator, Callable, Type

from asyncpg.connection import Connection
from asyncpg.pool import Pool
from fastapi import Depends
from starlette.requests import Request

from app.db.repositories.base import BaseRepository
from pymongo.database import Database
from typing import AsyncGenerator


def _get_db_pool(request: Request) -> Database:
    return request.app.state.db


def get_repository(
    repo_type: Type[BaseRepository],
) -> Callable[[Database], BaseRepository]:
    def _get_repo(
        db: Database = Depends(_get_connection_from_pool),
    ) -> BaseRepository:
        return repo_type(db)

    return _get_repo


async def _get_connection_from_pool(
    pool: Database = Depends(_get_db_pool),
) -> AsyncGenerator[Database, None]:
    yield pool
