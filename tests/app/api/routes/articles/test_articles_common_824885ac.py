import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.api.routes.articles.articles_common import remove_article_from_favorites, mark_article_as_favorite, get_articles_for_user_feed
from app.models.domain.articles import Article
from app.models.domain.users import User
from app.models.schemas.articles import ArticleInResponse, ListOfArticlesInResponse, ArticleForResponse
from app.db.repositories.articles import ArticlesRepository
from app.resources import strings

@pytest.fixture
def mock_article():
    return Article(id='article_id', favorited=False, favorites_count=0)

@pytest.fixture
def mock_user():
    return User(id='user_id')

@pytest.fixture
def mock_articles_repo():
    return MagicMock(spec=ArticlesRepository)



def test_remove_article_from_favorites_not_favorited(mock_article, mock_user, mock_articles_repo):
    with pytest.raises(HTTPException) as exc_info:
        remove_article_from_favorites(mock_article, mock_user, mock_articles_repo)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == strings.ARTICLE_IS_NOT_FAVORITED

def test_remove_article_from_favorites_success(mock_article, mock_user, mock_articles_repo):
    mock_article.favorited = True
    mock_article.favorites_count = 1
    with patch('app.api.routes.articles.articles_common.users_collection.update_one') as mock_update_one_user, \
         patch('app.api.routes.articles.articles_common.articles_collection.update_one') as mock_update_one_article:
        response = remove_article_from_favorites(mock_article, mock_user, mock_articles_repo)
        mock_update_one_user.assert_called_once()
        mock_update_one_article.assert_called_once()
        assert response.article.favorited == False
        assert response.article.favorites_count == 0

def test_mark_article_as_favorite_already_favorited(mock_article, mock_user, mock_articles_repo):
    mock_article.favorited = True
    with pytest.raises(HTTPException) as exc_info:
        mark_article_as_favorite(mock_article, mock_user, mock_articles_repo)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == strings.ARTICLE_IS_ALREADY_FAVORITED

def test_mark_article_as_favorite_success(mock_article, mock_user, mock_articles_repo):
    with patch('app.api.routes.articles.articles_common.users_collection.update_one') as mock_update_one_user, \
         patch('app.api.routes.articles.articles_common.articles_collection.update_one') as mock_update_one_article:
        response = mark_article_as_favorite(mock_article, mock_user, mock_articles_repo)
        mock_update_one_user.assert_called_once()
        mock_update_one_article.assert_called_once()
        assert response.article.favorited == True
        assert response.article.favorites_count == 1

def test_get_articles_for_user_feed_no_user_data(mock_user, mock_articles_repo):
    with patch('app.api.routes.articles.articles_common.users_collection.find_one', return_value=None):
        with pytest.raises(HTTPException) as exc_info:
            get_articles_for_user_feed(user=mock_user, articles_repo=mock_articles_repo)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == strings.USER_DOES_NOT_EXIST

def test_get_articles_for_user_feed_success(mock_user, mock_articles_repo):
    user_data = {'followings': ['author_id']}
    article_data = {'author_id': 'author_id', 'title': 'Test Article'}
    with patch('app.api.routes.articles.articles_common.users_collection.find_one', return_value=user_data), \
         patch('app.api.routes.articles.articles_common.articles_collection.find', return_value=[article_data]):
        response = get_articles_for_user_feed(user=mock_user, articles_repo=mock_articles_repo)
        assert len(response.articles) == 1
        assert response.articles[0].title == 'Test Article'
        assert response.articles_count == 1