import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.api.dependencies.articles import check_article_modification_permissions, get_articles_filters, get_article_by_slug_from_path
from app.models.domain.articles import Article
from app.models.domain.users import User
from app.models.schemas.articles import ArticlesFilters
from app.resources import strings
from starlette import status



@pytest.fixture
def mock_user():
    return User(username='testuser', email='testuser@example.com')

@pytest.fixture
def mock_article():
    return Article(slug='test-article', title='Test Article', description='Test Description', body='Test Body', author='testuser')

@pytest.fixture
def mock_articles_repo():
    mock_repo = MagicMock()
    return mock_repo

def test_check_article_modification_permissions(mock_article, mock_user):
    with patch('app.services.articles.check_user_can_modify_article', return_value=True):
        try:
            check_article_modification_permissions(current_article=mock_article, user=mock_user)
        except HTTPException:
            pytest.fail('HTTPException raised unexpectedly!')

    with patch('app.services.articles.check_user_can_modify_article', return_value=False):
        with pytest.raises(HTTPException) as excinfo:
            check_article_modification_permissions(current_article=mock_article, user=mock_user)
        assert excinfo.value.status_code == status.HTTP_403_FORBIDDEN
        assert excinfo.value.detail == strings.USER_IS_NOT_AUTHOR_OF_ARTICLE

def test_get_articles_filters():
    filters = get_articles_filters(tag='tag1', author='author1', favorited='user1', limit=10, offset=0)
    assert isinstance(filters, ArticlesFilters)
    assert filters.tag == 'tag1'
    assert filters.author == 'author1'
    assert filters.favorited == 'user1'
    assert filters.limit == 10
    assert filters.offset == 0

@pytest.mark.asyncio
async def test_get_article_by_slug_from_path(mock_user, mock_articles_repo):
    mock_articles_repo.find_one.return_value = {
        'slug': 'test-article',
        'title': 'Test Article',
        'description': 'Test Description',
        'body': 'Test Body',
        'author': 'testuser'
    }
    with patch('app.api.dependencies.articles.articles_collection.find_one', return_value=mock_articles_repo.find_one.return_value):
        article = await get_article_by_slug_from_path(slug='test-article', user=mock_user, articles_repo=mock_articles_repo)
        assert isinstance(article, Article)
        assert article.slug == 'test-article'
        assert article.title == 'Test Article'
        assert article.description == 'Test Description'
        assert article.body == 'Test Body'
        assert article.author == 'testuser'

    with patch('app.api.dependencies.articles.articles_collection.find_one', return_value=None):
        with pytest.raises(HTTPException) as excinfo:
            await get_article_by_slug_from_path(slug='non-existent-article', user=mock_user, articles_repo=mock_articles_repo)
        assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
        assert excinfo.value.detail == strings.ARTICLE_DOES_NOT_EXIST_ERROR