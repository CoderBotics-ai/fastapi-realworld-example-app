from typing import Callable

from fastapi import FastAPI
from loguru import logger

from app.core.settings.app import AppSettings
from app.db.events import close_db_connection, connect_to_db
from pymongo import MongoClient


def create_start_app_handler(
    app: FastAPI,
    settings: AppSettings,
) -> Callable:
    """Creates a start app handler that connects to the database."""
    client = MongoClient(settings.DB_URL)
    database = client[settings.DB_NAME]

    async def start_app() -> None:
        await connect_to_db(app, database)

    return start_app

def create_stop_app_handler(app: FastAPI) -> Callable:
    """Creates a stop app handler that closes the MongoDB connection."""
    @logger.catch
    async def stop_app() -> None:
        client: MongoClient = app.state.db_client
        client.close()

    return stop_app
