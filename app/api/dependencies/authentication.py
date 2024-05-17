# noqa:WPS201
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette import requests, status
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.dependencies.database import get_repository
from app.core.config import get_app_settings
from app.core.settings.app import AppSettings
from app.db.errors import EntityDoesNotExist
from app.db.repositories.users import UsersRepository
from app.models.domain.users import User
from app.resources import strings
from app.services import jwt


from pymongo import MongoClient
from pymongo.collection import Collection
from app.db.repositories.base import BaseRepository

HEADER_KEY = "Authorization"


class RWAPIKeyHeader(APIKeyHeader):

    async def __call__(self, request: requests.Request) -> Optional[str]:
        try:
            api_key: str = request.headers.get("X-API-KEY")
            if not api_key:
                raise StarletteHTTPException(status_code=401, detail=strings.AUTHENTICATION_REQUIRED)
            client: MongoClient = MongoClient("mongodb://localhost:27017/")
            users_collection: Collection = client["app"]["users"]
            user: dict = users_collection.find_one({"api_key": api_key})
            if not user:
                raise StarletteHTTPException(status_code=401, detail=strings.AUTHENTICATION_REQUIRED)
            return api_key
        except StarletteHTTPException as original_auth_exc:
            raise HTTPException(status_code=original_auth_exc.status_code, detail=strings.AUTHENTICATION_REQUIRED)


def get_current_user_authorizer(*, required: bool = True) -> Callable:  # type: ignore
    return _get_current_user if required else _get_current_user_optional


def _get_authorization_header_retriever(
    *,
    required: bool = True,
) -> Callable:  # type: ignore
    return _get_authorization_header if required else _get_authorization_header_optional


def _get_authorization_header(
    api_key: str = Security(RWAPIKeyHeader(name=HEADER_KEY)),
    settings: AppSettings = Depends(get_app_settings),
) -> str:
    try:
        token_prefix, token = api_key.split(" ")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=strings.WRONG_TOKEN_PREFIX,
        )
    if token_prefix != settings.jwt_token_prefix:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=strings.WRONG_TOKEN_PREFIX,
        )

    return token

async def _get_current_user_optional(
    repo: BaseRepository = Depends(get_repository(UsersRepository)),
    token: str = Depends(_get_authorization_header_retriever(required=False)),
    settings: AppSettings = Depends(get_app_settings),
) -> Optional[User]:
    if token:
        user_collection: Collection = repo.collection
        user = user_collection.find_one({"username": jwt.get_username_from_token(token, settings)})
        if user:
            return User(**user)
        else:
            return None
    return None


def _get_authorization_header_optional(
    authorization: Optional[str] = Security(
        RWAPIKeyHeader(name=HEADER_KEY, auto_error=False),
    ),
    settings: AppSettings = Depends(get_app_settings),
) -> str:
    if authorization:
        return _get_authorization_header(authorization, settings)

    return ""

async def _get_current_user(
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token: str = Depends(_get_authorization_header_retriever()),
    settings: AppSettings = Depends(get_app_settings),
) -> User:
    try:
        username = jwt.get_username_from_token(
            token,
            str(settings.secret_key.get_secret_value()),
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=strings.MALFORMED_PAYLOAD,
        )

    try:
        user = await users_repo.get_user_by_username(username=username)
        if user is None:
            raise EntityDoesNotExist
        return user
    except EntityDoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=strings.MALFORMED_PAYLOAD,
        )
