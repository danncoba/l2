from typing import Optional, List
from pydantic import BaseModel, field_validator, ValidationInfo


class OptionModel(BaseModel):
    option: str
    is_correct: bool


class MatrixSkillKnowledgeBaseRequest(BaseModel):
    skill_id: int
    difficulty_level: int
    question: str
    answer: str
    options: Optional[List[OptionModel]] = None
    rules: str
    question_type: str
    is_code_question: bool

    @field_validator('options')
    @classmethod
    def validate_options(cls, v, info):
        if v is None:
            return v
        
        question_type = info.data.get('question_type')
        correct_count = sum(1 for opt in v if opt.is_correct)
        
        if question_type == 'single' and correct_count != 1:
            raise ValueError('Single choice questions must have exactly one correct answer')
        elif question_type == 'multi' and correct_count < 1:
            raise ValueError('Multi choice questions must have at least one correct answer')
        
        return v


class MatrixSkillKnowledgeBaseUpdate(BaseModel):
    skill_id: Optional[int] = None
    difficulty_level: Optional[int] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    options: Optional[List[OptionModel]] = None
    rules: Optional[str] = None
    question_type: Optional[str] = None
    is_code_question: Optional[bool] = None