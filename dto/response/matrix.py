from typing import List, Optional

from pydantic import BaseModel

from routers.dto.response.grades import GradeResponseBase
from routers.dto.response.skills import SkillResponseBase, SkillResponseSmall
from routers.dto.response.users import UserResponseBase, UserResponseSmall


class UserMatrixResponseBase(BaseModel):

    id: int
    user: UserResponseSmall
    skill: SkillResponseSmall
    grade: Optional[GradeResponseBase] = None
