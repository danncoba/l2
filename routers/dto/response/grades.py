from pydantic import BaseModel


class GradeResponseBase(BaseModel):
    id: int
    label: str
    value: int
