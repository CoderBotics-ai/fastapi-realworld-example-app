from typing import Optional

from fastapi import Depends, HTTPException, Path, Query
from starlette import status

from app.api.dependencies.authentication import get_current_user_authorizer
from app.api.dependencies.database import get_repository
from app.db.errors import EntityDoesNotExist
from app.db.repositories.articles import ArticlesRepository
from app.models.domain.articles import Article
from app.models.domain.users import User
from app.resources import strings
from app.services.articles import check_user_can_modify_article
from pymongo import MongoClient

from pymongo import MongoClient
from pymongo.collection import Collection
from fastapi import HTTPException, status
from app.models.schemas.articles import (
    DEFAULT_ARTICLES_LIMIT,
    DEFAULT_ARTICLES_OFFSET,
    ArticlesFilters,
)


def get_articles_filters(
    tag: Optional[str] = None,
    author: Optional[str] = None,
    favorited: Optional[str] = None,
    limit: int = Query(DEFAULT_ARTICLES_LIMIT, ge=1),
    offset: int = Query(DEFAULT_ARTICLES_OFFSET, ge=0),
) -> ArticlesFilters:
    return ArticlesFilters(
        tag=tag,
        author=author,
        favorited=favorited,
        limit=limit,
        offset=offset,
    )

def check_article_modification_permissions(
    current_article: Article = Depends(get_article_by_slug_from_path),
    user: User = Depends(get_current_user_authorizer()),
) -> None:
    if not check_user_can_modify_article(current_article, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=strings.USER_IS_NOT_AUTHOR_OF_ARTICLE,
        )


async def get_article_by_slug_from_path(
    slug: str = Path(..., min_length=1),
    user: Optional[User] = Depends(get_current_user_authorizer(required=False)),
    db: MongoClient = Depends(get_repository(MongoClient)),
) -> Article:
    try:
        article_collection = db.articles
        article = article_collection.find_one({"slug": slug})
        if article:
            return Article(**article)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=strings.ARTICLE_DOES_NOT_EXIST_ERROR,
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=strings.INTERNAL_SERVER_ERROR,
        )
