import pytest
from app.api.routes.profiles import follow_for_user, unsubscribe_from_user, retrieve_profile_by_username
from app.models.domain.profiles import Profile
from app.models.domain.users import User
from app.models.schemas.profiles import ProfileInResponse
from app.api.dependencies.profiles import get_profile_by_username_from_path
from app.api.dependencies.authentication import get_current_user_authorizer
from app.api.dependencies.database import get_repository
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

client = MongoClient('mongodb://localhost:27017')
db = client['your_database_name']
users_collection = db['users']
profiles_collection = db['profiles']

def mock_get_profile_by_username_from_path(username):
    return Profile(username=username, id='123', following=False)

def mock_get_current_user_authorizer(username):
    return User(username=username, id='123')

def mock_get_repository():
    return MagicMock(spec=ProfilesRepository)

def test_follow_for_user():
    with patch('app.api.routes.profiles.get_profile_by_username_from_path', side_effect=mock_get_profile_by_username_from_path):
        with patch('app.api.routes.profiles.get_current_user_authorizer', side_effect=mock_get_current_user_authorizer):
            with patch('app.api.routes.profiles.get_repository', side_effect=mock_get_repository):
                response = follow_for_user('username')
                assert response.profile.following == True

def test_follow_for_user_same_username():
    with patch('app.api.routes.profiles.get_profile_by_username_from_path', side_effect=mock_get_profile_by_username_from_path):
        with patch('app.api.routes.profiles.get_current_user_authorizer', side_effect=mock_get_current_user_authorizer):
            with patch('app.api.routes.profiles.get_repository', side_effect=mock_get_repository):
                with pytest.raises(HTTPException):
                    follow_for_user('username', username='username')

def test_follow_for_user_already_following():
    profile = Profile(username='username', id='123', following=True)
    with patch('app.api.routes.profiles.get_profile_by_username_from_path', return_value=profile):
        with patch('app.api.routes.profiles.get_current_user_authorizer', side_effect=mock_get_current_user_authorizer):
            with patch('app.api.routes.profiles.get_repository', side_effect=mock_get_repository):
                with pytest.raises(HTTPException):
                    follow_for_user('username')

def test_unsubscribe_from_user():
    with patch('app.api.routes.profiles.get_profile_by_username_from_path', side_effect=mock_get_profile_by_username_from_path):
        with patch('app.api.routes.profiles.get_current_user_authorizer', side_effect=mock_get_current_user_authorizer):
            with patch('app.api.routes.profiles.get_repository', side_effect=mock_get_repository):
                response = unsubscribe_from_user('username')
                assert response.profile.following == False

def test_unsubscribe_from_user_same_username():
    with patch('app.api.routes.profiles.get_profile_by_username_from_path', side_effect=mock_get_profile_by_username_from_path):
        with patch('app.api.routes.profiles.get_current_user_authorizer', side_effect=mock_get_current_user_authorizer):
            with patch('app.api.routes.profiles.get_repository', side_effect=mock_get_repository):
                with pytest.raises(HTTPException):
                    unsubscribe_from_user('username', username='username')

def test_unsubscribe_from_user_not_following():
    profile = Profile(username='username', id='123', following=False)
    with patch('app.api.routes.profiles.get_profile_by_username_from_path', return_value=profile):
        with patch('app.api.routes.profiles.get_current_user_authorizer', side_effect=mock_get_current_user_authorizer):
            with patch('app.api.routes.profiles.get_repository', side_effect=mock_get_repository):
                with pytest.raises(HTTPException):
                    unsubscribe_from_user('username')

def test_retrieve_profile_by_username():
    profile_data = {'username': 'username', 'bio': 'bio', 'image': 'image'}
    with patch('app.api.routes.profiles.profiles_collection.find_one', return_value=profile_data):
        response = retrieve_profile_by_username('username')
        assert response.profile.username == 'username'

def test_retrieve_profile_by_username_not_found():
    with patch('app.api.routes.profiles.profiles_collection.find_one', return_value=None):
        with pytest.raises(HTTPException):
            retrieve_profile_by_username('username')