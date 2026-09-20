"""Integration tests for database connection and session management."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from infrastructure.database.session import check_database_connection


@pytest.mark.asyncio
async def test_database_connectivity_and_session() -> None:
    """Verify SQLAlchemy connects and executes queries successfully."""
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, echo=False)

    # 1. Verify health check helper
    is_connected = await check_database_connection(engine=engine)
    assert is_connected is True

    # 2. Verify session execution and lifecycle
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        result = await session.execute(text("SELECT 42 AS val"))
        row = result.mappings().one()
        assert row["val"] == 42

    await engine.dispose()
