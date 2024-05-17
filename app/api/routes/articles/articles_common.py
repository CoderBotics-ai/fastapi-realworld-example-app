from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status

from app.api.dependencies.articles import get_article_by_slug_from_path
from app.api.dependencies.authentication import get_current_user_authorizer
from app.api.dependencies.database import get_repository
from app.db.repositories.articles import ArticlesRepository
from app.models.domain.articles import Article
from app.models.domain.users import User
from app.resources import strings
from pymongo import MongoClient
from bson import ObjectId
from typing import List

from pymongo import MongoClient
from bson import ObjectId
from typing import List


@router.delete(
    "/{slug}/favorite",
    response_model=ArticleInResponse,
    name="articles:unmark-article-favorite",
)
async def remove_article_from_favorites(
    article: Article = Depends(get_article_by_slug_from_path),
    user: User = Depends(get_current_user_authorizer()),
    articles_repo: ArticlesRepository = Depends(get_repository(ArticlesRepository)),
) -> ArticleInResponse:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    users_collection = db["users"]
    articles_collection = db["articles"]

    if article.favorited:
        # Remove article from user's favorites
        users_collection.update_one(
            {"_id": ObjectId(user.id)},
            {"$pull": {"favorites": ObjectId(article.id)}}
        )

        # Remove user from article's favorited_by list
        articles_collection.update_one(
            {"_id": ObjectId(article.id)},
            {"$pull": {"favorited_by": ObjectId(user.id)}}
        )

        client.close()

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

    client.close()
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
    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    articles_collection = db["articles"]
    users_collection = db["users"]

    if not article.favorited:
        # Add article to user's favorites
        users_collection.update_one(
            {"_id": ObjectId(user.id)},
            {"$addToSet": {"favorites": ObjectId(article.id)}}
        )

        # Increment the article's favorites count and add user to favorited_by
        articles_collection.update_one(
            {"_id": ObjectId(article.id)},
            {
                "$addToSet": {"favorited_by": ObjectId(user.id)},
                "$inc": {"favorites_count": 1}
            }
        )

        updated_article = articles_collection.find_one({"_id": ObjectId(article.id)})

        return ArticleInResponse(
            article=ArticleForResponse.from_orm(
                article.copy(
                    update={
                        "favorited": True,
                        "favorites_count": updated_article["favorites_count"],
                    },
                ),
            ),
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=strings.ARTICLE_IS_ALREADY_FAVORITED,
    )
from app.models.schemas.articles import (
    DEFAULT_ARTICLES_LIMIT,
    DEFAULT_ARTICLES_OFFSET,
    ArticleForResponse,
    ArticleInResponse,
    ListOfArticlesInResponse,
)

router = APIRouter()


@router.get(
    "/feed",
    response_model=ListOfArticlesInResponse,
    name="articles:get-user-feed-articles",
)
async def get_articles_for_user_feed(
    limit: int = Query(DEFAULT_ARTICLES_LIMIT, ge=1),
    offset: int = Query(DEFAULT_ARTICLES_OFFSET, ge=0),
    user: User = Depends(get_current_user_authorizer()),
    articles_repo: ArticlesRepository = Depends(get_repository(ArticlesRepository)),
) -> ListOfArticlesInResponse:
    articles = await articles_repo.get_articles_for_user_feed(
        user=user,
        limit=limit,
        offset=offset,
    )
    articles_for_response = [
        ArticleForResponse(**article.dict()) for article in articles
    ]
    return ListOfArticlesInResponse(
        articles=articles_for_response,
        articles_count=len(articles),
    )
