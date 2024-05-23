import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, Security
from starlette import status
from bson import ObjectId
from pymongo import MongoClient
from app.api.dependencies.authentication import _get_current_user, _get_current_user_optional, _get_authorization_header_optional, _get_authorization_header_retriever, get_current_user_authorizer, _get_authorization_header, RWAPIKeyHeader
from app.db.repositories.users import UsersRepository
from app.models.domain.users import User
from app.core.settings.app import AppSettings
from app.resources import strings
from app.services import jwt

@pytest.fixture
def mock_settings():
    settings = MagicMock(AppSettings)
    settings.secret_key.get_secret_value.return_value = 'secret'
    settings.database_url = 'mongodb://localhost:27017'
    settings.database_name = 'testdb'
    settings.jwt_token_prefix = 'Bearer'
    return settings

@pytest.fixture
def mock_users_repo():
    return AsyncMock(UsersRepository)



@pytest.mark.asyncio
async def test_get_current_user(mock_users_repo, mock_settings):
    token = 'Bearer testtoken'
    user_data = {'username': 'testuser', 'email': 'test@example.com'}
    with patch('app.services.jwt.get_username_from_token', return_value='testuser') as mock_get_username, patch('pymongo.MongoClient') as mock_mongo_client:
        mock_mongo_client.return_value.__getitem__.return_value.__getitem__.return_value.find_one.return_value = user_data
        user = await _get_current_user(mock_users_repo, token, mock_settings)
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(mock_users_repo, mock_settings):
    token = 'Bearer invalidtoken'
    with patch('app.services.jwt.get_username_from_token', side_effect=ValueError):
        with pytest.raises(HTTPException) as exc_info:
            await _get_current_user(mock_users_repo, token, mock_settings)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == strings.MALFORMED_PAYLOAD

@pytest.mark.asyncio
async def test_get_current_user_optional_with_token(mock_users_repo, mock_settings):
    token = 'Bearer testtoken'
    user_data = {'username': 'testuser', 'email': 'test@example.com'}
    with patch('app.services.jwt.get_username_from_token', return_value='testuser') as mock_get_username, patch('pymongo.MongoClient') as mock_mongo_client:
        mock_mongo_client.return_value.__getitem__.return_value.__getitem__.return_value.find_one.return_value = user_data
        user = await _get_current_user_optional(mock_users_repo, token, mock_settings)
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'

@pytest.mark.asyncio
async def test_get_current_user_optional_without_token(mock_users_repo, mock_settings):
    user = await _get_current_user_optional(mock_users_repo, None, mock_settings)
    assert user is None

def test_get_authorization_header_optional_with_authorization(mock_settings):
    authorization = 'Bearer testtoken'
    with patch('app.api.dependencies.authentication._get_authorization_header', return_value='testtoken') as mock_get_authorization_header:
        token = _get_authorization_header_optional(authorization, mock_settings)
        assert token == 'testtoken'

def test_get_authorization_header_optional_without_authorization(mock_settings):
    token = _get_authorization_header_optional(None, mock_settings)
    assert token == ''

def test_get_authorization_header_retriever_required():
    retriever = _get_authorization_header_retriever(required=True)
    assert retriever == _get_authorization_header

def test_get_authorization_header_retriever_optional():
    retriever = _get_authorization_header_retriever(required=False)
    assert retriever == _get_authorization_header_optional

def test_get_current_user_authorizer_required():
    authorizer = get_current_user_authorizer(required=True)
    assert authorizer == _get_current_user

def test_get_current_user_authorizer_optional():
    authorizer = get_current_user_authorizer(required=False)
    assert authorizer == _get_current_user_optional

def test_get_authorization_header_valid_token(mock_settings):
    api_key = 'Bearer testtoken'
    token = _get_authorization_header(api_key, mock_settings)
    assert token == 'testtoken'

def test_get_authorization_header_invalid_token_prefix(mock_settings):
    api_key = 'Invalid testtoken'
    with pytest.raises(HTTPException) as exc_info:
        _get_authorization_header(api_key, mock_settings)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == strings.WRONG_TOKEN_PREFIX

def test_get_authorization_header_malformed_token(mock_settings):
    api_key = 'Bearer'
    with pytest.raises(HTTPException) as exc_info:
        _get_authorization_header(api_key, mock_settings)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == strings.WRONG_TOKEN_PREFIX

@pytest.mark.asyncio
async def test_rw_api_key_header_call_valid():
    request = MagicMock()
    request.headers = {'Authorization': 'Bearer testtoken'}
    header = RWAPIKeyHeader(name='Authorization')
    with patch('fastapi.security.APIKeyHeader.__call__', return_value='Bearer testtoken') as mock_super_call:
        token = await header.__call__(request)
        assert token == 'Bearer testtoken'

@pytest.mark.asyncio
async def test_rw_api_key_header_call_invalid():
    request = MagicMock()
    request.headers = {}
    header = RWAPIKeyHeader(name='Authorization')
    with patch('fastapi.security.APIKeyHeader.__call__', side_effect=StarletteHTTPException(status_code=status.HTTP_403_FORBIDDEN)) as mock_super_call:
        with pytest.raises(HTTPException) as exc_info:
            await header.__call__(request)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == strings.AUTHENTICATION_REQUIRED