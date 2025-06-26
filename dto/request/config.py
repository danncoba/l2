from typing import Optional, Literal

from pydantic import BaseModel, Field, model_validator


class ConfigurationRequestBase(BaseModel):
    matrix_cadence: str = Literal["Day", "Week", "Month", "Year"]
    matrix_interval: int = Field(ge=1)
    matrix_duration: int = Field(ge=1)
    matrix_ending_at: int
    matrix_starting_at: int
    matrix_reminders: bool = False
    reminders_format: Optional[str] = None

    # @model_validator(mode="after")
    # def validate_matrix_ending_at(self) -> 'ConfigurationRequestBase':
    #     self.matrix_starting_at = self.matrix_starting_at or self.matrix_ending_at
    #     matrix_starting_at = values.get("matrix_starting_at")
    #     if matrix_ending_at < matrix_starting_at:
    #         raise ValueError("Ending time must be greater than starting time")
    #     return values
