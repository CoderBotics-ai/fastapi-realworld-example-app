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
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.results import Cursor

from app.api.dependencies.articles import (
    check_article_modification_permissions,
    get_article_by_slug_from_path,
    get_articles_filters,
)

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



@router.get("/{slug}", response_model=ArticleInResponse, name="articles:get-article")
async def retrieve_article_by_slug(
    slug: str,
    articles_repo: ArticlesRepository = Depends(get_repository(ArticlesRepository)),
) -> ArticleInResponse:
    article = await articles_repo.get_article_by_slug(slug)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=strings.ARTICLE_NOT_FOUND)
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
    articles_repo: ArticlesRepository = Depends(get_repository(ArticlesRepository)),
) -> ArticleInResponse:
    slug = get_slug_for_article(article_update.title) if article_update.title else None
    article = await articles_repo.update_article(
        article=current_article,
        slug=slug,
        **article_update.dict(),
    )
    return ArticleInResponse(article=ArticleForResponse.from_orm(article))



@router.delete(
    "/{slug}",
    status_code=status.HTTP_204_NO_CONTENT,
    name="articles:delete-article",
    dependencies=[Depends(check_article_modification_permissions)],
    response_class=Response,
)
async def delete_article_by_slug(
    article: Article = Depends(get_article_by_slug_from_path),
    articles_repo: ArticlesRepository = Depends(get_repository(ArticlesRepository)),
) -> None:
    await articles_repo.delete_article(article=article)
from app.models.schemas.articles import (
    ArticleForResponse,
    ArticleInCreate,
    ArticleInResponse,
    ArticleInUpdate,
    ArticlesFilters,
    ListOfArticlesInResponse,
)

router = APIRouter()


# Assuming the MongoClient and database are already set up and accessible via the 'articles_repo' dependency

@router.get("", response_model=ListOfArticlesInResponse, name="articles:list-articles")
async def list_articles(
    articles_filters: ArticlesFilters = Depends(get_articles_filters),
    user: Optional[User] = Depends(get_current_user_authorizer(required=False)),
    articles_repo: ArticlesRepository = Depends(get_repository(ArticlesRepository)),
) -> ListOfArticlesInResponse:
    # Connect to the MongoDB collection
    collection = MongoClient().get_database().get_collection('articles')

    # Construct the query based on filters
    query = {}
    if articles_filters.tag:
        query['tags'] = articles_filters.tag
    if articles_filters.author:
        query['author_id'] = articles_filters.author
    if articles_filters.favorited:
        # Assuming 'favorited' is a user ID, we need to check if the user has favorited the article
        query['favorited_by'] = {'$in': [articles_filters.favorited]}

    # Apply pagination
    skip = articles_filters.offset
    limit = articles_filters.limit

    # Execute the query
    cursor: Cursor = collection.find(query).skip(skip).limit(limit)

    # Fetch the articles and apply the user filter if provided
    articles = []
    for doc in cursor:
        # Convert ObjectId to string if necessary
        doc['_id'] = str(doc['_id'])
        if user and user._id in doc['favorited_by']:
            articles.append(Article(**doc))
        elif not user:
            articles.append(Article(**doc))

    # Convert articles to the response model
    articles_for_response = [
        ArticleForResponse.from_orm(article) for article in articles
    ]

    return ListOfArticlesInResponse(
        articles=articles_for_response,
        articles_count=len(articles),
    )
