import pytest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from app.db.repositories.profiles import ProfilesRepository
from app.models.domain.users import User
from app.models.domain.profiles import Profile

@pytest.fixture
def profiles_repo():
    with patch('app.db.repositories.profiles.MongoClient') as mongo_client_mock:
        mock_conn = mongo_client_mock.return_value
        return ProfilesRepository(mock_conn)

def create_user(username, email, salt, hashed_password, bio, image, created_at, updated_at):
    return User(
        username=username,
        email=email,
        salt=salt,
        hashed_password=hashed_password,
        bio=bio,
        image=image,
        created_at=created_at,
        updated_at=updated_at
    )

@pytest.mark.asyncio
async def test_get_profile_by_username(profiles_repo):
    user_data = {
        'username': 'testuser',
        'email': 'testuser@example.com',
        'salt': 'salt',
        'hashed_password': 'hashed_password',
        'bio': 'bio',
        'image': 'image',
        'created_at': '2021-01-01',
        'updated_at': '2021-01-02'
    }
    with patch('app.db.repositories.profiles.MongoClient') as mongo_client_mock:
        mock_db = mongo_client_mock.return_value.get_database.return_value
        mock_users_collection = mock_db.__getitem__.return_value
        mock_users_collection.find_one.return_value = user_data

        requested_user = create_user('requesteduser', 'requesteduser@example.com', 'salt', 'hashed_password', 'bio', 'image', '2021-01-01', '2021-01-02')
        profile = await profiles_repo.get_profile_by_username(username='testuser', requested_user=requested_user)

        assert profile.username == 'testuser'
        assert profile.bio == 'bio'
        assert profile.image == 'image'

@pytest.mark.asyncio
async def test_is_user_following_for_another_user(profiles_repo):
    target_user_data = {
        'username': 'targetuser',
        '_id': ObjectId(),
        'followers': [ObjectId()]
    }
    requested_user_data = {
        'username': 'requesteduser',
        '_id': target_user_data['followers'][0]
    }
    with patch('app.db.repositories.profiles.MongoClient') as mongo_client_mock:
        mock_db = mongo_client_mock.return_value.get_database.return_value
        mock_users_collection = mock_db.__getitem__.return_value
        mock_users_collection.find_one.side_effect = [target_user_data, requested_user_data]

        target_user = create_user('targetuser', 'targetuser@example.com', 'salt', 'hashed_password', 'bio', 'image', '2021-01-01', '2021-01-02')
        requested_user = create_user('requesteduser', 'requesteduser@example.com', 'salt', 'hashed_password', 'bio', 'image', '2021-01-01', '2021-01-02')

        is_following = await profiles_repo.is_user_following_for_another_user(target_user=target_user, requested_user=requested_user)
        assert is_following is True

@pytest.mark.asyncio
async def test_add_user_into_followers(profiles_repo):
    with patch('app.db.repositories.profiles.MongoClient') as mongo_client_mock:
        target_user = create_user('targetuser', 'targetuser@example.com', 'salt', 'hashed_password', 'bio', 'image', '2021-01-01', '2021-01-02')
        requested_user = create_user('requesteduser', 'requesteduser@example.com', 'salt', 'hashed_password', 'bio', 'image', '2021-01-01', '2021-01-02')
        target_user.id = '60d5ec49f1e5e8a1b8b7b7b7'
        requested_user.id = '60d5ec49f1e5e8a1b8b7b7b8'

        mock_db = mongo_client_mock.return_value.get_database.return_value
        mock_users_collection = mock_db.__getitem__.return_value

        await profiles_repo.add_user_into_followers(target_user=target_user, requested_user=requested_user)

        mock_users_collection.update_one.assert_any_call(
            {'_id': ObjectId('60d5ec49f1e5e8a1b8b7b7b7')},
            {'$addToSet': {'followers': ObjectId('60d5ec49f1e5e8a1b8b7b7b8')}}
        )
        mock_users_collection.update_one.assert_any_call(
            {'_id': ObjectId('60d5ec49f1e5e8a1b8b7b7b8')},
            {'$addToSet': {'followings': ObjectId('60d5ec49f1e5e8a1b8b7b7b7')}}
        )

@pytest.mark.asyncio
async def test_remove_user_from_followers(profiles_repo):
    with patch('app.db.repositories.profiles.MongoClient') as mongo_client_mock:
        target_user = create_user('targetuser', 'targetuser@example.com', 'salt', 'hashed_password', 'bio', 'image', '2021-01-01', '2021-01-02')
        requested_user = create_user('requesteduser', 'requesteduser@example.com', 'salt', 'hashed_password', 'bio', 'image', '2021-01-01', '2021-01-02')
        target_user.id = '60d5ec49f1e5e8a1b8b7b7b7'
        requested_user.id = '60d5ec49f1e5e8a1b8b7b7b8'

        mock_db = mongo_client_mock.return_value.get_database.return_value
        mock_users_collection = mock_db.__getitem__.return_value

        await profiles_repo.remove_user_from_followers(target_user=target_user, requested_user=requested_user)

        mock_users_collection.update_one.assert_any_call(
            {'username': 'targetuser'},
            {'$pull': {'followers': ObjectId('60d5ec49f1e5e8a1b8b7b7b8')}}
        )
        mock_users_collection.update_one.assert_any_call(
            {'username': 'requesteduser'},
            {'$pull': {'followings': ObjectId('60d5ec49f1e5e8a1b8b7b7b7')}}
        )