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
from bson import ObjectId

client = MongoClient("mongodb://localhost:27017")


@router.post(
    "/{username}/follow",
    response_model=ProfileInResponse,
    name="profiles:follow-user",
)
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

    client = MongoClient("mongodb://localhost:27017/")
    db = client["your_database_name"]
    users_collection = db["users"]

    user_id = ObjectId(user.id)
    profile_id = ObjectId(profile.id)

    users_collection.update_one(
        {"_id": profile_id},
        {"$addToSet": {"followers": user_id}}
    )

    users_collection.update_one(
        {"_id": user_id},
        {"$addToSet": {"followings": profile_id}}
    )

    profile.following = True

    return ProfileInResponse(profile=profile.copy(update={"following": True}))


@router.delete(
    "/{username}/follow",
    response_model=ProfileInResponse,
    name="profiles:unsubscribe-from-user",
)
async def unsubscribe_from_user(
    profile: Profile = Depends(get_profile_by_username_from_path),
    user: User = Depends(get_current_user_authorizer()),
    profiles_repo: ProfilesRepository = Depends(get_repository(ProfilesRepository)),
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

    client = MongoClient()
    db = client.your_database_name
    users_collection = db.users

    users_collection.update_one(
        {"_id": ObjectId(profile.id)},
        {"$pull": {"followers": ObjectId(user.id)}}
    )

    users_collection.update_one(
        {"_id": ObjectId(user.id)},
        {"$pull": {"followings": ObjectId(profile.id)}}
    )

    return ProfileInResponse(profile=profile.copy(update={"following": False}))
db = client["your_database_name"]
profiles_collection = db["profiles"]

router = APIRouter()


@router.get(
    "/{username}",
    response_model=ProfileInResponse,
    name="profiles:get-profile",
)
async def retrieve_profile_by_username(
    profile: Profile = Depends(get_profile_by_username_from_path),
) -> ProfileInResponse:
    profile_data = profiles_collection.find_one({"username": profile.username})
    if not profile_data:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=strings.PROFILE_NOT_FOUND)
    
    profile = Profile(
        username=profile_data["username"],
        bio=profile_data.get("bio", ""),
        image=profile_data.get("image", ""),
        following=False  # Assuming you have logic to determine if the current user is following this profile
    )
    return ProfileInResponse(profile=profile)
