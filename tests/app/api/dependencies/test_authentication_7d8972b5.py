import pytest
from app.api.dependencies.authentication import RWAPIKeyHeader, get_current_user_authorizer, _get_authorization_header_retriever, _get_authorization_header, _get_authorization_header_optional, _get_current_user_optional, _get_current_user
from app.core.config import get_app_settings
from app.db.repositories.users import UsersRepository
from app.models.domain.users import User
from app.resources import strings
from app.services import jwt
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.exceptions import HTTPException as StarletteHTTPException
from unittest.mock import patch, MagicMock

app_settings = get_app_settings()
users_repo = UsersRepository(client=MagicMock())

def mock_get_app_settings():
    return AppSettings(secret_key='secret')

def mock_get_repository(repo_type):
    return users_repo

def test_RWAPIKeyHeader__call__():
    rw_api_key_header = RWAPIKeyHeader(name='Authorization')
    request = MagicMock()
    with patch('app.api.dependencies.authentication.MongoClient') as mock_mongo_client:
        mock_mongo_client.return_value = MagicMock()
        result = rw_api_key_header(request)
        assert result == ''

def test_get_current_user_authorizer():
    authorizer = get_current_user_authorizer()
    assert callable(authorizer)

def test__get_authorization_header_retriever():
    retriever = _get_authorization_header_retriever()
    assert callable(retriever)

def test__get_authorization_header():
    api_key = 'Bearer token'
    with patch('app.api.dependencies.authentication.get_app_settings') as mock_get_app_settings:
        mock_get_app_settings.return_value = app_settings
        result = _get_authorization_header(api_key)
        assert result == 'token'

def test__get_authorization_header_optional():
    api_key = 'Bearer token'
    with patch('app.api.dependencies.authentication.get_app_settings') as mock_get_app_settings:
        mock_get_app_settings.return_value = app_settings
        result = _get_authorization_header_optional(api_key)
        assert result == 'token'

def test__get_current_user_optional():
    token = 'token'
    with patch('app.api.dependencies.authentication.get_app_settings') as mock_get_app_settings:
        mock_get_app_settings.return_value = app_settings
        with patch('app.api.dependencies.authentication.get_repository') as mock_get_repository:
            mock_get_repository.return_value = users_repo
            result = _get_current_user_optional(token)
            assert isinstance(result, User)

def test__get_current_user():
    token = 'token'
    with patch('app.api.dependencies.authentication.get_app_settings') as mock_get_app_settings:
        mock_get_app_settings.return_value = app_settings
        with patch('app.api.dependencies.authentication.get_repository') as mock_get_repository:
            mock_get_repository.return_value = users_repo
            result = _get_current_user(token)
            assert isinstance(result, User)