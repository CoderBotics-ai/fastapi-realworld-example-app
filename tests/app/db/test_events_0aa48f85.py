import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from app.db.events import connect_to_db, close_db_connection

@pytest.fixture
def app():
    return FastAPI()

@pytest.fixture
def settings():
    class MockSettings:
        database_url = 'mongodb://test:test@localhost:27017/testdb'
    return MockSettings()



@pytest.mark.asyncio
async def test_connect_to_db(app, settings):
    with patch('app.db.events.MongoClient') as MockMongoClient:
        mock_client = MagicMock()
        MockMongoClient.return_value = mock_client
        mock_db = MagicMock()
        mock_client.get_database.return_value = mock_db

        await connect_to_db(app, settings)

        MockMongoClient.assert_called_once_with(settings.database_url)
        assert app.state.db == mock_db

@pytest.mark.asyncio
async def test_close_db_connection(app):
    mock_client = MagicMock()
    app.state.mongo_client = mock_client

    await close_db_connection(app)

    mock_client.close.assert_called_once()