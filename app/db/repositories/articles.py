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
from pymongo.collection import Collection
from datetime import datetime
from typing import List, Optional
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
    def __init__(self, conn: Connection) -> None:
        super().__init__(conn)
        self._profiles_repo = ProfilesRepository(conn)
        self._tags_repo = TagsRepository(conn)

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
        """Creates a new article."""
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
        result = await self.db.articles.insert_one(article_data)
        article_id = result.inserted_id
        article_data["_id"] = article_id
        if tags:
            await self._tags_repo.create_tags_that_dont_exist(tags=tags)
            await self._link_article_with_tags(slug=slug, tags=tags)
        return await self._get_article_from_db_record(
            article_row=article_data,
            slug=slug,
            author_username=author.username,
            requested_user=author,
        )


    async def update_article(
        self,
        *,
        article: Article,
        slug: Optional[str] = None,
        title: Optional[str] = None,
        body: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Article:
        """Updates an article in the database."""
        updated_article = article.copy(deep=True)
        updated_article.slug = slug or updated_article.slug
        updated_article.title = title or article.title
        updated_article.body = body or article.body
        updated_article.description = description or article.description

        updated_article.updated_at = datetime.utcnow()

        filter_query = {"_id": article.id}
        update_query = {
            "$set": {
                "slug": updated_article.slug,
                "title": updated_article.title,
                "body": updated_article.body,
                "description": updated_article.description,
                "updated_at": updated_article.updated_at,
            }
        }

        self.articles_collection.update_one(filter_query, update_query)

        return updated_article


    async def delete_article(self, *, article: Article) -> None:
        """Deletes an article from the database."""
        filter_query = {"slug": article.slug, "author_id": article.author.username}
        self.articles_collection.delete_one(filter_query)


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
        articles_collection: Collection = self.db["articles"]
        articles_filter = {}

        if tag:
            articles_filter["tags"] = tag
        if author:
            articles_filter["author_id"] = self.db["users"].find_one({"username": author})["_id"]

        if favorited:
            favorited_user_id = self.db["users"].find_one({"username": favorited})["_id"]
            articles_filter["_id"] = {"$in": self.db["articles"].find({"favorited_by": favorited_user_id}, {"_id": 1})}

        articles_cursor = articles_collection.find(articles_filter).limit(limit).skip(offset)
        articles = await articles_cursor.to_list(length=limit)

        return [
            Article(
                id=article["_id"],
                slug=article["slug"],
                title=article["title"],
                description=article["description"],
                body=article["body"],
                created_at=article["created_at"],
                updated_at=article["updated_at"],
                author_username=self.db["users"].find_one({"_id": article["author_id"]})["username"],
            )
            for article in articles
        ]


    async def get_articles_for_user_feed(
        self,
        *,
        user: User,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Article]:
        pipeline = [
            {"$lookup": {"from": "users", "localField": "author_id", "foreignField": "_id", "as": "author"}},
            {"$unwind": {"path": "$author"}},
            {"$match": {"author.followers": user.username}},
            {"$sort": {"created_at": -1}},
            {"$skip": offset},
            {"$limit": limit}
        ]
        articles_cursor = self.articles_collection.aggregate(pipeline)
        articles = []
        async for article in articles_cursor:
            articles.append(
                Article(
                    slug=article["slug"],
                    title=article["title"],
                    description=article["description"],
                    body=article["body"],
                    author_id=article["author_id"],
                    tags=article["tags"],
                    created_at=article["created_at"],
                    updated_at=article["updated_at"],
                    favorited_by=article["favorited_by"],
                    comments=article["comments"]
                )
            )
        return articles


    async def get_article_by_slug(
        self,
        *,
        slug: str,
        requested_user: Optional[User] = None,
    ) -> Article:
        """Get an article by its slug."""
        article_doc = self.articles_collection.find_one({"slug": slug})
        if article_doc:
            return await self._get_article_from_db_record(
                article_row=article_doc,
                slug=article_doc["slug"],
                author_username=article_doc["author_id"],
                requested_user=requested_user,
            )

        raise EntityDoesNotExist("article with slug {0} does not exist".format(slug))


    async def get_tags_for_article_by_slug(self, *, slug: str) -> List[str]:
        article = self.articles_collection.find_one({"slug": slug})
        if article is None:
            raise EntityDoesNotExist
        return article.get("tags", [])


    async def get_favorites_count_for_article_by_slug(self, *, slug: str) -> int:
        """Get the count of users who have favorited an article by its slug."""
        article = self.articles_collection.find_one({"slug": slug})
        if article is None:
            raise EntityDoesNotExist("Article not found")
        favorited_by = article.get("favorited_by", [])
        return len(favorited_by)


    async def is_article_favorited_by_user(self, *, slug: str, user: User) -> bool:
        """Checks if an article is favorited by a user."""
        article = self.articles_collection.find_one({"slug": slug})
        if article is None:
            raise EntityDoesNotExist("Article not found")
        user_data = self.users_collection.find_one({"username": user.username})
        if user_data is None:
            raise EntityDoesNotExist("User not found")
        return article["_id"] in user_data["favorites"]


    async def add_article_into_favorites(self, *, article: Article, user: User) -> None:
        """Adds an article to a user's favorites."""
        self.users_collection.update_one({"username": user.username}, {"$push": {"favorites": article._id}})


    async def remove_article_from_favorites(
        self,
        *,
        article: Article,
        user: User,
    ) -> None:
        self.users_collection.update_one(
            {"_id": user.id},
            {"$pull": {"favorites": article.id}},
        )


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
        """Links an article with tags."""
        article_filter = {"slug": slug}
        article_update = {"$set": {"tags": tags}}
        self._articles_collection.update_one(article_filter, article_update)

        for tag in tags:
            tag_filter = {"tag": tag}
            tag_update = {"$addToSet": {"articles": slug}}
            self._tags_collection.update_one(tag_filter, tag_update, upsert=True)
