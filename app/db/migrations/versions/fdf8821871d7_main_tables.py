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
    client = MongoClient()
    db = client['your_database_name']
    
    # Create a MongoDB trigger to update the 'updated_at' field
    db.command({
        "create": "update_updated_at_trigger",
        "pipeline": [
            {
                "$set": {
                    "updated_at": {"$currentDate": {"$type": "date"}}
                }
            }
        ],
        "when": "update"
    })
    client.close()

def create_users_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    users_collection = db["users"]

    users_collection.create_index("username", unique=True)
    users_collection.create_index("email", unique=True)

    # Create a sample document to ensure the collection is created with the desired schema
    sample_user = {
        "username": "sample_user",
        "email": "sample_user@example.com",
        "salt": "sample_salt",
        "hashed_password": "sample_hashed_password",
        "bio": "",
        "image": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "followers": [],
        "followings": [],
        "favorites": [],
        "comments": []
    }
    users_collection.insert_one(sample_user)
    users_collection.delete_one({"username": "sample_user"})

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
    db = client["your_database_name"]
    articles_collection = db["articles"]

    articles_collection.create_index("slug", unique=True)
    articles_collection.create_index("author_id")
    articles_collection.create_index("created_at")
    articles_collection.create_index("updated_at")

    # Ensure the collection has the necessary fields
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
    articles_collection.insert_one(sample_article)
    articles_collection.delete_one({"_id": sample_article["_id"]})

    client.close()

def create_tags_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    tags_collection = db["tags"]
    tags_collection.create_index("tag", unique=True)

def create_articles_to_tags_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]

    # Ensure indexes for the articles_to_tags collection
    db.articles_to_tags.create_index([("article_id", 1), ("tag", 1)], unique=True)
    db.articles_to_tags.create_index("article_id")
    db.articles_to_tags.create_index("tag")

    client.close()

def create_favorites_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    
    # Assuming 'users' and 'articles' collections already exist
    users_collection = db["users"]
    articles_collection = db["articles"]
    
    # No need to create a separate 'favorites' collection as we will embed the favorites in the users collection
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

def create_commentaries_table() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]

    # Create the commentaries collection with the necessary fields
    db.create_collection("commentaries")
    db.commentaries.create_index("author_id")
    db.commentaries.create_index("article_id")

    # Create the trigger equivalent in MongoDB
    # MongoDB does not support triggers natively, so we will use a change stream to simulate this
    with db.commentaries.watch([{'$match': {'operationType': 'update'}}]) as stream:
        for change in stream:
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
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]

    db.commentaries.drop()
    db.favorites.drop()
    db.articles_to_tags.drop()
    db.tags.drop()
    db.articles.drop()
    db.followers_to_followings.drop()
    db.users.drop()

    # MongoDB does not have functions like SQL, so we do not need to drop any function

    client.close()


def timestamps() -> Tuple[dict, dict]:
    return (
        {
            "created_at": datetime.utcnow(),
        },
        {
            "updated_at": datetime.utcnow(),
        },
    )
