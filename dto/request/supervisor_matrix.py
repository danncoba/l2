import uuid

from pydantic import BaseModel


class CreateSupervisorMatrixRequest(BaseModel):
    id: str
    skill_id: int
    user_id: int


class CreateSupervisorWelcomeRequest(BaseModel):
    id: str
    supervisor_matrix_id: str
    message: str
