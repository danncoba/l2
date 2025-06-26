import uuid
from typing import Sequence, Annotated, Optional, Any

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import User, MatrixChat
from dto.request.users import UserCreateRequest, UserRequestBase
from dto.response.users import UserResponseBase, FullUserResponseBase
from service.service import BaseService
from security import security, get_current_user
from tasks import get_start_and_end, get_required_users
from utils.common import common_parameters

users_router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@users_router.get("", response_model=Sequence[UserResponseBase])
async def get_users(
    session: Annotated[AsyncSession, Depends(get_session)],
    common: Annotated[dict, Depends(common_parameters)],
) -> Sequence[UserResponseBase]:
    service: BaseService[User, int, UserCreateRequest, UserCreateRequest] = BaseService(
        User, session
    )
    return await service.list_all(
        offset=common["offset"],
        limit=common["limit"],
    )


@users_router.get("/{user_id}", response_model=Optional[UserResponseBase])
async def get_user_by_id(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> Optional[User]:
    service: BaseService[User, int, UserCreateRequest, UserCreateRequest] = BaseService(
        User, session
    )
    return await service.get(user_id)


@users_router.post("", response_model=FullUserResponseBase)
async def create_user(
    user_create_request: UserCreateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> FullUserResponseBase:
    service: BaseService[User, int, UserCreateRequest, UserCreateRequest] = BaseService(
        User, session
    )
    user = await service.create(user_create_request)
    return FullUserResponseBase(**user.model_dump())


@users_router.put("/{user_id}", response_model=UserResponseBase)
async def update_user(
    user_id: int,
    user_update_request: UserRequestBase,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> UserResponseBase:
    service: BaseService[User, int, UserCreateRequest, UserRequestBase] = BaseService(
        User, session
    )
    user = await service.update(user_id, user_update_request)
    return UserResponseBase(**user.model_dump())


@users_router.delete("/{user_id}", response_model=bool)
async def update_user(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> bool:
    service: BaseService[User, int, UserCreateRequest, UserRequestBase] = BaseService(
        User, session
    )
    return await service.delete(user_id)


@users_router.post("/{user_id}/select", response_model=FullUserResponseBase)
async def choose_user(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FullUserResponseBase:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return FullUserResponseBase(**user.model_dump())


@users_router.get("/test/test", response_model=Any)
async def test_get_users(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await get_required_users()
