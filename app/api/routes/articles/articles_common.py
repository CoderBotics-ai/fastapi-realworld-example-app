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
from typing import List
from app.models.schemas.articles import ListOfArticlesInResponse, ArticleForResponse

from pymongo import MongoClient
from typing import List
from app.models.schemas.articles import ListOfArticlesInResponse, ArticleForResponse, ArticleInResponse


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
    if article.favorited:
        # Remove the article from the user's favorites
        users_collection.update_one(
            {"_id": user.id},
            {"$pull": {"favorites": article.id}}
        )

        # Remove the user from the article's favorited_by list
        articles_collection.update_one(
            {"_id": article.id},
            {"$pull": {"favorited_by": user.id}}
        )

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
        # Update the article to be favorited
        articles_collection.update_one(
            {"_id": article.id},
            {
                "$addToSet": {"favorited_by": user.id},
                "$inc": {"favorites_count": 1}
            }
        )

        # Update the user to include this article in their favorites
        users_collection.update_one(
            {"_id": user.id},
            {"$addToSet": {"favorites": article.id}}
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

client = MongoClient("mongodb://localhost:27017/")
db = client["your_database_name"]
articles_collection = db["articles"]
users_collection = db["users"]
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
    user_data = users_collection.find_one({"_id": user.id})
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=strings.USER_DOES_NOT_EXIST)

    followings = user_data.get("followings", [])
    articles_cursor = articles_collection.find({"author_id": {"$in": followings}}).skip(offset).limit(limit)
    articles = list(articles_cursor)

    articles_for_response = [
        ArticleForResponse(**article) for article in articles
    ]
    return ListOfArticlesInResponse(
        articles=articles_for_response,
        articles_count=len(articles),
    )
