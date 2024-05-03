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

    # Assuming the migrations involve setting up collections and indexes
    # Here we just simulate the migration process as no specific migrations are detailed
    collections = ["users", "articles", "tags"]
    for collection_name in collections:
        collection = db[collection_name]
        # Example: Ensuring an index on 'username' for the 'users' collection
        if collection_name == "users":
            collection.create_index("username", unique=True)
        elif collection_name == "articles":
            collection.create_index("slug", unique=True)
        elif collection_name == "tags":
            collection.create_index("tag", unique=True)

    client.close()


run_migrations_online()
