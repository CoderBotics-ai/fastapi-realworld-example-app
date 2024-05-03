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
    op.execute(
        """
    CREATE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS
    $$
    BEGIN
        NEW.updated_at = now();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """
    )


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
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.Text, unique=True, nullable=False, index=True),
        sa.Column("email", sa.Text, unique=True, nullable=False, index=True),
        sa.Column("salt", sa.Text, nullable=False),
        sa.Column("hashed_password", sa.Text),
        sa.Column("bio", sa.Text, nullable=False, server_default=""),
        sa.Column("image", sa.Text),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_user_modtime
            BEFORE UPDATE
            ON users
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )

def create_followers_to_followings_table() -> None:
    # In MongoDB, we do not create tables or relationships in the same way as SQL.
    # Instead, we ensure that the database schema is designed to handle the relationships.
    # For a followers-followings relationship, we would typically use an array of references
    # in the user document itself to represent followers and followings.
    # This function would be used to set up such a schema if it were not already implied.
    # Since MongoDB does not require explicit table or relationship creation like SQL,
    # this function can be considered a placeholder to ensure the schema supports
    # followers and followings as arrays of ObjectIds in the user documents.
    pass


def create_articles_table() -> None:
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.Text, unique=True, nullable=False, index=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "author_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_article_modtime
            BEFORE UPDATE
            ON articles
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )

def create_tags_table() -> None:
    db = client.get_database("your_database_name")
    db.create_collection("tags")
    db.tags.create_index([("tag", pymongo.ASCENDING)], unique=True)

def create_articles_to_tags_table() -> None:
    # In MongoDB, we do not need to explicitly create tables (collections) or define their schema upfront.
    # The schema is implied and created on the fly when documents are inserted.
    # However, to align with the task of migrating the SQL table creation to MongoDB, we can ensure the collection exists.
    # This is typically done by just attempting to access the collection.
    db = client.get_database("your_database_name")
    articles_to_tags_collection = db["articles_to_tags"]
    # MongoDB creates the collection when the first document is inserted.
    # Since we are not inserting any documents here, and MongoDB does not require explicit collection creation,
    # this function effectively ensures the collection is ready for use when needed.

def create_favorites_table() -> None:
    # Since MongoDB does not use table creation statements like SQL databases,
    # this function will not perform any operations in a MongoDB context.
    # MongoDB creates collections and fields as they are used.
    pass

def create_commentaries_table() -> None:
    db = client.get_database("your_database_name")
    db.create_collection("commentaries")
    db.commentaries.create_index([("author_id", pymongo.ASCENDING)], unique=False)
    db.commentaries.create_index([("article_id", pymongo.ASCENDING)], unique=False)
    db.commentaries.create_index([("created_at", pymongo.DESCENDING)], unique=False)
    db.commentaries.create_index([("updated_at", pymongo.DESCENDING)], unique=False)


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
    db = op.get_bind()
    db["users"].drop()
    db["comments"].drop()
    db["articles"].drop()
    db["tags"].drop()
    db.command("DROP FUNCTION IF EXISTS update_updated_at_column")
