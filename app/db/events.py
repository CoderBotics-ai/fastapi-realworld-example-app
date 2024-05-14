import asyncpg
from fastapi import FastAPI
from loguru import logger

from app.core.settings.app import AppSettings
from motor.motor_asyncio import AsyncIOMotorClient


async def connect_to_db(app: FastAPI, settings: AppSettings) -> None:
    logger.info("Connecting to MongoDB")

    client = AsyncIOMotorClient(settings.database_url)
    app.state.db = client[settings.database_name]

    logger.info("Connection established")


async def close_db_connection(app: FastAPI) -> None:
    logger.info("Closing connection to database")

    # Assuming app.state.client is the AsyncIOMotorClient instance
    await app.state.client.close()

    logger.info("Connection closed")
