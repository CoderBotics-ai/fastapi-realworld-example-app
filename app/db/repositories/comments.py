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
































































class CommentsRepository(BaseRepository):
    def __init__(self, conn: Connection) -> None:
        super().__init__(conn)
        self._profiles_repo = ProfilesRepository(conn)


    async def get_comment_by_id(
        self,
        *,
        comment_id: int,
        article: Article,
        user: Optional[User] = None,
    ) -> Comment:
        comments_collection = self.db.get_collection("comments")
        comment_document = await comments_collection.find_one(
            {"_id": comment_id, "article_slug": article.slug}
        )
        if comment_document:
            return await self._get_comment_from_db_document(
                comment_document=comment_document,
                author_username=comment_document["author_username"],
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
        comments_collection: Collection = self.connection.get_collection('comments')
        comments_cursor = comments_collection.find({"article_slug": article.slug})
        comments_rows = await comments_cursor.to_list(None)
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
        comments_collection: Collection,
    ) -> Comment:
        comment_data = {
            "body": body,
            "article_slug": article.slug,
            "author_username": user.username,
        }
        insert_result = comments_collection.insert_one(comment_data)
        if not insert_result.inserted_id:
            raise Exception("Failed to create comment for article.")

        inserted_comment_data = comments_collection.find_one({"_id": insert_result.inserted_id})
        if not inserted_comment_data:
            raise EntityDoesNotExist("Newly created comment not found.")

        return await self._get_comment_from_db_record(
            comment_row=inserted_comment_data,
            author_username=inserted_comment_data["author_username"],
            requested_user=user,
        )


    async def delete_comment(self, *, comment: Comment) -> None:
        delete_result = self.collection.delete_one({"_id": comment.id_, "author.username": comment.author.username})
        if delete_result.deleted_count == 0:
            raise EntityDoesNotExist("comment with the given id and author username does not exist")

    async def _get_comment_from_db_record(
        self,
        *,
        comment_doc: dict,
        author_username: str,
        requested_user: Optional[User],
    ) -> Comment:
        return Comment(
            id_=comment_doc["_id"],
            body=comment_doc["body"],
            author=await self._profiles_repo.get_profile_by_username(
                username=author_username,
                requested_user=requested_user,
            ),
            created_at=comment_doc["created_at"],
            updated_at=comment_doc["updated_at"],
        )
