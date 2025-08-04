from typing import Optional
from pydantic import BaseModel


class UserSkillsRequestBase(BaseModel):
    user_id: int
    skill_id: int
    grade_id: int
    note: Optional[str] = None