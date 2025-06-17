import uuid
from typing import Literal

from pydantic import BaseModel


class CreateMatrixChatBase(BaseModel):
    id: uuid.UUID
    skill_id: int
    user_id: int
    status: Literal["IN_PROGRESS", "COMPLETED", "FAILED"]
