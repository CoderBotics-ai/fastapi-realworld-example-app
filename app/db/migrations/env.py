import pathlib
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_app_settings  # isort:skip
from pymongo import MongoClient
from pymongo.database import Database

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

SETTINGS = get_app_settings()
DATABASE_URL = SETTINGS.database_url

config = context.config

fileConfig(config.config_file_name)  # type: ignore

target_metadata = None

config.set_main_option("sqlalchemy.url", str(DATABASE_URL))


def run_migrations_online() -> None:
    """Run migrations online."""
    client: MongoClient = MongoClient(get_app_settings().MONGODB_URL)
    database: Database = client.get_database(get_app_settings().MONGODB_DB)
    context.configure(target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


run_migrations_online()
