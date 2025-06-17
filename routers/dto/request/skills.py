from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SkillRequestBase(BaseModel):
    name: str
    description: Optional[str] = None
    deleted: bool = False
    parent_id: Optional[int] = None
