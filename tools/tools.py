from typing import List, Any

from sqlalchemy.ext.asyncio import AsyncSession

from routers.db.db import get_session
from routers.db.models import Grade
from routers.dto.response.grades import GradeResponseBase
from routers.service.service import BaseService


async def get_expertise_level_or_grades(query: str) -> List[GradeResponseBase]:
    """Use this tool to get expertise level (grades) from within the system"""
    async for session in get_session():
        service: BaseService[Grade, int, Any, Any] = BaseService(Grade, session)
        return await service.list_all()
