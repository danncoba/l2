import uuid
from typing import Sequence, Annotated, Optional, Any, List

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.params import Depends
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import User, MatrixChat
from dto.request.users import UserCreateRequest, UserRequestBase
from dto.response.users import UserResponseBase, FullUserResponseBase
from service.service import BaseService
from service.file_processor import FileProcessor
from service.uploader import UploaderFactory, UploaderType
from security import security, get_current_user
from tasks import get_start_and_end
from utils.common import common_parameters

users_router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@users_router.get("", response_model=Sequence[UserResponseBase])
async def get_users(
    session: Annotated[AsyncSession, Depends(get_session)],
    common: Annotated[dict, Depends(common_parameters)],
) -> Sequence[UserResponseBase]:
    service: BaseService[User, int, UserCreateRequest, UserCreateRequest] = BaseService(
        User, session
    )
    return await service.list_all(
        offset=common["offset"],
        limit=common["limit"],
    )


@users_router.get("/{user_id}", response_model=Optional[UserResponseBase])
async def get_user_by_id(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> Optional[User]:
    service: BaseService[User, int, UserCreateRequest, UserCreateRequest] = BaseService(
        User, session
    )
    return await service.get(user_id)


@users_router.post("", response_model=FullUserResponseBase)
async def create_user(
    user_create_request: UserCreateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> FullUserResponseBase:
    service: BaseService[User, int, UserCreateRequest, UserCreateRequest] = BaseService(
        User, session
    )
    user = await service.create(user_create_request)
    return FullUserResponseBase(**user.model_dump())


@users_router.put("/{user_id}", response_model=UserResponseBase)
async def update_user(
    user_id: int,
    user_update_request: UserRequestBase,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> UserResponseBase:
    service: BaseService[User, int, UserCreateRequest, UserRequestBase] = BaseService(
        User, session
    )
    user = await service.update(user_id, user_update_request)
    return UserResponseBase(**user.model_dump())


@users_router.delete("/{user_id}", response_model=bool)
async def update_user(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> bool:
    service: BaseService[User, int, UserCreateRequest, UserRequestBase] = BaseService(
        User, session
    )
    return await service.delete(user_id)


@users_router.post("/{user_id}/select", response_model=FullUserResponseBase)
async def choose_user(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FullUserResponseBase:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return FullUserResponseBase(**user.model_dump())


@users_router.post("/upload", response_model=List[FullUserResponseBase])
async def upload_users(
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    file: UploadFile = File(...),
) -> List[FullUserResponseBase]:
    """Upload users from CSV or Excel file"""
    # Upload file to MinIO
    uploader = UploaderFactory().set_uploader_type(UploaderType.MINIO).build()
    await uploader.put_file("users", file.filename, file)
    
    # Process file
    file.file.seek(0)  # Reset file pointer
    data = await FileProcessor.process_csv_excel(file)
    
    # Create users
    service: BaseService[User, int, UserCreateRequest, UserCreateRequest] = BaseService(
        User, session
    )
    created_users = []
    
    for user_data in data:
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'password']
        if not all(field in user_data for field in required_fields):
            raise HTTPException(status_code=400, detail=f"Missing required fields: {required_fields}")
        
        user_request = UserCreateRequest(
            first_name=str(user_data['first_name']),
            last_name=str(user_data['last_name']),
            email=str(user_data['email']),
            password=str(user_data['password']),
            is_admin=bool(user_data.get('is_admin', False))
        )
        created_user = await service.create(user_request)
        created_users.append(FullUserResponseBase(**created_user.model_dump()))
    
    return created_users


@users_router.get("/test/test", response_model=Any)
async def test_get_users(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    pass
