from typing import Optional

from app.db.errors import EntityDoesNotExist
from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.models.domain.users import User, UserInDB
from pymongo.collection import Collection
from bson.objectid import ObjectId
from app.models.domain.users import UserInDB


class UsersRepository(BaseRepository):

    async def get_user_by_email(self, *, email: str) -> UserInDB:
        collection: Collection = self.connection["users"]
        user_doc = await collection.find_one({"email": email})
        if user_doc:
            return UserInDB(**user_doc)

        raise EntityDoesNotExist("user with email {0} does not exist".format(email))


    async def get_user_by_username(self, *, username: str) -> UserInDB:
        user_collection: Collection = self.connection.get_database().get_collection("users")
        user_document = await user_collection.find_one({"username": username})
        
        if user_document:
            return UserInDB(**user_document)

        raise EntityDoesNotExist(
            "user with username {0} does not exist".format(username),
        )


    async def create_user(
        self,
        *,
        username: str,
        email: str,
        password: str,
    ) -> UserInDB:
        user = UserInDB(username=username, email=email)
        user.change_password(password)

        user_data = {
            "username": user.username,
            "email": user.email,
            "salt": user.salt,
            "hashed_password": user.hashed_password,
            "bio": "",
            "image": "",
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "followers": [],
            "followings": [],
            "favorites": [],
            "comments": []
        }

        collection: Collection = self.connection["users"]
        result = await collection.insert_one(user_data)
        user_data["_id"] = result.inserted_id

        return user.copy(update=dict(user_data))


    async def update_user(  # noqa: WPS211
        self,
        *,
        user: User,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        bio: Optional[str] = None,
        image: Optional[str] = None,
    ) -> UserInDB:
        user_in_db = await self.get_user_by_username(username=user.username)

        user_in_db.username = username or user_in_db.username
        user_in_db.email = email or user_in_db.email
        user_in_db.bio = bio or user_in_db.bio
        user_in_db.image = image or user_in_db.image
        if password:
            user_in_db.change_password(password)

        collection: Collection = self.connection["users"]
        update_fields = {
            "username": user_in_db.username,
            "email": user_in_db.email,
            "salt": user_in_db.salt,
            "hashed_password": user_in_db.hashed_password,
            "bio": user_in_db.bio,
            "image": user_in_db.image,
            "updated_at": user_in_db.updated_at,
        }

        result = await collection.update_one(
            {"username": user.username},
            {"$set": update_fields}
        )

        if result.matched_count == 0:
            raise EntityDoesNotExist(f"User with username {user.username} does not exist")

        return user_in_db
