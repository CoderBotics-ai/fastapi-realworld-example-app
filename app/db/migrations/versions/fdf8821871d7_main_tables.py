"""main tables

Revision ID: fdf8821871d7
Revises:
Create Date: 2019-09-22 01:36:44.791880

"""
from typing import Tuple

import sqlalchemy as sa
from alembic import op
from sqlalchemy import func
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from datetime import datetime

revision = "fdf8821871d7"
down_revision = None
branch_labels = None
depends_on = None


def create_users_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    users_collection = db["users"]

    users_collection.create_index([("username", ASCENDING)], unique=True)
    users_collection.create_index([("email", ASCENDING)], unique=True)

    # Assuming the timestamps function returns a tuple of created_at and updated_at fields
    created_at, updated_at = timestamps()

    # Insert a document to ensure the collection is created with the necessary fields
    users_collection.insert_one({
        "username": "",
        "email": "",
        "salt": "",
        "hashed_password": "",
        "bio": "",
        "image": "",
        "created_at": created_at,
        "updated_at": updated_at
    })

    client.close()


def create_followers_to_followings_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    users_collection: Collection = db["users"]

    # Ensure indexes for followers and followings arrays
    users_collection.create_index([("followers", ASCENDING)])
    users_collection.create_index([("followings", ASCENDING)])

    client.close()


def create_articles_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["mydatabase"]
    articles: Collection = db["articles"]

    # Create indexes
    articles.create_index([("slug", ASCENDING)], unique=True)
    articles.create_index([("author_id", ASCENDING)])
    
    # Ensure the collection exists by inserting a dummy document and then deleting it
    dummy_article = {
        "slug": "dummy",
        "title": "dummy",
        "description": "dummy",
        "body": "dummy",
        "author_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = articles.insert_one(dummy_article)
    articles.delete_one({"_id": result.inserted_id})

    client.close()


def create_tags_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    tags_collection: Collection = db["tags"]
    tags_collection.create_index([("tag", ASCENDING)], unique=True)


def create_articles_to_tags_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    
    articles_to_tags: Collection = db["articles_to_tags"]
    
    # Create indexes to ensure uniqueness and improve query performance
    articles_to_tags.create_index(
        [("article_id", ASCENDING), ("tag", ASCENDING)], 
        unique=True, 
        name="pk_articles_to_tags"
    )

    # Close the connection
    client.close()


def create_favorites_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    
    users_collection: Collection = db["users"]
    articles_collection: Collection = db["articles"]
    
    # Ensure the 'favorites' field exists in the users collection
    users_collection.update_many(
        {},
        {"$set": {"favorites": []}}
    )
    
    # Ensure the 'favorited_by' field exists in the articles collection
    articles_collection.update_many(
        {},
        {"$set": {"favorited_by": []}}
    )
    
    # Create indexes for efficient querying
    users_collection.create_index([("favorites", ASCENDING)])
    articles_collection.create_index([("favorited_by", ASCENDING)])


def create_commentaries_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]

    # Create the commentaries collection with the necessary fields
    commentaries: Collection = db["commentaries"]
    commentaries.create_index([("author_id", ASCENDING)])
    commentaries.create_index([("article_id", ASCENDING)])
    commentaries.create_index([("created_at", ASCENDING)])
    commentaries.create_index([("updated_at", ASCENDING)])

    # Create the trigger equivalent in MongoDB
    # MongoDB doesn't support triggers, so you would need to handle this in your application logic
    # For example, you could use a MongoDB change stream to watch for updates and then update the `updated_at` field

    # Example of how you might handle this in application logic:
    # This is just a placeholder and should be implemented in the actual application code
    def update_comment_modtime():
        with commentaries.watch([{"$match": {"operationType": "update"}}]) as stream:
            for change in stream:
                comment_id = change["documentKey"]["_id"]
                commentaries.update_one(
                    {"_id": comment_id},
                    {"$set": {"updated_at": datetime.utcnow()}}
                )

    # Call the function to start watching for changes
    update_comment_modtime()


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
    client = MongoClient("mongodb://localhost:27017/")
    db = client["mydatabase"]

    db["commentaries"].drop()
    db["favorites"].drop()
    db["articles_to_tags"].drop()
    db["tags"].drop()
    db["articles"].drop()
    db["followers_to_followings"].drop()
    db["users"].drop()

    # MongoDB does not have functions like SQL, so we skip the equivalent of dropping a function
    # op.execute("DROP FUNCTION update_updated_at_column")

    client.close()


def timestamps() -> Tuple[dict, dict]:
    return (
        {
            "created_at": {
                "type": "date",
                "default": datetime.utcnow,
                "required": True
            }
        },
        {
            "updated_at": {
                "type": "date",
                "default": datetime.utcnow,
                "required": True
            }
        }
    )


def create_updated_at_trigger() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]

    def add_updated_at_trigger(collection: Collection) -> None:
        collection.update_many(
            {},
            [
                {
                    "$set": {
                        "updated_at": {
                            "$cond": {
                                "if": {"$eq": ["$updated_at", None]},
                                "then": "$$NOW",
                                "else": "$updated_at"
                            }
                        }
                    }
                }
            ]
        )

    collections = ["users", "articles", "tags"]
    for collection_name in collections:
        collection = db[collection_name]
        add_updated_at_trigger(collection)

    client.close()
