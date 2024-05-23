import pytest
from unittest.mock import patch, MagicMock
from pymongo.collection import Collection
from datetime import datetime
from app.db.migrations.versions.fdf8821871d7_main_tables import create_users_table, create_followers_to_followings_table, create_articles_table, create_tags_table, create_articles_to_tags_table, create_favorites_table, create_commentaries_table, upgrade, downgrade, timestamps, create_updated_at_trigger





def test_create_users_table():
    with patch('app.db.migrations.versions.fdf8821871d7_main_tables.MongoClient') as mock_client, patch('app.db.migrations.versions.fdf8821871d7_main_tables.timestamps', return_value=({'created_at': datetime.utcnow()}, {'updated_at': datetime.utcnow()})):
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        create_users_table()
        assert mock_db['users'].create_index.call_count == 2
        assert mock_db['users'].insert_one.call_count == 1

def test_create_followers_to_followings_table():
    with patch('app.db.migrations.versions.fdf8821871d7_main_tables.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        create_followers_to_followings_table()
        assert mock_db['users'].create_index.call_count == 2

def test_create_articles_table():
    with patch('app.db.migrations.versions.fdf8821871d7_main_tables.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        create_articles_table()
        assert mock_db['articles'].create_index.call_count == 2
        assert mock_db['articles'].insert_one.call_count == 1
        assert mock_db['articles'].delete_one.call_count == 1

def test_create_tags_table():
    with patch('app.db.migrations.versions.fdf8821871d7_main_tables.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        create_tags_table()
        assert mock_db['tags'].create_index.call_count == 1

def test_create_articles_to_tags_table():
    with patch('app.db.migrations.versions.fdf8821871d7_main_tables.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        create_articles_to_tags_table()
        assert mock_db['articles_to_tags'].create_index.call_count == 1

def test_create_favorites_table():
    with patch('app.db.migrations.versions.fdf8821871d7_main_tables.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        create_favorites_table()
        assert mock_db['users'].update_many.call_count == 1
        assert mock_db['articles'].update_many.call_count == 1
        assert mock_db['users'].create_index.call_count == 1
        assert mock_db['articles'].create_index.call_count == 1

def test_create_commentaries_table():
    with patch('app.db.migrations.versions.fdf8821871d7_main_tables.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        create_commentaries_table()
        assert mock_db['commentaries'].create_index.call_count == 4

def test_upgrade():
    with patch('app.db.migrations.versions.fdf8821871d7_main_tables.create_updated_at_trigger') as mock_trigger, patch('app.db.migrations.versions.fdf8821871d7_main_tables.create_users_table') as mock_users, patch('app.db.migrations.versions.fdf8821871d7_main_tables.create_followers_to_followings_table') as mock_followers, patch('app.db.migrations.versions.fdf8821871d7_main_tables.create_articles_table') as mock_articles, patch('app.db.migrations.versions.fdf8821871d7_main_tables.create_tags_table') as mock_tags, patch('app.db.migrations.versions.fdf8821871d7_main_tables.create_articles_to_tags_table') as mock_articles_to_tags, patch('app.db.migrations.versions.fdf8821871d7_main_tables.create_favorites_table') as mock_favorites, patch('app.db.migrations.versions.fdf8821871d7_main_tables.create_commentaries_table') as mock_commentaries:
        upgrade()
        mock_trigger.assert_called_once()
        mock_users.assert_called_once()
        mock_followers.assert_called_once()
        mock_articles.assert_called_once()
        mock_tags.assert_called_once()
        mock_articles_to_tags.assert_called_once()
        mock_favorites.assert_called_once()
        mock_commentaries.assert_called_once()

def test_downgrade():
    with patch('app.db.migrations.versions.fdf8821871d7_main_tables.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        downgrade()
        assert mock_db['commentaries'].drop.call_count == 1
        assert mock_db['favorites'].drop.call_count == 1
        assert mock_db['articles_to_tags'].drop.call_count == 1
        assert mock_db['tags'].drop.call_count == 1
        assert mock_db['articles'].drop.call_count == 1
        assert mock_db['followers_to_followings'].drop.call_count == 1
        assert mock_db['users'].drop.call_count == 1

def test_timestamps():
    created_at, updated_at = timestamps()
    assert 'created_at' in created_at
    assert 'updated_at' in updated_at

def test_create_updated_at_trigger():
    with patch('app.db.migrations.versions.fdf8821871d7_main_tables.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        create_updated_at_trigger()
        assert mock_db['users'].update_many.call_count == 1
        assert mock_db['articles'].update_many.call_count == 1
        assert mock_db['tags'].update_many.call_count == 1