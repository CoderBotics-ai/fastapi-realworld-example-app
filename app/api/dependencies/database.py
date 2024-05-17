from typing import AsyncGenerator, Callable, Type

from asyncpg.connection import Connection
from asyncpg.pool import Pool
from fastapi import Depends
from starlette.requests import Request

from app.db.repositories.base import BaseRepository
from pymongo import MongoClient
from pymongo.database import Database

async def _get_connection_from_pool(
    pool: MongoClient = Depends(_get_db_pool),
) -> AsyncGenerator[Database, None]:
    async with pool.start_session() as session:
        yield session.client.get_database()

def get_repository(
    repo_type: Type[BaseRepository],
) -> Callable[[Database], BaseRepository]:
    def _get_repo(
        db: Database = Depends(_get_db_pool),
    ) -> BaseRepository:
        return repo_type(db)

    return _get_repo


def _get_db_pool(request: Request) -> Database:
    """Get the MongoDB database instance from the request."""
    return MongoClient(request.app.state.mongo_uri)[request.app.state.db_name]
