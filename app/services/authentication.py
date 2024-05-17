from app.db.errors import EntityDoesNotExist
from app.db.repositories.users import UsersRepository

from pymongo.collection import Collection
from typing import Awaitable

async def check_email_is_taken(repo: UsersRepository, email: str) -> bool:
    """Checks if an email is already taken."""
    user = await repo.collection.find_one({"email": email})
    return user is not None

async def check_username_is_taken(repo: UsersRepository, username: str) -> bool:
    """Checks if a username is taken."""
    result = await repo.collection.find_one({"username": username})
    return result is not None
