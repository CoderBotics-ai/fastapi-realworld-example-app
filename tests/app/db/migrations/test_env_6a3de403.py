import pytest
from unittest.mock import patch, MagicMock
from app.db.migrations.env import run_migrations_online
from app.core.config import get_app_settings





@patch('app.db.migrations.env.MongoClient')
@patch('app.db.migrations.env.get_app_settings')
@patch('app.db.migrations.env.context.configure')
@patch('app.db.migrations.env.context.begin_transaction')
@patch('app.db.migrations.env.context.run_migrations')
def test_run_migrations_online(mock_run_migrations, mock_begin_transaction, mock_configure, mock_get_app_settings, mock_mongo_client):
    # Mock settings
    mock_settings = MagicMock()
    mock_settings.MONGO_URI = 'mongodb://test_mongo_uri'
    mock_settings.MONGO_DB_NAME = 'test_db_name'
    mock_get_app_settings.return_value = mock_settings

    # Mock MongoClient
    mock_db = MagicMock()
    mock_mongo_client.return_value.__getitem__.return_value = mock_db

    # Call the function
    run_migrations_online()

    # Assertions
    mock_get_app_settings.assert_called_once()
    mock_mongo_client.assert_called_once_with('mongodb://test_mongo_uri')
    mock_mongo_client.return_value.__getitem__.assert_called_once_with('test_db_name')
    mock_configure.assert_called_once_with(connection=mock_db, target_metadata=None)
    mock_begin_transaction.assert_called_once()
    mock_run_migrations.assert_called_once()