import pathlib
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_app_settings  # isort:skip

from pymongo import MongoClient
from pymongo.client_session import ClientSession

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

SETTINGS = get_app_settings()
DATABASE_URL = SETTINGS.database_url

config = context.config

fileConfig(config.config_file_name)  # type: ignore

target_metadata = None

config.set_main_option("sqlalchemy.url", str(DATABASE_URL))

def run_migrations_online() -> None:
    """Runs migrations online using PyMongo."""
    client = MongoClient(get_app_settings().MONGODB_URL)
    db = client[get_app_settings().MONGODB_DB]

    context.configure(target_metadata=target_metadata)

    with client.start_session() as session:
        with session.start_transaction():
            context.run_migrations()


run_migrations_online()
