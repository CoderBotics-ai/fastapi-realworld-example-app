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
from typing import Optional, List
from fastapi import APIRouter, Depends
from app.models.schemas.articles import ListOfArticlesInResponse, ArticleForResponse, ArticlesFilters
from pymongo.collection import Collection
from bson import ObjectId
from datetime import datetime


@router.get("/{slug}", response_model=ArticleInResponse, name="articles:get-article")
async def retrieve_article_by_slug(
    slug: str,
    articles_repo: Collection = Depends(get_repository(ArticlesRepository)),
) -> ArticleInResponse:
    article_data = await articles_repo.find_one({"slug": slug})
    if not article_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=strings.ARTICLE_DOES_NOT_EXIST,
        )
    article = Article(**article_data)
    return ArticleInResponse(article=ArticleForResponse.from_orm(article))


@router.put(
    "/{slug}",
    response_model=ArticleInResponse,
    name="articles:update-article",
    dependencies=[Depends(check_article_modification_permissions)],
)
async def update_article_by_slug(
    article_update: ArticleInUpdate = Body(..., embed=True, alias="article"),
    current_article: Article = Depends(get_article_by_slug_from_path),
    articles_repo: Collection = Depends(get_repository(ArticlesRepository)),
) -> ArticleInResponse:
    slug = get_slug_for_article(article_update.title) if article_update.title else None
    update_data = article_update.dict()
    if slug:
        update_data['slug'] = slug
    update_data['updated_at'] = datetime.utcnow()

    result = articles_repo.update_one(
        {"_id": current_article.id},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=strings.ARTICLE_NOT_FOUND)

    updated_article = articles_repo.find_one({"_id": current_article.id})
    return ArticleInResponse(article=ArticleForResponse.from_orm(updated_article))


@router.delete(
    "/{slug}",
    status_code=status.HTTP_204_NO_CONTENT,
    name="articles:delete-article",
    dependencies=[Depends(check_article_modification_permissions)],
    response_class=Response,
)
async def delete_article_by_slug(
    article: Article = Depends(get_article_by_slug_from_path),
    articles_repo: Collection = Depends(get_repository(ArticlesRepository)),
) -> None:
    await articles_repo.delete_one({"slug": article.slug})


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ArticleInResponse,
    name="articles:create-article",
)
async def create_new_article(
    article_create: ArticleInCreate = Body(..., embed=True, alias="article"),
    user: User = Depends(get_current_user_authorizer()),
    articles_repo: Collection = Depends(get_repository(ArticlesRepository)),
) -> ArticleInResponse:
    slug = get_slug_for_article(article_create.title)
    if await check_article_exists(articles_repo, slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=strings.ARTICLE_ALREADY_EXISTS,
        )

    article_data = {
        "slug": slug,
        "title": article_create.title,
        "description": article_create.description,
        "body": article_create.body,
        "author_id": ObjectId(user.id),
        "tags": article_create.tags,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "favorited_by": [],
        "comments": []
    }

    result = await articles_repo.insert_one(article_data)
    article_data["_id"] = result.inserted_id

    article = Article(**article_data)
    return ArticleInResponse(article=ArticleForResponse.from_orm(article))

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

router = APIRouter()


@router.get("", response_model=ListOfArticlesInResponse, name="articles:list-articles")
async def list_articles(
    articles_filters: ArticlesFilters = Depends(get_articles_filters),
    user: Optional[User] = Depends(get_current_user_authorizer(required=False)),
    articles_repo: Collection = Depends(get_repository(ArticlesRepository)),
) -> ListOfArticlesInResponse:
    query = {}
    
    if articles_filters.tag:
        query["tags"] = articles_filters.tag
    if articles_filters.author:
        author = await articles_repo.find_one({"username": articles_filters.author})
        if author:
            query["author_id"] = author["_id"]
    if articles_filters.favorited:
        favorited_user = await articles_repo.find_one({"username": articles_filters.favorited})
        if favorited_user:
            query["favorited_by"] = favorited_user["_id"]
    
    articles_cursor = articles_repo.find(query).skip(articles_filters.offset).limit(articles_filters.limit)
    articles = await articles_cursor.to_list(length=articles_filters.limit)
    
    articles_for_response = [
        ArticleForResponse.from_orm(Article(**article)) for article in articles
    ]
    
    return ListOfArticlesInResponse(
        articles=articles_for_response,
        articles_count=len(articles),
    )
