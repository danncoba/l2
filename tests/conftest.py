import asyncio
import uuid
from typing import AsyncGenerator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from main import app
from db.db import get_session
from db.models import User, Grade, Skill, UserSkills, Config
from security import get_current_user


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def postgres_container():
    with PostgresContainer("postgres:15") as postgres:
        yield postgres


@pytest.fixture(scope="session")
async def redis_container():
    with RedisContainer("redis:7") as redis:
        yield redis


@pytest.fixture(scope="session")
async def test_engine(postgres_container):
    database_url = postgres_container.get_connection_url().replace(
        "psycopg2", "asyncpg"
    )
    engine = create_async_engine(database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_client(test_session):
    def override_get_session():
        return test_session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_session):
    user = User(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        password="password123",
        is_admin=False,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(test_session):
    user = User(
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        password="admin123",
        is_admin=True,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def test_grade(test_session):
    grade = Grade(label="Beginner", value=1)
    test_session.add(grade)
    await test_session.commit()
    await test_session.refresh(grade)
    return grade


@pytest.fixture
async def test_skill(test_session):
    skill = Skill(name="Python", description="Python programming")
    test_session.add(skill)
    await test_session.commit()
    await test_session.refresh(skill)
    return skill


@pytest.fixture
async def test_config(test_session):
    config = Config(
        id=1,
        matrix_cadence="weekly",
        matrix_interval=7,
        matrix_duration=30,
        matrix_ending_at=1800,
        matrix_starting_at=900,
        matrix_reminders=True,
    )
    test_session.add(config)
    await test_session.commit()
    await test_session.refresh(config)
    return config


@pytest.fixture
def auth_headers():
    return {"Authorization": "Basic dGVzdEBleGFtcGxlLmNvbTpwYXNzd29yZDEyMw=="}


@pytest.fixture
def admin_auth_headers():
    return {"Authorization": "Basic YWRtaW5AZXhhbXBsZS5jb206YWRtaW4xMjM="}


@pytest.fixture
def mock_current_user(test_user):
    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield test_user
    app.dependency_overrides.clear()


@pytest.fixture
def mock_admin_user(admin_user):
    def override_get_current_user():
        return admin_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield admin_user
    app.dependency_overrides.clear()
