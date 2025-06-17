import uuid
from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel

from routers.dto.response.skills import SkillResponseSmall
from routers.dto.response.users import UserResponseSmall


class MessageDict(BaseModel):
    msg_type: str
    message: str
    is_execution_blocked: bool = False
    are_separate_messages: bool = False


class MatrixChatResponseBase(BaseModel):
    id: uuid.UUID
    skill: SkillResponseSmall
    user: UserResponseSmall
    created_at: datetime
    status: str
    updated_at: datetime
    messages: List[MessageDict] = []


class MatrixMessageChatResponse(BaseModel):
    message: str
    is_execution_blocked: bool = False
