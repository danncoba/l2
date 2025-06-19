from typing import List

from pydantic import BaseModel

from dto.response.matrix_chats import MessageDict


class MatrixChatRequestBase(BaseModel):
    messages: List[MessageDict]


class MatrixChatInterruptRequestBase(BaseModel):
    grade: str
