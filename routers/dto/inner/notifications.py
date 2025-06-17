import uuid
from typing import Optional, Literal

from pydantic import BaseModel


class CreateNotificationRequestBase(BaseModel):
    notification_type: str
    user_id: Optional[int] = None
    chat_uuid: uuid.UUID
    status: Literal["READ", "UNREAD"]
    message: str
    user_group: Optional[str] = None
