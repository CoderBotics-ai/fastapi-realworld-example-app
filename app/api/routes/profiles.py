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
from typing import Optional
from pymongo.collection import Collection

from pymongo.collection import Collection
from pymongo import ReturnDocument

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
    result = profiles_collection.find_one_and_update(filter, update, return_document=ReturnDocument.AFTER)

    if result is None:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=strings.USER_NOT_FOUND,
        )

    return ProfileInResponse(profile=Profile(**result))


@router.post(
    "/{username}/follow",
    response_model=ProfileInResponse,
    name="profiles:follow-user",
)
async def follow_for_user(
    profile: Profile = Depends(get_profile_by_username_from_path),
    user: User = Depends(get_current_user_authorizer()),
    profiles_collection: Collection = Depends(get_repository(ProfilesRepository)),
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

    updated_profile = profiles_collection.find_one_and_update(
        {"_id": profile.id},
        {"$push": {"followers": user.id}, "$set": {"following": True}},
        return_document=ReturnDocument.AFTER,
    )

    return ProfileInResponse(profile=Profile(**updated_profile))

router = APIRouter()


async def retrieve_profile_by_username(
    username: str,
    profiles_collection: Collection
) -> ProfileInResponse:
    """Retrieve a profile by username."""
    profile_document = profiles_collection.find_one({"username": username})
    if profile_document:
        profile = Profile(
            username=profile_document["username"],
            email=profile_document["email"],
            bio=profile_document["bio"],
            image=profile_document["image"],
            created_at=profile_document["created_at"],
            updated_at=profile_document["updated_at"],
            followers=profile_document["followers"],
            followings=profile_document["followings"],
            favorites=profile_document["favorites"],
            comments=profile_document["comments"]
        )
        return ProfileInResponse(profile=profile)
    else:
        return ProfileInResponse(profile=None)
