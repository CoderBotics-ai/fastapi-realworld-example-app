import pytest
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch
from app.core.events import create_start_app_handler, create_stop_app_handler
from app.core.settings.app import AppSettings

@pytest.fixture
def app() -> FastAPI:
    return FastAPI()

@pytest.fixture
def settings() -> AppSettings:
    class MockSettings:
        mongodb_uri = 'mongodb://test'
        mongodb_db = 'test_db'
    return MockSettings()



def test_create_start_app_handler(app: FastAPI, settings: AppSettings):
    start_app_handler = create_start_app_handler(app, settings)
    assert callable(start_app_handler)

    with patch('app.core.events.MongoClient') as mock_mongo_client:
        mock_client_instance = mock_mongo_client.return_value
        mock_client_instance.__getitem__.return_value = 'mock_db'

        # Run the start_app function
        import asyncio
        asyncio.run(start_app_handler())

        # Check if MongoClient was called with the correct URI
        mock_mongo_client.assert_called_with(settings.mongodb_uri)
        # Check if the app state has been set correctly
        assert app.state.mongodb_client == mock_client_instance
        assert app.state.mongodb == 'mock_db'

def test_create_stop_app_handler(app: FastAPI):
    stop_app_handler = create_stop_app_handler(app)
    assert callable(stop_app_handler)

    with patch('app.core.events.close_db_connection', new_callable=AsyncMock) as mock_close_db_connection:
        # Run the stop_app function
        import asyncio
        asyncio.run(stop_app_handler())

        # Check if close_db_connection was called with the app
        mock_close_db_connection.assert_awaited_once_with(app)