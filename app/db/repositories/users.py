from typing import Optional

from app.db.errors import EntityDoesNotExist
from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.models.domain.users import User, UserInDB
from pymongo.collection import Collection
from app.models.domain.users import UserInDB


class UsersRepository(BaseRepository):

    async def get_user_by_email(self, *, email: str) -> UserInDB:
        """Get a user by email."""
        from pymongo.collection import Collection
        collection: Collection = self.connection  # Assuming self.connection is a pymongo collection
        user_row = await collection.find_one({"email": email})
        if user_row:
            return UserInDB(**user_row)

        raise EntityDoesNotExist("user with email {0} does not exist".format(email))

    async def get_user_by_username(self, *, username: str) -> UserInDB:
        """Get a user by username."""
        user_row = self.collection.find_one({"username": username})
        if user_row:
            return UserInDB(**user_row)

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
        """Creates a new user in the database."""
        user = UserInDB(username=username, email=email)
        user.change_password(password)

        user_data = {
            "username": user.username,
            "email": user.email,
            "salt": user.salt,
            "hashed_password": user.hashed_password,
        }

        result = await self.users_collection.insert_one(user_data)
        user_id = result.inserted_id

        user_row = await self.users_collection.find_one({"_id": user_id})
        return user.copy(update=dict(user_row))

    def __init__(self, collection: Collection):
        self.collection = collection


    async def update_user(
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

        user_in_db.updated_at = await self.collection.update_one(
            {"_id": user_in_db.id},
            {
                "$set": {
                    "username": user_in_db.username,
                    "email": user_in_db.email,
                    "bio": user_in_db.bio,
                    "image": user_in_db.image,
                    "updated_at": user_in_db.updated_at,
                },
            },
        )

        return user_in_db
