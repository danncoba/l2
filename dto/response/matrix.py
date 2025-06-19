from typing import Optional

from pydantic import BaseModel

from dto.response.grades import GradeResponseBase
from dto.response.skills import SkillResponseSmall
from dto.response.users import UserResponseSmall


class UserMatrixResponseBase(BaseModel):

    id: int
    user: UserResponseSmall
    skill: SkillResponseSmall
    grade: Optional[GradeResponseBase] = None
