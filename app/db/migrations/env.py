import pathlib
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_app_settings  # isort:skip
from pymongo import MongoClient
from bson.objectid import ObjectId

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

SETTINGS = get_app_settings()
DATABASE_URL = SETTINGS.database_url

config = context.config

fileConfig(config.config_file_name)  # type: ignore

target_metadata = None

config.set_main_option("sqlalchemy.url", str(DATABASE_URL))


def run_migrations_online() -> None:
    settings = get_app_settings()
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB_NAME]

    with client:
        db.users.insert_many([
            {
                "_id": ObjectId(),
                "username": "String",
                "email": "String",
                "salt": "String",
                "hashed_password": "String",
                "bio": "String",
                "image": "String",
                "created_at": "ISODate",
                "updated_at": "ISODate",
                "followers": [ObjectId()],
                "followings": [ObjectId()],
                "favorites": [ObjectId()],
                "comments": [
                    {
                        "comment_id": ObjectId(),
                        "body": "String",
                        "article_id": ObjectId(),
                        "created_at": "ISODate",
                        "updated_at": "ISODate"
                    }
                ]
            },
            # Add more user documents as needed
        ])

        db.articles.insert_many([
            {
                "_id": ObjectId(),
                "slug": "String",
                "title": "String",
                "description": "String",
                "body": "String",
                "author_id": ObjectId(),
                "tags": ["String"],
                "created_at": "ISODate",
                "updated_at": "ISODate",
                "favorited_by": [ObjectId()],
                "comments": [ObjectId()]
            },
            # Add more article documents as needed
        ])

        db.tags.insert_many([
            {
                "tag": "String",
                "articles": [ObjectId()]
            },
            # Add more tag documents as needed
        ])


run_migrations_online()
