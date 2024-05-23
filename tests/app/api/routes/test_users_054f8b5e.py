import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.api.routes.users import update_current_user, retrieve_current_user
from app.models.domain.users import User
from app.models.schemas.users import UserInUpdate, UserInResponse, UserWithToken
from app.core.settings.app import AppSettings
from app.resources import strings

@pytest.fixture
def current_user():
    return User(id='507f1f77bcf86cd799439011', username='testuser', email='test@example.com', bio='bio', image='image')

@pytest.fixture
def user_update():
    return UserInUpdate(username='newusername', email='newemail@example.com')

@pytest.fixture
def settings():
    return AppSettings(database_url='mongodb://localhost:27017', database_name='testdb', secret_key='secret')

@pytest.fixture
def users_repo():
    return MagicMock()



@pytest.mark.asyncio
async def test_update_current_user(current_user, user_update, settings, users_repo):
    with patch('app.api.routes.users.MongoClient') as MockMongoClient, \
         patch('app.api.routes.users.check_username_is_taken', new_callable=AsyncMock) as mock_check_username_is_taken, \
         patch('app.api.routes.users.check_email_is_taken', new_callable=AsyncMock) as mock_check_email_is_taken, \
         patch('app.api.routes.users.jwt.create_access_token_for_user') as mock_create_access_token_for_user:

        mock_client = MockMongoClient.return_value
        mock_db = mock_client[settings.database_name]
        mock_collection = mock_db['users']

        mock_collection.update_one.return_value.modified_count = 1
        mock_collection.find_one.return_value = {
            '_id': '507f1f77bcf86cd799439011',
            'username': 'newusername',
            'email': 'newemail@example.com',
            'bio': 'bio',
            'image': 'image'
        }

        mock_create_access_token_for_user.return_value = 'newtoken'

        response = await update_current_user(user_update, current_user, users_repo, settings)

        assert response.user.username == 'newusername'
        assert response.user.email == 'newemail@example.com'
        assert response.user.token == 'newtoken'

@pytest.mark.asyncio
async def test_retrieve_current_user(current_user, settings):
    with patch('app.api.routes.users.MongoClient') as MockMongoClient, \
         patch('app.api.routes.users.jwt.create_access_token_for_user') as mock_create_access_token_for_user:

        mock_client = MockMongoClient.return_value
        mock_db = mock_client[settings.database_name]
        mock_collection = mock_db['users']

        mock_collection.find_one.return_value = {
            '_id': '507f1f77bcf86cd799439011',
            'username': 'testuser',
            'email': 'test@example.com',
            'bio': 'bio',
            'image': 'image'
        }

        mock_create_access_token_for_user.return_value = 'token'

        response = await retrieve_current_user(current_user, settings)

        assert response.user.username == 'testuser'
        assert response.user.email == 'test@example.com'
        assert response.user.token == 'token'