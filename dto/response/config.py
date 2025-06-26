from typing import Optional

from pydantic import BaseModel


class ConfigurationResponseBase(BaseModel):
    id: int
    matrix_cadence: str
    matrix_interval: int
    matrix_duration: int
    matrix_ending_at: int
    matrix_starting_at: int
    matrix_reminders: bool = False
    reminders_format: Optional[str] = None
