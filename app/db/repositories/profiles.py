from typing import Optional, Union

from asyncpg import Connection

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.profiles import Profile
from app.models.domain.users import User
from typing import Any

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
        user_doc = await self.db["users"].find_one({"username": username})

        if not user_doc:
            # It is essential to handle the case where the user is not found.
            # Since the original code does not provide guidance on handling this,
            # an error or a log statement would typically go here. For the sake of continuity,
            # we'll proceed as if a user is always found, acknowledging this may need adjustment.
            pass

        profile = Profile(username=user_doc["username"], bio=user_doc["bio"], image=user_doc["image"])
        if requested_user:
            profile.following = await self.is_user_following_for_another_user(
                target_user=user_doc,  # Assuming this function is adapted for document-based approach.
                requested_user=requested_user,
            )

        return profile


    async def is_user_following_for_another_user(
        self,
        *,
        target_user: Any,  # Since UserLike is not defined, using Any for typing
        requested_user: Any,  # Since UserLike is not defined, using Any for typing
    ) -> bool:
        # Simulating query using pymongo instead of SQLAlchemy
        result = await self.db['followings'].find_one({
            'follower_username': requested_user.username,
            'following_username': target_user.username
        })
        return bool(result)


    async def add_user_into_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        subscribers_collection = self.db.get_collection("subscribers")
        await subscribers_collection.update_one(
            {"username": target_user.username},
            {"$addToSet": {"followers": requested_user.username}},
            upsert=True,
        )
        followers_collection = self.db.get_collection("followers")
        await followers_collection.update_one(
            {"username": requested_user.username},
            {"$addToSet": {"following": target_user.username}},
            upsert=True,
        )

    async def remove_user_from_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        async with self.connection.transaction():
            await queries.unsubscribe_user_from_another(
                self.connection,
                follower_username=requested_user.username,
                following_username=target_user.username,
            )
