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

from pymongo import MongoClient
from bson.objectid import ObjectId

from datetime import datetime
from typing import Optional
from typing import List, Optional, Union
from typing import List

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

        author_id = users_collection.find_one({"username": author.username})["_id"]

        article_data = {
            "slug": slug,
            "title": title,
            "description": description,
            "body": body,
            "author_id": author_id,
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

        client = MongoClient("mongodb://localhost:27017/")
        db = client["your_database_name"]
        articles_collection = db["articles"]

        updated_article.updated_at = datetime.utcnow()

        result = articles_collection.update_one(
            {"slug": article.slug, "author_id": ObjectId(article.author.id)},
            {
                "$set": {
                    "slug": updated_article.slug,
                    "title": updated_article.title,
                    "body": updated_article.body,
                    "description": updated_article.description,
                    "updated_at": updated_article.updated_at,
                }
            }
        )

        if result.matched_count == 0:
            raise EntityDoesNotExist("Article does not exist")

        return updated_article


    async def delete_article(self, *, article: Article) -> None:
        client = MongoClient()
        db = client['your_database_name']
        articles_collection = db['articles']

        result = articles_collection.delete_one({
            "slug": article.slug,
            "author_id": ObjectId(article.author.id)
        })

        if result.deleted_count == 0:
            raise EntityDoesNotExist(f"Article with slug {article.slug} does not exist.")


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
            favorited_user = users_collection.find_one({'username': favorited})
            if favorited_user:
                query['favorited_by'] = favorited_user['_id']

        articles_cursor = articles_collection.find(query).skip(offset).limit(limit)
        articles_list = await articles_cursor.to_list(length=limit)

        result = []
        for article_doc in articles_list:
            author_doc = users_collection.find_one({'_id': article_doc['author_id']})
            author_username = author_doc['username'] if author_doc else None
            article = await self._get_article_from_db_record(
                article_row=article_doc,
                slug=article_doc['slug'],
                author_username=author_username,
                requested_user=requested_user,
            )
            result.append(article)

        client.close()
        return result


    async def get_articles_for_user_feed(
        self,
        *,
        user: User,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Article]:
        client = MongoClient()
        db = client['your_database_name']
        articles_collection = db['articles']
        users_collection = db['users']

        # Find the user document
        user_doc = users_collection.find_one({"username": user.username})
        if not user_doc:
            raise EntityDoesNotExist(f"User with username {user.username} does not exist.")

        # Get the list of users the current user is following
        following_ids = user_doc.get("followings", [])

        # Find articles authored by users the current user is following
        articles_cursor = articles_collection.find(
            {"author_id": {"$in": following_ids}}
        ).skip(offset).limit(limit)

        articles = []
        async for article_doc in articles_cursor:
            article = await self._get_article_from_db_record(
                article_row=article_doc,
                slug=article_doc["slug"],
                author_username=user.username,
                requested_user=user,
            )
            articles.append(article)

        return articles


    async def get_article_by_slug(
        self,
        *,
        slug: str,
        requested_user: Optional[User] = None,
    ) -> Article:
        client = MongoClient()
        db = client['your_database_name']
        articles_collection = db['articles']

        article_row = articles_collection.find_one({"slug": slug})
        if article_row:
            return await self._get_article_from_db_record(
                article_row=article_row,
                slug=article_row["slug"],
                author_username=article_row["author_id"],  # Assuming author_id is used to fetch username
                requested_user=requested_user,
            )

        raise EntityDoesNotExist("article with slug {0} does not exist".format(slug))


    async def get_tags_for_article_by_slug(self, *, slug: str) -> List[str]:
        client = MongoClient()
        db = client['your_database_name']
        articles_collection = db['articles']

        article = articles_collection.find_one({"slug": slug}, {"tags": 1})
        if article is None:
            return []

        return article.get("tags", [])


    async def get_favorites_count_for_article_by_slug(self, *, slug: str) -> int:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["your_database_name"]
        articles_collection = db["articles"]

        article = articles_collection.find_one({"slug": slug}, {"favorited_by": 1})
        if article and "favorited_by" in article:
            return len(article["favorited_by"])
        return 0


    async def is_article_favorited_by_user(self, *, slug: str, user: User) -> bool:
        client = MongoClient()
        db = client['your_database_name']
        articles_collection = db['articles']
        users_collection = db['users']

        user_record = users_collection.find_one({"username": user.username})
        if not user_record:
            return False

        article_record = articles_collection.find_one({"slug": slug})
        if not article_record:
            return False

        return ObjectId(article_record['_id']) in user_record.get('favorites', [])


    async def add_article_into_favorites(self, *, article: Article, user: User) -> None:
        client = MongoClient()
        db = client['your_database_name']
        users_collection = db['users']
        articles_collection = db['articles']

        # Add article to user's favorites
        users_collection.update_one(
            {"username": user.username},
            {"$addToSet": {"favorites": ObjectId(article.id)}}
        )

        # Add user to article's favorited_by
        articles_collection.update_one(
            {"slug": article.slug},
            {"$addToSet": {"favorited_by": ObjectId(user.id)}}
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

        article_id = article['_id']

        # Update the article with the new tags
        articles_collection.update_one(
            {"_id": article_id},
            {"$addToSet": {"tags": {"$each": tags}}}
        )

        # Update the tags collection with the article ID
        for tag in tags:
            tags_collection.update_one(
                {"tag": tag},
                {"$addToSet": {"articles": article_id}},
                upsert=True
            )
