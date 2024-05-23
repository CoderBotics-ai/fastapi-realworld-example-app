import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.api.routes.tags import router, get_all_tags
from app.db.repositories.tags import TagsRepository
from app.models.schemas.tags import TagsInList
from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix='/tags')

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_tags_repo():
    mock_repo = AsyncMock(TagsRepository)
    mock_repo.get_all_tags.return_value = ['tag1', 'tag2', 'tag3']
    return mock_repo

@patch('app.api.routes.tags.get_repository')
def test_get_all_tags(mock_get_repository, client, mock_tags_repo):
    mock_get_repository.return_value = mock_tags_repo
    response = client.get('/tags')
    assert response.status_code == 200
    assert response.json() == {'tags': ['tag1', 'tag2', 'tag3']}