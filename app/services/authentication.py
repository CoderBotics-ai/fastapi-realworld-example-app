from app.db.errors import EntityDoesNotExist
from app.db.repositories.users import UsersRepository
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from typing import Any


from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from typing import Any


async def check_email_is_taken(repo: UsersRepository, email: str) -> bool:
    try:
        user = await repo.collection.find_one({"email": email})
        if user is None:
            raise EntityDoesNotExist
    except PyMongoError:
        return False

    return True


async def check_username_is_taken(repo: UsersRepository, username: str) -> bool:
    try:
        user_collection: Collection = repo.db.get_collection("users")
        user = await user_collection.find_one({"username": username})
        if user is None:
            raise EntityDoesNotExist
    except (EntityDoesNotExist, PyMongoError):
        return False

    return True
