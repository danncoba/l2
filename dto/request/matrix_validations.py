from pydantic import BaseModel

from dto.request.testing import MessagesRequestBase


class CreateMatrixValidation(BaseModel):
    messages: list[MessagesRequestBase]
