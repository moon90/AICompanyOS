"""Database engine and session management for AI Company OS."""

from collections.abc import AsyncGenerator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from infrastructure.config import get_settings


def create_app_async_engine(database_url: str | None = None) -> AsyncEngine:
    """Create an asynchronous SQLAlchemy engine."""
    url = database_url or get_settings().database_url
    return create_async_engine(
        url,
        echo=get_settings().debug,
        future=True,
    )


def create_app_sync_engine(sync_database_url: str | None = None) -> Engine:
    """Create a synchronous SQLAlchemy engine for migrations and sync utilities."""
    url = sync_database_url or get_settings().sync_database_url
    return create_engine(
        url,
        echo=get_settings().debug,
        future=True,
    )


# Default engines and session factories
async_engine = create_app_async_engine()
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

sync_engine = create_app_sync_engine()
sync_session_factory = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency yielding an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_connection(engine: AsyncEngine | None = None) -> bool:
    """Verify database connectivity by executing a simple SELECT 1 query."""
    eng = engine or async_engine
    try:
        async with eng.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
