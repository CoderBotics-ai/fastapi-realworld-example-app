from typing import List, Optional

from asyncpg import Connection, Record

from app.db.errors import EntityDoesNotExist
from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.profiles import ProfilesRepository
from app.models.domain.articles import Article
from app.models.domain.comments import Comment
from app.models.domain.users import User
































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
        comment_collection = self.db.get_collection('comments')
        comment_document = await comment_collection.find_one({
            "comment_id": comment_id,
            "article_id": article._id
        })

        if comment_document:
            return await self._get_comment_from_db_record(
                comment_row=comment_document,
                author_username=comment_document["author_username"],
                requested_user=user,
            )

        raise EntityDoesNotExist(
            f"comment with id {comment_id} does not exist"
        )

    async def get_comments_for_article(
        self,
        *,
        article: Article,
        user: Optional[User] = None,
    ) -> List[Comment]:
        comments_cursor = self.connection["comments"].find({"article_id": article.article_id})
        comments = await comments_cursor.to_list(None)
        
        return [
            await self._get_comment_from_db_record(
                comment_row=comment,
                author_username=comment["author_username"],
                requested_user=user,
            )
            for comment in comments
        ]

    async def create_comment_for_article(
        self,
        *,
        body: str,
        article: Article,
        user: User,
    ) -> Comment:
        comment_document = {
            "body": body,
            "article_id": article.id,
            "author_id": user.id,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow(),
        }
        result = await self.db.comments.insert_one(comment_document)
        comment_document["_id"] = result.inserted_id
        return await self._get_comment_from_db_record(
            comment_row=comment_document,
            author_username=user.username,
            requested_user=user,
        )

    async def delete_comment(self, *, comment: Comment) -> None:
        result = await self.connection["users"].update_many(
            {},
            {
                "$pull": {
                    "comments": {"comment_id": comment.id_}
                }
            }
        )
        if result.modified_count == 0:
            raise EntityDoesNotExist("comment with id {0} does not exist".format(comment.id_))

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
