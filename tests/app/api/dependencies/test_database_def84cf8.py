import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Request, Depends
from app.api.dependencies.database import _get_db_pool, get_repository, _get_connection_from_pool
from app.db.repositories.base import BaseRepository
from pymongo.database import Database



@pytest.fixture
def mock_request():
    request = Mock(spec=Request)
    request.app.state.db = Mock(spec=Database)
    return request

@pytest.fixture
def mock_repo_type():
    return Mock(spec=BaseRepository)

@pytest.fixture
def mock_db():
    return Mock(spec=Database)

def test_get_db_pool(mock_request):
    db = _get_db_pool(mock_request)
    assert db == mock_request.app.state.db

def test_get_repository(mock_repo_type, mock_db):
    repo_callable = get_repository(mock_repo_type)
    repo_instance = repo_callable(mock_db)
    assert isinstance(repo_instance, mock_repo_type)
    mock_repo_type.assert_called_once_with(mock_db)

@pytest.mark.asyncio
async def test_get_connection_from_pool(mock_db):
    async def mock_get_db_pool():
        yield mock_db
    pool = await anext(mock_get_db_pool())
    async for db in _get_connection_from_pool(pool):
        assert db == mock_db