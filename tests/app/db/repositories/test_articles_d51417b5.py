import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from bson.objectid import ObjectId
from app.db.repositories.articles import ArticlesRepository
from app.models.domain.articles import Article
from app.models.domain.users import User
from app.db.errors import EntityDoesNotExist

@pytest.fixture
def articles_repo():
    client = MagicMock()
    repo = ArticlesRepository(client)
    return repo



@pytest.mark.asyncio
async def test_create_article(articles_repo):
    mock_user = User(username='testuser', id=ObjectId('507f1f77bcf86cd799439011'), email='testuser@example.com')
    articles_repo._users_collection.find_one = MagicMock(return_value={'_id': ObjectId('507f1f77bcf86cd799439011'), 'username': 'testuser'})
    articles_repo._articles_collection.insert_one = MagicMock(return_value=MagicMock(inserted_id=ObjectId('507f1f77bcf86cd799439012')))
    articles_repo._articles_collection.find_one = MagicMock(return_value={'_id': ObjectId('507f1f77bcf86cd799439012'), 'slug': 'test-article', 'title': 'Test Article', 'description': 'Test Description', 'body': 'Test Body', 'author_id': ObjectId('507f1f77bcf86cd799439011'), 'tags': [], 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow(), 'favorited_by': [], 'comments': []})
    articles_repo._get_article_from_db_record = AsyncMock(return_value=Article(id_=ObjectId('507f1f77bcf86cd799439012'), slug='test-article', title='Test Article', description='Test Description', body='Test Body', author=mock_user, tags=[], favorites_count=0, favorited=False, created_at=datetime.utcnow(), updated_at=datetime.utcnow()))
    article = await articles_repo.create_article(slug='test-article', title='Test Article', description='Test Description', body='Test Body', author=mock_user, tags=[])
    assert article.slug == 'test-article'
    assert article.title == 'Test Article'
    assert article.description == 'Test Description'
    assert article.body == 'Test Body'
    assert article.author.username == 'testuser'
    assert article.tags == []
    assert article.favorites_count == 0
    assert article.favorited == False
    assert article.comments == []

@pytest.mark.asyncio
async def test_update_article(articles_repo):
    mock_article = Article(id_=ObjectId('507f1f77bcf86cd799439012'), slug='test-article', title='Test Article', description='Test Description', body='Test Body', author=User(username='testuser', id=ObjectId('507f1f77bcf86cd799439011'), email='testuser@example.com'), tags=['test'], favorites_count=0, favorited=False, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    articles_repo._articles_collection.update_one = MagicMock(return_value=MagicMock(matched_count=1))
    updated_article = await articles_repo.update_article(article=mock_article, title='Updated Test Article')
    assert updated_article.title == 'Updated Test Article'

@pytest.mark.asyncio
async def test_delete_article(articles_repo):
    mock_article = Article(id_=ObjectId('507f1f77bcf86cd799439012'), slug='test-article', title='Test Article', description='Test Description', body='Test Body', author=User(username='testuser', id=ObjectId('507f1f77bcf86cd799439011'), email='testuser@example.com'), tags=['test'], favorites_count=0, favorited=False, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    articles_repo._articles_collection.delete_one = MagicMock()
    await articles_repo.delete_article(article=mock_article)
    articles_repo._articles_collection.delete_one.assert_called_once_with({'slug': 'test-article', 'author_id': ObjectId('507f1f77bcf86cd799439011')})

@pytest.mark.asyncio
async def test_get_article_by_slug(articles_repo):
    mock_article_data = {'_id': ObjectId('507f1f77bcf86cd799439012'), 'slug': 'test-article', 'title': 'Test Article', 'description': 'Test Description', 'body': 'Test Body', 'author_id': ObjectId('507f1f77bcf86cd799439011'), 'tags': ['test'], 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow(), 'favorited_by': [], 'comments': []}
    articles_repo._articles_collection.find_one = MagicMock(return_value=mock_article_data)
    articles_repo._get_article_from_db_record = AsyncMock(return_value=Article(id_=ObjectId('507f1f77bcf86cd799439012'), slug='test-article', title='Test Article', description='Test Description', body='Test Body', author=User(username='testuser', id=ObjectId('507f1f77bcf86cd799439011'), email='testuser@example.com'), tags=['test'], favorites_count=0, favorited=False, created_at=datetime.utcnow(), updated_at=datetime.utcnow()))
    article = await articles_repo.get_article_by_slug(slug='test-article')
    assert article.slug == 'test-article'
    assert article.title == 'Test Article'
    assert article.description == 'Test Description'
    assert article.body == 'Test Body'
    assert article.author.username == 'testuser'
    assert article.tags == ['test']

@pytest.mark.asyncio
async def test_is_article_favorited_by_user(articles_repo):
    mock_user = User(username='testuser', id=ObjectId('507f1f77bcf86cd799439011'), email='testuser@example.com')
    articles_repo._articles_collection.find_one = MagicMock(return_value={'favorited_by': [ObjectId('507f1f77bcf86cd799439011')]})
    is_favorited = await articles_repo.is_article_favorited_by_user(slug='test-article', user=mock_user)
    assert is_favorited == True

@pytest.mark.asyncio
async def test_add_article_into_favorites(articles_repo):
    mock_user = User(username='testuser', id=ObjectId('507f1f77bcf86cd799439011'), email='testuser@example.com')
    mock_article = Article(id_=ObjectId('507f1f77bcf86cd799439012'), slug='test-article', title='Test Article', description='Test Description', body='Test Body', author=mock_user, tags=['test'], favorites_count=0, favorited=False, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    articles_repo._users_collection.update_one = MagicMock()
    articles_repo._articles_collection.update_one = MagicMock()
    await articles_repo.add_article_into_favorites(article=mock_article, user=mock_user)
    articles_repo._users_collection.update_one.assert_called_once_with({'_id': ObjectId('507f1f77bcf86cd799439011')}, {'$addToSet': {'favorites': ObjectId('507f1f77bcf86cd799439012')}})
    articles_repo._articles_collection.update_one.assert_called_once_with({'_id': ObjectId('507f1f77bcf86cd799439012')}, {'$addToSet': {'favorited_by': ObjectId('507f1f77bcf86cd799439011')}})

@pytest.mark.asyncio
async def test_remove_article_from_favorites(articles_repo):
    mock_user = User(username='testuser', id=ObjectId('507f1f77bcf86cd799439011'), email='testuser@example.com')
    mock_article = Article(id_=ObjectId('507f1f77bcf86cd799439012'), slug='test-article', title='Test Article', description='Test Description', body='Test Body', author=mock_user, tags=['test'], favorites_count=0, favorited=False, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    articles_repo._users_collection.update_one = MagicMock()
    articles_repo._articles_collection.update_one = MagicMock()
    await articles_repo.remove_article_from_favorites(article=mock_article, user=mock_user)
    articles_repo._users_collection.update_one.assert_called_once_with({'username': 'testuser'}, {'$pull': {'favorites': ObjectId('507f1f77bcf86cd799439012')}})
    articles_repo._articles_collection.update_one.assert_called_once_with({'slug': 'test-article'}, {'$pull': {'favorited_by': ObjectId('507f1f77bcf86cd799439011')}})