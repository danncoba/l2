from typing import Optional, List

from pydantic import BaseModel

from dto.response.user_skills import UserSkillsResponseBase


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


class FullUserResponse(FullUserResponseBase):
    description: Optional[str] = None
    profile_pic: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    additional_data: Optional[dict] = None
    skills: List[UserSkillsResponseBase] = []
