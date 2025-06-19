import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from dto.response.users import UserResponseSmall


class NotificationSmallResponseBase(BaseModel):
    id: int
    notification_type: str
    user_group: Optional[str]
    created_at: datetime
    updated_at: datetime
    message: str
    status: str
    chat_uuid: Optional[uuid.UUID] = None


class NotificationResponseBase(NotificationSmallResponseBase):
    user: Optional[UserResponseSmall]
