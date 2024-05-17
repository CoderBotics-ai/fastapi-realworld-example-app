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
    """Creates a start app handler that connects to the MongoDB database."""
    client = MongoClient(settings.DB_HOST, settings.DB_PORT)
    db = client[settings.DB_NAME]

    async def start_app() -> None:
        await db.command("ping")

    return start_app

def create_stop_app_handler(app: FastAPI) -> Callable:
    """Creates a stop app handler that closes the MongoDB connection."""
    @logger.catch
    async def stop_app() -> None:
        client: MongoClient = app.state.db_client
        client.close()

    return stop_app
