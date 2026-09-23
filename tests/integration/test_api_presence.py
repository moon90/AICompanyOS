"""Integration tests for Agent Presence API endpoints adhering to docs/Phases.md Section 18."""

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

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await engine.dispose()


@pytest.mark.asyncio
async def test_presence_requires_auth(app_client: AsyncClient) -> None:
    """Verify unauthenticated requests to presence endpoints are rejected with 401."""
    resp = await app_client.get("/api/v1/companies/some-company-id/presence")
    assert resp.status_code == 401

    resp_summary = await app_client.get("/api/v1/companies/some-company-id/presence/summary")
    assert resp_summary.status_code == 401


@pytest.mark.asyncio
async def test_presence_multi_tenant_isolation(app_client: AsyncClient) -> None:
    """Verify operators cannot view presence of a foreign company."""
    # Register and login operator 1
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Op One",
            "email": "op1@presence.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_res = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "op1@presence.test", "password": "Password123!"},
    )
    assert login_res.status_code == 200

    # Create company 1
    c1_res = await app_client.post(
        "/api/v1/companies",
        json={"name": "Company One", "mission": "First"},
    )
    assert c1_res.status_code == 201
    c1_id = c1_res.json()["id"]

    # Register and login operator 2
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Op Two",
            "email": "op2@presence.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "op2@presence.test", "password": "Password123!"},
    )

    # Operator 2 attempts to view Company 1 presence -> 403 Forbidden
    resp = await app_client.get(f"/api/v1/companies/{c1_id}/presence")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_presence_endpoints_and_lifecycle(app_client: AsyncClient) -> None:
    """Verify full presence lifecycle, summary, heartbeat, and operator update."""
    # 1. Register & login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Admin",
            "email": "admin@presence.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_res = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@presence.test", "password": "Password123!"},
    )
    assert login_res.status_code == 200

    # 2. Create company
    c_res = await app_client.post(
        "/api/v1/companies",
        json={"name": "Live Presence Inc", "mission": "Track active agents"},
    )
    assert c_res.status_code == 201
    company_id = c_res.json()["id"]

    # 3. Create department and agent
    dept_res = await app_client.post(
        f"/api/v1/companies/{company_id}/departments",
        json={"name": "Marketing", "code": "MKT"},
    )
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["id"]

    agent_res = await app_client.post(
        f"/api/v1/companies/{company_id}/agents",
        json={
            "name": "CMO Lead",
            "role": "Chief Marketing Officer",
            "type": "lead",
            "department_id": dept_id,
        },
    )
    assert agent_res.status_code == 201
    agent_id = agent_res.json()["id"]

    # 4. Query company presence list
    list_res = await app_client.get(f"/api/v1/companies/{company_id}/presence")
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] == 1
    agent_presence = data["items"][0]
    assert agent_presence["agent_id"] == agent_id
    assert agent_presence["status"] == "IDLE"
    assert agent_presence["agent_name"] == "CMO Lead"

    # 5. Query presence summary
    summary_res = await app_client.get(f"/api/v1/companies/{company_id}/presence/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_agents"] == 1
    assert summary["idle_count"] == 1
    assert summary["working_count"] == 0

    # 6. Send heartbeat check-in
    hb_res = await app_client.post(
        f"/api/v1/companies/{company_id}/agents/{agent_id}/presence/heartbeat",
        json={
            "current_step": "Analyzing market survey responses",
            "current_activity": "Researching Germany market",
        },
    )
    assert hb_res.status_code == 200
    hb_data = hb_res.json()
    assert hb_data["current_step"] == "Analyzing market survey responses"
    assert hb_data["current_activity"] == "Researching Germany market"

    # 7. Operator override to WORKING
    patch_res = await app_client.patch(
        f"/api/v1/companies/{company_id}/agents/{agent_id}/presence",
        json={
            "status": "WORKING",
            "current_activity": "Leading international campaign kickoff",
        },
    )
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["status"] == "WORKING"
    assert patch_data["current_activity"] == "Leading international campaign kickoff"

    # 8. Check updated summary
    summary_res2 = await app_client.get(f"/api/v1/companies/{company_id}/presence/summary")
    assert summary_res2.status_code == 200
    assert summary_res2.json()["working_count"] == 1
    assert summary_res2.json()["idle_count"] == 0
