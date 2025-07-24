from typing import List

from pydantic import BaseModel

from dto.request.testing import MessagesRequestBase


class AnswerInputQuestionRequest(BaseModel):
    messages: List[MessagesRequestBase]


class SingleOptionQuestionRequest(BaseModel):
    selected_option: int


class MultiOptionQuestionRequest(BaseModel):
    selected_option: List[int]
