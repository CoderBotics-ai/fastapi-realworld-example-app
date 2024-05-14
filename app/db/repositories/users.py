from typing import Optional

from app.db.errors import EntityDoesNotExist
from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.models.domain.users import User, UserInDB
from bson.objectid import ObjectId
from pymongo import MongoClient
































class UsersRepository(BaseRepository):

    async def get_user_by_email(self, *, email: str) -> Optional[UserInDB]:
        user_doc = self.users_collection.find_one({"email": email})
        if user_doc:
            return UserInDB(**user_doc)

        raise EntityDoesNotExist("user with email {0} does not exist".format(email))


    async def get_user_by_username(self, *, username: str) -> Optional[UserInDB]:
        user_document = self.users_collection.find_one({"username": username})
        if user_document:
            return UserInDB(**user_document)
        raise EntityDoesNotExist(
            f"user with username {username} does not exist"
        )

    def __init__(self, mongo_client: MongoClient):
        self.db = mongo_client['your_database_name']  # Replace with your actual database name
        self.users_collection = self.db['users']  # Replace with your actual collection name


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
            "_id": ObjectId(),
            "username": user.username,
            "email": user.email,
            "salt": user.salt,
            "hashed_password": user.hashed_password,
            "bio": "",  # Assuming bio is optional and default to an empty string
            "image": "",  # Assuming image is optional and default to an empty string
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "followers": [],
            "followings": [],
            "favorites": [],
            "comments": []
        }

        result = self.users_collection.insert_one(user_data)
        user_row = self.users_collection.find_one({"_id": result.inserted_id})

        return user.copy(update=dict(user_row))


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

        # Update the user in the database
        update_data = {
            "username": user_in_db.username,
            "email": user_in_db.email,
            "bio": user_in_db.bio,
            "image": user_in_db.image,
        }
        if password:
            update_data["salt"] = user_in_db.salt
            update_data["hashed_password"] = user_in_db.hashed_password

        await self.users_collection.update_one(
            {"username": user.username},
            {"$set": update_data},
            upsert=False
        )

        # Update the updated_at field
        user_in_db.updated_at = datetime.utcnow()

        return user_in_db
