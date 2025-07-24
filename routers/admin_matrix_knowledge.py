from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import MatrixSkillKnowledgeBase, User
from dto.request.matrix_skill_knowledge import MatrixSkillKnowledgeBaseRequest, MatrixSkillKnowledgeBaseUpdate
from dto.response.matrix_skill_knowledge import MatrixSkillKnowledgeBaseResponse
from service.service import BaseService
from security import get_current_user, admin_required
from utils.common import common_parameters

admin_matrix_knowledge_router = APIRouter(
    prefix="/api/v1/admin/matrix-knowledge",
    tags=["Admin Matrix Knowledge"],
    dependencies=[Depends(admin_required)]
)


@admin_matrix_knowledge_router.get("", response_model=List[MatrixSkillKnowledgeBaseResponse])
async def get_all_matrix_knowledge(
    session: Annotated[AsyncSession, Depends(get_session)],
    common: Annotated[dict, Depends(common_parameters)],
    current_user: Optional[User] = Depends(get_current_user),
) -> List[MatrixSkillKnowledgeBaseResponse]:
    service = BaseService(MatrixSkillKnowledgeBase, session)
    items = await service.list_all(limit=common["limit"], offset=common["offset"])
    return [MatrixSkillKnowledgeBaseResponse(**item.model_dump()) for item in items]


@admin_matrix_knowledge_router.get("/{knowledge_id}", response_model=MatrixSkillKnowledgeBaseResponse)
async def get_matrix_knowledge(
    knowledge_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> MatrixSkillKnowledgeBaseResponse:
    service = BaseService(MatrixSkillKnowledgeBase, session)
    item = await service.get(knowledge_id)
    return MatrixSkillKnowledgeBaseResponse(**item.model_dump())


@admin_matrix_knowledge_router.post("", response_model=MatrixSkillKnowledgeBaseResponse)
async def create_matrix_knowledge(
    session: Annotated[AsyncSession, Depends(get_session)],
    create_dto: MatrixSkillKnowledgeBaseRequest,
    current_user: Optional[User] = Depends(get_current_user),
) -> MatrixSkillKnowledgeBaseResponse:
    service = BaseService(MatrixSkillKnowledgeBase, session)
    item = await service.create(create_dto)
    return MatrixSkillKnowledgeBaseResponse(**item.model_dump())


@admin_matrix_knowledge_router.put("/{knowledge_id}", response_model=MatrixSkillKnowledgeBaseResponse)
async def update_matrix_knowledge(
    knowledge_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    update_dto: MatrixSkillKnowledgeBaseUpdate,
    current_user: Optional[User] = Depends(get_current_user),
) -> MatrixSkillKnowledgeBaseResponse:
    service = BaseService(MatrixSkillKnowledgeBase, session)
    item = await service.update(knowledge_id, update_dto)
    return MatrixSkillKnowledgeBaseResponse(**item.model_dump())


@admin_matrix_knowledge_router.delete("/{knowledge_id}", response_model=bool)
async def delete_matrix_knowledge(
    knowledge_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> bool:
    service = BaseService(MatrixSkillKnowledgeBase, session)
    return await service.delete(knowledge_id)