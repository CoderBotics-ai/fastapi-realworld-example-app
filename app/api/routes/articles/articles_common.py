from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status

from app.api.dependencies.articles import get_article_by_slug_from_path
from app.api.dependencies.authentication import get_current_user_authorizer
from app.api.dependencies.database import get_repository
from app.db.repositories.articles import ArticlesRepository
from app.models.domain.articles import Article
from app.models.domain.users import User
from app.resources import strings
from bson.objectid import ObjectId
from typing import List
from app.models.schemas.articles import (
    DEFAULT_ARTICLES_LIMIT,
    DEFAULT_ARTICLES_OFFSET,
    ArticleForResponse,
    ArticleInResponse,
    ListOfArticlesInResponse,
)

router = APIRouter()

async def get_articles_for_user_feed(
    user: User,
    limit: int,
    offset: int,
    articles_repo: ArticlesRepository,
) -> List[Article]:
    # Assuming that the ArticlesRepository has been updated to use PyMongo
    # and has a method to get articles for a user's feed
    articles = await articles_repo.get_articles_for_user_feed_pymongo(
        user=user,
        limit=limit,
        offset=offset,
    )
    return articles


async def remove_article_from_favorites(
    article: Article,
    user: User,
    articles_repo: ArticlesRepository,
) -> ArticleInResponse:
    if article.favorited:
        # Convert user._id and article._id to ObjectId
        user_id = ObjectId(user._id)
        article_id = ObjectId(article._id)

        # Remove the article from the user's favorites
        await articles_repo.db.users.update_one(
            {"_id": user_id},
            {"$pull": {"favorites": article_id}}
        )

        # Remove the user from the article's favorited_by
        await articles_repo.db.articles.update_one(
            {"_id": article_id},
            {"$pull": {"favorited_by": user_id}}
        )

        # Update the article's favorites_count
        await articles_repo.db.articles.update_one(
            {"_id": article_id},
            {"$inc": {"favorites_count": -1}}
        )

        # Update the article's favorited status
        article = await articles_repo.db.articles.find_one({"_id": article_id})
        article.favorited = False

        return ArticleInResponse(
            article=ArticleForResponse.from_orm(
                article.copy(
                    update={
                        "favorited": False,
                        "favorites_count": article.favorites_count - 1,
                    },
                ),
            ),
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=strings.ARTICLE_IS_NOT_FAVORITED,
    )


@router.post(
    "/{slug}/favorite",
    response_model=ArticleInResponse,
    name="articles:mark-article-favorite",
)
async def mark_article_as_favorite(
    article: Article = Depends(get_article_by_slug_from_path),
    user: User = Depends(get_current_user_authorizer()),
    articles_repo: ArticlesRepository = Depends(get_repository(ArticlesRepository)),
) -> ArticleInResponse:
    if not article.favorited:
        # Assuming that articles_repo.db is the PyMongo database instance
        # and that the collection names match the schema provided
        user_collection = articles_repo.db["users"]
        article_collection = articles_repo.db["articles"]

        # Add the article's ObjectId to the user's favorites array
        user_document = await user_collection.find_one({"_id": ObjectId(user.id)})
        if user_document:
            await user_collection.update_one(
                {"_id": ObjectId(user.id)},
                {"$addToSet": {"favorites": ObjectId(article.id)}}
            )

        # Add the user's ObjectId to the article's favorited_by array
        article_document = await article_collection.find_one({"_id": ObjectId(article.id)})
        if article_document:
            await article_collection.update_one(
                {"_id": ObjectId(article.id)},
                {"$addToSet": {"favorited_by": ObjectId(user.id)}}
            )

            # Update the article's favorites_count
            await article_collection.update_one(
                {"_id": ObjectId(article.id)},
                {"$inc": {"favorites_count": 1}}
            )

        return ArticleInResponse(
            article=ArticleForResponse.from_orm(
                article.copy(
                    update={
                        "favorited": True,
                        "favorites_count": article.favorites_count + 1,
                    },
                ),
            ),
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=strings.ARTICLE_IS_ALREADY_FAVORITED,
    )
