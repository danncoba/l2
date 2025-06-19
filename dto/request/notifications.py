from typing import Literal, List

from openai import BaseModel


class SingleNotificationRequestStatusBase(BaseModel):
    id: int
    status: Literal["READ", "UNREAD"]


class UpdateNotificationRequestStatusBase(BaseModel):
    notifications: List[SingleNotificationRequestStatusBase]
