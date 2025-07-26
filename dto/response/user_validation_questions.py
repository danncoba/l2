from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, field_validator

from dto.response.skills import SkillResponseSmall
from dto.response.users import UserResponseBase


class UserKnowledgeBaseResponse(BaseModel):
    id: int
    skill_id: int
    difficulty_level: int
    question: str
    answer: Optional[str] = None
    options: Optional[List[Dict[str, Any]]] = None
    rules: Optional[str] = None
    question_type: str
    is_code_question: bool
    created_at: datetime

    @field_validator("options", mode="before")
    @classmethod
    def hide_correct_answers(cls, v, info):
        if v is None:
            return v
        question_type = info.data.get("question_type")
        if question_type in ["multi", "single"]:
            # Remove is_correct from options for multi/single choice
            return [{"option": opt.get("option")} for opt in v]
        return v

    @field_validator("answer", mode="before")
    @classmethod
    def hide_answer(cls, v, info):
        question_type = info.data.get("question_type")
        if question_type == "input":
            # Hide answer for input questions
            return None
        return v


class UserValidationQuestionResponse(BaseModel):
    id: int
    skill: SkillResponseSmall
    user: UserResponseBase
    knowledge_base: UserKnowledgeBaseResponse
    created_at: datetime


class KnowledgeBaseQuestionResponse(BaseModel):
    id: int
    skill_id: int
    difficulty_level: int
    question: str
    answer: Optional[str]
    options: Optional[List[Dict[str, Any]]]
    rules: Optional[str] = None
    question_type: str
    is_code_question: bool
    created_at: datetime
