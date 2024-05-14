from typing import List, Optional

from asyncpg import Connection, Record

from app.db.errors import EntityDoesNotExist
from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.profiles import ProfilesRepository
from app.models.domain.articles import Article
from app.models.domain.comments import Comment
from app.models.domain.users import User
from bson.objectid import ObjectId
from pymongo import MongoClient
































































































































class CommentsRepository(BaseRepository):

    def __init__(self, client: MongoClient, db_name: str, collection_name: str) -> None:
        self._collection = client[db_name][collection_name]
        self._profiles_repo = ProfilesRepository(client, db_name, 'users')  # Assuming 'users' is the collection for profiles


    async def get_comment_by_id(
        self,
        *,
        comment_id: ObjectId,
        article: Article,
        user: Optional[User] = None,
    ) -> Comment:
        # Assuming MongoClient and database are already set up
        db = MongoClient().get_database()
        collection = db.get_collection('articles')

        # Query the article collection to find the article with the given slug
        article_doc = collection.find_one({'slug': article.slug})

        if article_doc:
            # Extract the comment IDs from the article document
            comment_ids = article_doc.get('comments', [])

            # Find the comment with the given ID
            comment_doc = db.get_collection('users').find_one({'comments.comment_id': comment_id})

            if comment_doc:
                # Extract the comment from the user document
                for comment in comment_doc.get('comments', []):
                    if comment['comment_id'] == comment_id:
                        return await self._get_comment_from_db_record(
                            comment_row=comment,
                            author_username=comment['author_username'],
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
        article_obj_id = ObjectId(article.slug)  # Assuming slug is used as the ObjectId for articles
        article_document = self.articles_collection.find_one({"_id": article_obj_id})

        if article_document is None:
            raise EntityDoesNotExist("Article does not exist")

        comment_ids = article_document.get("comments", [])
        comments = []

        for comment_id in comment_ids:
            comment_document = self.users_collection.find_one(
                {"comments.comment_id": ObjectId(comment_id)}
            )

            if comment_document is None:
                continue  # Skip if the comment does not exist

            comment = Comment(
                id=comment_document["comments"][0]["comment_id"],
                body=comment_document["comments"][0]["body"],
                author=User(
                    username=comment_document["username"],
                    email=comment_document["email"],
                    bio=comment_document["bio"],
                    image=comment_document["image"],
                ),
                created_at=comment_document["comments"][0]["created_at"],
                updated_at=comment_document["comments"][0]["updated_at"],
            )

            comments.append(comment)

        return comments


    async def create_comment_for_article(
        self,
        *,
        body: str,
        article: Article,
        user: User,
    ) -> Comment:
        # Create a new comment document
        new_comment = {
            "body": body,
            "article_id": article.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert the new comment into the user's comments array
        user_filter = {"username": user.username}
        user_update = {"$push": {"comments": new_comment}}
        await self.users_collection.update_one(user_filter, user_update)

        # Insert the new comment into the article's comments array
        article_filter = {"slug": article.slug}
        article_update = {"$push": {"comments": new_comment["_id"]}}
        await self.articles_collection.update_one(article_filter, article_update)

        # Return the new comment
        return Comment(**new_comment)


    async def delete_comment(self, *, comment: Comment) -> None:
        # Assuming comment.author.username is the username of the author and comment.id_ is the comment id
        user_query = {"username": comment.author.username}
        article_query = {"_id": comment.id_}

        # Find the user document and the article document
        user_document = self.users_collection.find_one(user_query)
        article_document = self.articles_collection.find_one(article_query)

        if not user_document or not article_document:
            raise EntityDoesNotExist("Comment does not exist")

        # Remove the comment from the user's comments array
        self.users_collection.update_one(user_query, {"$pull": {"comments": {"comment_id": comment.id_}}})

        # Remove the comment from the article's comments array
        self.articles_collection.update_one(article_query, {"$pull": {"comments": comment.id_}})


    async def _get_comment_from_db_record(
        self,
        *,
        comment_id: ObjectId,
        author_username: str,
        requested_user: Optional[User],
    ) -> Comment:
        comment_doc = self.db.users.find_one(
            {"comments.comment_id": comment_id}
        )
        if not comment_doc:
            raise EntityDoesNotExist("Comment does not exist")

        comment_data = comment_doc["comments"][0]  # Assuming only one comment per user
        author_doc = self.db.users.find_one({"username": author_username})
        if not author_doc:
            raise EntityDoesNotExist("Author does not exist")

        author_profile = User(
            id_=author_doc["_id"],
            username=author_doc["username"],
            email=author_doc["email"],
            bio=author_doc["bio"],
            image=author_doc["image"],
            following=requested_user and requested_user.id_ in author_doc["followers"],
        )

        return Comment(
            id_=comment_data["comment_id"],
            body=comment_data["body"],
            author=author_profile,
            created_at=comment_data["created_at"],
            updated_at=comment_data["updated_at"],
        )
