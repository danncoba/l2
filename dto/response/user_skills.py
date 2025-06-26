from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from dto.response.grades import GradeResponseBase
from dto.response.skills import SkillResponseBase


class UserSkillsResponseBase(BaseModel):
    skill: SkillResponseBase
    grade: Optional[GradeResponseBase] = None
    created_at: datetime
    updated_at: datetime
    note: Optional[str] = None
