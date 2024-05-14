from typing import Optional, Union

from asyncpg import Connection

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.profiles import Profile
from app.models.domain.users import User
from pymongo.collection import Collection
from pymongo.database import Database
from bson import ObjectId

UserLike = Union[User, Profile]
































































class ProfilesRepository(BaseRepository):

    def __init__(self, db: Database):
        self._db = db
        self._users_repo = UsersRepository(db)


    async def get_profile_by_username(
        self,
        *,
        username: str,
        requested_user: Optional[UserLike],
        db: Database
    ) -> Profile:
        users_collection: Collection = db['users']
        user_data = await users_collection.find_one({"username": username})

        if not user_data:
            raise ValueError("User not found")

        user = User(
            username=user_data['username'],
            bio=user_data.get('bio', ''),
            image=user_data.get('image', '')
        )

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
        users_collection: Collection = self.db.get_collection("users")
        target_user_doc = await users_collection.find_one({"username": target_user.username})
        requested_user_doc = await users_collection.find_one({"username": requested_user.username})

        if not target_user_doc or not requested_user_doc:
            return False

        return ObjectId(requested_user_doc["_id"]) in target_user_doc.get("followers", [])


    async def add_user_into_followers(
        self,
        *,
        target_user: User,
        requested_user: User,
    ) -> None:
        users_collection: Collection = self.connection['users']
        
        # Find the target user and requested user in the database
        target_user_doc = await users_collection.find_one({"username": target_user.username})
        requested_user_doc = await users_collection.find_one({"username": requested_user.username})
        
        if target_user_doc and requested_user_doc:
            # Add the requested user's ID to the target user's followers list
            await users_collection.update_one(
                {"_id": target_user_doc["_id"]},
                {"$addToSet": {"followers": requested_user_doc["_id"]}}
            )
            # Add the target user's ID to the requested user's followings list
            await users_collection.update_one(
                {"_id": requested_user_doc["_id"]},
                {"$addToSet": {"followings": target_user_doc["_id"]}}
            )


    async def remove_user_from_followers(
        self,
        *,
        target_user: User,
        requested_user: User,
    ) -> None:
        users_collection: Collection = self.db.get_collection("users")
        
        await users_collection.update_one(
            {"username": target_user.username},
            {"$pull": {"followers": ObjectId(requested_user.id)}}
        )
