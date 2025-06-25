import asyncio
import uuid
import time

from datetime import datetime, timedelta, date
from typing import Any, Tuple

from celery import shared_task
from sqlmodel import select

from db.db import get_session
from db.models import User, MatrixChat, UserSkills
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
        service: BaseService[MatrixChat, uuid.UUID, Any, Any] = BaseService(
            MatrixChat, session
        )
        filters = [
            FilterModel(f_type=FilterType.GTE, f_attribute="timespan_start", f_value=start),
            FilterModel(f_type=FilterType.LTE, f_attribute="timespan_end", f_value=end),
        ]
        all_chats = await service.filter(
            filters, limit=1000000000000, offset=0
        )
        print("ALL CHATS", all_chats)


@shared_task
def create_matrix_validations(starting_from: int, ending_at: int):
    asyncio.run(get_required_users())
