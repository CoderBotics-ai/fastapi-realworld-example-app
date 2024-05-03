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

router = APIRouter()


@router.get(
    "/{username}",
    response_model=ProfileInResponse,
    name="profiles:get-profile",
)
async def retrieve_profile_by_username(
    profile: Profile = Depends(get_profile_by_username_from_path),
) -> ProfileInResponse:
    return ProfileInResponse(profile=profile)

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

    # MongoDB operation to add user into followers
    await profiles_repo.collection.update_one(
        {"_id": profile.id},
        {"$addToSet": {"followers": user.id}}
    )

    profile.following = True  # Update the profile object to reflect the change

    return ProfileInResponse(profile=profile)

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

    await profiles_repo.mongo_collection.update_one(
        {"_id": profile.id},
        {"$pull": {"followers": user.id}}
    )

    profile.following = False

    return ProfileInResponse(profile=profile)
