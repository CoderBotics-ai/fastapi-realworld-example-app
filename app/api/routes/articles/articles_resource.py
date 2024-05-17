from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Response
from starlette import status
from app.api.dependencies.authentication import get_current_user_authorizer
from app.api.dependencies.database import get_repository
from app.db.repositories.articles import ArticlesRepository
from app.models.domain.articles import Article
from app.models.domain.users import User
from app.resources import strings
from app.services.articles import check_article_exists, get_slug_for_article
from typing import List, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from app.api.dependencies.database import ArticlesRepository
from app.services.articles import get_slug_for_article, get_article_by_slug_from_path
from app.models.domain.articles import ArticleInResponse, ArticleInUpdate, ArticleForResponse, ListOfArticlesInResponse, ArticlesFilters

from app.api.dependencies.articles import (
    check_article_modification_permissions,
    get_article_by_slug_from_path,
    get_articles_filters,
)
from app.models.schemas.articles import (
    ArticleForResponse,
    ArticleInCreate,
    ArticleInResponse,
    ArticleInUpdate,
    ArticlesFilters,
    ListOfArticlesInResponse,
)

async def delete_article_by_slug(
    article: Article = Depends(get_article_by_slug_from_path),
    articles_repo: ArticlesRepository = Depends(get_repository(ArticlesRepository)),
) -> None:
    articles_collection: Collection = articles_repo.collection
    await articles_collection.delete_one({"_id": article.id})

router = APIRouter()


async def retrieve_article_by_slug(
    slug: str,
    articles_collection: Collection
) -> ArticleInResponse:
    """Retrieves an article by its slug."""
    article = articles_collection.find_one({"slug": slug})
    if article is None:
        raise HTTPException(status_code=404, detail=strings.ARTICLE_NOT_FOUND)
    return ArticleInResponse(article=ArticleForResponse.from_orm(article))

async def update_article_by_slug(
    article_update: ArticleInUpdate = Body(..., embed=True, alias="article"),
    current_article: Article = Depends(get_article_by_slug_from_path),
    articles_repo: ArticlesRepository = Depends(get_repository(ArticlesRepository)),
) -> ArticleInResponse:
    slug = get_slug_for_article(article_update.title) if article_update.title else None
    article_data = article_update.dict()
    if slug:
        article_data["slug"] = slug
    articles_repo.collection.update_one({"slug": current_article.slug}, {"$set": article_data})
    article = articles_repo.collection.find_one({"slug": current_article.slug})
    return ArticleInResponse(article=ArticleForResponse.from_orm(article))


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ArticleInResponse,
    name="articles:create-article",
)
async def create_new_article(
    article_create: ArticleInCreate = Body(..., embed=True, alias="article"),
    user: User = Depends(get_current_user_authorizer()),
    articles_repo: ArticlesRepository = Depends(get_repository(ArticlesRepository)),
) -> ArticleInResponse:
    slug = get_slug_for_article(article_create.title)
    if await check_article_exists(articles_repo, slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=strings.ARTICLE_ALREADY_EXISTS,
        )

    article = await articles_repo.create_article(
        slug=slug,
        title=article_create.title,
        description=article_create.description,
        body=article_create.body,
        author=user,
        tags=article_create.tags,
    )
    return ArticleInResponse(article=ArticleForResponse.from_orm(article))


@router.get("", response_model=ListOfArticlesInResponse, name="articles:list-articles")
async def list_articles(
    articles_filters: ArticlesFilters = Depends(get_articles_filters),
    user: Optional[User] = Depends(get_current_user_authorizer(required=False)),
    articles_repo: ArticlesRepository = Depends(get_repository(ArticlesRepository)),
) -> ListOfArticlesInResponse:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["database"]
    articles_collection = db["articles"]
    articles_query = {}
    if articles_filters.tag:
        articles_query["tags"] = articles_filters.tag
    if articles_filters.author:
        articles_query["author_id"] = articles_filters.author.id
    if articles_filters.favorited:
        articles_query["favorited_by"] = user.id
    articles_cursor = articles_collection.find(articles_query).limit(articles_filters.limit).skip(articles_filters.offset)
    articles = [Article(**article) for article in articles_cursor]
    articles_for_response = [ArticleForResponse.from_orm(article) for article in articles]
    return ListOfArticlesInResponse(
        articles=articles_for_response,
        articles_count=articles_collection.count_documents(articles_query),
    )
