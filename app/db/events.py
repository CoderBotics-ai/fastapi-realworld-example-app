import asyncpg
from fastapi import FastAPI
from loguru import logger

from app.core.settings.app import AppSettings
from typing import None
from pymongo import MongoClient

async def close_db_connection(app: FastAPI) -> None:
    """Closes the connection to the MongoDB database."""
    logger.info("Closing connection to database")

    app.state.mongo_client.close()

    logger.info("Connection closed")


async def connect_to_db(app: FastAPI, settings: AppSettings) -> None:
    """Connects to the MongoDB database."""
    logger.info("Connecting to MongoDB")

    client = MongoClient(str(settings.database_url))
    app.state.db = client[settings.database_name]

    logger.info("Connection established")
