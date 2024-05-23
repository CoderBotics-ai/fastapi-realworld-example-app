import pytest
from unittest.mock import Mock
from asyncpg.connection import Connection
from app.db.repositories.base import BaseRepository





def test_base_repository_init():
    mock_conn = Mock(spec=Connection)
    repo = BaseRepository(mock_conn)
    assert repo._conn == mock_conn

def test_base_repository_connection_property():
    mock_conn = Mock(spec=Connection)
    repo = BaseRepository(mock_conn)
    assert repo.connection == mock_conn