import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from app.api.dependencies.comments import check_comment_modification_permissions, get_mongo_client, get_comment_by_id_from_path
from app.models.domain.articles import Article
from app.models.domain.comments import Comment
from app.models.domain.users import User
from app.db.errors import EntityDoesNotExist
from app.resources import strings



@pytest.fixture
def mock_comment():
    return Comment(id=1, body='Test comment', author_id=1, article_id=1)

@pytest.fixture
def mock_user():
    return User(id=1, username='testuser')

@pytest.fixture
def mock_article():
    return Article(id=1, slug='test-article', author_id=1)

@pytest.fixture
def mock_comments_repo():
    repo = AsyncMock()
    repo.get_comment_by_id = AsyncMock()
    return repo

def test_check_comment_modification_permissions(mock_comment, mock_user):
    with patch('app.services.comments.check_user_can_modify_comment', return_value=True):
        try:
            check_comment_modification_permissions(comment=mock_comment, user=mock_user)
        except HTTPException:
            pytest.fail('HTTPException was raised unexpectedly!')

    with patch('app.services.comments.check_user_can_modify_comment', return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            check_comment_modification_permissions(comment=mock_comment, user=mock_user)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == strings.USER_IS_NOT_AUTHOR_OF_ARTICLE

def test_get_mongo_client():
    client = get_mongo_client()
    assert isinstance(client, MongoClient)

@pytest.mark.asyncio
async def test_get_comment_by_id_from_path(mock_article, mock_user, mock_comments_repo, mock_comment):
    mock_comments_repo.get_comment_by_id.return_value = mock_comment
    with patch('app.api.dependencies.articles.get_article_by_slug_from_path', return_value=mock_article):
        with patch('app.api.dependencies.authentication.get_current_user_authorizer', return_value=mock_user):
            comment = await get_comment_by_id_from_path(comment_id=1, article=mock_article, user=mock_user, comments_repo=mock_comments_repo)
            assert comment == mock_comment

    mock_comments_repo.get_comment_by_id.side_effect = EntityDoesNotExist
    with pytest.raises(HTTPException) as exc_info:
        await get_comment_by_id_from_path(comment_id=1, article=mock_article, user=mock_user, comments_repo=mock_comments_repo)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == strings.COMMENT_DOES_NOT_EXIST