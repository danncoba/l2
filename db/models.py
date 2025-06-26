import uuid
from uuid import UUID as UUID4
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Boolean, BigInteger, Integer, Text, DateTime, UUID, JSON
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlmodel import SQLModel, Field, Column, Relationship, ForeignKey


# op.add_column('users', sa.Column('description', sa.Text, nullable=True))
#     op.add_column('users', sa.Column('profile_pic', sa.String, nullable=True))
#     op.add_column('users', sa.Column('city', sa.String(100), nullable=True))
#     op.add_column('users', sa.Column('address', sa.String(100), nullable=True))
#     op.add_column('users', sa.Column('phone_number', sa.String(100), nullable=True))
#     op.add_column('users', sa.Column('additional_data', sa.JSON, nullable=True))
class User(AsyncAttrs, SQLModel, table=True):
    """
    User table named users
    """

    __tablename__ = "users"

    id: int = Field(
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, nullable=False
        )
    )
    first_name: str = Field(sa_column=Column(String(100), nullable=False))
    last_name: str = Field(sa_column=Column(String(100), nullable=False))
    email: str = Field(sa_column=Column(String(100), nullable=False, unique=True))
    password: str = Field(sa_column=Column(String(100), nullable=False))
    is_admin: bool = Field(sa_column=Column(Boolean, default=False, nullable=False))
    description: str = Field(sa_column=Column(Text, nullable=True))
    profile_pic: str = Field(sa_column=Column(String, nullable=True))
    city: str = Field(sa_column=Column(String(100), nullable=True))
    address: str = Field(sa_column=Column(String(100), nullable=True))
    phone_number: str = Field(sa_column=Column(String(100), nullable=True))
    additional_data: str = Field(sa_column=Column(JSON, nullable=True))

    skills: List["UserSkills"] = Relationship(back_populates="user")
    notifications: List["Notification"] = Relationship(back_populates="user")
    matrix_chats: List["MatrixChat"] = Relationship(back_populates="user")


class Grade(SQLModel, table=True):
    __tablename__ = "grades"

    id: int = Field(
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, nullable=False
        )
    )
    label: str = Field(sa_column=Column(String(255), nullable=False))
    value: int = Field(Integer(), nullable=False)
    deleted: bool = Field(sa_column=Column(Boolean, nullable=False, default=False))
    users_skills: List["UserSkills"] = Relationship(back_populates="grade")


class Skill(AsyncAttrs, SQLModel, table=True):
    __tablename__ = "skills"

    id: int = Field(
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, nullable=False
        )
    )
    name: str = Field(sa_column=Column(String(100), nullable=False))
    description: str = Field(sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        sa_column=Column(DateTime(), nullable=False, insert_default=datetime.now)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(), nullable=False, insert_default=datetime.now)
    )
    deleted: bool = Field(sa_column=Column(Boolean, nullable=False, default=False))
    deleted_at: datetime = Field(sa_column=Column(DateTime(), nullable=False))
    parent_id: Optional[int] = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("skills.id"),
            nullable=True,
            default=None,
        )
    )

    parent: Optional["Skill"] = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "Skill.id"}
    )
    children: List["Skill"] = Relationship(back_populates="parent")
    users: List["UserSkills"] = Relationship(back_populates="skill")
    matrix_chats: List["MatrixChat"] = Relationship(back_populates="skill")


class UserSkills(AsyncAttrs, SQLModel, table=True):
    __tablename__ = "users_skills"
    id: int = Field(
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, nullable=False
        )
    )
    user_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=False)
    )
    skill_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("skills.id"), nullable=False)
    )
    grade_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("grades.id"), nullable=False)
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(), nullable=False, insert_default=datetime.now)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(), nullable=False, insert_default=datetime.now)
    )
    note: str = Field(sa_column=Column(Text, nullable=True))
    user: User = Relationship(back_populates="skills")
    skill: Skill = Relationship(back_populates="users")
    grade: Grade = Relationship(back_populates="users_skills")


class Notification(AsyncAttrs, SQLModel, table=True):
    __tablename__ = "notifications"
    id: int = Field(
        sa_column=Column(
            BigInteger, primary_key=True, autoincrement=True, nullable=False
        )
    )
    notification_type: str = Field(String, nullable=False, max_length=100, min_length=1)
    message: str = Field(sa_column=Column(Text, nullable=False))
    user_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=True)
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(), nullable=False, insert_default=datetime.now)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(), nullable=False, insert_default=datetime.now)
    )
    status: str = Field(sa_column=Column(String(20), nullable=False))
    chat_uuid: UUID4 = Field(sa_column=Column(UUID, nullable=False))
    user_group: str = Field(sa_column=Column(String(20), nullable=True))
    user: User = Relationship(back_populates="notifications")


class MatrixChat(AsyncAttrs, SQLModel, table=True):
    __tablename__ = "matrix_chats"
    id: uuid.UUID = Field(sa_column=Column(UUID, primary_key=True, autoincrement=False))
    skill_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("skills.id"), nullable=False)
    )
    user_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("users.id"), nullable=False)
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(), nullable=False, insert_default=datetime.now)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(), nullable=False, insert_default=datetime.now)
    )
    timespan_start: int = Field(sa_column=Column(BigInteger, nullable=False))
    timespan_end: int = Field(sa_column=Column(BigInteger, nullable=False))
    status: str = Field(sa_column=Column(String(20), nullable=False))
    user: User = Relationship(back_populates="matrix_chats")
    skill: Skill = Relationship(back_populates="matrix_chats")


class Runnable(AsyncAttrs, SQLModel, table=True):
    __tablename__ = "runnables"
    thread_id: uuid.UUID = Field(
        sa_column=Column(
            UUID, primary_key=True, nullable=False, autoincrement=False, unique=True
        )
    )
    recursion_limit: int = Field(sa_column=Column(Integer, nullable=False))
    max_concurrency: int = Field(sa_column=Column(Integer, nullable=True))
    run_id: uuid.UUID = Field(sa_column=Column(UUID, nullable=False, unique=True))
    run_name: str = Field(sa_column=Column(String, nullable=True))
    runnable_metadata: List["RunnableMetadata"] = Relationship(back_populates="thread")
    runnable_tags: List["RunnableTag"] = Relationship(back_populates="thread")


class RunnableMetadata(AsyncAttrs, SQLModel, table=True):
    __tablename__ = "runnables_metadata"
    metadata_id: uuid.UUID = Field(
        sa_column=Column(
            UUID, primary_key=True, nullable=False, autoincrement=False, unique=True
        )
    )
    thread_id: uuid.UUID = Field(
        sa_column=Column(UUID, ForeignKey("runnables.thread_id"), nullable=False)
    )
    run_id: uuid.UUID = Field(sa_column=Column(UUID, nullable=False))
    key: str = Field(sa_column=Column(String, nullable=False))
    value: str = Field(sa_column=Column(JSON, nullable=False))
    thread: Runnable = Relationship(back_populates="runnable_metadata")


class RunnableTag(AsyncAttrs, SQLModel, table=True):
    __tablename__ = "runnables_tags"
    tag_id: uuid.UUID = Field(
        sa_column=Column(
            UUID, primary_key=True, nullable=False, autoincrement=False, unique=True
        )
    )
    thread_id: uuid.UUID = Field(
        sa_column=Column(UUID, ForeignKey("runnables.thread_id"), nullable=False)
    )
    value: str = Field(sa_column=Column(String, nullable=False))
    thread: Runnable = Relationship(back_populates="runnable_tags")


class Config(SQLModel, table=True):
    __tablename__ = "configs"
    id: int = Field(sa_column=Column(BigInteger, primary_key=True, autoincrement=False))
    matrix_cadence: str = Field(sa_column=Column(String, nullable=False))
    matrix_interval: int = Field(sa_column=Column(BigInteger, nullable=False))
    matrix_duration: int = Field(sa_column=Column(BigInteger, nullable=False))
    matrix_ending_at: int = Field(sa_column=Column(BigInteger, nullable=False))
    matrix_starting_at: int = Field(sa_column=Column(BigInteger, nullable=False))
    matrix_reminders: bool = Field(sa_column=Column(Boolean, nullable=False))
    reminders_format: str = Field(sa_column=Column(Text, nullable=True))
