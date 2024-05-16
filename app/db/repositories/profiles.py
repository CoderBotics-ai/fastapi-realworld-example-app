from typing import Optional, Union

from asyncpg import Connection

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.domain.profiles import Profile
from app.models.domain.users import User
from pymongo import MongoClient
from bson import ObjectId
from app.models.domain.users import UserLike

UserLike = Union[User, Profile]


class ProfilesRepository(BaseRepository):

    def __init__(self, conn: MongoClient):
        self._db = conn['your_database_name']  # Replace 'your_database_name' with the actual database name
        self._users_repo = UsersRepository(conn)


    async def get_profile_by_username(
        self,
        *,
        username: str,
        requested_user: Optional[UserLike],
    ) -> Profile:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["your_database_name"]
        users_collection = db["users"]

        user_data = users_collection.find_one({"username": username})
        if not user_data:
            raise ValueError("User not found")

        user = User(
            username=user_data["username"],
            bio=user_data["bio"],
            image=user_data["image"],
            # Add other fields as necessary
        )

        profile = Profile(username=user.username, bio=user.bio, image=user.image)
        if requested_user:
            profile.following = await self.is_user_following_for_another_user(
                target_user=user,
                requested_user=requested_user,
            )

        client.close()
        return profile


    async def is_user_following_for_another_user(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> bool:
        client = MongoClient()
        db = client['your_database_name']
        users_collection = db['users']

        target_user_doc = users_collection.find_one({"username": target_user.username})
        requested_user_doc = users_collection.find_one({"username": requested_user.username})

        if not target_user_doc or not requested_user_doc:
            return False

        return requested_user_doc['_id'] in target_user_doc.get('followers', [])


    async def add_user_into_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        client = MongoClient()
        db = client['your_database_name']
        users_collection = db['users']

        target_user_id = ObjectId(target_user.id)
        requested_user_id = ObjectId(requested_user.id)

        # Add requested_user to target_user's followers
        users_collection.update_one(
            {"_id": target_user_id},
            {"$addToSet": {"followers": requested_user_id}}
        )

        # Add target_user to requested_user's followings
        users_collection.update_one(
            {"_id": requested_user_id},
            {"$addToSet": {"followings": target_user_id}}
        )

        client.close()


    async def remove_user_from_followers(
        self,
        *,
        target_user: UserLike,
        requested_user: UserLike,
    ) -> None:
        client = MongoClient()
        db = client['your_database_name']
        users_collection = db['users']

        target_user_id = ObjectId(target_user.id)
        requested_user_id = ObjectId(requested_user.id)

        users_collection.update_one(
            {'_id': target_user_id},
            {'$pull': {'followers': requested_user_id}}
        )

        users_collection.update_one(
            {'_id': requested_user_id},
            {'$pull': {'followings': target_user_id}}
        )
