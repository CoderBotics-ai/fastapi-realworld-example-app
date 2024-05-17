from typing import List, Optional, Sequence, Union

from asyncpg import Connection, Record
from pypika import Query

from app.db.errors import EntityDoesNotExist
from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.profiles import ProfilesRepository
from app.db.repositories.tags import TagsRepository
from app.models.domain.articles import Article
from app.models.domain.users import User

from pymongo import MongoClient
from datetime import datetime
from typing import Any
from typing import Optional
from app.db.queries.tables import (
    Parameter,
    articles,
    articles_to_tags,
    favorites,
    tags as tags_table,
    users,
)

AUTHOR_USERNAME_ALIAS = "author_username"
SLUG_ALIAS = "slug"

CAMEL_OR_SNAKE_CASE_TO_WORDS = r"^[a-z\d_\-]+|[A-Z\d_\-][^A-Z\d_\-]*"


class ArticlesRepository(BaseRepository):

    def __init__(self, client: MongoClient) -> None:
        """Initializes the ArticlesRepository with a MongoDB client."""
        self._profiles_repo = ProfilesRepository(client)
        self._tags_repo = TagsRepository(client)


    async def create_article(
        self,
        *,
        slug: str,
        title: str,
        description: str,
        body: str,
        author: User,
        tags: Optional[Sequence[str]] = None,
    ) -> Article:
        article_data = {
            "slug": slug,
            "title": title,
            "description": description,
            "body": body,
            "author_id": author.id,
            "tags": tags if tags else [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "favorited_by": [],
            "comments": []
        }
        result = self.articles_collection.insert_one(article_data)
        article_id = result.inserted_id

        if tags:
            for tag in tags:
                tag_data = {"tag": tag, "articles": [article_id]}
                self.tags_collection.update_one({"tag": tag}, {"$addToSet": {"articles": article_id}}, upsert=True)

        article_data["_id"] = article_id
        return Article(**article_data)


    async def update_article(
        self,
        *,
        article: Article,
        slug: Optional[str] = None,
        title: Optional[str] = None,
        body: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Article:
        updated_article = article.copy(deep=True)
        updated_article.slug = slug or updated_article.slug
        updated_article.title = title or article.title
        updated_article.body = body or article.body
        updated_article.description = description or article.description

        updated_article.updated_at = datetime.now()

        filter = {"_id": article.author_id, "slug": article.slug}
        update = {"$set": {
            "slug": updated_article.slug,
            "title": updated_article.title,
            "body": updated_article.body,
            "description": updated_article.description,
            "updated_at": updated_article.updated_at
        }}
        self.articles_collection.update_one(filter, update)

        return updated_article


    async def delete_article(self, *, article: Article) -> None:
        """Deletes an article from the database."""
        filter = {"slug": article.slug, "author_id": article.author.username}
        self.articles_collection.delete_one(filter)

    async def filter_articles(
        self,
        *,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        favorited: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        requested_user: Optional[User] = None,
    ) -> List[Article]:
        client = MongoClient()
        db = client["database_name"]
        articles_collection = db["articles"]
        users_collection = db["users"]
        tags_collection = db["tags"]
        articles_to_tags_collection = db["articles_to_tags"]
        favorites_collection = db["favorites"]

        query_filter = {}
        if tag:
            query_filter["tags"] = tag
        if author:
            query_filter["author_id"] = author
        if favorited:
            query_filter["favorited_by"] = favorited

        articles_cursor = articles_collection.find(query_filter).limit(limit).skip(offset)
        articles_rows = await articles_cursor.to_list(length=limit)

        return [
            await self._get_article_from_db_record(
                article_row={
                    "id": article["_id"],
                    "slug": article["slug"],
                    "title": article["title"],
                    "description": article["description"],
                    "body": article["body"],
                    "created_at": article["created_at"],
                    "updated_at": article["updated_at"],
                    "author_username": next((user["username"] for user in users_collection.find({"_id": article["author_id"]}, {"username": 1})), None),
                },
                slug=article["slug"],
                author_username=next((user["username"] for user in users_collection.find({"_id": article["author_id"]}, {"username": 1})), None),
                requested_user=requested_user,
            )
            for article in articles_rows
        ]


    async def get_articles_for_user_feed(
        self,
        *,
        user: User,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Article]:
        pipeline = [
            {"$lookup": {"from": "articles", "localField": "followers", "foreignField": "_id", "as": "articles"}},
            {"$unwind": {"path": "$articles"}},
            {"$replaceRoot": {"newRoot": "$articles"}},
            {"$lookup": {"from": "users", "localField": "author_id", "foreignField": "_id", "as": "author"}},
            {"$unwind": {"path": "$author"}},
            {"$addFields": {"author_username": "$author.username"}},
            {"$project": {"_id": 1, "slug": 1, "author_username": 1}},
        ]
        articles_cursor = self.articles_collection.aggregate(pipeline)
        articles = await articles_cursor.to_list(length=limit)
        return [
            Article(
                id=article["_id"],
                slug=article["slug"],
                author_username=article["author_username"],
                requested_user=user,
            )
            for article in articles[offset:offset + limit]
        ]


    async def get_article_by_slug(
        self,
        *,
        slug: str,
        requested_user: Optional[User] = None,
    ) -> Article:
        article = self.articles_collection.find_one({"slug": slug})
        if article:
            return await self._get_article_from_db_record(
                article_row=article,
                slug=article["slug"],
                author_username=article["author_id"],
                requested_user=requested_user,
            )

        raise EntityDoesNotExist("article with slug {0} does not exist".format(slug))


    async def get_tags_for_article_by_slug(self, *, slug: str) -> List[str]:
        """Get tags for an article by slug."""
        article = self.articles_collection.find_one({"slug": slug})
        if article is None:
            raise EntityDoesNotExist
        return article.get("tags", [])


    async def get_favorites_count_for_article_by_slug(self, *, slug: str) -> int:
        """Get the count of users who favorited an article by slug."""
        article = self.articles_collection.find_one({"slug": slug})
        if article is None:
            raise EntityDoesNotExist
        favorited_by = article.get("favorited_by", [])
        return len(favorited_by)


    async def is_article_favorited_by_user(self, *, slug: str, user: User) -> bool:
        """Checks if an article is favorited by a user."""
        article = self.articles_collection.find_one({"slug": slug})
        if article is None:
            raise EntityDoesNotExist
        user_data = self.users_collection.find_one({"username": user.username})
        if user_data is None:
            raise EntityDoesNotExist
        return article["_id"] in user_data["favorites"]


    async def add_article_into_favorites(self, *, article: Article, user: User) -> None:
        """Adds an article to a user's favorites."""
        self.users_collection.update_one({"username": user.username}, {"$push": {"favorites": article.slug}})


    async def remove_article_from_favorites(
        self,
        *,
        article: Article,
        user: User,
    ) -> None:
        self.users_collection.update_one({"username": user.username}, {"$pull": {"favorites": article._id}})


    async def _get_article_from_db_record(
        self,
        *,
        article_row: dict,
        slug: str,
        author_username: str,
        requested_user: Optional[User],
    ) -> Article:
        return Article(
            id_=article_row["_id"],
            slug=slug,
            title=article_row["title"],
            description=article_row["description"],
            body=article_row["body"],
            author=await self._profiles_repo.get_profile_by_username(
                username=author_username,
                requested_user=requested_user,
            ),
            tags=await self.get_tags_for_article_by_slug(slug=slug),
            favorites_count=await self.get_favorites_count_for_article_by_slug(
                slug=slug,
            ),
            favorited=await self.is_article_favorited_by_user(
                slug=slug,
                user=requested_user,
            )
            if requested_user
            else False,
            created_at=article_row["created_at"],
            updated_at=article_row["updated_at"],
        )


    async def _link_article_with_tags(self, *, slug: str, tags: Sequence[str]) -> None:
        article_filter = {"slug": slug}
        article_update = {"$set": {"tags": tags}}
        self.articles_collection.update_one(article_filter, article_update)
        for tag in tags:
            tag_filter = {"tag": tag}
            tag_update = {"$addToSet": {"articles": slug}}
            self.tags_collection.update_one(tag_filter, tag_update, upsert=True)
