"""main tables

Revision ID: fdf8821871d7
Revises:
Create Date: 2019-09-22 01:36:44.791880

"""
from typing import Tuple

import sqlalchemy as sa
from alembic import op
from sqlalchemy import func
from datetime import datetime
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from bson.objectid import ObjectId
from bson.son import SON
from typing import List

def create_users_table() -> None:
    users_collection: Collection = db["users"]
    users_collection.insert_one(
        {
            "_id": ObjectId(),
            "username": "",
            "email": "",
            "salt": "",
            "hashed_password": "",
            "bio": "",
            "image": "",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "followers": [],
            "followings": [],
            "favorites": [],
            "comments": [],
        }
    )

revision = "fdf8821871d7"


def create_articles_table() -> None:
    # Assuming the MongoClient instance is available in the scope or can be created
    # If not, you need to create a MongoClient instance and connect to the database
    # client = MongoClient('mongodb://localhost:27017/')
    # db = client['your_database_name']

    # Define the collection schema
    articles_collection = db['articles']

    # Create indexes on the collection
    articles_collection.create_index([('slug', 1)], unique=True)

    # No need to create a trigger in MongoDB as it automatically updates the 'updated_at' field
    # when a document is updated.


def create_tags_table(db: Database) -> None:
    """
    Creates a collection in the MongoDB database for tags.

    Args:
        db (Database): The MongoDB database instance.
    """
    tags_collection: Collection = db["tags"]
    tags_collection.create_index("tag", unique=True)

def create_articles_to_tags_table(db: Database) -> None:
    articles_collection = db["articles"]
    tags_collection = db["tags"]

    # Create an index on 'slug' field for 'articles' collection
    articles_collection.create_index([("slug", 1)], unique=True)

    # Create an index on 'tag' field for 'tags' collection
    tags_collection.create_index([("tag", 1)], unique=True)

    # Create a compound index on 'article_id' and 'tag' fields for 'articles_to_tags' collection
    articles_to_tags_collection = db["articles_to_tags"]
    articles_to_tags_collection.create_index([("article_id", 1), ("tag", 1)], unique=True)

    # Create a compound index on 'author_id' and 'created_at' fields for 'articles' collection
    articles_collection.create_index([("author_id", 1), ("created_at", -1)])

    # Create a compound index on 'author_id' and 'created_at' fields for 'comments' collection
    comments_collection = db["comments"]
    comments_collection.create_index([("article_id", 1), ("created_at", -1)])


def create_favorites_table(db: Database) -> None:
    """
    Creates a collection in MongoDB to store favorites.
    """
    favorites_collection = db.favorites
    favorites_collection.create_index(
        [("user_id", 1), ("article_id", 1)],
        unique=True,
        name="idx_favorites_user_article",
    )

def upgrade() -> None:
    db = MongoClient('mongodb://localhost:27017/')['your_database_name']
    
    # Create collections
    create_users_collection(db)
    create_articles_collection(db)
    create_tags_collection(db)
    create_favorites_collection(db)
    create_commentaries_collection(db)
    
    # Create indexes
    db.users.create_index([("username", pymongo.ASCENDING)], unique=True)
    db.users.create_index([("email", pymongo.ASCENDING)], unique=True)
    db.articles.create_index([("slug", pymongo.ASCENDING)], unique=True)
    db.tags.create_index([("tag", pymongo.ASCENDING)])

    # Add triggers or hooks for updating 'updated_at' field
    db.users.update_one({"_id": {"$exists": True}}, {"$set": {"updated_at": datetime.utcnow()}}, upsert=True)
    db.articles.update_one({"_id": {"$exists": True}}, {"$set": {"updated_at": datetime.utcnow()}}, upsert=True)
    db.tags.update_one({"_id": {"$exists": True}}, {"$set": {"updated_at": datetime.utcnow()}}, upsert=True)

    # Add follower or following
    add_follower_or_following(db.users, ObjectId(), ObjectId())

    # Add favorite
    add_favorite(db.users, ObjectId(), ObjectId())

    # Add comment
    add_comment(db.users, ObjectId(), ObjectId())

    # Add article tag
    add_article_tag(db.tags, ObjectId(), "tag_name")

def downgrade() -> None:
    db = MongoClient().get_database()  # Assuming MongoClient instance is available in the scope
    collections = [
        "users",
        "articles",
        "tags",
        "articles_to_tags",
        "favorites",
        "commentaries",
        "followers_to_followings",
    ]
    for collection_name in collections:
        collection = db[collection_name]
        collection.drop()

def create_commentaries_collection(db: Database) -> None:
    collection = db["commentaries"]
    collection.create_index("author_id", unique=False)
    collection.create_index("article_id", unique=False)

    # Assuming the timestamps function has been migrated to return appropriate fields for MongoDB
    timestamps_fields = timestamps()
    collection.create_index(timestamps_fields[0], expireAfterSeconds=0)
    collection.create_index(timestamps_fields[1], expireAfterSeconds=0)


# Assuming the MongoClient instance is available in the scope or can be created
# If not, you need to create a MongoClient instance and connect to the database
# client = MongoClient('mongodb://localhost:27017/')
# db = client['your_database_name']

def add_follower_or_following(collection: Collection, user_id: ObjectId, target_id: ObjectId) -> None:
    """Add a follower or following to a user's list."""
    user = collection.find_one({"_id": user_id})
    if user:
        if target_id not in user.get("followers", []) and target_id not in user.get("followings", []):
            if target_id in user.get("followers", []):
                collection.update_one({"_id": user_id}, {"$pull": {"followers": target_id}})
            if target_id in user.get("followings", []):
                collection.update_one({"_id": user_id}, {"$pull": {"followings": target_id}})
            collection.update_one({"_id": user_id}, {"$addToSet": {"followers": target_id, "followings": target_id}})


# Assuming the MongoClient instance is available in the scope or can be created
# If not, you need to create a MongoClient instance and connect to the database
# client = MongoClient('mongodb://localhost:27017/')
# db = client['your_database_name']

def timestamps() -> Tuple[dict, dict]:
    return (
        {"created_at": {"$type": 9, "$date": datetime.utcnow()}},
        {"updated_at": {"$type": 9, "$date": datetime.utcnow()}}
    )
down_revision = None
branch_labels = None
depends_on = None

def create_updated_at_trigger() -> None:
    # This function does not need to execute any code since MongoDB does not support triggers
    # Instead, the 'updated_at' field should be updated in the application code before saving
    pass


# Assuming the MongoClient instance is available in the scope or can be created
# If not, you need to create a MongoClient instance and connect to the database
# client = MongoClient('mongodb://localhost:27017/')
# db = client['your_database_name']

def update_updated_at_field(collection: Collection, document: dict) -> dict:
    """Update the 'updated_at' field with the current datetime before saving the document."""
    document['updated_at'] = datetime.utcnow()
    return document

# Example usage in a function that saves a document
def save_document(collection: Collection, document: dict) -> Any:
    # Update the 'updated_at' field before saving
    updated_document = update_updated_at_field(collection, document)
    return collection.insert_one(updated_document).inserted_id


def create_followers_to_followings_table() -> None:
    op.create_table(
        "followers_to_followings",
        sa.Column(
            "follower_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "following_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    op.create_primary_key(
        "pk_followers_to_followings",
        "followers_to_followings",
        ["follower_id", "following_id"],
    )


def create_commentaries_table() -> None:
    op.create_table(
        "commentaries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "author_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "article_id",
            sa.Integer,
            sa.ForeignKey("articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_comment_modtime
            BEFORE UPDATE
            ON commentaries
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )
