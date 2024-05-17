from typing import Optional, Union

from asyncpg import Connection

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.profiles import Profile
from app.models.domain.users import User

from pymongo import MongoClient
from typing import TypeVar
from typing import Any
UserLike = TypeVar("UserLike")

UserLike = Union[User, Profile]


class ProfilesRepository(BaseRepository):

    def __init__(self, client):
        super().__init__(client)
        self._users_repo = UsersRepository(client)


    async def get_profile_by_username(
        self,
        *,
        username: str,
        requested_user: Optional[UserLike],
    ) -> Profile:
        user = self.users_collection.find_one({"username": username})
        if user is None:
            raise Exception("User not found")

        profile = Profile(username=user["username"], bio=user["bio"], image=user["image"])
        if requested_user:
            if requested_user.username in user["followers"]:
                profile.following = True
            else:
                profile.following = False

        return profile


    async def is_user_following_for_another_user(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> bool:
        """Checks if a user is following another user."""
        target_user_id = target_user.id
        requested_user_id = requested_user.id
        user_data = self.users_collection.find_one({"_id": target_user_id})
        if user_data and "followers" in user_data:
            return requested_user_id in user_data["followers"]
        return False


    async def add_user_into_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        """Adds a user into the followers of another user."""
        self.users_collection.update_one(
            {"_id": target_user.id},
            {"$push": {"followers": requested_user.id}},
        )


    async def remove_user_from_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        """Removes a user from the followers of another user."""
        filter = {"_id": target_user.id}
        update = {"$pull": {"followers": requested_user.id}}
        self.users_collection.update_one(filter, update)
