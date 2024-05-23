from typing import List, Optional

from asyncpg import Connection, Record

from app.db.errors import EntityDoesNotExist
from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.profiles import ProfilesRepository
from app.models.domain.articles import Article
from app.models.domain.comments import Comment
from app.models.domain.users import User
from pymongo.collection import Collection
from pymongo.database import Database

from pymongo.database import Database
from bson import ObjectId

from pymongo import MongoClient
from bson import ObjectId

from datetime import datetime


class CommentsRepository(BaseRepository):

    def __init__(self, db: Database) -> None:
        self._db = db
        self._profiles_repo = ProfilesRepository(db)


    async def get_comment_by_id(
        self,
        *,
        comment_id: int,
        article: Article,
        user: Optional[User] = None,
    ) -> Comment:
        comment_id_obj = ObjectId(comment_id)
        article_id_obj = ObjectId(article.id)
        
        comment_row = await self.db.comments.find_one(
            {"_id": comment_id_obj, "article_id": article_id_obj}
        )
        
        if comment_row:
            return await self._get_comment_from_db_record(
                comment_row=comment_row,
                author_username=comment_row["author_username"],
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
        comments_rows = await queries.get_comments_for_article_by_slug(
            self.connection,
            slug=article.slug,
        )
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
        db: Database = self.connection
        comments_collection: Collection = db.get_collection("comments")
        articles_collection: Collection = db.get_collection("articles")

        comment_data = {
            "body": body,
            "article_id": ObjectId(article.id),
            "author_username": user.username,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = comments_collection.insert_one(comment_data)
        comment_id = result.inserted_id

        articles_collection.update_one(
            {"_id": ObjectId(article.id)},
            {"$push": {"comments": comment_id}}
        )

        comment_row = comments_collection.find_one({"_id": comment_id})

        return await self._get_comment_from_db_record(
            comment_row=comment_row,
            author_username=comment_row["author_username"],
            requested_user=user,
        )


    async def delete_comment(self, *, comment: Comment) -> None:
        db: Database = self.connection
        comments_collection: Collection = db.get_collection("comments")
        articles_collection: Collection = db.get_collection("articles")

        # Delete the comment from the comments collection
        comments_collection.delete_one({"_id": ObjectId(comment.id_)})

        # Remove the comment reference from the article's comments array
        articles_collection.update_one(
            {"_id": ObjectId(comment.article_id)},
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
            id_=comment_row["_id"],
            body=comment_row["body"],
            author=await self._profiles_repo.get_profile_by_username(
                username=author_username,
                requested_user=requested_user,
            ),
            created_at=comment_row["created_at"],
            updated_at=comment_row["updated_at"],
        )
