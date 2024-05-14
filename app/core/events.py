from typing import Callable

from fastapi import FastAPI
from loguru import logger

from app.core.settings.app import AppSettings
from app.db.events import close_db_connection, connect_to_db
from pymongo import MongoClient
from pymongo.server_api import ServerApi



def create_start_app_handler(
    app: FastAPI,
    settings: AppSettings,
) -> Callable:  # type: ignore
    async def start_app() -> None:
        client = MongoClient(settings.DB_URI, server_api=ServerApi('1'))
        try:
            await client.admin.command('ping')
            logger.info("Connected to MongoDB")
            app.mongodb_client = client
            app.mongodb = client[settings.DB_NAME]
        except Exception as e:
            logger.error("Failed to connect to MongoDB", exc_info=True)

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:  # type: ignore
    @logger.catch
    async def stop_app() -> None:
        await close_db_connection(app)

    return stop_app
