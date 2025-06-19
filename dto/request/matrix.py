from pydantic import BaseModel


class PopulateMatrixRequestBase(BaseModel):
    grade_id: int
    note: str | None = None


class PopulateMatrixRequestAllBase(PopulateMatrixRequestBase):
    skill_id: int
    user_id: int
