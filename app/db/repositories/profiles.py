from typing import Optional, Union

from asyncpg import Connection

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.profiles import Profile
from app.models.domain.users import User
from bson.objectid import ObjectId
from pymongo import MongoClient

UserLike = Union[User, Profile]
































class ProfilesRepository(BaseRepository):

    def __init__(self, conn: MongoClient):
        super().__init__(conn)
        self._users_repo = UsersRepository(conn)

    async def get_profile_by_username(
        self,
        *,
        username: str,
        requested_user: Optional[UserLike],
    ) -> Profile:
        user = await self._users_repo.get_user_by_username(username=username)

        profile = Profile(username=user.username, bio=user.bio, image=user.image)
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
        # Assuming MongoClient is initialized and accessible via self.client
        db = self.client.get_database()
        users_collection = db.get_collection('users')

        # Fetch the target_user and requested_user documents
        target_user_doc = users_collection.find_one({'_id': ObjectId(target_user.id)})
        requested_user_doc = users_collection.find_one({'_id': ObjectId(requested_user.id)})

        # Check if requested_user is in the followers list of target_user
        return ObjectId(requested_user.id) in target_user_doc['followers']


    async def add_user_into_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        target_user_id = target_user.id
        requested_user_id = requested_user.id

        # Add target_user_id to requested_user's followers
        self.users_collection.update_one(
            {"_id": requested_user_id},
            {"$push": {"followers": target_user_id}}
        )

        # Add requested_user_id to target_user's followings
        self.users_collection.update_one(
            {"_id": target_user_id},
            {"$push": {"followings": requested_user_id}}
        )


    async def remove_user_from_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        target_user_id = target_user.id  # Assuming UserLike has an 'id' attribute
        requested_user_id = requested_user.id  # Assuming UserLike has an 'id' attribute

        # Remove the target_user_id from the followers array of the requested_user
        self.users_collection.update_one(
            {"_id": requested_user_id},
            {"$pull": {"followers": target_user_id}}
        )

        # Remove the requested_user_id from the followings array of the target_user
        self.users_collection.update_one(
            {"_id": target_user_id},
            {"$pull": {"followings": requested_user_id}}
        )
