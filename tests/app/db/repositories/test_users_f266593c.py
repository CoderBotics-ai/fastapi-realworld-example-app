import pytest
from unittest.mock import patch, MagicMock
from app.db.repositories.users import UsersRepository
from app.models.domain.users import User, UserInDB
from app.db.errors import EntityDoesNotExist

@pytest.fixture
def user_data():
    return {
        'username': 'testuser',
        'email': 'testuser@example.com',
        'salt': 'somesalt',
        'hashed_password': 'hashedpassword',
        'bio': '',
        'image': '',
        'created_at': '2023-01-01T00:00:00',
        'updated_at': '2023-01-01T00:00:00',
        'followers': [],
        'followings': [],
        'favorites': [],
        'comments': []
    }



@pytest.mark.asyncio
async def test_get_user_by_email_existing_user(user_data):
    conn = MagicMock()
    repo = UsersRepository(conn)
    with patch('app.db.repositories.users.MongoClient') as mock_client:
        mock_db = mock_client.return_value.__getitem__.return_value
        mock_collection = mock_db.__getitem__.return_value
        user_data['_id'] = 'some_id'
        mock_collection.find_one.return_value = user_data
        user = await repo.get_user_by_email(email='testuser@example.com')
        assert user.email == 'testuser@example.com'

@pytest.mark.asyncio
async def test_get_user_by_email_non_existing_user():
    conn = MagicMock()
    repo = UsersRepository(conn)
    with patch('app.db.repositories.users.MongoClient') as mock_client:
        mock_db = mock_client.return_value.__getitem__.return_value
        mock_collection = mock_db.__getitem__.return_value
        mock_collection.find_one.return_value = None
        with pytest.raises(EntityDoesNotExist):
            await repo.get_user_by_email(email='nonexistent@example.com')

@pytest.mark.asyncio
async def test_get_user_by_username_existing_user(user_data):
    conn = MagicMock()
    repo = UsersRepository(conn)
    with patch('app.db.repositories.users.MongoClient') as mock_client:
        mock_db = mock_client.return_value.__getitem__.return_value
        mock_collection = mock_db.__getitem__.return_value
        mock_collection.find_one.return_value = user_data
        user = await repo.get_user_by_username(username='testuser')
        assert user.username == 'testuser'

@pytest.mark.asyncio
async def test_get_user_by_username_non_existing_user():
    conn = MagicMock()
    repo = UsersRepository(conn)
    with patch('app.db.repositories.users.MongoClient') as mock_client:
        mock_db = mock_client.return_value.__getitem__.return_value
        mock_collection = mock_db.__getitem__.return_value
        mock_collection.find_one.return_value = None
        with pytest.raises(EntityDoesNotExist):
            await repo.get_user_by_username(username='nonexistent')

@pytest.mark.asyncio
async def test_create_user(user_data):
    conn = MagicMock()
    repo = UsersRepository(conn)
    with patch('app.db.repositories.users.MongoClient') as mock_client:
        mock_db = mock_client.return_value.__getitem__.return_value
        mock_collection = mock_db.__getitem__.return_value
        mock_collection.insert_one.return_value.inserted_id = 'some_id'
        user = await repo.create_user(username='newuser', email='newuser@example.com', password='password')
        assert user.username == 'newuser'
        assert user.email == 'newuser@example.com'

@pytest.mark.asyncio
async def test_update_user(user_data):
    conn = MagicMock()
    repo = UsersRepository(conn)
    user = User(**user_data)
    with patch('app.db.repositories.users.MongoClient') as mock_client:
        mock_db = mock_client.return_value.__getitem__.return_value
        mock_collection = mock_db.__getitem__.return_value
        mock_collection.find_one.return_value = user_data
        mock_collection.update_one.return_value = None
        updated_user = await repo.update_user(user=user, username='updateduser')
        assert updated_user.username == 'updateduser'