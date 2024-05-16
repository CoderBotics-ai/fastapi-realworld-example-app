from typing import List, Optional

from asyncpg import Connection, Record

from app.db.errors import EntityDoesNotExist
from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.profiles import ProfilesRepository
from app.models.domain.articles import Article
from app.models.domain.comments import Comment
from app.models.domain.users import User
from pymongo import MongoClient

from pymongo import MongoClient
from bson import ObjectId

from datetime import datetime


class CommentsRepository(BaseRepository):

    def __init__(self, client: MongoClient) -> None:
        self._client = client
        self._db = self._client.get_database()
        self._profiles_repo = ProfilesRepository(client)


    async def get_comment_by_id(
        self,
        *,
        comment_id: int,
        article: Article,
        user: Optional[User] = None,
    ) -> Comment:
        client = MongoClient()
        db = client['your_database_name']
        articles_collection = db['articles']
        comments_collection = db['comments']

        article_doc = articles_collection.find_one({"slug": article.slug})
        if not article_doc:
            raise EntityDoesNotExist(
                "article with slug {0} does not exist".format(article.slug),
            )

        comment_doc = comments_collection.find_one({"_id": ObjectId(comment_id), "article_id": article_doc["_id"]})
        if comment_doc:
            return await self._get_comment_from_db_record(
                comment_row=comment_doc,
                author_username=comment_doc["author_username"],
                requested_user=user,
            )

        raise EntityDoesNotExist(
            "comment with id {0} does not exist".format(comment_id),
        )


    async def get_comments_for_article(
        self,
        *,
        article: Article,
        user: Optional[User] = None,
    ) -> List[Comment]:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["your_database_name"]
        articles_collection = db["articles"]
        comments_collection = db["comments"]

        article_doc = articles_collection.find_one({"slug": article.slug})
        if not article_doc:
            raise EntityDoesNotExist(f"Article with slug {article.slug} does not exist")

        comment_ids = article_doc.get("comments", [])
        comments_cursor = comments_collection.find({"_id": {"$in": comment_ids}})
        comments_rows = list(comments_cursor)

        return [
            await self._get_comment_from_db_record(
                comment_row=comment_row,
                author_username=comment_row["author_username"],
                requested_user=user,
            )
            for comment_row in comments_rows
        ]


    async def create_comment_for_article(
        self,
        *,
        body: str,
        article: Article,
        user: User,
    ) -> Comment:
        client = MongoClient()
        db = client['your_database_name']
        comments_collection = db['comments']
        articles_collection = db['articles']
        users_collection = db['users']

        comment_data = {
            "body": body,
            "article_id": ObjectId(article.id),
            "author_id": ObjectId(user.id),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = comments_collection.insert_one(comment_data)
        comment_id = result.inserted_id

        # Update the article document to include this comment
        articles_collection.update_one(
            {"_id": ObjectId(article.id)},
            {"$push": {"comments": comment_id}}
        )

        # Fetch the comment document to return
        comment_document = comments_collection.find_one({"_id": comment_id})

        return Comment(
            id=str(comment_document["_id"]),
            body=comment_document["body"],
            article_id=str(comment_document["article_id"]),
            author_id=str(comment_document["author_id"]),
            created_at=comment_document["created_at"],
            updated_at=comment_document["updated_at"]
        )


    async def delete_comment(self, *, comment: Comment) -> None:
        client = MongoClient()
        db = client['your_database_name']
        comments_collection = db['comments']
        articles_collection = db['articles']

        # Delete the comment from the comments collection
        comments_collection.delete_one({"_id": ObjectId(comment.id_)})

        # Remove the comment ID from the article's comments array
        articles_collection.update_one(
            {"comments": ObjectId(comment.id_)},
            {"$pull": {"comments": ObjectId(comment.id_)}}
        )


    async def _get_comment_from_db_record(
        self,
        *,
        comment_row: dict,
        author_username: str,
        requested_user: Optional[User],
    ) -> Comment:
        return Comment(
            id_=str(comment_row["_id"]),
            body=comment_row["body"],
            author=await self._profiles_repo.get_profile_by_username(
                username=author_username,
                requested_user=requested_user,
            ),
            created_at=comment_row["created_at"],
            updated_at=comment_row["updated_at"],
        )
