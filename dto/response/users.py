from pydantic import BaseModel


class UserResponseBase(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    is_admin: bool


class FullUserResponseBase(UserResponseBase):
    password: str


class UserResponseSmall(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
