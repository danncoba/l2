from typing import Annotated, Any, List, Optional

from fastapi import APIRouter
from fastapi.params import Depends
from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import Skill, UserSkills, User, Grade
from dto.request.matrix import (
    PopulateMatrixRequestBase,
    PopulateMatrixRequestAllBase,
)
from dto.response.matrix import UserMatrixResponseBase
from logger import logger
from service.service import BaseService
from security import security
from utils.common import common_parameters

matrix_router = APIRouter(
    prefix="/api/v1/users/{user_id}/matrix", tags=["Users Knowledge Matrix"]
)

AWAITABLES = ["user", "skill", "grade"]


class CreateMatrixBase(BaseModel):
    skill: Skill
    grade: Grade
    user: User
    note: str | None = None


async def get_matrix_response_dto(skill: UserSkills) -> UserMatrixResponseBase:
    skill_user = await skill.awaitable_attrs.user
    user_skill = await skill.awaitable_attrs.skill
    skill_grade = await skill.awaitable_attrs.grade
    grade_dump = None if skill_grade is None else skill_grade.model_dump()
    return UserMatrixResponseBase(
        **skill.model_dump(),
        user=skill_user.model_dump(),
        skill=user_skill.model_dump(),
        grade=grade_dump,
    )


@matrix_router.get("", response_model=List[UserMatrixResponseBase])
async def get_matrix(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    common: Annotated[dict, Depends(common_parameters)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    grade_id: Optional[int] = None,
    null_grade: bool = False,
) -> List[UserMatrixResponseBase]:
    logger.info(f"Getting matrix for user {user_id}")
    service: BaseService[UserSkills, int, Any, Any] = BaseService(UserSkills, session)
    filters = {
        "user_id": user_id,
    }
    if null_grade:
        filters["grade_id"] = None
    if grade_id is not None:
        filters["grade_id"] = grade_id
    all_skills = await service.list_all(
        offset=common["offset"],
        limit=common["limit"],
        filters=filters,
    )
    response_list: List[UserMatrixResponseBase] = []
    for skill in all_skills:
        full_skill = await get_matrix_response_dto(skill)
        response_list.append(full_skill)
    return response_list


@matrix_router.get("/{skill_id}", response_model=List[UserMatrixResponseBase])
async def get_matrix(
    user_id: int,
    skill_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    common: Annotated[dict, Depends(common_parameters)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    grade_id: Optional[int] = None,
    null_grade: bool = False,
) -> List[UserMatrixResponseBase]:
    logger.info(f"Getting skill id for user {user_id}")
    service: BaseService[UserSkills, int, Any, Any] = BaseService(UserSkills, session)
    filters = {
        "user_id": user_id,
        "skill_id": skill_id,
    }
    if null_grade:
        filters["grade_id"] = None
    if grade_id is not None:
        filters["grade_id"] = grade_id
    all_skills = await service.list_all(
        offset=common["offset"],
        limit=common["limit"],
        filters=filters,
    )
    response_list: List[UserMatrixResponseBase] = []
    for skill in all_skills:
        full_skill = await get_matrix_response_dto(skill)
        response_list.append(full_skill)
    return response_list


@matrix_router.post("/{skill_id}", response_model=UserMatrixResponseBase)
async def populate_matrix(
    user_id: int,
    skill_id: int,
    create_dto: PopulateMatrixRequestBase,
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserMatrixResponseBase:
    service: BaseService[UserSkills, int, PopulateMatrixRequestAllBase, Any] = (
        BaseService(UserSkills, session)
    )
    full_dto = PopulateMatrixRequestAllBase(
        **create_dto.model_dump(), skill_id=skill_id, user_id=user_id
    )
    created = await service.create(full_dto)
    full_skill = await get_matrix_response_dto(created)
    return full_skill


@matrix_router.delete("/{skill_id}", response_model=bool)
async def delete_matrix(
    user_id: int,
    skill_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> bool:
    service: BaseService[UserSkills, int, Any, Any] = BaseService(UserSkills, session)
    filters = {
        "user_id": user_id,
        "skill_id": skill_id,
    }
    elements = await service.list_all(filters=filters)
    for element in elements:
        await service.delete(element.id)

    return True
