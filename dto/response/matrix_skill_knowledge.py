from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class OptionModel(BaseModel):
    option: str
    is_correct: bool


class MatrixSkillKnowledgeBaseResponse(BaseModel):
    id: int
    skill_id: int
    difficulty_level: int
    question: str
    answer: Optional[str]
    options: Optional[List[OptionModel]]
    rules: Optional[str]
    question_type: str
    is_code_question: bool
    created_at: datetime
    updated_at: Optional[datetime]