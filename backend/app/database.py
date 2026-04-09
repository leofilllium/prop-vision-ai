"""
Async SQLAlchemy database engine and session factory for PostgreSQL + PostGIS.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, before_log

from app.config import get_settings

logger = logging.getLogger("propvision.database")

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before=before_log(logger, logging.INFO),
    reraise=True,
)
async def init_db() -> None:
    """Initialize database — create PostGIS extension and tables if needed."""
    async with engine.begin() as conn:
        await conn.execute(__import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.execute(__import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
