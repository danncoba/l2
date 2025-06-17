from typing import Annotated, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from routers.db.db import get_session
from routers.db.models import User
from routers.dto.response.users import FullUserResponseBase, UserResponseBase
from security import get_current_user

profile_router = APIRouter(prefix="/api/v1/profile", tags=["Profile"])


@profile_router.get("/me", response_model=UserResponseBase)
async def choose_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> UserResponseBase:
    return current_user
