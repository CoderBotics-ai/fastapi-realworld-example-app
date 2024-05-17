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
from pymongo import MongoClient
from app.models.schemas.users import UserInResponse, UserWithToken
from typing import AsyncGenerator
from pymongo.collection import Collection
from app.models.schemas.users import UserInUpdate, UserInResponse, UserWithToken

router = APIRouter()


async def update_current_user(
    user_update: UserInUpdate = Body(..., embed=True, alias="user"),
    current_user: User = Depends(get_current_user_authorizer()),
    users_collection: Collection = Depends(get_repository("users")),
    settings: AppSettings = Depends(get_app_settings),
) -> UserInResponse:
    if user_update.username and user_update.username != current_user.username:
        if await users_collection.count_documents({"username": user_update.username}) > 0:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=strings.USERNAME_TAKEN,
            )

    if user_update.email and user_update.email != current_user.email:
        if await users_collection.count_documents({"email": user_update.email}) > 0:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=strings.EMAIL_TAKEN,
            )

    update_data = user_update.dict(exclude_unset=True)
    await users_collection.update_one({"_id": current_user.id}, {"$set": update_data})

    user = await users_collection.find_one({"_id": current_user.id})
    token = jwt.create_access_token_for_user(
        user,
        str(settings.secret_key.get_secret_value()),
    )
    return UserInResponse(
        user=UserWithToken(
            username=user["username"],
            email=user["email"],
            bio=user["bio"],
            image=user["image"],
            token=token,
        ),
    )


@router.get("", response_model=UserInResponse, name="users:get-current-user")
async def retrieve_current_user(
    user: User = Depends(get_current_user_authorizer()),
    settings: AppSettings = Depends(get_app_settings),
) -> UserInResponse:
    client = MongoClient(settings.mongo_db_uri)
    db = client["app"]
    users_collection = db["users"]
    user_data = users_collection.find_one({"_id": user.id})
    token = jwt.create_access_token_for_user(
        user,
        str(settings.secret_key.get_secret_value()),
    )
    return UserInResponse(
        user=UserWithToken(
            username=user_data["username"],
            email=user_data["email"],
            bio=user_data["bio"],
            image=user_data["image"],
            token=token,
        ),
    )
