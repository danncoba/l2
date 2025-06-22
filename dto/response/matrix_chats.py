import uuid
from datetime import datetime

from pydantic import BaseModel

from dto.response.skills import SkillResponseSmall
from dto.response.users import UserResponseSmall


class MessageDict(BaseModel):
    msg_type: str
    message: str
    is_execution_blocked: bool = False
    are_separate_messages: bool = False
    is_ambiguous: bool = False
    should_admin_continue: bool = False


class MatrixChatResponseBase(BaseModel):
    id: uuid.UUID
    skill: SkillResponseSmall
    user: UserResponseSmall
    created_at: datetime
    status: str
    updated_at: datetime


class MatrixMessageChatResponse(BaseModel):
    message: str
    is_execution_blocked: bool = False
