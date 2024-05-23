import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.articles import check_article_exists, get_slug_for_article, check_user_can_modify_article
from app.db.repositories.articles import ArticlesRepository
from app.models.domain.articles import Article
from app.models.domain.users import User





@pytest.mark.asyncio
async def test_check_article_exists():
    mock_articles_repo = MagicMock(spec=ArticlesRepository)
    mock_articles_repo.db = {'articles': AsyncMock()}
    mock_articles_repo.db['articles'].find_one = AsyncMock(return_value={'slug': 'test-slug'})
    result = await check_article_exists(mock_articles_repo, 'test-slug')
    assert result is True

    mock_articles_repo.db['articles'].find_one = AsyncMock(return_value=None)
    result = await check_article_exists(mock_articles_repo, 'test-slug')
    assert result is False

def test_get_slug_for_article():
    title = 'Test Article'
    expected_slug = 'test-article'
    assert get_slug_for_article(title) == expected_slug

def test_check_user_can_modify_article():
    mock_article = MagicMock(spec=Article)
    mock_user = MagicMock(spec=User)
    mock_article.author.username = 'author'
    mock_user.username = 'author'
    assert check_user_can_modify_article(mock_article, mock_user) is True

    mock_user.username = 'different_user'
    assert check_user_can_modify_article(mock_article, mock_user) is False