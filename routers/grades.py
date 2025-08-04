from typing import Annotated, Sequence, Any, List

from fastapi import APIRouter, UploadFile, File
from fastapi.params import Depends
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import Grade
from dto.request.grade import GradeRequestBase
from dto.response.grades import GradeResponseBase
from service.service import BaseService
from service.file_processor import FileProcessor
from service.uploader import UploaderFactory, UploaderType
from security import security, user_required
from utils.common import common_parameters

grades_router = APIRouter(
    prefix="/api/v1/grades", tags=["Grades"], dependencies=[Depends(user_required)]
)


@grades_router.get("", response_model=Sequence[GradeResponseBase])
async def get_grades(
    session: Annotated[AsyncSession, Depends(get_session)],
    common: Annotated[dict, Depends(common_parameters)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    service: BaseService[Grade, int, GradeResponseBase, Any] = BaseService(
        Grade, session
    )
    return await service.list_all(
        limit=common["limit"],
        offset=common["offset"],
    )


@grades_router.get("/{grade_id}", response_model=GradeResponseBase)
async def get_grade(
    grade_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    service: BaseService[Grade, int, GradeResponseBase, Any] = BaseService(
        Grade, session
    )
    return await service.get(grade_id)


@grades_router.post("", response_model=GradeResponseBase)
async def create_grade(
    create_dto: GradeRequestBase,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    service: BaseService[Grade, int, GradeRequestBase, Any] = BaseService(
        Grade, session
    )
    return await service.create(create_dto)


@grades_router.put("/{grade_id}", response_model=GradeResponseBase)
async def create_grade(
    grade_id: int,
    update_dto: GradeRequestBase,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    service: BaseService[Grade, int, GradeRequestBase, GradeRequestBase] = BaseService(
        Grade, session
    )
    return await service.update(grade_id, update_dto)


@grades_router.delete("/{grade_id}", response_model=bool)
async def create_grade(
    grade_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    service: BaseService[Grade, int, GradeRequestBase, GradeRequestBase] = BaseService(
        Grade, session
    )
    return await service.delete(grade_id)


@grades_router.post("/upload", response_model=List[GradeResponseBase])
async def upload_grades(
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    file: UploadFile = File(...)
):
    uploader = UploaderFactory().set_uploader_type(UploaderType.MINIO).build()
    await uploader.put_file("grades", file.filename, file)
    file.file.seek(0)  # Reset file pointer
    data = await FileProcessor.process_csv_excel(file)
    validated_data = FileProcessor.validate_grades_data(data)
    service: BaseService[Grade, int, GradeRequestBase, Any] = BaseService(Grade, session)
    created_grades = []
    
    for grade_data in validated_data:
        grade_request = GradeRequestBase(**grade_data)
        created_grade = await service.create(grade_request)
        created_grades.append(created_grade)
    
    return created_grades
