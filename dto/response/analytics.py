from pydantic import BaseModel


class AnalyticsResponseCompletionRate(BaseModel):
    count: int
    status: str
    evaluation_start: int
    evaluation_end: int
