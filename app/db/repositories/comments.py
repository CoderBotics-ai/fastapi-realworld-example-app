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

    def __init__(self, client: MongoClient) -> None:
        """Initializes the CommentsRepository with a MongoDB client."""
        self._client = client
        self._db = client["app"]
        self._profiles_repo = ProfilesRepository(client)

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
        article_comments = self.articles_collection.find_one({"_id": ObjectId(article.id)}, {"comments": 1})
        if article_comments is None:
            raise EntityDoesNotExist
        comments_ids = article_comments["comments"]
        comments = self.users_collection.find({"comments.comment_id": {"$in": comments_ids}})
        return [
            Comment(
                id=comment["_id"],
                body=next(comment["comments"] for comment in comments if comment["_id"] == comment_id)["body"],
                article_id=article.id,
                author_username=comment["username"],
                created_at=comment["created_at"],
                updated_at=comment["updated_at"]
            )
            for comment_id in comments_ids
        ]


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
        comment = Comment(
            id=result.inserted_id,
            body=body,
            article_id=article.id,
            author_id=user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return comment


    async def delete_comment(self, *, comment: Comment) -> None:
        """Deletes a comment from the database."""
        filter_ = {"_id": comment.author.id_, "comments.comment_id": comment.id_}
        update_ = {"$pull": {"comments": {"comment_id": comment.id_}}}
        self.users_collection.update_one(filter_, update_)
        filter_ = {"_id": comment.article_id, "comments": comment.id_}
        update_ = {"$pull": {"comments": comment.id_}}
        self.articles_collection.update_one(filter_, update_)


    async def _get_comment_from_db_record(
        self,
        *,
        comment_id: str,
        author_username: str,
        requested_user: Optional[User],
    ) -> Comment:
        comment = self.articles_collection.find_one({"comments.comment_id": ObjectId(comment_id)}, {"comments.$": 1})["comments"][0]
        author = self.users_collection.find_one({"username": author_username})
        return Comment(
            id_=str(comment["comment_id"]),
            body=comment["body"],
            author=await self._profiles_repo.get_profile_by_username(
                username=author_username,
                requested_user=requested_user,
            ),
            created_at=comment["created_at"],
            updated_at=comment["updated_at"],
        )
