import pytest
from unittest.mock import AsyncMock, patch
from pymongo.errors import PyMongoError
from app.db.errors import EntityDoesNotExist
from app.db.repositories.users import UsersRepository
from app.services.authentication import check_email_is_taken, check_username_is_taken





@pytest.mark.asyncio
async def test_check_email_is_taken_email_exists():
    repo = AsyncMock(spec=UsersRepository)
    repo.collection.find_one = AsyncMock(return_value={'email': 'test@example.com'})
    result = await check_email_is_taken(repo, 'test@example.com')
    assert result is True

@pytest.mark.asyncio
async def test_check_email_is_taken_email_not_exists():
    repo = AsyncMock(spec=UsersRepository)
    repo.collection.find_one = AsyncMock(return_value=None)
    result = await check_email_is_taken(repo, 'test@example.com')
    assert result is False

@pytest.mark.asyncio
async def test_check_email_is_taken_pymongo_error():
    repo = AsyncMock(spec=UsersRepository)
    repo.collection.find_one = AsyncMock(side_effect=PyMongoError)
    result = await check_email_is_taken(repo, 'test@example.com')
    assert result is False

@pytest.mark.asyncio
async def test_check_username_is_taken_username_exists():
    repo = AsyncMock(spec=UsersRepository)
    repo.db.get_collection = AsyncMock(return_value=AsyncMock())
    repo.db.get_collection().find_one = AsyncMock(return_value={'username': 'testuser'})
    result = await check_username_is_taken(repo, 'testuser')
    assert result is True

@pytest.mark.asyncio
async def test_check_username_is_taken_username_not_exists():
    repo = AsyncMock(spec=UsersRepository)
    repo.db.get_collection = AsyncMock(return_value=AsyncMock())
    repo.db.get_collection().find_one = AsyncMock(return_value=None)
    result = await check_username_is_taken(repo, 'testuser')
    assert result is False

@pytest.mark.asyncio
async def test_check_username_is_taken_pymongo_error():
    repo = AsyncMock(spec=UsersRepository)
    repo.db.get_collection = AsyncMock(return_value=AsyncMock())
    repo.db.get_collection().find_one = AsyncMock(side_effect=PyMongoError)
    result = await check_username_is_taken(repo, 'testuser')
    assert result is False

@pytest.mark.asyncio
async def test_check_username_is_taken_entity_does_not_exist():
    repo = AsyncMock(spec=UsersRepository)
    repo.db.get_collection = AsyncMock(return_value=AsyncMock())
    repo.db.get_collection().find_one = AsyncMock(return_value=None)
    result = await check_username_is_taken(repo, 'testuser')
    assert result is False