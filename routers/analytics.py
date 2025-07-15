from typing import Annotated, Any, List, Dict, Optional

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import Skill, User
from dto.request.skills import SkillRequestBase
from dto.response.analytics import AnalyticsResponseCompletionRate
from dto.response.skills import SkillResponseFull
from service.analytics import AnalyticsServiceFactory, AnalyticsServiceType
from service.service import BaseService
from security import get_current_user, admin_required
from utils.common import common_parameters

analytics_router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"],
    dependencies=[Depends(admin_required)],
)


@analytics_router.get("", response_model=List[AnalyticsResponseCompletionRate])
async def get_analytics(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> List[AnalyticsResponseCompletionRate]:
    analytics_service = (
        AnalyticsServiceFactory(AnalyticsServiceType.NORMAL)
        .set_session(session)
        .build()
    )
    return await analytics_service.get_completion_rate()
