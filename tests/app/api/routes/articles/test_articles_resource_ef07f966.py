import pytest
import asyncio
from app.api.routes.articles.articles_resource import delete_article_by_slug, retrieve_article_by_slug, update_article_by_slug, create_new_article, list_articles
from app.api.dependencies.database import get_repository
from app.db.repositories.articles import ArticlesRepository
from app.models.domain.articles import Article
from app.models.domain.users import User
from app.services.articles import get_slug_for_article, get_article_by_slug_from_path
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

@pytest.fixture
async def articles_repo():
    return get_repository(ArticlesRepository)()

async def mock_get_article_by_slug_from_path(slug):
    article = Article(id='article_id', slug=slug, title='article_title', description='article_description', body='article_body', author=User(id='user_id', username='username'))
    return article
async def mock_get_slug_for_article(title):
    return 'slug_for_article'
async def mock_check_article_exists(articles_repo, slug):
    return False
async def mock_get_articles_filters():
    return ArticlesFilters(tag='tag', author=User(id='user_id', username='username'), favorited=True, limit=10, offset=0)

def test_delete_article_by_slug(articles_repo):
    article = Article(id='article_id', slug='slug', title='article_title', description='article_description', body='article_body', author=User(id='user_id', username='username'))
    with patch('app.api.routes.articles.articles_resource.get_article_by_slug_from_path', side_effect=mock_get_article_by_slug_from_path):
        delete_article_by_slug(article, articles_repo)
    articles_repo.collection.delete_one.assert_awaited_with({'_id': article.id})

def test_retrieve_article_by_slug():
    slug = 'slug'
    articles_collection = MagicMock()
    articles_collection.find_one.return_value = {'_id': 'article_id', 'slug': slug, 'title': 'article_title', 'description': 'article_description', 'body': 'article_body', 'author_id': 'user_id'}
    result = retrieve_article_by_slug(slug, articles_collection)
    assert result.article.title == 'article_title'

def test_update_article_by_slug(articles_repo):
    article_update = ArticleInUpdate(title='new_title', description='new_description', body='new_body')
    current_article = Article(id='article_id', slug='slug', title='article_title', description='article_description', body='article_body', author=User(id='user_id', username='username'))
    with patch('app.api.routes.articles.articles_resource.get_article_by_slug_from_path', side_effect=mock_get_article_by_slug_from_path):
        result = update_article_by_slug(article_update, current_article, articles_repo)
    assert result.article.title == 'new_title'

def test_create_new_article(articles_repo):
    article_create = ArticleInCreate(title='new_title', description='new_description', body='new_body', tags=['tag'])
    user = User(id='user_id', username='username')
    with patch('app.api.routes.articles.articles_resource.check_article_exists', side_effect=mock_check_article_exists):
        result = create_new_article(article_create, user, articles_repo)
    assert result.article.title == 'new_title'

def test_list_articles(articles_repo):
    articles_filters = ArticlesFilters(tag='tag', author=User(id='user_id', username='username'), favorited=True, limit=10, offset=0)
    with patch('app.api.routes.articles.articles_resource.get_articles_filters', side_effect=mock_get_articles_filters):
        result = list_articles(articles_filters, None, articles_repo)
    assert len(result.articles) == 10