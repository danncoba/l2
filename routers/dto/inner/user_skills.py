from pydantic import BaseModel


class UpdateUserSkillsRequest(BaseModel):
    skill_id: int
