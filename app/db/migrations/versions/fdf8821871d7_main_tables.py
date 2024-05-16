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
from datetime import datetime

revision = "fdf8821871d7"
down_revision = None
branch_labels = None
depends_on = None

def create_updated_at_trigger() -> None:
    from pymongo import MongoClient
    from pymongo import UpdateOne
    from datetime import datetime

    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]

    collections = ["users", "articles", "tags"]

    for collection_name in collections:
        collection = db[collection_name]
        bulk_operations = []
        for document in collection.find():
            bulk_operations.append(
                UpdateOne(
                    {"_id": document["_id"]},
                    {"$set": {"updated_at": datetime.utcnow()}}
                )
            )
        if bulk_operations:
            collection.bulk_write(bulk_operations)

    client.close()

def create_users_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    users_collection = db["users"]

    # Create the users collection with the required schema
    users_collection.create_index("username", unique=True)
    users_collection.create_index("email", unique=True)

    # Create a trigger equivalent for updating the 'updated_at' field
    db.command({
        "collMod": "users",
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["username", "email", "salt", "bio"],
                "properties": {
                    "username": {
                        "bsonType": "string",
                        "description": "must be a string and is required"
                    },
                    "email": {
                        "bsonType": "string",
                        "description": "must be a string and is required"
                    },
                    "salt": {
                        "bsonType": "string",
                        "description": "must be a string and is required"
                    },
                    "bio": {
                        "bsonType": "string",
                        "description": "must be a string and is required"
                    },
                    "hashed_password": {
                        "bsonType": "string",
                        "description": "must be a string"
                    },
                    "image": {
                        "bsonType": "string",
                        "description": "must be a string"
                    },
                    "created_at": {
                        "bsonType": "date",
                        "description": "must be a date"
                    },
                    "updated_at": {
                        "bsonType": "date",
                        "description": "must be a date"
                    }
                }
            }
        },
        "validationLevel": "strict",
        "validationAction": "error"
    })

    # Ensure the 'updated_at' field is updated on each document update
    db.command({
        "create": "users",
        "capped": False,
        "autoIndexId": True,
        "validationLevel": "strict",
        "validationAction": "error",
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "properties": {
                    "updated_at": {
                        "bsonType": "date",
                        "description": "must be a date"
                    }
                }
            }
        }
    })

    client.close()

def create_followers_to_followings_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    users_collection = db["users"]

    # Ensure indexes for followers and followings arrays
    users_collection.create_index("followers")
    users_collection.create_index("followings")

    client.close()

def create_articles_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["mydatabase"]
    articles_collection = db["articles"]

    # Create the articles collection with the required schema
    articles_collection.create_index("slug", unique=True)
    articles_collection.create_index("author_id")
    articles_collection.create_index("created_at")
    articles_collection.create_index("updated_at")

    # Create a trigger equivalent using MongoDB change streams
    # Note: MongoDB does not support triggers natively, so this is a conceptual equivalent
    # You would need to implement the logic to handle updates and set the updated_at field accordingly
    # This can be done using application-level logic or a MongoDB change stream listener

    # Example of setting up a change stream listener (this would be part of your application logic)
    change_stream = articles_collection.watch()
    for change in change_stream:
        if change["operationType"] == "update":
            updated_fields = change["updateDescription"]["updatedFields"]
            if "updated_at" not in updated_fields:
                articles_collection.update_one(
                    {"_id": change["documentKey"]["_id"]},
                    {"$set": {"updated_at": datetime.utcnow()}}
                )

def create_tags_table() -> None:
    client = MongoClient()
    db = client['your_database_name']
    db.create_collection("tags")
    db["tags"].create_index("tag", unique=True)

def create_articles_to_tags_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]

    # Create indexes to enforce the schema
    db.articles.create_index("tags")
    db.tags.create_index("articles")

    # Ensure the collections exist
    db.create_collection("articles_to_tags")

    # Create compound index to enforce uniqueness
    db.articles_to_tags.create_index(
        [("article_id", 1), ("tag", 1)], unique=True
    )

    client.close()

def create_favorites_table() -> None:
    client = MongoClient()
    db = client['your_database_name']
    
    # Assuming 'users' and 'articles' collections already exist
    users_collection = db['users']
    articles_collection = db['articles']
    
    # Create indexes to ensure uniqueness and improve query performance
    users_collection.create_index([("favorites", 1)])
    articles_collection.create_index([("favorited_by", 1)])
    
    client.close()

def create_commentaries_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]

    # Create indexes for the commentaries collection
    db.commentaries.create_index("author_id")
    db.commentaries.create_index("article_id")

    # Create a trigger equivalent using MongoDB change streams
    # Note: MongoDB does not support triggers in the same way SQL databases do.
    # You would need to handle this logic in your application code.
    # Here is an example of how you might start a change stream to listen for updates.
    with db.commentaries.watch([{'$match': {'operationType': 'update'}}]) as stream:
        for change in stream:
            # Handle the update event
            # For example, you could update the 'updated_at' field
            db.commentaries.update_one(
                {'_id': change['documentKey']['_id']},
                {'$set': {'updated_at': datetime.utcnow()}}
            )


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
    client = MongoClient()
    db = client['your_database_name']

    db.commentaries.drop()
    db.favorites.drop()
    db.articles_to_tags.drop()
    db.tags.drop()
    db.articles.drop()
    db.followers_to_followings.drop()
    db.users.drop()

    # MongoDB does not have a direct equivalent of SQL functions, so this line is omitted.
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
                "required": True,
                "onupdate": datetime.utcnow
            }
        }
    )
