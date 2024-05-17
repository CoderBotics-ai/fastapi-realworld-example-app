from fastapi import APIRouter, Body, Depends, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from app.api.dependencies.database import get_repository
from app.core.config import get_app_settings
from app.core.settings.app import AppSettings
from app.db.errors import EntityDoesNotExist
from app.db.repositories.users import UsersRepository
from app.resources import strings
from app.services import jwt
from app.services.authentication import check_email_is_taken, check_username_is_taken
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from app.models.schemas.users import (
    UserInCreate,
    UserInLogin,
    UserInResponse,
    UserWithToken,
)

router = APIRouter()

async def register(
    user_create: UserInCreate = Body(..., embed=True, alias="user"),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    settings: AppSettings = Depends(get_app_settings),
) -> UserInResponse:
    if await check_username_is_taken(users_repo, user_create.username):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=strings.USERNAME_TAKEN,
        )

    if await check_email_is_taken(users_repo, user_create.email):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=strings.EMAIL_TAKEN,
        )

    user_data = user_create.dict()
    user_data["_id"] = ObjectId()
    user_data["created_at"] = datetime.utcnow()
    user_data["updated_at"] = datetime.utcnow()

    result = await users_repo.client["users"].insert_one(user_data)
    user = await users_repo.get_user_by_id(result.inserted_id)

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


@router.post("/login", response_model=UserInResponse, name="auth:login")
async def login(
    user_login: UserInLogin = Body(..., embed=True, alias="user"),
    settings: AppSettings = Depends(get_app_settings),
) -> UserInResponse:
    wrong_login_error = HTTPException(
        status_code=HTTP_400_BAD_REQUEST,
        detail=strings.INCORRECT_LOGIN_INPUT,
    )

    client = MongoClient(settings.mongo_db_url)
    db = client["app"]
    users_collection = db["users"]

    try:
        user = users_collection.find_one({"email": user_login.email})
        if user is None:
            raise wrong_login_error
    except Exception as existence_error:
        raise wrong_login_error from existence_error

    if not user["hashed_password"] == user_login.password:
        raise wrong_login_error

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
