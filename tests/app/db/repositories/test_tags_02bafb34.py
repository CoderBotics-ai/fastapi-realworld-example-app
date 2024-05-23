import pytest
from unittest.mock import AsyncMock, MagicMock
from app.db.repositories.tags import TagsRepository

@pytest.fixture
def mock_connection():
    return MagicMock()

@pytest.fixture
def tags_repo(mock_connection):
    repo = TagsRepository()
    repo.connection = mock_connection
    return repo



@pytest.mark.asyncio
async def test_get_all_tags(tags_repo, mock_connection):
    tags_collection = mock_connection.__getitem__.return_value
    tags_cursor = tags_collection.find.return_value
    tags_cursor.to_list = AsyncMock(return_value=[{'tag': 'python'}, {'tag': 'pytest'}])

    result = await tags_repo.get_all_tags()

    assert result == ['python', 'pytest']
    tags_collection.find.assert_called_once_with({}, {'_id': 0, 'tag': 1})
    tags_cursor.to_list.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_tags_that_dont_exist(tags_repo, mock_connection):
    tags_collection = mock_connection.__getitem__.return_value
    tags_collection.find.return_value.to_list = AsyncMock(return_value=[{'tag': 'python'}])
    tags_collection.insert_many = AsyncMock()

    await tags_repo.create_tags_that_dont_exist(tags=['python', 'pytest'])

    tags_collection.find.assert_called_once_with({'tag': {'$in': ['python', 'pytest']}})
    tags_collection.insert_many.assert_awaited_once_with([{'tag': 'pytest'}])

@pytest.mark.asyncio
async def test_create_tags_that_dont_exist_no_new_tags(tags_repo, mock_connection):
    tags_collection = mock_connection.__getitem__.return_value
    tags_collection.find.return_value.to_list = AsyncMock(return_value=[{'tag': 'python'}, {'tag': 'pytest'}])
    tags_collection.insert_many = AsyncMock()

    await tags_repo.create_tags_that_dont_exist(tags=['python', 'pytest'])

    tags_collection.find.assert_called_once_with({'tag': {'$in': ['python', 'pytest']}})
    tags_collection.insert_many.assert_not_awaited()