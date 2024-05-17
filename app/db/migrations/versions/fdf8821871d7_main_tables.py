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
from pymongo.collection import Collection
from pymongo.database import Database

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from bson import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db: Database = client['mydatabase']


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
    client: MongoClient = MongoClient("mongodb://localhost:27017/")
    db: Database = client["your_database_name"]
    users_collection: Collection = db["users"]

    # Create the users collection with the required schema
    users_collection.create_index("username", unique=True)
    users_collection.create_index("email", unique=True)

    # Add a trigger equivalent for updating 'updated_at' on document update
    # MongoDB does not support triggers, so this would need to be handled in the application logic

    # Close the connection
    client.close()


def create_tags_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db: Database = client["your_database_name"]
    tags_collection: Collection = db["tags"]

    # Create the tags collection with the required schema
    tags_collection.create_index("tag", unique=True)


def create_articles_to_tags_table() -> None:
    client: MongoClient = MongoClient("mongodb://localhost:27017/")
    db: Database = client["your_database_name"]
    
    articles_collection: Collection = db["articles"]
    tags_collection: Collection = db["tags"]

    # Ensure indexes for fast lookup and uniqueness
    articles_collection.create_index("tags")
    tags_collection.create_index("articles")

    # Close the client connection
    client.close()


def create_favorites_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db: Database = client["your_database_name"]
    users_collection: Collection = db["users"]
    articles_collection: Collection = db["articles"]

    # Ensure indexes for user favorites
    users_collection.create_index("favorites")
    articles_collection.create_index("favorited_by")

    client.close()


def downgrade() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db: Database = client["mydatabase"]

    # Drop collections
    db["commentaries"].drop()
    db["favorites"].drop()
    db["articles_to_tags"].drop()
    db["tags"].drop()
    db["articles"].drop()
    db["followers_to_followings"].drop()
    db["users"].drop()

    # MongoDB does not have functions like SQL, so no equivalent for dropping a function
    # op.execute("DROP FUNCTION update_updated_at_column")


def create_commentaries_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db: Database = client["your_database_name"]
    commentaries: Collection = db["commentaries"]

    # Ensure indexes for foreign keys and timestamps
    commentaries.create_index("author_id")
    commentaries.create_index("article_id")
    commentaries.create_index("created_at")
    commentaries.create_index("updated_at")

    # Create a trigger equivalent using MongoDB's change streams if necessary
    # Note: MongoDB does not support triggers natively like SQL databases.
    # You might need to implement application-level logic to handle such cases.

    # Example of inserting a document to ensure the collection is created
    commentaries.insert_one({
        "body": "",
        "author_id": ObjectId(),
        "article_id": ObjectId(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    # Remove the example document
    commentaries.delete_one({"body": ""})


def upgrade() -> None:
    create_updated_at_trigger()
    create_users_table()
    create_followers_to_followings_table()
    create_articles_table()
    create_tags_table()
    create_articles_to_tags_table()
    create_favorites_table()
    create_commentaries_table()


def create_followers_to_followings_table() -> None:
    client: MongoClient = MongoClient("mongodb://localhost:27017/")
    db: Database = client["your_database_name"]
    users_collection: Collection = db["users"]

    # Ensure indexes for followers and followings arrays
    users_collection.create_index("followers")
    users_collection.create_index("followings")


def create_articles_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db: Database = client["mydatabase"]
    articles: Collection = db["articles"]

    # Ensure indexes
    articles.create_index("slug", unique=True)
    articles.create_index("author_id")
    articles.create_index("created_at")
    articles.create_index("updated_at")

    # Create a sample document to ensure the collection is created with the correct schema
    sample_article = {
        "slug": "",
        "title": "",
        "description": "",
        "body": "",
        "author_id": None,
        "tags": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "favorited_by": [],
        "comments": []
    }
    articles.insert_one(sample_article)
    articles.delete_one({"_id": sample_article["_id"]})

    client.close()

revision = "fdf8821871d7"
down_revision = None
branch_labels = None
depends_on = None


def create_updated_at_trigger() -> None:
    client: MongoClient = MongoClient("mongodb://localhost:27017/")
    db: Database = client["your_database_name"]
    collection: Collection = db["your_collection_name"]

    # Create an index to automatically update the `updated_at` field on document updates
    collection.create_index(
        [("updated_at", 1)],
        name="updated_at_index",
        partialFilterExpression={"updated_at": {"$exists": True}}
    )

    # Create a change stream to listen for updates and modify the `updated_at` field
    with collection.watch([{"$match": {"operationType": "update"}}]) as stream:
        for change in stream:
            document_id = change["documentKey"]["_id"]
            collection.update_one(
                {"_id": document_id},
                {"$set": {"updated_at": change["clusterTime"].as_datetime()}}
            )
