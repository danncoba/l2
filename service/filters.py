from typing import Any

from enum import Enum
from pydantic import BaseModel


class FilterType(Enum):
    EQUALS = 0
    GTE = 1
    LTE = 2
    GT = 3
    LT = 4


class FilterModel(BaseModel):
    f_type: FilterType
    f_attribute: str
    f_value: Any
