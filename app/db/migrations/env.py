import pathlib
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_app_settings  # isort:skip
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from bson.objectid import ObjectId
from datetime import datetime
from typing import List, Dict, Any

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from bson.objectid import ObjectId
from datetime import datetime
from typing import List, Dict, Any

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

SETTINGS = get_app_settings()
DATABASE_URL = SETTINGS.database_url

config = context.config

fileConfig(config.config_file_name)  # type: ignore

target_metadata = None

config.set_main_option("sqlalchemy.url", str(DATABASE_URL))


def run_migrations_online() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db: Database = client["your_database_name"]

    # Assuming you have a collection named 'migrations' to track migration status
    migrations_collection: Collection = db["migrations"]

    # Example migration: Add a new field to all user documents
    users_collection: Collection = db["users"]
    users_collection.update_many(
        {},
        {"$set": {"new_field": "default_value"}}
    )

    # Log the migration
    migrations_collection.insert_one({
        "migration_id": ObjectId(),
        "description": "Added new_field to users collection",
        "applied_at": datetime.utcnow()
    })

    client.close()


run_migrations_online()
