from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from routers.db.db import get_session
from routers.dto.response.users import FullUserResponseBase
from security import security, admin_required

config_router = APIRouter(
    prefix="/api/v1/configuration",
    tags=["Configurations"],
    dependencies=[Depends(admin_required)],
)


@config_router.get("", response_model=FullUserResponseBase)
async def get_configs(
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> FullUserResponseBase:
    return None


@config_router.post("", response_model=FullUserResponseBase)
async def create_config(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FullUserResponseBase:
    return None
