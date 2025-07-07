from typing import Optional, List, Literal

from pydantic import BaseModel, Field


class MessagesRequestBase(BaseModel):
    role: Literal["human", "ai", "admin"]
    message: str = Field(
        max_length=10000, description="Message send to the agent", min_length=1
    )


class DiscrepancyValueBase(BaseModel):
    grade_id: int
    skill_id: int
    user_id: int


class TestingRequestBase(BaseModel):
    discrepancy: DiscrepancyValueBase
    messages: List[MessagesRequestBase]
