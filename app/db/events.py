import asyncpg
from fastapi import FastAPI
from loguru import logger

from app.core.settings.app import AppSettings

async def connect_to_db(app: FastAPI, settings: AppSettings) -> None:
    logger.info("Connecting to MongoDB")

    client = AsyncIOMotorClient(str(settings.database_url))
    app.state.db = client.get_default_database()

    logger.info("Connection established")

async def close_db_connection(app: FastAPI) -> None:
    logger.info("Closing connection to database")

    await app.state.db_client.close()

    logger.info("Connection closed")
