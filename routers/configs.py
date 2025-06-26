from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import Config
from dto.request.config import ConfigurationRequestBase
from dto.response.config import ConfigurationResponseBase
from dto.response.users import FullUserResponseBase
from security import security, admin_required
from service.service import BaseService

config_router = APIRouter(
    prefix="/api/v1/configuration",
    tags=["Configurations"],
    dependencies=[Depends(admin_required)],
)


@config_router.get("", response_model=ConfigurationResponseBase)
async def get_configs(
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> ConfigurationResponseBase:
    service: BaseService[Config, int, Any, Any] = BaseService(Config, session)
    configuration = await service.list_all()
    return configuration[0]


@config_router.put("", response_model=ConfigurationResponseBase)
async def create_config(
    update_dto: ConfigurationRequestBase,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ConfigurationResponseBase:
    service: BaseService[Config, int, Any, ConfigurationRequestBase] = BaseService(
        Config, session
    )
    configs = await service.list_all()
    if len(configs) > 0:
        configuration = await service.update(configs[0].id, update_dto)
    return configuration
