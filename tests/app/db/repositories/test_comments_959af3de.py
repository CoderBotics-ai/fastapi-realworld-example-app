import pytest
from unittest.mock import AsyncMock, patch
from bson import ObjectId
from datetime import datetime
from app.db.repositories.comments import CommentsRepository
from app.models.domain.articles import Article
from app.models.domain.comments import Comment
from app.models.domain.users import User
from app.models.domain.profiles import Profile
from app.db.errors import EntityDoesNotExist

@pytest.fixture
def sample_user():
    return User(username='testuser', email='testuser@example.com', bio='', image='')

@pytest.fixture
def sample_article(sample_user):
    return Article(created_at=None, updated_at=None, id_='507f1f77bcf86cd799439011', slug='test-article', title='Test Title', description='Test Description', body='Test Body', tags=[], author=Profile(username='testuser', bio='', image='', following=False), favorited=False, favorites_count=0)

@pytest.fixture
def sample_comment(sample_user, sample_article):
    return Comment(id_=ObjectId(), body='Test Comment', author=sample_user, created_at=datetime.utcnow(), updated_at=datetime.utcnow(), article_id=sample_article.id_)

@pytest.fixture
def comments_repo():
    db = AsyncMock()
    return CommentsRepository(db)



@pytest.mark.asyncio
async def test_get_comment_by_id_found(comments_repo, sample_article, sample_user):
    comment_id = ObjectId()
    comment_data = {
        '_id': comment_id,
        'body': 'Test Comment',
        'author_username': sample_user.username,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'article_id': ObjectId(sample_article.id_)
    }
    comments_repo._db.comments.find_one = AsyncMock(return_value=comment_data)
    comment = await comments_repo.get_comment_by_id(comment_id=comment_id, article=sample_article, user=sample_user)
    assert comment.body == 'Test Comment'
    assert comment.author.username == 'testuser'

@pytest.mark.asyncio
async def test_get_comment_by_id_not_found(comments_repo, sample_article):
    comment_id = ObjectId()
    comments_repo._db.comments.find_one = AsyncMock(return_value=None)
    with pytest.raises(EntityDoesNotExist):
        await comments_repo.get_comment_by_id(comment_id=comment_id, article=sample_article)

@pytest.mark.asyncio
async def test_get_comments_for_article(comments_repo, sample_article, sample_user):
    comment_data = {
        '_id': ObjectId(),
        'body': 'Test Comment',
        'author_username': sample_user.username,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'article_id': ObjectId(sample_article.id_)
    }
    comments_repo._db.comments.find = AsyncMock(return_value=[comment_data])
    comments = await comments_repo.get_comments_for_article(article=sample_article, user=sample_user)
    assert len(comments) == 1
    assert comments[0].body == 'Test Comment'

@pytest.mark.asyncio
async def test_create_comment_for_article(comments_repo, sample_article, sample_user):
    comment_data = {
        '_id': ObjectId(),
        'body': 'Test Comment',
        'author_username': sample_user.username,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'article_id': ObjectId(sample_article.id_)
    }
    comments_repo._db.comments.insert_one = AsyncMock(return_value=AsyncMock(inserted_id=comment_data['_id']))
    comments_repo._db.comments.find_one = AsyncMock(return_value=comment_data)
    comment = await comments_repo.create_comment_for_article(body='Test Comment', article=sample_article, user=sample_user)
    assert comment.body == 'Test Comment'
    assert comment.author.username == 'testuser'

@pytest.mark.asyncio
async def test_delete_comment(comments_repo, sample_comment):
    comments_repo._db.comments.delete_one = AsyncMock()
    comments_repo._db.articles.update_one = AsyncMock()
    await comments_repo.delete_comment(comment=sample_comment)
    comments_repo._db.comments.delete_one.assert_called_once_with({'_id': ObjectId(sample_comment.id_)})
    comments_repo._db.articles.update_one.assert_called_once_with({'_id': ObjectId(sample_comment.article_id)}, {'$pull': {'comments': ObjectId(sample_comment.id_)}})