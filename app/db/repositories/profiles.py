from typing import Optional, Union

from asyncpg import Connection

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.profiles import Profile
from app.models.domain.users import User

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
        user_doc = await self.db.users.find_one({"username": username})
        if not user_doc:
            raise Exception("User not found")

        user = User(**user_doc)

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
        target_user_document = await self.connection["users"].find_one({"username": target_user.username})
        requested_user_document = await self.connection["users"].find_one({"username": requested_user.username})
        
        return target_user_document["_id"] in requested_user_document["followings"]


    async def add_user_into_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        target_user_id = await self.db.users.find_one({'username': target_user.username}, {'_id': 1})
        requested_user_id = await self.db.users.find_one({'username': requested_user.username}, {'_id': 1})

        if target_user_id and requested_user_id:
            await self.db.users.update_one(
                {'_id': target_user_id['_id']},
                {'$addToSet': {'followers': requested_user_id['_id']}}
            )
            await self.db.users.update_one(
                {'_id': requested_user_id['_id']},
                {'$addToSet': {'followings': target_user_id['_id']}}
            )

    async def remove_user_from_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        await self.db.users.update_one(
            {"username": target_user.username},
            {"$pull": {"followers": requested_user._id}}
        )
        await self.db.users.update_one(
            {"username": requested_user.username},
            {"$pull": {"followings": target_user._id}}
        )
