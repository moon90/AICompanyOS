"""Integration tests for Real-Time Operations API adhering to docs/Phases.md Section 21."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.main import create_application
from infrastructure.config import Settings
from infrastructure.database.base import Base
from infrastructure.database.session import get_db_session
from infrastructure.events.dispatcher import EventDispatcher


@pytest.fixture(autouse=True)
def reset_dispatcher() -> None:
    """Ensure clean global dispatcher instance for each integration test."""
    EventDispatcher.reset_instance()


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
async def test_realtime_routes_require_auth(app_client: AsyncClient) -> None:
    """Verify unauthenticated requests to real-time endpoints are rejected with 401."""
    company_id = "test-comp-id"
    resp_events = await app_client.get(f"/api/v1/companies/{company_id}/realtime/events")
    assert resp_events.status_code == 401

    resp_emit = await app_client.post(
        f"/api/v1/companies/{company_id}/realtime/emit",
        json={"event_type": "test.pulse", "message": "Test"},
    )
    assert resp_emit.status_code == 401

    resp_status = await app_client.get(f"/api/v1/companies/{company_id}/realtime/status")
    assert resp_status.status_code == 401


@pytest.mark.asyncio
async def test_realtime_routes_access_denied_for_non_member(
    app_client: AsyncClient,
) -> None:
    """Verify authenticated operators cannot access real-time streams of unauthorized companies."""
    # Register and login operator
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Foreign",
            "email": "foreign@company.os",
            "password": "secure-password-123",
            "confirm_password": "secure-password-123",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={
            "email": "foreign@company.os",
            "password": "secure-password-123",
        },
    )

    resp = await app_client.get("/api/v1/companies/foreign-company-id/realtime/events")
    assert resp.status_code == 403
    assert "does not have access" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_realtime_emit_and_status(app_client: AsyncClient) -> None:
    """Verify authenticated member can emit real-time events and query channel telemetry."""
    # 1. Register and login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Alpha",
            "email": "alpha@company.os",
            "password": "secure-password-123",
            "confirm_password": "secure-password-123",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "alpha@company.os", "password": "secure-password-123"},
    )

    # 2. Create company
    comp_resp = await app_client.post(
        "/api/v1/companies",
        json={
            "name": "IceSoft Corp",
            "mission": "Autonomous company OS",
            "industry": "Software",
        },
    )
    assert comp_resp.status_code == 201
    company_id = comp_resp.json()["id"]

    # 3. Check initial channel status
    status_resp = await app_client.get(f"/api/v1/companies/{company_id}/realtime/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["company_id"] == company_id
    assert status_data["active_subscribers"] == 0
    assert status_data["channel_status"] == "idle"
    assert status_data["events_dispatched"] == 0

    # 4. Emit an operational event
    emit_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/realtime/emit",
        json={
            "event_type": "agent.started",
            "message": "Specialist Agent 'Architecture Guardian' started execution",
            "actor_type": "agent",
            "actor_name": "Architecture Guardian",
            "metadata": {"specialization": "Backend"},
        },
    )
    assert emit_resp.status_code == 201
    event_data = emit_resp.json()
    assert event_data["event_type"] == "agent.started"
    assert event_data["actor_name"] == "Architecture Guardian"
    assert event_data["company_id"] == company_id
    assert "timestamp" in event_data

    # 5. Verify status updated counter
    status_resp_2 = await app_client.get(f"/api/v1/companies/{company_id}/realtime/status")
    assert status_resp_2.status_code == 200
    assert status_resp_2.json()["events_dispatched"] == 1
