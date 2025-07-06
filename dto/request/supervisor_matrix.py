import uuid

from pydantic import BaseModel


class CreateSupervisorMatrixRequest(BaseModel):
    id: str
    skill_id: int
    user_id: int
