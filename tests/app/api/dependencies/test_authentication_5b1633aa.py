import pytest
from app.api.dependencies.authentication import _get_authorization_header_retriever, _get_authorization_header_optional, _get_current_user, _get_current_user_optional, get_current_user_authorizer, _get_authorization_header, RWAPIKeyHeader
from app.core.config import get_app_settings
from app.core.settings.app import AppSettings
from app.db.repositories.users import UsersRepository
from app.models.domain.users import User
from app.resources import strings
from app.services import jwt
from pymongo import MongoClient
from bson import ObjectId
from fastapi.security import APIKeyHeader
from fastapi import Depends, HTTPException, Security
from starlette import requests, status
from starlette.exceptions import HTTPException as StarletteHTTPException
import asyncio

@pytest.fixture
def app_settings():
    return AppSettings(secret_key='secret', database_url='mongodb://localhost:27017/', database_name='test')
@pytest.fixture
def users_repo():
    return UsersRepository()

def mock_get_app_settings():
    return {'secret_key': 'secret', 'database_url': 'mongodb://localhost:27017/', 'database_name': 'test'}
def mock_get_repository(repo_type):
    return repo_type()

def test__get_authorization_header_retriever():
    assert _get_authorization_header_retriever() == _get_authorization_header
def test__get_authorization_header_optional():
    assert _get_authorization_header_optional(authorization='token', settings=app_settings()) == 'token'
def test__get_current_user():
    token = 'token'
    users_repo = users_repo()
    settings = app_settings()
    result = asyncio.run(_get_current_user(users_repo, token, settings))
    assert isinstance(result, User)
def test__get_current_user_optional():
    token = 'token'
    users_repo = users_repo()
    settings = app_settings()
    result = asyncio.run(_get_current_user_optional(users_repo, token, settings))
    assert isinstance(result, User)
def test_get_current_user_authorizer():
    assert get_current_user_authorizer() == _get_current_user
def test__get_authorization_header():
    api_key = 'Bearer token'
    settings = app_settings()
    result = _get_authorization_header(api_key, settings)
    assert result == 'token'
def test_RWAPIKeyHeader__call__():
    request = requests.Request(scope={'type': 'http'})
    rw_api_key_header = RWAPIKeyHeader(name='Authorization')
    result = asyncio.run(rw_api_key_header(request))
    assert result is not None