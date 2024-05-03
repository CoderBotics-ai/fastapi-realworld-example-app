from app.db.errors import EntityDoesNotExist
from app.db.repositories.users import UsersRepository

async def check_username_is_taken(repo: UsersRepository, username: str) -> bool:
    try:
        await repo.collection.find_one({"username": username})
    except EntityDoesNotExist:
        return False

    return True

async def check_email_is_taken(repo: UsersRepository, email: str) -> bool:
    try:
        await repo.collection.find_one({"email": email})
    except EntityDoesNotExist:
        return False

    return True
