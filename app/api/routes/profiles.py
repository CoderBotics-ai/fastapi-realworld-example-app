from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from app.api.dependencies.authentication import get_current_user_authorizer
from app.api.dependencies.database import get_repository
from app.api.dependencies.profiles import get_profile_by_username_from_path
from app.db.repositories.profiles import ProfilesRepository
from app.models.domain.profiles import Profile
from app.models.domain.users import User
from app.models.schemas.profiles import ProfileInResponse
from app.resources import strings
from pymongo import MongoClient
from typing import AsyncGenerator
from pymongo.collection import Collection
from pymongo.results import UpdateResult

async def unsubscribe_from_user(
    profile: Profile = Depends(get_profile_by_username_from_path),
    user: User = Depends(get_current_user_authorizer()),
    db: MongoClient = Depends(get_repository(MongoClient)),
) -> ProfileInResponse:
    if user.username == profile.username:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=strings.UNABLE_TO_UNSUBSCRIBE_FROM_YOURSELF,
        )

    if not profile.following:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=strings.USER_IS_NOT_FOLLOWED,
        )

    profiles_collection: Collection = db["profiles"]
    filter = {"_id": profile.id}
    update = {"$pull": {"followings": user.id}}
    result: UpdateResult = profiles_collection.update_one(filter, update)
    if result.modified_count == 0:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=strings.USER_IS_NOT_FOLLOWED,
        )

    followers_collection: Collection = db["profiles"]
    filter = {"_id": user.id}
    update = {"$pull": {"followers": profile.id}}
    result: UpdateResult = followers_collection.update_one(filter, update)
    if result.modified_count == 0:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=strings.USER_IS_NOT_FOLLOWED,
        )

    return ProfileInResponse(profile=profile.copy(update={"following": False}))

router = APIRouter()


async def retrieve_profile_by_username(
    username: str,
) -> ProfileInResponse:
    """Retrieve a profile by username."""
    client = MongoClient()
    db = client["database"]
    profiles_collection = db["profiles"]
    profile_data = profiles_collection.find_one({"username": username})
    if profile_data is None:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=strings.USER_NOT_FOUND)
    profile = Profile(**profile_data)
    return ProfileInResponse(profile=profile)


@router.post(
    "/{username}/follow",
    response_model=ProfileInResponse,
    name="profiles:follow-user",
)
async def follow_for_user(
    profile: Profile = Depends(get_profile_by_username_from_path),
    user: User = Depends(get_current_user_authorizer()),
    db: MongoClient = Depends(get_repository(MongoClient)),
) -> ProfileInResponse:
    if user.username == profile.username:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=strings.UNABLE_TO_FOLLOW_YOURSELF,
        )

    if profile.following:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=strings.USER_IS_ALREADY_FOLLOWED,
        )

    users_collection: Collection = db["users"]
    result: UpdateResult = users_collection.update_one(
        {"_id": profile.username}, 
        {"$push": {"followers": user.username}, "$set": {"following": True}}
    )

    if result.modified_count != 1:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=strings.UNABLE_TO_FOLLOW_USER,
        )

    return ProfileInResponse(profile=profile.copy(update={"following": True}))
