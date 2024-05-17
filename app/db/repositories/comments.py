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
from bson import ObjectId

from datetime import datetime
self.client = MongoClient()
self.db = self.client["database_name"]
self.collection = self.db["articles"]


class CommentsRepository(BaseRepository):
    def __init__(self, conn: Connection) -> None:
        super().__init__(conn)
        self._profiles_repo = ProfilesRepository(conn)

    async def get_comment_by_id(
        self,
        *,
        comment_id: ObjectId,
        article: Article,
        user: Optional[User] = None,
    ) -> Comment:
        """Get a comment by its ID."""
        comment = await self.collection.find_one({"comments.comment_id": comment_id, "slug": article.slug})
        if comment:
            comment_row = next((c for c in comment["comments"] if c["comment_id"] == comment_id), None)
            if comment_row:
                return await self._get_comment_from_db_record(
                    comment_row=comment_row,
                    author_username=comment_row["body"].split(":")[0],
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
        article_comments = self.articles_collection.find_one({"_id": ObjectId(article.id)})["comments"]
        comments = []
        for comment_id in article_comments:
            comment = self.users_collection.find_one({"comments.comment_id": ObjectId(comment_id)})["comments"][0]
            comments.append(
                Comment(
                    id=comment["comment_id"],
                    body=comment["body"],
                    article_id=comment["article_id"],
                    created_at=comment["created_at"],
                    updated_at=comment["updated_at"],
                    author_username=comment["author_username"],
                )
            )
        return comments


    async def create_comment_for_article(
        self,
        *,
        body: str,
        article: Article,
        user: User,
    ) -> Comment:
        comment_data = {
            "body": body,
            "article_id": article.id,
            "author_id": user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = self.comments_collection.insert_one(comment_data)
        comment_id = result.inserted_id
        return Comment(id=comment_id, body=body, article=article, user=user)


    async def delete_comment(self, *, comment: Comment) -> None:
        """Deletes a comment from the database."""
        filter_ = {"_id": ObjectId(comment.id_)}
        self.comments_collection.delete_one(filter_)


    async def _get_comment_from_db_record(
        self,
        *,
        comment_id: ObjectId,
        author_username: str,
        requested_user: Optional[User],
    ) -> Comment:
        comment_doc = self.articles_collection.find_one({"comments.comment_id": comment_id}, {"comments.$": 1})
        comment = comment_doc["comments"][0]
        author_doc = self.users_collection.find_one({"username": author_username})
        author = await self._profiles_repo.get_profile_by_username(
            username=author_username,
            requested_user=requested_user,
        )
        return Comment(
            id_=comment["comment_id"],
            body=comment["body"],
            author=author,
            created_at=comment["created_at"],
            updated_at=comment["updated_at"],
        )
