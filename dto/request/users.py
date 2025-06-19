from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class UserRequestBase(BaseModel):
    first_name: str = Field(max_length=100, min_length=3)
    last_name: str = Field(max_length=100, min_length=3)
    email: EmailStr = Field(max_length=100, min_length=3)
    is_admin: Optional[bool] = Field(default=False)


class UserCreateRequest(UserRequestBase):
    password: str = Field(max_length=100, min_length=4)
