from fastapi import APIRouter, Body, Depends, HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from app.api.dependencies.authentication import get_current_user_authorizer
from app.api.dependencies.database import get_repository
from app.core.config import get_app_settings
from app.core.settings.app import AppSettings
from app.db.repositories.users import UsersRepository
from app.models.domain.users import User
from app.models.schemas.users import UserInResponse, UserInUpdate, UserWithToken
from app.resources import strings
from app.services import jwt
from app.services.authentication import check_email_is_taken, check_username_is_taken

router = APIRouter()


@router.get("", response_model=UserInResponse, name="users:get-current-user")
async def retrieve_current_user(
    user: User = Depends(get_current_user_authorizer()),
    settings: AppSettings = Depends(get_app_settings),
) -> UserInResponse:
    token = jwt.create_access_token_for_user(
        user,
        str(settings.secret_key.get_secret_value()),
    )
    return UserInResponse(
        user=UserWithToken(
            username=user.username,
            email=user.email,
            bio=user.bio,
            image=user.image,
            token=token,
        ),
    )

@router.put("", response_model=UserInResponse, name="users:update-current-user")
async def update_current_user(
    user_update: UserInUpdate = Body(..., embed=True, alias="user"),
    current_user: User = Depends(get_current_user_authorizer()),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    settings: AppSettings = Depends(get_app_settings),
) -> UserInResponse:
    if user_update.username and user_update.username != current_user.username:
        if await users_repo.check_username_exists(user_update.username):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=strings.USERNAME_TAKEN,
            )

    if user_update.email and user_update.email != current_user.email:
        if await users_repo.check_email_exists(user_update.email):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=strings.EMAIL_TAKEN,
            )

    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    await users_repo.collection.update_one(
        {"_id": current_user.id},
        {"$set": update_data}
    )
    updated_user = await users_repo.collection.find_one({"_id": current_user.id})

    token = jwt.create_access_token_for_user(
        updated_user,
        str(settings.secret_key.get_secret_value()),
    )
    return UserInResponse(
        user=UserWithToken(
            username=updated_user["username"],
            email=updated_user["email"],
            bio=updated_user.get("bio", ""),
            image=updated_user.get("image", ""),
            token=token,
        ),
    )
