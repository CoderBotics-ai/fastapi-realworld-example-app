from unittest.mock import AsyncMock, patch

import pytest

from app.db.repositories.profiles import *


class UserLike:
    def __init__(self, username: str):
        self.username = username


@pytest.fixture
def profiles_repository(monkeypatch):
    async def fake_init(self, conn):
        self.collection = AsyncMock()

    with patch("app.db.repositories.profiles.UsersRepository"):
        profiles_repo = ProfilesRepository(conn=None)
        monkeypatch.setattr(profiles_repo, "__init__", fake_init)
        profiles_repo.collection = AsyncMock()
        return profiles_repo


@pytest.fixture
def user_like_objects():
    return UserLike("user1"), UserLike("user2")


@pytest.mark.asyncio
async def test_is_user_following_for_another_user_no_error(
    profiles_repository, user_like_objects
):
    assert (
        await profiles_repository.is_user_following_for_another_user(
            target_user=user_like_objects[0], requested_user=user_like_objects[1]
        )
        is not None
    )


@pytest.mark.asyncio
async def test_is_user_following_for_another_user_returns_true_if_following(
    profiles_repository, user_like_objects
):
    profiles_repository.collection.find_one.return_value = {
        "follower_username": "user2",
        "following_username": "user1",
    }
    result = await profiles_repository.is_user_following_for_another_user(
        target_user=user_like_objects[0], requested_user=user_like_objects[1]
    )
    assert result is True


@pytest.mark.asyncio
async def test_is_user_following_for_another_user_returns_false_if_not_following(
    profiles_repository, user_like_objects
):
    profiles_repository.collection.find_one.return_value = None
    result = await profiles_repository.is_user_following_for_another_user(
        target_user=user_like_objects[0], requested_user=user_like_objects[1]
    )
    assert result is False
