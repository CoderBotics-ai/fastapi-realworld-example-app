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
from bson.objectid import ObjectId

from datetime import datetime
from typing import List, Optional
from typing import List, Optional
from typing import List
from typing import List, Optional, Sequence

from typing import Sequence
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

    def __init__(self, conn: MongoClient) -> None:
        super().__init__(conn)
        self._profiles_repo = ProfilesRepository(conn)
        self._tags_repo = TagsRepository(conn)
        self._db = conn['your_database_name']  # Replace 'your_database_name' with your actual database name
        self._articles_collection = self._db['articles']
        self._users_collection = self._db['users']
        self._tags_collection = self._db['tags']


    async def create_article(  # noqa: WPS211
        self,
        *,
        slug: str,
        title: str,
        description: str,
        body: str,
        author: User,
        tags: Optional[Sequence[str]] = None,
    ) -> Article:
        client = MongoClient()
        db = client['your_database_name']
        articles_collection = db['articles']
        users_collection = db['users']
        tags_collection = db['tags']

        author_record = users_collection.find_one({"username": author.username})
        if not author_record:
            raise EntityDoesNotExist(f"User with username {author.username} does not exist")

        article_data = {
            "slug": slug,
            "title": title,
            "description": description,
            "body": body,
            "author_id": author_record["_id"],
            "tags": tags if tags else [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "favorited_by": [],
            "comments": []
        }

        result = articles_collection.insert_one(article_data)
        article_id = result.inserted_id

        if tags:
            for tag in tags:
                tags_collection.update_one(
                    {"tag": tag},
                    {"$addToSet": {"articles": article_id}},
                    upsert=True
                )

        article_row = articles_collection.find_one({"_id": article_id})

        return await self._get_article_from_db_record(
            article_row=article_row,
            slug=slug,
            author_username=author.username,
            requested_user=author,
        )


    async def update_article(  # noqa: WPS211
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

        client = MongoClient()
        db = client['your_database_name']
        articles_collection = db['articles']

        filter_query = {"slug": article.slug, "author_id": ObjectId(article.author.id)}
        update_query = {
            "$set": {
                "slug": updated_article.slug,
                "title": updated_article.title,
                "body": updated_article.body,
                "description": updated_article.description,
                "updated_at": datetime.utcnow()
            }
        }

        result = articles_collection.update_one(filter_query, update_query)
        if result.matched_count == 0:
            raise EntityDoesNotExist(f"Article with slug '{article.slug}' does not exist.")

        updated_article.updated_at = datetime.utcnow()
        return updated_article


    async def delete_article(self, *, article: Article) -> None:
        client = MongoClient()
        db = client.your_database_name
        articles_collection = db.articles

        # Delete the article by slug and author username
        articles_collection.delete_one({
            "slug": article.slug,
            "author_id": ObjectId(article.author.id)
        })

        client.close()


    async def filter_articles(  # noqa: WPS211
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
        db = client['your_database_name']
        articles_collection = db['articles']
        users_collection = db['users']

        query = {}

        if tag:
            query['tags'] = tag

        if author:
            author_doc = users_collection.find_one({'username': author})
            if author_doc:
                query['author_id'] = author_doc['_id']

        if favorited:
            favorited_user_doc = users_collection.find_one({'username': favorited})
            if favorited_user_doc:
                query['favorited_by'] = favorited_user_doc['_id']

        articles_cursor = articles_collection.find(query).skip(offset).limit(limit)
        articles_list = await articles_cursor.to_list(length=limit)

        return [
            await self._get_article_from_db_record(
                article_row=article,
                slug=article['slug'],
                author_username=users_collection.find_one({'_id': article['author_id']})['username'],
                requested_user=requested_user,
            )
            for article in articles_list
        ]

    async def get_articles_for_user_feed(
        self,
        *,
        user: User,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Article]:
        articles_rows = await queries.get_articles_for_feed(
            self.connection,
            follower_username=user.username,
            limit=limit,
            offset=offset,
        )
        return [
            await self._get_article_from_db_record(
                article_row=article_row,
                slug=article_row[SLUG_ALIAS],
                author_username=article_row[AUTHOR_USERNAME_ALIAS],
                requested_user=user,
            )
            for article_row in articles_rows
        ]


    async def get_article_by_slug(
        self,
        *,
        slug: str,
        requested_user: Optional[User] = None,
    ) -> Article:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["your_database_name"]
        articles_collection = db["articles"]

        article_row = articles_collection.find_one({"slug": slug})
        if article_row:
            return await self._get_article_from_db_record(
                article_row=article_row,
                slug=article_row["slug"],
                author_username=article_row["author_id"],  # Assuming you will fetch author details separately
                requested_user=requested_user,
            )

        raise EntityDoesNotExist("article with slug {0} does not exist".format(slug))


    async def get_tags_for_article_by_slug(self, *, slug: str) -> List[str]:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["your_database_name"]
        articles_collection = db["articles"]

        article = articles_collection.find_one({"slug": slug}, {"tags": 1})
        if article is None:
            raise EntityDoesNotExist(f"Article with slug {slug} does not exist")

        return article.get("tags", [])


    async def get_favorites_count_for_article_by_slug(self, *, slug: str) -> int:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["your_database_name"]
        articles_collection = db["articles"]

        article = articles_collection.find_one({"slug": slug}, {"favorited_by": 1})
        if article is None:
            raise EntityDoesNotExist(f"Article with slug '{slug}' does not exist")

        favorites_count = len(article.get("favorited_by", []))
        client.close()
        return favorites_count


    async def is_article_favorited_by_user(self, *, slug: str, user: User) -> bool:
        client = MongoClient()
        db = client['your_database_name']
        articles_collection = db['articles']
        
        article = articles_collection.find_one({"slug": slug})
        if article is None:
            return False
        
        return ObjectId(user.id) in article.get("favorited_by", [])


    async def add_article_into_favorites(self, *, article: Article, user: User) -> None:
        client = MongoClient()
        db = client['your_database_name']
        users_collection = db['users']
        articles_collection = db['articles']

        user_id = ObjectId(user.id)
        article_id = ObjectId(article.id)

        # Add article to user's favorites
        users_collection.update_one(
            {'_id': user_id},
            {'$addToSet': {'favorites': article_id}}
        )

        # Add user to article's favorited_by
        articles_collection.update_one(
            {'_id': article_id},
            {'$addToSet': {'favorited_by': user_id}}
        )

        client.close()


    async def remove_article_from_favorites(
        self,
        *,
        article: Article,
        user: User,
    ) -> None:
        client = MongoClient()
        db = client['your_database_name']
        users_collection = db['users']
        articles_collection = db['articles']

        # Remove the article from the user's favorites
        users_collection.update_one(
            {"username": user.username},
            {"$pull": {"favorites": ObjectId(article.id)}}
        )

        # Remove the user from the article's favorited_by list
        articles_collection.update_one(
            {"slug": article.slug},
            {"$pull": {"favorited_by": ObjectId(user.id)}}
        )

        client.close()


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
        client = MongoClient()
        db = client['your_database_name']
        articles_collection = db['articles']
        tags_collection = db['tags']

        # Find the article by slug
        article = articles_collection.find_one({"slug": slug})
        if not article:
            raise EntityDoesNotExist(f"Article with slug {slug} does not exist")

        # Update the article with the new tags
        articles_collection.update_one(
            {"_id": article["_id"]},
            {"$set": {"tags": tags}}
        )

        # Update the tags collection
        for tag in tags:
            tags_collection.update_one(
                {"tag": tag},
                {"$addToSet": {"articles": article["_id"]}},
                upsert=True
            )

        client.close()
