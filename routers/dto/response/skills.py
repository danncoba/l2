from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel


class SkillResponseBase(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted: bool = False
    deleted_at: Optional[datetime] = None
    parent_id: Optional[int] = None


class SkillResponseFull(SkillResponseBase):
    parent: Optional[SkillResponseBase] = None
    children: List[SkillResponseBase] = []


class SkillResponseSmall(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
