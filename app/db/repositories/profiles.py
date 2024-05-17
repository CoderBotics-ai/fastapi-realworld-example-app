from typing import Optional, Union

from asyncpg import Connection

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.profiles import Profile
from app.models.domain.users import User

from pymongo import MongoClient
from app.models.domain.users import UserLike
from typing import Any

UserLike = Union[User, Profile]


class ProfilesRepository(BaseRepository):

    def __init__(self, client: MongoClient):
        self._client = client
        self._users_repo = UsersRepository(client)

    async def get_profile_by_username(
        self,
        *,
        username: str,
        requested_user: Optional[UserLike],
    ) -> Profile:
        """Get a profile by username."""
        client = MongoClient()
        db = client["app"]
        users_collection = db["users"]
        user = await self._get_user_by_username(username, users_collection)
        
        profile = Profile(username=user["username"], bio=user["bio"], image=user["image"])
        if requested_user:
            profile.following = await self.is_user_following_for_another_user(
                target_user=user,
                requested_user=requested_user,
            )

        return profile


    async def is_user_following_for_another_user(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> bool:
        """Checks if a user is following another user."""
        user_data = self.db.users.find_one({"username": target_user.username})
        if user_data and "followers" in user_data:
            return requested_user.username in user_data["followers"]
        return False

    async def _get_user_by_username(self, username: str, users_collection) -> dict:
        """Get a user by username."""
        user = await users_collection.find_one({"username": username})
        return user


    async def add_user_into_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        """Adds a user into followers of another user."""
        self.db["users"].update_one({"_id": target_user.id}, {"$push": {"followers": requested_user.id}})


    async def remove_user_from_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        filter = {"_id": target_user.id}
        update = {"$pull": {"followers": requested_user.id}}
        self.users_collection.update_one(filter, update)
