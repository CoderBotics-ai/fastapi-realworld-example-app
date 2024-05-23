import asyncpg
from fastapi import FastAPI
from loguru import logger

from app.core.settings.app import AppSettings
from pymongo import MongoClient


async def connect_to_db(app: FastAPI, settings: AppSettings) -> None:
    logger.info("Connecting to MongoDB")

    client = MongoClient(settings.database_url)
    app.state.db = client.get_database()

    logger.info("Connection established")


async def close_db_connection(app: FastAPI) -> None:
    logger.info("Closing connection to database")

    app.state.mongo_client.close()

    logger.info("Connection closed")
