from typing import Optional

from app.db.errors import EntityDoesNotExist
from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.models.domain.users import User, UserInDB
from pymongo import MongoClient
from bson import ObjectId
from app.models.domain.users import UserInDB


from pymongo import MongoClient
from bson import ObjectId


class UsersRepository(BaseRepository):

    async def get_user_by_email(self, *, email: str) -> UserInDB:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["your_database_name"]
        collection = db["users"]

        user_document = collection.find_one({"email": email})
        if user_document:
            user_document["_id"] = str(user_document["_id"])
            return UserInDB(**user_document)

        raise EntityDoesNotExist("user with email {0} does not exist".format(email))


    async def get_user_by_username(self, *, username: str) -> UserInDB:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["your_database_name"]
        collection = db["users"]

        user_document = collection.find_one({"username": username})
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

        client = MongoClient("mongodb://localhost:27017/")
        db = client["your_database_name"]
        users_collection = db["users"]

        user_document = {
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

        result = users_collection.insert_one(user_document)
        user.id = result.inserted_id

        client.close()

        return user


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
        client = MongoClient("mongodb://localhost:27017/")
        db = client["your_database_name"]
        users_collection = db["users"]

        user_in_db = await self.get_user_by_username(username=user.username)

        updated_fields = {}
        if username:
            updated_fields["username"] = username
        if email:
            updated_fields["email"] = email
        if bio:
            updated_fields["bio"] = bio
        if image:
            updated_fields["image"] = image
        if password:
            user_in_db.change_password(password)
            updated_fields["salt"] = user_in_db.salt
            updated_fields["hashed_password"] = user_in_db.hashed_password

        if updated_fields:
            updated_fields["updated_at"] = user_in_db.updated_at
            users_collection.update_one(
                {"username": user.username},
                {"$set": updated_fields}
            )

        client.close()

        return user_in_db
