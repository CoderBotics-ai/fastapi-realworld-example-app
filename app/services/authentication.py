from app.db.errors import EntityDoesNotExist
from app.db.repositories.users import UsersRepository
from pymongo.collection import Collection
from typing import Any

async def check_email_is_taken(repo: Collection, email: str) -> bool:
    """Check if a user with the given email already exists."""
    user = await repo.find_one({"email": email})
    return user is not None


async def check_username_is_taken(repo: UsersRepository, username: str) -> bool:
    users_collection: Collection = repo.db.get_collection("users")
    user = await users_collection.find_one({"username": username})
    if user is None:
        return False
    return True
