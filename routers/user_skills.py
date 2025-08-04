from typing import Annotated, List, Any

from fastapi import APIRouter, UploadFile, File
from fastapi.params import Depends
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import UserSkills, User
from dto.request.user_skills import UserSkillsRequestBase
from dto.response.user_skills import UserSkillsResponseBase
from service.service import BaseService
from service.file_processor import FileProcessor
from service.uploader import UploaderFactory, UploaderType
from security import security, get_current_user
from utils.common import common_parameters

user_skills_router = APIRouter(
    prefix="/api/v1/user-skills", tags=["User Skills"], dependencies=[Depends(security)]
)


@user_skills_router.get("", response_model=List[UserSkillsResponseBase])
async def get_user_skills(
    session: Annotated[AsyncSession, Depends(get_session)],
    common: Annotated[dict, Depends(common_parameters)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    service: BaseService[UserSkills, int, UserSkillsRequestBase, Any] = BaseService(
        UserSkills, session
    )
    return await service.list_all(
        limit=common["limit"],
        offset=common["offset"],
    )


@user_skills_router.post("", response_model=UserSkillsResponseBase)
async def create_user_skill(
    create_dto: UserSkillsRequestBase,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    service: BaseService[UserSkills, int, UserSkillsRequestBase, Any] = BaseService(
        UserSkills, session
    )
    return await service.create(create_dto)


@user_skills_router.post("/upload", response_model=List[UserSkillsResponseBase])
async def upload_user_skills(
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    file: UploadFile = File(...),
):
    """Upload user skills from CSV or Excel file"""
    # Upload file to MinIO
    uploader = UploaderFactory().set_uploader_type(UploaderType.MINIO).build()
    await uploader.put_file("user-skills", file.filename, file)
    
    # Process file
    file.file.seek(0)  # Reset file pointer
    data = await FileProcessor.process_csv_excel(file)
    validated_data = FileProcessor.validate_user_skills_data(data)
    
    # Create user skills
    service: BaseService[UserSkills, int, UserSkillsRequestBase, Any] = BaseService(
        UserSkills, session
    )
    created_user_skills = []
    
    for user_skill_data in validated_data:
        user_skill_request = UserSkillsRequestBase(**user_skill_data)
        created_user_skill = await service.create(user_skill_request)
        created_user_skills.append(created_user_skill)
    
    return created_user_skills