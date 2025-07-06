from typing import Optional, List, Literal

from pydantic import BaseModel


class MessagesRequestBase(BaseModel):
    role: Literal["human", "ai", "admin"]
    message: str


class DiscrepancyValueBase(BaseModel):
    grade_id: int
    skill_id: int
    user_id: int


class TestingRequestBase(BaseModel):
    discrepancy: DiscrepancyValueBase
    messages: List[MessagesRequestBase]
