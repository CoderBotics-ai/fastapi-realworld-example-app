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

client = MongoClient("mongodb://localhost:27017/")
db = client["your_database_name"]

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
    articles_collection = db["articles"]
    users_collection = db["users"]

    if article.favorited:
        # Remove the article from the user's favorites
        users_collection.update_one(
            {"_id": ObjectId(user.id)},
            {"$pull": {"favorites": ObjectId(article.id)}}
        )

        # Remove the user from the article's favorited_by list
        articles_collection.update_one(
            {"_id": ObjectId(article.id)},
            {"$pull": {"favorited_by": ObjectId(user.id)}}
        )

        # Update the article object
        article.favorited = False
        article.favorites_count -= 1

        return ArticleInResponse(
            article=ArticleForResponse.from_orm(
                article.copy(
                    update={
                        "favorited": False,
                        "favorites_count": article.favorites_count,
                    },
                ),
            ),
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=strings.ARTICLE_IS_NOT_FAVORITED,
    )
articles_collection = db["articles"]
users_collection = db["users"]

DEFAULT_ARTICLES_LIMIT = 20


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
    article_data = articles_collection.find_one({"slug": article.slug})
    user_data = users_collection.find_one({"_id": ObjectId(user.id)})

    if not article_data or not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=strings.ARTICLE_NOT_FOUND if not article_data else strings.USER_NOT_FOUND,
        )

    if ObjectId(user.id) not in article_data["favorited_by"]:
        articles_collection.update_one(
            {"_id": article_data["_id"]},
            {
                "$addToSet": {"favorited_by": ObjectId(user.id)},
                "$inc": {"favorites_count": 1},
            },
        )
        users_collection.update_one(
            {"_id": ObjectId(user.id)},
            {"$addToSet": {"favorites": article_data["_id"]}},
        )

        updated_article_data = articles_collection.find_one({"_id": article_data["_id"]})

        return ArticleInResponse(
            article=ArticleForResponse.from_orm(
                article.copy(
                    update={
                        "favorited": True,
                        "favorites_count": updated_article_data["favorites_count"],
                    },
                ),
            ),
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=strings.ARTICLE_IS_ALREADY_FAVORITED,
    )
DEFAULT_ARTICLES_OFFSET = 0
from app.models.schemas.articles import (
    DEFAULT_ARTICLES_LIMIT,
    DEFAULT_ARTICLES_OFFSET,
    ArticleForResponse,
    ArticleInResponse,
    ListOfArticlesInResponse,
)

router = APIRouter()


async def get_articles_for_user_feed(
    limit: int = Query(DEFAULT_ARTICLES_LIMIT, ge=1),
    offset: int = Query(DEFAULT_ARTICLES_OFFSET, ge=0),
    user: User = Depends(get_current_user_authorizer()),
    articles_repo: ArticlesRepository = Depends(get_repository(ArticlesRepository)),
) -> ListOfArticlesInResponse:
    client = MongoClient("mongodb://localhost:27017")
    db = client["your_database_name"]
    articles_collection = db["articles"]
    users_collection = db["users"]

    user_data = users_collection.find_one({"_id": ObjectId(user.id)})
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=strings.USER_DOES_NOT_EXIST)

    following_ids = user_data.get("followings", [])
    articles_cursor = articles_collection.find(
        {"author_id": {"$in": following_ids}}
    ).skip(offset).limit(limit)

    articles = [Article(**article) for article in articles_cursor]
    articles_for_response = [ArticleForResponse(**article.dict()) for article in articles]

    return ListOfArticlesInResponse(
        articles=articles_for_response,
        articles_count=articles_collection.count_documents({"author_id": {"$in": following_ids}})
    )
