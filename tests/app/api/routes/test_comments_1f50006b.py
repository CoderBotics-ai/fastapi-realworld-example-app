import pytest
from app.api.routes.comments import delete_comment_from_article, create_comment_for_article, list_comments_for_article
from app.models.domain.comments import Comment
from app.models.domain.articles import Article
from app.models.domain.users import User
from app.db.repositories.comments import CommentsRepository
from unittest.mock import AsyncMock, MagicMock
from fastapi import Depends

@pytest.fixture
async def mock_comments_repo():
    return MagicMock(spec=CommentsRepository)

async def mock_get_comment_by_id_from_path():
    return Comment(id='123', body='test comment')

async def mock_get_article_by_slug_from_path():
    return Article(slug='test-slug', title='Test Article')

async def mock_get_current_user_authorizer():
    return User(username='test-user', email='test@example.com')

def test_delete_comment_from_article(mock_comments_repo):
    comment = Comment(id='123', body='test comment')
    mock_comments_repo.collection.delete_one = AsyncMock(return_value={})
    delete_comment_from_article(comment=comment, comments_repo=mock_comments_repo)
    mock_comments_repo.collection.delete_one.assert_awaited_with({'_id': '123'})

def test_create_comment_for_article(mock_comments_repo):
    comment_create = {'body': 'test comment'}
    article = Article(slug='test-slug', title='Test Article')
    user = User(username='test-user', email='test@example.com')
    mock_comments_repo.create_comment_for_article = AsyncMock(return_value=Comment(id='123', body='test comment'))
    result = create_comment_for_article(comment_create=comment_create, article=article, user=user, comments_repo=mock_comments_repo)
    assert result.comment.id == '123'
    assert result.comment.body == 'test comment'

def test_list_comments_for_article(mock_comments_repo):
    article = Article(slug='test-slug', title='Test Article')
    user = User(username='test-user', email='test@example.com')
    mock_comments_repo.get_comments_for_article = AsyncMock(return_value=[Comment(id='123', body='test comment')])
    result = list_comments_for_article(article=article, user=user, comments_repo=mock_comments_repo)
    assert len(result.comments) == 1
    assert result.comments[0].id == '123'