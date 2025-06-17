from typing import Annotated, Any, Optional

from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from routers.db.db import get_session
from routers.db.models import User
from routers.service.service import BaseService

security = HTTPBasic()


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    credentials: HTTPBasicCredentials = Depends(security),
) -> Optional[User]:
    # Replace with your actual user authentication logic
    service: BaseService[User, int, Any, Any] = BaseService(User, session)
    users = await service.list_all(
        filters={
            "email": credentials.username,
            "password": credentials.password,
        },
        limit=1,
    )
    if len(users) == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return users[0]


def admin_required(current_user: User = Depends(get_current_user)):
    if current_user.is_admin:
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Forbidden",
        headers={"WWW-Authenticate": "Basic"},
    )


def user_required(current_user: User = Depends(get_current_user)):
    return True
