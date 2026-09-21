"""Integration tests for CEO Orchestrator API endpoints and multi-company isolation."""

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
async def test_ceo_api_complete_lifecycle_and_isolation(app_client: AsyncClient) -> None:
    """Verify complete CEO context retrieval, plan generation, DAG construction, and cross-company isolation."""
    # 1. Unauthenticated requests rejected
    unauth_resp = await app_client.get("/api/v1/companies/some-id/ceo/context")
    assert unauth_resp.status_code == 401

    # 2. Register & login User A
    reg_a = await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Alpha",
            "email": "alpha@enterprise.os",
            "password": "password123!",
            "confirm_password": "password123!",
        },
    )
    assert reg_a.status_code == 201

    login_a = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "alpha@enterprise.os", "password": "password123!"},
    )
    assert login_a.status_code == 200

    # 3. Create Company A
    comp_a_res = await app_client.post(
        "/api/v1/companies",
        json={"name": "Alpha Corp", "mission": "Lead AI transformation", "industry": "Technology"},
    )
    assert comp_a_res.status_code == 201
    comp_a_id = comp_a_res.json()["id"]

    # 4. GET /context before CEO is registered
    ctx_before = await app_client.get(f"/api/v1/companies/{comp_a_id}/ceo/context")
    assert ctx_before.status_code == 200
    assert ctx_before.json()["ceo_agent"] is None
    assert ctx_before.json()["agent_count"] == 0

    # 5. POST /plan before CEO registered returns 404
    plan_err = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/ceo/plan",
        json={"objective": "Expand business internationally"},
    )
    assert plan_err.status_code == 404
    assert "No active CEO agent is registered" in plan_err.json()["detail"]

    # 6. Provision default agents (which includes CEO)
    prov_res = await app_client.post(f"/api/v1/companies/{comp_a_id}/agents/provision-defaults")
    assert prov_res.status_code == 201
    assert len(prov_res.json()) == 11

    # 7. GET /context now shows CEO and 11 agents
    ctx_after = await app_client.get(f"/api/v1/companies/{comp_a_id}/ceo/context")
    assert ctx_after.status_code == 200
    ctx_data = ctx_after.json()
    assert ctx_data["ceo_agent"] is not None
    assert ctx_data["ceo_agent"]["role"] == "Chief Executive Officer"
    assert ctx_data["agent_count"] == 11
    assert ctx_data["department_count"] >= 5

    # 8. POST /plan with valid goal
    plan_res = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/ceo/plan",
        json={
            "objective": "Research launch of product into European market",
            "requested_outcome": "Strategic evaluation and execution plan",
            "priority": "high",
            "constraints": ["No paid advertising", "Timeline: 30 days"],
            "requirements": ["Evaluate GDPR", "Identify key distribution partners"],
        },
    )
    assert plan_res.status_code == 201
    plan_data = plan_res.json()
    assert plan_data["status"] == "proposed"
    assert plan_data["priority"] == "high"
    assert len(plan_data["plan_steps"]) == 4
    assert len(plan_data["delegation_proposals"]) >= 1
    assert len(plan_data["approval_requirements"]) >= 1
    plan_id = plan_data["id"]

    # 9. GET /plans lists the created plan
    plans_list = await app_client.get(f"/api/v1/companies/{comp_a_id}/ceo/plans")
    assert plans_list.status_code == 200
    plans_arr = plans_list.json()
    assert len(plans_arr) == 1
    assert plans_arr[0]["id"] == plan_id
    assert plans_arr[0]["step_count"] == 4

    # 10. GET /plans/{plan_id} retrieves full details
    plan_detail = await app_client.get(f"/api/v1/companies/{comp_a_id}/ceo/plans/{plan_id}")
    assert plan_detail.status_code == 200
    assert plan_detail.json()["id"] == plan_id
    assert plan_detail.json()["goal"] == "Research launch of product into European market"

    # 11. Multi-Company Isolation: User B cannot access Company A's CEO endpoints
    reg_b = await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Beta",
            "email": "beta@enterprise.os",
            "password": "password123!",
            "confirm_password": "password123!",
        },
    )
    assert reg_b.status_code == 201

    login_b = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "beta@enterprise.os", "password": "password123!"},
    )
    assert login_b.status_code == 200

    # User B attempting Company A endpoints must receive 403 Forbidden
    b_ctx = await app_client.get(f"/api/v1/companies/{comp_a_id}/ceo/context")
    assert b_ctx.status_code == 403

    b_plan = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/ceo/plan",
        json={"objective": "Intrusion plan"},
    )
    assert b_plan.status_code == 403

    b_list = await app_client.get(f"/api/v1/companies/{comp_a_id}/ceo/plans")
    assert b_list.status_code == 403

    b_get = await app_client.get(f"/api/v1/companies/{comp_a_id}/ceo/plans/{plan_id}")
    assert b_get.status_code == 403
