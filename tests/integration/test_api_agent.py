"""Integration tests for Agent Registry API endpoints and multi-company isolation."""

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
async def test_agent_api_complete_lifecycle_and_isolation(app_client: AsyncClient) -> None:
    """Verify complete agent registration, retrieval, updating, versioning, and tenant isolation."""
    # 1. Unauthenticated access rejected
    unauth_resp = await app_client.get("/api/v1/companies/some-id/agents")
    assert unauth_resp.status_code == 401

    # 2. Register & login User A
    reg_a = await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "CEO Operator",
            "email": "ceo@operating.os",
            "password": "strong-password-123",
            "confirm_password": "strong-password-123",
        },
    )
    assert reg_a.status_code == 201

    login_a = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "ceo@operating.os", "password": "strong-password-123"},
    )
    assert login_a.status_code == 200

    # 3. User A creates Company A
    comp_a_resp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Synthetix Corp", "industry": "Artificial Intelligence"},
    )
    assert comp_a_resp.status_code == 201
    comp_a = comp_a_resp.json()
    comp_a_id = comp_a["id"]

    # 4. User A registers an Agent in Company A
    agent_create_resp = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/agents",
        json={
            "name": "Research Specialist",
            "role": "Lead Market Analyst",
            "type": "specialist",
            "mission": "Analyze competitors and market signals.",
            "authority_level": "specialist",
            "system_prompt": "You are the Lead Market Analyst.",
            "model": "gemini-1.5-pro",
            "capabilities": ["market_analysis", "report_generation"],
            "tools": ["web_search"],
        },
    )
    assert agent_create_resp.status_code == 201
    agent_data = agent_create_resp.json()
    assert agent_data["name"] == "Research Specialist"
    assert agent_data["role"] == "Lead Market Analyst"
    assert agent_data["current_definition"]["version"] == "1.0"
    agent_id = agent_data["id"]

    # 5. User A lists agents
    list_resp = await app_client.get(f"/api/v1/companies/{comp_a_id}/agents")
    assert list_resp.status_code == 200
    agents_list = list_resp.json()
    assert len(agents_list) == 1
    assert agents_list[0]["id"] == agent_id

    # 6. User A retrieves agent detail
    detail_resp = await app_client.get(f"/api/v1/companies/{comp_a_id}/agents/{agent_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["name"] == "Research Specialist"
    assert len(detail["definitions"]) == 1
    assert detail["definitions"][0]["version"] == "1.0"

    # 7. User A updates agent status to inactive
    update_resp = await app_client.patch(
        f"/api/v1/companies/{comp_a_id}/agents/{agent_id}",
        json={"status": "inactive"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "inactive"

    # 8. User A adds a new definition version (1.1)
    new_def_resp = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/agents/{agent_id}/definitions",
        json={
            "version": "1.1",
            "system_prompt": "Updated v1.1 prompt.",
            "model": "claude-3-5-sonnet",
            "capabilities": ["market_analysis", "sentiment_analysis"],
        },
    )
    assert new_def_resp.status_code == 201
    assert new_def_resp.json()["version"] == "1.1"

    # 9. List definitions shows history
    defs_resp = await app_client.get(f"/api/v1/companies/{comp_a_id}/agents/{agent_id}/definitions")
    assert defs_resp.status_code == 200
    defs_list = defs_resp.json()
    assert len(defs_list) == 2

    # 10. Multi-Company Isolation: User B logs in and attempts to access Company A's agents
    reg_b = await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Rival Operator",
            "email": "rival@external.os",
            "password": "rival-password-456",
            "confirm_password": "rival-password-456",
        },
    )
    assert reg_b.status_code == 201

    login_b = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "rival@external.os", "password": "rival-password-456"},
    )
    assert login_b.status_code == 200

    # User B listing Company A agents -> 403 Forbidden
    b_list_resp = await app_client.get(f"/api/v1/companies/{comp_a_id}/agents")
    assert b_list_resp.status_code == 403

    # User B viewing Company A agent detail -> 403 Forbidden
    b_detail_resp = await app_client.get(f"/api/v1/companies/{comp_a_id}/agents/{agent_id}")
    assert b_detail_resp.status_code == 403

    # User B modifying Company A agent -> 403 Forbidden
    b_update_resp = await app_client.patch(
        f"/api/v1/companies/{comp_a_id}/agents/{agent_id}",
        json={"name": "Hacked Name"},
    )
    assert b_update_resp.status_code == 403

    # User B creating agent in Company A -> 403 Forbidden
    b_create_resp = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/agents",
        json={"name": "Rogue Agent", "role": "Infiltrator"},
    )
    assert b_create_resp.status_code == 403
