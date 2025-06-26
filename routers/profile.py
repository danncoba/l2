from typing import Annotated, Optional, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import User
from dto.request.users import FullUserRequest
from dto.response.users import UserResponseBase, FullUserResponse
from security import get_current_user
from service.service import BaseService

profile_router = APIRouter(prefix="/api/v1/profile", tags=["Profile"])


@profile_router.get("/me", response_model=FullUserResponse)
async def choose_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> FullUserResponse:
    skills = await current_user.awaitable_attrs.skills
    for skill in skills:
        await skill.awaitable_attrs.skill
        await skill.awaitable_attrs.grade
    return current_user


@profile_router.put("/me", response_model=FullUserResponse)
async def choose_user(
    update_dto: FullUserRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> FullUserResponse:
    service: BaseService[User, int, Any, FullUserRequest] = BaseService(User, session)
    saved_user = await service.update(current_user.id, update_dto)
    skills = await saved_user.awaitable_attrs.skills
    for skill in skills:
        await skill.awaitable_attrs.skill
        await skill.awaitable_attrs.grade
    return saved_user
