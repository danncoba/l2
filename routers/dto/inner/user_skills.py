from pydantic import BaseModel


class UpdateUserSkillsRequest(BaseModel):
    grade_id: int
