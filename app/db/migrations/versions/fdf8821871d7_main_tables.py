"""main tables

Revision ID: fdf8821871d7
Revises:
Create Date: 2019-09-22 01:36:44.791880

"""
from typing import Tuple

import sqlalchemy as sa
from alembic import op
from sqlalchemy import func

from pymongo import MongoClient
from pymongo.database import Database

revision = "fdf8821871d7"
down_revision = None
branch_labels = None
depends_on = None

def timestamps() -> Tuple[dict, dict]:
    """Returns two dictionaries representing the created_at and updated_at fields."""
    return (
        {"created_at": {"type": "ISODate"}},
        {"updated_at": {"type": "ISODate"}},
    )

def create_users_table() -> None:
    """Creates the users table in the database."""
    client: MongoClient = MongoClient()
    db: Database = client["mydatabase"]
    db.create_collection("users")
    db["users"].create_index("username", unique=True)
    db["users"].create_index("email", unique=True)
    db["users"].create_index("created_at")
    db["users"].create_index("updated_at")

def create_followers_to_followings_table() -> None:
    """Creates the followers_to_followings collection in the database."""
    db: Database = MongoClient()["database_name"]
    db.create_collection("followers_to_followings")
    db["followers_to_followings"].create_index([("follower_id", 1), ("following_id", 1)], unique=True)

def create_articles_table() -> None:
    """Creates the articles table in the database."""
    client: MongoClient = MongoClient()
    db: Database = client["database"]
    db.create_collection("articles")
    db["articles"].create_index("slug", unique=True)
    db["articles"].create_index("author_id")
    db["articles"].create_index("created_at")
    db["articles"].create_index("updated_at")

def create_tags_table() -> None:
    """Creates a tags collection in the database."""
    client: MongoClient = MongoClient()
    db: Database = client["database"]
    db.create_collection("tags")

def create_articles_to_tags_table() -> None:
    """Creates the articles_to_tags collection in the database."""
    db: Database = MongoClient()["database_name"]
    db.create_collection("articles_to_tags")
    db["articles_to_tags"].create_index([("article_id", 1), ("tag", 1)], unique=True)

def create_favorites_table() -> None:
    """Creates the favorites table in the database."""
    db: Database = MongoClient()["database_name"]
    db.create_collection("favorites")
    db["favorites"].create_index([("user_id", 1), ("article_id", 1)], unique=True)

def create_commentaries_table() -> None:
    """Creates the commentaries collection in the database."""
    db: Database = MongoClient()["database_name"]
    db.create_collection("commentaries")
    db["commentaries"].create_index("author_id")
    db["commentaries"].create_index("article_id")

def upgrade() -> None:
    """Upgrades the database schema."""
    client: MongoClient = MongoClient()
    db: Database = client.get_database()
    db.create_collection("users")
    db.create_collection("articles")
    db.create_collection("tags")
    db.create_collection("articles_to_tags")
    db.create_collection("favorites")
    db.create_collection("commentaries")
    timestamps()
    create_users_table()
    create_followers_to_followings_table()
    create_articles_table()
    create_tags_table()
    create_articles_to_tags_table()
    create_favorites_table()
    create_commentaries_table()
    create_updated_at_trigger()

def downgrade() -> None:
    """Drops all collections in the database."""
    client: MongoClient = MongoClient()
    db: Database = client.get_database()
    db["commentaries"].drop()
    db["favorites"].drop()
    db["articles_to_tags"].drop()
    db["tags"].drop()
    db["articles"].drop()
    db["followers_to_followings"].drop()
    db["users"].drop()
    db.command({"drop": "update_updated_at_column"})

def create_updated_at_trigger() -> None:
    """Creates a trigger to update the 'updated_at' field in the database."""
    from pymongo.database import Database
    db: Database = ...  # assuming db is already defined
    db.create_collection("system.version", validator={"$jsonSchema": {"bsonType": "object", "required": ["updated_at"], "properties": {"updated_at": {"bsonType": "date"}}}})
    db.command({"collMod": "users", "validator": {"$jsonSchema": {"bsonType": "object", "required": ["updated_at"], "properties": {"updated_at": {"bsonType": "date"}}}}})
    db.command({"collMod": "articles", "validator": {"$jsonSchema": {"bsonType": "object", "required": ["updated_at"], "properties": {"updated_at": {"bsonType": "date"}}}}})
    db.command({"collMod": "tags", "validator": {"$jsonSchema": {"bsonType": "object", "required": ["updated_at"], "properties": {"updated_at": {"bsonType": "date"}}}}})
