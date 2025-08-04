from typing import Annotated, Any, List, Dict, Optional

from fastapi import APIRouter, UploadFile, File
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import Skill, User
from dto.request.skills import SkillRequestBase
from dto.response.skills import SkillResponseFull
from service.service import BaseService
from service.file_processor import FileProcessor
from service.uploader import UploaderFactory, UploaderType
from security import get_current_user, admin_required
from utils.common import common_parameters

skills_router = APIRouter(
    prefix="/api/v1/skills", tags=["Skills"], dependencies=[Depends(admin_required)]
)

AWAITABLES = ["children", "parent"]


async def filtering_options(
    include_children: bool = False,
    include_parent: bool = False,
    parent_id: Optional[int] = None,
) -> Dict[str, Any]:
    return {
        "include_children": include_children,
        "include_parent": include_parent,
        "parent_id": parent_id,
    }


@skills_router.get("", response_model=List[SkillResponseFull])
async def get_all_skills(
    session: Annotated[AsyncSession, Depends(get_session)],
    common: Annotated[dict, Depends(common_parameters)],
    filters: Annotated[dict, Depends(filtering_options)],
    current_user: Optional[User] = Depends(get_current_user),
) -> List[SkillResponseFull]:
    service: BaseService[Skill, int, Any, Any] = BaseService(Skill, session)
    all_skills = await service.list_all(limit=common["limit"], offset=common["offset"])
    response_skills: List[SkillResponseFull] = []
    for skill in all_skills:
        parent = await skill.awaitable_attrs.parent
        parent_dump = None if parent is None else parent.model_dump()
        children = await skill.awaitable_attrs.children
        response_skills.append(
            SkillResponseFull(
                **skill.model_dump(),
                parent=parent_dump,
                children=[c.model_dump() for c in children],
            )
        )
    return response_skills


@skills_router.get("/{skill_id}", response_model=SkillResponseFull)
async def get_skill(
    skill_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> SkillResponseFull:
    service: BaseService[Skill, int, Any, Any] = BaseService(Skill, session)
    res_skill: Skill = await service.get(skill_id)
    parent = await res_skill.awaitable_attrs.parent
    children = await res_skill.awaitable_attrs.children
    parent_dump = None if parent is None else parent.model_dump()
    return SkillResponseFull(
        **res_skill.model_dump(),
        parent=parent_dump,
        children=[c.model_dump() for c in children],
    )


@skills_router.post("", response_model=SkillResponseFull)
async def create_skill(
    session: Annotated[AsyncSession, Depends(get_session)],
    create_dto: SkillRequestBase,
    current_user: Optional[User] = Depends(get_current_user),
) -> SkillResponseFull:
    service: BaseService[Skill, int, SkillRequestBase, Any] = BaseService(
        Skill, session
    )
    skill_response: Skill = await service.create(create_dto)
    return SkillResponseFull(**skill_response.model_dump())


@skills_router.delete("/{skill_id}", response_model=bool)
async def delete_skill(
    skill_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> bool:
    service: BaseService[Skill, int, Any, Any] = BaseService(Skill, session)
    deleted = await service.delete(skill_id)
    return deleted


@skills_router.post("/upload", response_model=List[SkillResponseFull])
async def upload_skills(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
    file: UploadFile = File(...)
) -> List[SkillResponseFull]:
    """Upload skills from CSV or Excel file"""
    # Upload file to MinIO
    uploader = UploaderFactory().set_uploader_type(UploaderType.MINIO).build()
    await uploader.put_file("skills", file.filename, file)
    
    # Process file
    file.file.seek(0)  # Reset file pointer
    data = await FileProcessor.process_csv_excel(file)
    validated_data = FileProcessor.validate_skills_data(data)
    
    # Create skills
    service: BaseService[Skill, int, SkillRequestBase, Any] = BaseService(Skill, session)
    created_skills = []
    
    for skill_data in validated_data:
        skill_request = SkillRequestBase(**skill_data)
        created_skill = await service.create(skill_request)
        created_skills.append(SkillResponseFull(**created_skill.model_dump()))
    
    return created_skills
