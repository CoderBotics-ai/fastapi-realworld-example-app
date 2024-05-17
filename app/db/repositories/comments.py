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
        comment = self.client["database"]["articles"].find_one({"_id": article.id, "comments.comment_id": comment_id})
        if comment:
            comment_body = next((c for c in comment["comments"] if c["comment_id"] == comment_id), None)
            if comment_body:
                return await self._get_comment_from_db_record(
                    comment_row=comment_body,
                    author_username=comment_body["author_username"],
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
        article_data = self.articles_collection.find_one({"slug": article.slug})
        if article_data is None:
            raise EntityDoesNotExist
        comments_ids = article_data.get("comments", [])
        comments_data = self.users_collection.find({"comments.comment_id": {"$in": comments_ids}})
        comments = []
        for comment_data in comments_data:
            for comment in comment_data["comments"]:
                if comment["comment_id"] in comments_ids:
                    comments.append(
                        await self._get_comment_from_db_record(
                            comment_row=comment,
                            author_username=comment_data["username"],
                            requested_user=user,
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
        article_id = article.id
        user_id = user.id
        comment = {"body": body, "article_id": article_id, "author_id": user_id}
        result = self.articles_collection.update_one({"_id": article_id}, {"$push": {"comments": comment}})
        if result.modified_count == 1:
            comment_id = self.articles_collection.find_one({"_id": article_id}, {"comments": {"$slice": -1}})["comments"][0]["_id"]
            return Comment(id=comment_id, body=body, article=article, user=user)
        else:
            raise EntityDoesNotExist("Article not found")


    async def delete_comment(self, *, comment: Comment) -> None:
        filter_ = {"_id": ObjectId(comment.id_)}
        self.comments_collection.delete_one(filter_)


    async def _get_comment_from_db_record(
        self,
        *,
        comment_id: str,
        author_username: str,
        requested_user: Optional[User],
    ) -> Comment:
        comment = self.comments_collection.find_one({"_id": ObjectId(comment_id)})
        if comment is None:
            raise EntityDoesNotExist
        return Comment(
            id_=str(comment["_id"]),
            body=comment["body"],
            author=await self._profiles_repo.get_profile_by_username(
                username=author_username,
                requested_user=requested_user,
            ),
            created_at=comment["created_at"],
            updated_at=comment["updated_at"],
        )
