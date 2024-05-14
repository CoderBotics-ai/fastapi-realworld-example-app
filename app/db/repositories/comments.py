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
from bson import ObjectId
































































































































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
        db: Database = self.connection
        comments_collection: Collection = db["comments"]
        articles_collection: Collection = db["articles"]

        article_doc = articles_collection.find_one({"slug": article.slug})
        if not article_doc:
            raise EntityDoesNotExist(
                "article with slug {0} does not exist".format(article.slug),
            )

        comment_doc = comments_collection.find_one({
            "comment_id": ObjectId(comment_id),
            "article_id": article_doc["_id"]
        })

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
        comments_collection: Collection = self.db["comments"]
        comments_cursor = comments_collection.find({"article_id": ObjectId(article.id)})
        comments_rows = await comments_cursor.to_list(length=None)
        
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
        comment_id = ObjectId()
        comment_data = {
            "_id": comment_id,
            "body": body,
            "article_id": article.id,
            "author_id": user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Insert the comment into the comments collection
        await self.db.comments.insert_one(comment_data)

        # Update the article to include the new comment ID
        await self.db.articles.update_one(
            {"_id": article.id},
            {"$push": {"comments": comment_id}}
        )

        # Fetch the comment from the database
        comment_row = await self.db.comments.find_one({"_id": comment_id})

        return await self._get_comment_from_db_record(
            comment_row=comment_row,
            author_username=user.username,
            requested_user=user,
        )


    async def delete_comment(self, *, comment: Comment) -> None:
        comments_collection: Collection = self.db.get_collection("comments")
        articles_collection: Collection = self.db.get_collection("articles")

        # Delete the comment from the comments collection
        await comments_collection.delete_one({"_id": ObjectId(comment.id_)})

        # Remove the comment reference from the article's comments array
        await articles_collection.update_one(
            {"comments": ObjectId(comment.id_)},
            {"$pull": {"comments": ObjectId(comment.id_)}}
        )


    async def _get_comment_from_db_record(
        self,
        *,
        comment_row: Record,
        author_username: str,
        requested_user: Optional[User],
    ) -> Comment:
        return Comment(
            id_=comment_row["id"],
            body=comment_row["body"],
            author=await self._profiles_repo.get_profile_by_username(
                username=author_username,
                requested_user=requested_user,
            ),
            created_at=comment_row["created_at"],
            updated_at=comment_row["updated_at"],
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
