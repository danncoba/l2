from pydantic import BaseModel


class GradeRequestBase(BaseModel):
    label: str
    value: int
