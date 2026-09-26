"""Integration tests for System Status API."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.main import create_application
from infrastructure.config import Settings
from infrastructure.database.base import Base
from infrastructure.database.session import get_db_session


@pytest.fixture
async def app_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client with in-memory database and overridden dependencies."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    settings = Settings(
        app_name="AI Company OS Test",
        app_env="test",
        session_cookie_name="ai_company_session_test",
        cookie_secure=False,
    )
    app = create_application(settings=settings)
    app.dependency_overrides[get_db_session] = override_get_db_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    await engine.dispose()


@pytest.mark.asyncio
async def test_system_status_requires_auth(app_client: AsyncClient) -> None:
    """Verify unauthenticated requests to system status endpoint are rejected with 401."""
    resp = await app_client.get("/api/v1/system/status")
    assert resp.status_code == 401
    assert "detail" in resp.json()


@pytest.mark.asyncio
async def test_system_status_authenticated(app_client: AsyncClient) -> None:
    """Verify authenticated operators can retrieve live system telemetry."""
    # 1. Register and login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Alpha",
            "email": "operator@company.os",
            "password": "secure-password-456",
            "confirm_password": "secure-password-456",
        },
    )
    login_resp = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "operator@company.os", "password": "secure-password-456"},
    )
    assert login_resp.status_code == 200

    # 2. Query system status
    status_resp = await app_client.get("/api/v1/system/status")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["status"] == "operational"
    assert data["database"] == "connected"
    assert data["auth_authority"] == "postgresql_sessions"
    assert data["current_phase"] == "Phase 23 — Security Hardening"
    assert data["environment"] == "test"
    assert "timestamp" in data
