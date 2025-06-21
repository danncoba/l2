import uuid
from typing import Annotated, Any, List, Optional, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_session
from db.models import Notification, UserSkills, User, MatrixChat
from dto.inner.matrix_chat import CreateMatrixChatBase
from dto.inner.notifications import CreateNotificationRequestBase
from dto.request.notifications import UpdateNotificationRequestStatusBase
from dto.response.common import ActionSuccessResponse
from dto.response.notifications import (
    NotificationResponseBase,
    NotificationSmallResponseBase,
)
from service.service import BaseService
from security import get_current_user
from utils.common import common_parameters

notifications_router = APIRouter(
    prefix="/api/v1/users/{user_id}/notifications", tags=["Notifications"]
)


@notifications_router.get("", response_model=List[NotificationResponseBase])
async def list_notifications(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    common: Annotated[dict, Depends(common_parameters)],
    current_user: Optional[User] = Depends(get_current_user),
) -> List[NotificationResponseBase]:
    service: BaseService[Notification, int, Any, Any] = BaseService(
        Notification, session
    )
    group = "ADMIN" if current_user.is_admin else "USER"
    filters = {"or_": {"user_id": user_id, "user_group": group}}
    notifications = await service.list_all_with_or(
        filters=filters,
        order_by=[Notification.created_at.desc()],
        limit=common["limit"],
        offset=common["offset"],
    )
    print(f"Notifications -> {notifications}")
    all_notifications = []
    for notif in notifications:
        user = await notif.awaitable_attrs.user
        user_dump = None
        if user is not None:
            user.model_dump()
        resp_notification = NotificationResponseBase(
            **notif.model_dump(),
            user=user_dump,
        )
        all_notifications.append(resp_notification)
    return all_notifications


@notifications_router.post("/status", response_model=ActionSuccessResponse)
async def mark_notification(
    user_id: int,
    status_update_dto: UpdateNotificationRequestStatusBase,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> ActionSuccessResponse:
    service: BaseService[Notification, int, Any, Notification] = BaseService(
        Notification, session
    )
    ids_list: List[int] = []
    id_new_status_map: Dict[int, str] = {}
    for single_update_dto in status_update_dto.notifications:
        ids_list.append(single_update_dto.id)
        id_new_status_map[single_update_dto.id] = single_update_dto.status
    all_notifications = await service.in_field("id", ids_list)
    updated_notifications = []
    for notif in all_notifications:
        notif.status = id_new_status_map[notif.id]
        updated_notifications.append(notif)
    await service.update_many(updated_notifications, "id")
    return ActionSuccessResponse(
        success=True,
        message="Successfully updated notifications",
    )


@notifications_router.post("", response_model=List[NotificationSmallResponseBase])
async def create_notification(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Optional[User] = Depends(get_current_user),
) -> List[NotificationSmallResponseBase]:
    user_skills_service: BaseService[UserSkills, int, Any, Any] = BaseService(
        UserSkills, session
    )
    service: BaseService[Notification, int, CreateNotificationRequestBase, Any] = (
        BaseService(Notification, session)
    )
    matrix_chat_service: BaseService[MatrixChat, int, CreateMatrixChatBase, Any] = (
        BaseService(MatrixChat, session)
    )
    filters = {"user_id": user_id, "grade_id": None}
    user_skills = await user_skills_service.list_all(filters=filters)
    all_matrix_chats = []
    for skill in user_skills:
        matrix_chat = CreateMatrixChatBase(
            id=uuid.uuid4(),
            skill_id=skill.skill_id,
            user_id=user_id,
            status="IN_PROGRESS",
        )
        all_matrix_chats.append(matrix_chat)
    created_matrix_chats = await matrix_chat_service.create_many(all_matrix_chats)
    notifications = []
    for matrix_chat in created_matrix_chats:
        notification = CreateNotificationRequestBase(
            notification_type="MATRIX_VALIDATION",
            user_id=user_id,
            chat_uuid=matrix_chat.id,
            status="UNREAD",
            message=f"Please validate your skill going here https://localhost:5173/matrix-chats/{matrix_chat.id}",
        )
        notifications.append(notification)
    created_notifications = await service.create_many(notifications)
    return created_notifications
