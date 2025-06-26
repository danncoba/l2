import asyncio
import uuid
import time

from datetime import datetime, timedelta, date
from typing import Any, Tuple

from celery import shared_task
from sqlalchemy import text
from sqlmodel import select

from db.db import get_session
from db.models import User, MatrixChat, UserSkills, Notification
from dto.inner.matrix_chat import CreateMatrixChatBase
from dto.inner.notifications import CreateNotificationRequestBase
from service.filters import FilterModel, FilterType
from service.service import BaseService


async def get_start_and_end() -> Tuple[int, int]:
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=7)
    start_timestamp = int(time.mktime(start.timetuple()))
    end_timestamp = int(time.mktime(end.timetuple()))
    print(f"START {str(start)} END {str(end)}")
    return start_timestamp, end_timestamp


async def get_required_users():
    start, end = await get_start_and_end()
    print(f"GET REQUIRED USERS START -> {start} END {end}")
    async for session in get_session():
        query = text(
            """
                     SELECT user_id, skill_id FROM users_skills
                     EXCEPT
                     SELECT user_id, skill_id FROM matrix_chats
                     WHERE timespan_start >= :timespan_start AND timespan_end <= :timespan_end;
                     """
        )

        results = await session.execute(
            query,
            {
                "timespan_start": start,
                "timespan_end": end,
            },
        )
        print("TOTAL RESULTS ->", results.rowcount)
        all_to_create = []
        for result in results:
            chat = CreateMatrixChatBase(
                id=uuid.uuid4(),
                user_id=result[0],
                skill_id=result[1],
                status="IN_PROGRESS",
                timespan_start=start,
                timespan_end=end,
            )
            all_to_create.append(chat)

        notifications = []
        for matrix_chat in all_to_create:
            notification = CreateNotificationRequestBase(
                notification_type="MATRIX_VALIDATION",
                user_id=matrix_chat.user_id,
                chat_uuid=matrix_chat.id,
                status="UNREAD",
                message=f"Please validate your skill going here https://localhost:5173/matrix-chats/{matrix_chat.id}",
            )
            notifications.append(notification)

        service: BaseService[MatrixChat, uuid.UUID, CreateMatrixChatBase, Any] = (
            BaseService(MatrixChat, session)
        )
        notification_service: BaseService[
            Notification, int, CreateNotificationRequestBase, Any
        ] = BaseService(Notification, session)
        all_results = await service.create_many(all_to_create)
        await notification_service.create_many(notifications)
        return all_results


@shared_task
def create_matrix_validations(starting_from: int, ending_at: int):
    asyncio.run(get_required_users())
