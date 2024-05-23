import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from app.api.routes.articles.articles_resource import delete_article_by_slug, update_article_by_slug, retrieve_article_by_slug, create_new_article, list_articles
from app.models.domain.articles import Article
from app.models.domain.users import User
from app.models.schemas.articles import ArticleInCreate, ArticleInUpdate, ArticleInResponse, ListOfArticlesInResponse, ArticleForResponse
from app.api.dependencies.articles import ArticlesFilters

@pytest.fixture
def mock_article():
    return Article(id='507f1f77bcf86cd799439011', slug='test-article', title='Test Article', description='Test Description', body='Test Body', author_id='507f1f77bcf86cd799439012', tags=['test'], created_at='2021-01-01T00:00:00', updated_at='2021-01-01T00:00:00')

@pytest.fixture
def mock_user():
    return User(id='507f1f77bcf86cd799439012', username='testuser', email='testuser@example.com', bio='Test Bio', image=None, password='password')

@pytest.fixture
def mock_article_create():
    return ArticleInCreate(title='New Article', description='New Description', body='New Body', tags=['new'])

@pytest.fixture
def mock_article_update():
    return ArticleInUpdate(title='Updated Article', description='Updated Description', body='Updated Body', tags=['updated'])

@pytest.fixture
def mock_articles_filters():
    return ArticlesFilters(tag='test', author='testuser', favorited='testuser', limit=10, offset=0)



@pytest.mark.asyncio
async def test_delete_article_by_slug(mock_article):
    mock_db = MagicMock()
    mock_db.get_database().get_collection().delete_one.return_value = None
    with patch('app.api.routes.articles.articles_resource.get_article_by_slug_from_path', return_value=mock_article), patch('app.api.routes.articles.articles_resource.get_repository', return_value=mock_db):
        response = await delete_article_by_slug(article=mock_article, db=mock_db)
        assert response is None

@pytest.mark.asyncio
async def test_update_article_by_slug(mock_article, mock_article_update):
    mock_db = MagicMock()
    mock_db.get_database().get_collection().update_one.return_value.matched_count = 1
    mock_db.get_database().get_collection().find_one.return_value = mock_article.dict()
    with patch('app.api.routes.articles.articles_resource.get_article_by_slug_from_path', return_value=mock_article), patch('app.api.routes.articles.articles_resource.get_repository', return_value=mock_db), patch('app.services.articles.get_slug_for_article', return_value='updated-article'):
        response = await update_article_by_slug(article_update=mock_article_update, current_article=mock_article, articles_repo=mock_db, db=mock_db)
        assert response.article.slug == 'updated-article'

@pytest.mark.asyncio
async def test_retrieve_article_by_slug(mock_article):
    mock_db = MagicMock()
    mock_db.get_database().get_collection().find_one.return_value = mock_article.dict()
    with patch('app.api.routes.articles.articles_resource.get_article_by_slug_from_path', return_value=mock_article):
        response = await retrieve_article_by_slug(article=mock_article)
        assert response.article.slug == mock_article.slug

@pytest.mark.asyncio
async def test_create_new_article(mock_article_create, mock_user):
    mock_db = MagicMock()
    mock_db.get_database().get_collection().insert_one.return_value.inserted_id = '507f1f77bcf86cd799439011'
    with patch('app.api.routes.articles.articles_resource.get_current_user_authorizer', return_value=mock_user), patch('app.api.routes.articles.articles_resource.get_repository', return_value=mock_db), patch('app.services.articles.get_slug_for_article', return_value='new-article'), patch('app.services.articles.check_article_exists', return_value=False):
        response = await create_new_article(article_create=mock_article_create, user=mock_user, articles_repo=mock_db)
        assert response.article.slug == 'new-article'

@pytest.mark.asyncio
async def test_list_articles(mock_articles_filters, mock_user):
    mock_db = MagicMock()
    mock_db.get_database().get_collection().find.return_value = [mock_article().dict()]
    with patch('app.api.routes.articles.articles_resource.get_articles_filters', return_value=mock_articles_filters), patch('app.api.routes.articles.articles_resource.get_current_user_authorizer', return_value=mock_user):
        response = await list_articles(articles_filters=mock_articles_filters, user=mock_user)
        assert len(response.articles) == 1
        assert response.articles[0].slug == 'test-article'