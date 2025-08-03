from typing import Literal

from pydantic import BaseModel


class UserValidationQuestionUpdateDTO(BaseModel):
    status: Literal["pending", "waiting_admin", "verified"]
    answer_correct: bool
