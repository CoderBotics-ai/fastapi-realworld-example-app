from typing import AsyncGenerator, Callable, Type

from asyncpg.connection import Connection
from asyncpg.pool import Pool
from fastapi import Depends
from starlette.requests import Request

from app.db.repositories.base import BaseRepository
from pymongo import MongoClient
from pymongo.client import MongoClient as MongoPool

async def _get_connection_from_pool(
    pool: MongoClient = Depends(_get_db_pool),
) -> AsyncGenerator[MongoClient, None]:
    async with pool.start_session() as session:
        yield session

def get_repository(
    repo_type: Type[BaseRepository],
) -> Callable[[MongoClient], BaseRepository]:
    def _get_repo(
        client: MongoClient = Depends(_get_db_pool),
    ) -> BaseRepository:
        return repo_type(client)

    return _get_repo


def _get_db_pool(request: Request) -> MongoClient:
    return request.app.state.pool
