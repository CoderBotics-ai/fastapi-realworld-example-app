import pathlib
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_app_settings  # isort:skip

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

SETTINGS = get_app_settings()
DATABASE_URL = SETTINGS.database_url

config = context.config

fileConfig(config.config_file_name)  # type: ignore

target_metadata = None

config.set_main_option("sqlalchemy.url", str(DATABASE_URL))

def run_migrations_online() -> None:
    client = MongoClient(get_app_settings().MONGO_URI)
    db = client.get_default_database()

    # Assuming migrations involve setting up collections and indexes
    # Example collections: users, articles, tags
    # This is a placeholder for actual migration logic which would be specific to the application needs

    # Setup users collection
    db.create_collection("users")
    db.users.create_index([("username", pymongo.ASCENDING)], unique=True)
    db.users.create_index([("email", pymongo.ASCENDING)], unique=True)

    # Setup articles collection
    db.create_collection("articles")
    db.articles.create_index([("slug", pymongo.ASCENDING)], unique=True)

    # Setup tags collection
    db.create_collection("tags")
    db.tags.create_index([("tag", pymongo.ASCENDING)], unique=True)

    client.close()


run_migrations_online()
