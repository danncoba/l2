from pydantic import BaseModel


class MatrixValidationsQAResponse(BaseModel):
    question: str
    answer: str
