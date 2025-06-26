import os

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


load_dotenv()


DB_URL: str = os.getenv("PG_PSY_DATABASE_URL")
engine: AsyncEngine = create_async_engine(
    DB_URL,
    echo=False,
    future=True,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
        await session.commit()
