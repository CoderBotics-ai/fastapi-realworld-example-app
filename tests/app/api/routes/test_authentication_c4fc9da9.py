import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST
from app.api.routes.authentication import register, login
from app.models.schemas.users import UserInCreate, UserInLogin, UserInResponse, UserWithToken
from app.resources import strings
from bson.objectid import ObjectId
from datetime import datetime



@pytest.fixture
def user_create():
    return UserInCreate(username='testuser', email='test@example.com', password='password123')

@pytest.fixture
def user_login():
    return UserInLogin(email='test@example.com', password='password123')

@pytest.fixture
def users_repo():
    repo = MagicMock()
    repo.collection = MagicMock()
    return repo

@pytest.fixture
def settings():
    settings = MagicMock()
    settings.secret_key.get_secret_value.return_value = 'secret'
    return settings

@pytest.mark.asyncio
async def test_register_success(user_create, users_repo, settings):
    users_repo.collection.find_one.return_value = {
        '_id': ObjectId(),
        'username': 'testuser',
        'email': 'test@example.com',
        'bio': None,
        'image': None
    }
    with patch('app.services.authentication.check_username_is_taken', new_callable=AsyncMock) as mock_check_username,
         patch('app.services.authentication.check_email_is_taken', new_callable=AsyncMock) as mock_check_email,
         patch('app.services.jwt.create_access_token_for_user', return_value='token') as mock_create_token:
        mock_check_username.return_value = False
        mock_check_email.return_value = False
        response = await register(user_create, users_repo, settings)
        assert response.user.username == 'testuser'
        assert response.user.email == 'test@example.com'
        assert response.user.token == 'token'

@pytest.mark.asyncio
async def test_register_username_taken(user_create, users_repo, settings):
    with patch('app.services.authentication.check_username_is_taken', new_callable=AsyncMock) as mock_check_username:
        mock_check_username.return_value = True
        with pytest.raises(HTTPException) as exc_info:
            await register(user_create, users_repo, settings)
        assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == strings.USERNAME_TAKEN

@pytest.mark.asyncio
async def test_register_email_taken(user_create, users_repo, settings):
    with patch('app.services.authentication.check_username_is_taken', new_callable=AsyncMock) as mock_check_username,
         patch('app.services.authentication.check_email_is_taken', new_callable=AsyncMock) as mock_check_email:
        mock_check_username.return_value = False
        mock_check_email.return_value = True
        with pytest.raises(HTTPException) as exc_info:
            await register(user_create, users_repo, settings)
        assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == strings.EMAIL_TAKEN

@pytest.mark.asyncio
async def test_login_success(user_login, users_repo, settings):
    user_data = {
        '_id': ObjectId(),
        'username': 'testuser',
        'email': 'test@example.com',
        'bio': None,
        'image': None,
        'password': 'hashedpassword'
    }
    users_repo.collection.find_one.return_value = user_data
    user = MagicMock()
    user.check_password.return_value = True
    users_repo.map_user_data_to_user.return_value = user
    with patch('app.services.jwt.create_access_token_for_user', return_value='token') as mock_create_token:
        response = await login(user_login, users_repo, settings)
        assert response.user.username == 'testuser'
        assert response.user.email == 'test@example.com'
        assert response.user.token == 'token'

@pytest.mark.asyncio
async def test_login_incorrect_email(user_login, users_repo, settings):
    users_repo.collection.find_one.return_value = None
    with pytest.raises(HTTPException) as exc_info:
        await login(user_login, users_repo, settings)
    assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == strings.INCORRECT_LOGIN_INPUT

@pytest.mark.asyncio
async def test_login_incorrect_password(user_login, users_repo, settings):
    user_data = {
        '_id': ObjectId(),
        'username': 'testuser',
        'email': 'test@example.com',
        'bio': None,
        'image': None,
        'password': 'hashedpassword'
    }
    users_repo.collection.find_one.return_value = user_data
    user = MagicMock()
    user.check_password.return_value = False
    users_repo.map_user_data_to_user.return_value = user
    with pytest.raises(HTTPException) as exc_info:
        await login(user_login, users_repo, settings)
    assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == strings.INCORRECT_LOGIN_INPUT