import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.api.routes.profiles import follow_for_user, unsubscribe_from_user, retrieve_profile_by_username
from app.models.domain.profiles import Profile
from app.models.domain.users import User
from app.models.schemas.profiles import ProfileInResponse
from app.resources import strings



@pytest.fixture
def mock_profile():
    return Profile(username='testuser', bio='Test bio', image='http://test.com/image.jpg', following=False)

@pytest.fixture
def mock_user():
    return User(username='testuser', email='testuser@test.com', id='507f1f77bcf86cd799439011')

@pytest.fixture
def mock_profiles_repo():
    return MagicMock()

def test_follow_for_user(mock_profile, mock_user, mock_profiles_repo):
    with patch('app.api.routes.profiles.MongoClient') as mock_mongo_client:
        mock_mongo_instance = mock_mongo_client.return_value
        mock_db = mock_mongo_instance.__getitem__.return_value
        mock_users_collection = mock_db.__getitem__.return_value

        response = follow_for_user(profile=mock_profile, user=mock_user, profiles_repo=mock_profiles_repo)

        assert isinstance(response, ProfileInResponse)
        assert response.profile.following is True

def test_follow_for_user_self_follow(mock_profile, mock_user, mock_profiles_repo):
    mock_profile.username = mock_user.username
    with pytest.raises(HTTPException) as exc_info:
        follow_for_user(profile=mock_profile, user=mock_user, profiles_repo=mock_profiles_repo)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == strings.UNABLE_TO_FOLLOW_YOURSELF

def test_follow_for_user_already_followed(mock_profile, mock_user, mock_profiles_repo):
    mock_profile.following = True
    with pytest.raises(HTTPException) as exc_info:
        follow_for_user(profile=mock_profile, user=mock_user, profiles_repo=mock_profiles_repo)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == strings.USER_IS_ALREADY_FOLLOWED

def test_unsubscribe_from_user(mock_profile, mock_user, mock_profiles_repo):
    mock_profile.following = True
    with patch('app.api.routes.profiles.MongoClient') as mock_mongo_client:
        mock_mongo_instance = mock_mongo_client.return_value
        mock_db = mock_mongo_instance.__getitem__.return_value
        mock_users_collection = mock_db.__getitem__.return_value

        response = unsubscribe_from_user(profile=mock_profile, user=mock_user, profiles_repo=mock_profiles_repo)

        assert isinstance(response, ProfileInResponse)
        assert response.profile.following is False

def test_unsubscribe_from_user_self_unfollow(mock_profile, mock_user, mock_profiles_repo):
    mock_profile.username = mock_user.username
    with pytest.raises(HTTPException) as exc_info:
        unsubscribe_from_user(profile=mock_profile, user=mock_user, profiles_repo=mock_profiles_repo)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == strings.UNABLE_TO_UNSUBSCRIBE_FROM_YOURSELF

def test_unsubscribe_from_user_not_followed(mock_profile, mock_user, mock_profiles_repo):
    with pytest.raises(HTTPException) as exc_info:
        unsubscribe_from_user(profile=mock_profile, user=mock_user, profiles_repo=mock_profiles_repo)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == strings.USER_IS_NOT_FOLLOWED

def test_retrieve_profile_by_username(mock_profile):
    with patch('app.api.routes.profiles.profiles_collection') as mock_profiles_collection:
        mock_profiles_collection.find_one.return_value = {
            'username': mock_profile.username,
            'bio': mock_profile.bio,
            'image': mock_profile.image
        }
        response = retrieve_profile_by_username(profile=mock_profile)
        assert isinstance(response, ProfileInResponse)
        assert response.profile.username == mock_profile.username
        assert response.profile.bio == mock_profile.bio
        assert response.profile.image == mock_profile.image

def test_retrieve_profile_by_username_not_found(mock_profile):
    with patch('app.api.routes.profiles.profiles_collection') as mock_profiles_collection:
        mock_profiles_collection.find_one.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            retrieve_profile_by_username(profile=mock_profile)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == strings.PROFILE_NOT_FOUND