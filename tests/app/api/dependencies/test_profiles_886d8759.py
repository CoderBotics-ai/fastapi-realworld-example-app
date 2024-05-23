import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from starlette.status import HTTP_404_NOT_FOUND
from app.api.dependencies.profiles import get_profile_by_username_from_path
from app.models.domain.profiles import Profile
from app.resources import strings



@pytest.fixture
def mock_mongo_client():
    with patch('app.api.dependencies.profiles.MongoClient') as mock_client:
        yield mock_client

@pytest.fixture
def mock_profiles_collection():
    return MagicMock()

def test_get_profile_by_username_from_path_success(mock_mongo_client, mock_profiles_collection):
    # Arrange
    username = 'testuser'
    profile_data = {
        'username': 'testuser',
        'bio': 'Test bio',
        'image': 'http://test.com/image.jpg'
    }
    mock_profiles_collection.find_one.return_value = profile_data
    mock_mongo_client.return_value.__getitem__.return_value.__getitem__.return_value = mock_profiles_collection

    # Act
    profile = pytest.run(get_profile_by_username_from_path(username))

    # Assert
    assert profile.username == profile_data['username']
    assert profile.bio == profile_data['bio']
    assert profile.image == profile_data['image']

def test_get_profile_by_username_from_path_not_found(mock_mongo_client, mock_profiles_collection):
    # Arrange
    username = 'nonexistentuser'
    mock_profiles_collection.find_one.return_value = None
    mock_mongo_client.return_value.__getitem__.return_value.__getitem__.return_value = mock_profiles_collection

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        pytest.run(get_profile_by_username_from_path(username))
    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert exc_info.value.detail == strings.USER_DOES_NOT_EXIST_ERROR