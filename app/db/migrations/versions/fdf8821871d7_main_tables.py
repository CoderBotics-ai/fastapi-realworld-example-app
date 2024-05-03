"""main tables

Revision ID: fdf8821871d7
Revises:
Create Date: 2019-09-22 01:36:44.791880

"""
from typing import Tuple

import sqlalchemy as sa
from alembic import op
from sqlalchemy import func

revision = "fdf8821871d7"
down_revision = None
branch_labels = None
depends_on = None

def create_updated_at_trigger() -> None:
    # MongoDB does not support triggers like SQL databases. 
    # This function will be left empty as MongoDB uses a different approach for handling such operations.
    pass


def timestamps() -> Tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.current_timestamp(),
        ),
    )

def create_users_table() -> None:
    db = client.get_database("your_database_name")
    users_collection = db.get_collection("users")

    users_collection.create_index([("username", pymongo.ASCENDING)], unique=True)
    users_collection.create_index([("email", pymongo.ASCENDING)], unique=True)

def create_followers_to_followings_table() -> None:
    # Since MongoDB does not use tables or schemas in the same way SQL databases do,
    # and the followers and followings are stored as arrays of ObjectIds in the user documents,
    # there is no need to create a separate table or collection for followers to followings.
    # This function will therefore be an empty operation in the context of MongoDB.
    pass

def create_articles_table() -> None:
    db = client.get_database("your_database_name")
    articles_collection = db.get_collection("articles")

    # Create indexes for the articles collection
    articles_collection.create_index([("slug", pymongo.ASCENDING)], unique=True)
    articles_collection.create_index([("author_id", pymongo.ASCENDING)])

    # Assuming the timestamps function provides created_at and updated_at fields
    # and that these fields are managed by the application logic or MongoDB's internal mechanisms

def create_tags_table() -> None:
    db = op.get_bind()
    db["tags"].create_index([("tag", pymongo.ASCENDING)], unique=True)

def create_articles_to_tags_table() -> None:
    db = op.get_database()
    articles_collection = db.get_collection("articles")
    tags_collection = db.get_collection("tags")

    # Ensure the 'tags' field exists in articles collection and is an array
    articles_collection.update_many(
        {},
        {"$set": {"tags": []}},
        upsert=False
    )

    # Ensure the 'articles' field exists in tags collection and is an array
    tags_collection.update_many(
        {},
        {"$set": {"articles": []}},
        upsert=False
    )

    # Create indexes to efficiently query by tags and articles
    articles_collection.create_index([("tags", 1)])
    tags_collection.create_index([("articles", 1)])

def create_favorites_table() -> None:
    # In MongoDB, we do not need to explicitly create tables (collections) or define their schema ahead of time.
    # The 'favorites' functionality can be handled by adding an array of article ObjectIds to the user document.
    # This function is left intentionally empty because MongoDB handles this dynamically.
    pass

def create_commentaries_table() -> None:
    db = client.get_database("your_database_name")
    db.create_collection("commentaries")
    db.commentaries.create_index([("author_id", pymongo.ASCENDING)], unique=False)
    db.commentaries.create_index([("article_id", pymongo.ASCENDING)], unique=False)
    db.command({
        "collMod": "commentaries",
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["body", "author_id", "article_id"],
                "properties": {
                    "body": {
                        "bsonType": "string",
                        "description": "must be a string and is required"
                    },
                    "author_id": {
                        "bsonType": "objectId",
                        "description": "must be an objectId and is required"
                    },
                    "article_id": {
                        "bsonType": "objectId",
                        "description": "must be an objectId and is required"
                    }
                }
            }
        }
    })


def upgrade() -> None:
    create_updated_at_trigger()
    create_users_table()
    create_followers_to_followings_table()
    create_articles_table()
    create_tags_table()
    create_articles_to_tags_table()
    create_favorites_table()
    create_commentaries_table()

def downgrade() -> None:
    db = op.get_database()
    db.drop_collection("users")
    db.drop_collection("articles")
    db.drop_collection("tags")
    db.drop_collection("commentaries")
    db.command("drop", "update_updated_at_column")
