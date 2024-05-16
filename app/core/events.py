from typing import Callable

from fastapi import FastAPI
from loguru import logger

from app.core.settings.app import AppSettings
from app.db.events import close_db_connection, connect_to_db
from motor.motor_asyncio import AsyncIOMotorClient


def create_start_app_handler(
    app: FastAPI,
    settings: AppSettings,
) -> Callable:  # type: ignore
    async def start_app() -> None:
        app.state.mongodb_client = AsyncIOMotorClient(settings.mongodb_url)
        app.state.mongodb = app.state.mongodb_client[settings.mongodb_db]
        logger.info("Connected to MongoDB")

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:  # type: ignore
    @logger.catch
    async def stop_app() -> None:
        await close_db_connection(app)

    return stop_app
