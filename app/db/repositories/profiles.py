from typing import Optional, Union

from asyncpg import Connection

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.profiles import Profile
from app.models.domain.users import User

from pymongo import MongoClient
from app.models.domain.users import UserLike

UserLike = Union[User, Profile]


class ProfilesRepository(BaseRepository):

    def __init__(self, client):
        super().__init__(client)
        self._users_repo = UsersRepository(client)
        self._db = client['app']
        self._profiles_collection = self._db['profiles']
        self._users_collection = self._db['users']
        self._articles_collection = self._db['articles']
        self._tags_collection = self._db['tags']
        self._comments_collection = self._db['comments']


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
            following = requested_user.username in user["followings"]
            profile.following = following

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
        """Removes a user from another user's followers."""
        self.db.users.update_one(
            {"_id": target_user.id},
            {"$pull": {"followers": requested_user.id}},
        )
