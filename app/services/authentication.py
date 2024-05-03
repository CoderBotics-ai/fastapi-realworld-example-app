from app.db.errors import EntityDoesNotExist
from app.db.repositories.users import UsersRepository

async def check_username_is_taken(repo: UsersRepository, username: str) -> bool:
    user = await repo.collection.find_one({"username": username})
    return user is not None

async def check_email_is_taken(repo: UsersRepository, email: str) -> bool:
    user = await repo.collection.find_one({"email": email})
    return user is not None
