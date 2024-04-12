from typing import Optional, Union

from asyncpg import Connection

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.profiles import Profile
from app.models.domain.users import User
from pymongo.collection import Collection
from bson import ObjectId

UserLike = Union[User, Profile]
































class ProfilesRepository(BaseRepository):
    def __init__(self, conn: Connection):
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
        requested_user: UserLike
    ) -> bool:
        result = await self.collection.find_one({
            'follower_username': requested_user.username,
            'following_username': target_user.username
        })
        return result is not None

    async def add_user_into_followers(self, *, target_user: UserLike, requested_user: UserLike) -> None:
        await self.collection.update_one(
            {"username": target_user.username},
            {"$addToSet": {"followers": requested_user.username}}
        )

    async def remove_user_from_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
        followers_collection: Collection
    ) -> None:
        """Remove a user from the followers of another user in MongoDB."""
        followers_collection.update_one(
            {"username": target_user.username},
            {"$pull": {"followers": requested_user.username}}
        )
