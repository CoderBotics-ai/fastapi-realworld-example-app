from typing import Optional

from app.db.errors import EntityDoesNotExist
from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.models.domain.users import User, UserInDB
































class UsersRepository(BaseRepository):

    async def get_user_by_email(self, *, email: str) -> UserInDB:
        user_document = await self.connection["users"].find_one({"email": email})
        if user_document:
            return UserInDB(**user_document)

        raise EntityDoesNotExist(f"user with email {email} does not exist")


    async def get_user_by_username(self, *, username: str) -> UserInDB:
        user_document = await self.db.users.find_one({"username": username})
        if user_document:
            return UserInDB(**user_document)

        raise EntityDoesNotExist(
            f"user with username {username} does not exist"
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

        document = {
            "username": user.username,
            "email": user.email,
            "salt": user.salt,
            "hashed_password": user.hashed_password,
            "bio": "",
            "image": "",
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow(),
            "followers": [],
            "followings": [],
            "favorites": [],
            "comments": []
        }

        result = await self.db.users.insert_one(document)
        user.id = result.inserted_id

        return user


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

        update_data = {
            "username": username or user_in_db.username,
            "email": email or user_in_db.email,
            "bio": bio or user_in_db.bio,
            "image": image or user_in_db.image,
            "updated_at": datetime.datetime.utcnow()
        }

        if password:
            user_in_db.change_password(password)
            update_data["salt"] = user_in_db.salt
            update_data["hashed_password"] = user_in_db.hashed_password

        await self.collection.update_one(
            {"username": user.username},
            {"$set": update_data}
        )

        user_in_db.username = update_data["username"]
        user_in_db.email = update_data["email"]
        user_in_db.bio = update_data["bio"]
        user_in_db.image = update_data["image"]
        user_in_db.updated_at = update_data["updated_at"]

        return user_in_db
