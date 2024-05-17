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
from typing import AsyncGenerator
from pymongo.collection import Collection

from pymongo.collection import Collection

async def follow_for_user(
    profile: Profile = Depends(get_profile_by_username_from_path),
    user: User = Depends(get_current_user_authorizer()),
    profiles_repo: ProfilesRepository = Depends(get_repository(ProfilesRepository)),
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

    profiles_collection: Collection = profiles_repo.collection
    await profiles_collection.update_one({"_id": profile.id}, {"$push": {"followings": user.id}})
    await profiles_collection.update_one({"_id": user.id}, {"$push": {"followers": profile.id}})

    return ProfileInResponse(profile=profile.copy(update={"following": True}))

async def unsubscribe_from_user(
    profile: Profile = Depends(get_profile_by_username_from_path),
    user: User = Depends(get_current_user_authorizer()),
    profiles_collection: Collection = Depends(get_repository(ProfilesRepository)),
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

    filter = {"_id": profile.id}
    update = {"$pull": {"followings": user.id}}
    await profiles_collection.update_one(filter, update)

    return ProfileInResponse(profile=profile.copy(update={"following": False}))

router = APIRouter()


async def retrieve_profile_by_username(
    username: str,
    profiles_collection: Collection
) -> ProfileInResponse:
    """Retrieve a profile by username."""
    profile_document = await profiles_collection.find_one({"username": username})
    if profile_document is None:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=strings.USER_NOT_FOUND)
    profile = Profile(**profile_document)
    return ProfileInResponse(profile=profile)
