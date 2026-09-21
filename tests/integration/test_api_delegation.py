"""Integration tests for Delegation API endpoints, plan decomposition, and tenant isolation."""

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
async def test_delegation_api_complete_lifecycle(app_client: AsyncClient) -> None:
    """Verify CEO plan delegation, task delegation, lineage retrieval, and tenant isolation."""
    # 1. Register User Alpha & Login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "CEO Alpha",
            "email": "alpha@delegation.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "alpha@delegation.os", "password": "Password123!"},
    )

    # 2. Create Company Alpha
    comp_res = await app_client.post(
        "/api/v1/companies",
        json={"name": "Delegation Alpha Corp", "mission": "Autonomous Execution"},
    )
    company_id = comp_res.json()["id"]

    # 3. Provision Default Agents
    prov_res = await app_client.post(f"/api/v1/companies/{company_id}/agents/provision-defaults")
    assert prov_res.status_code == 201
    agents = prov_res.json()
    ceo = next(
        a
        for a in agents
        if a["role"].lower() in ("ceo", "chief executive officer") or a["name"].lower() == "ceo"
    )
    cto = next(a for a in agents if a["role"] == "Chief Technology Officer")
    architect = next(a for a in agents if a["role"] == "Software Architect")

    # 4. Generate CEO Plan
    plan_res = await app_client.post(
        f"/api/v1/companies/{company_id}/ceo/plan",
        json={
            "objective": "Build and release real-time notifications engine.",
            "requested_outcome": "WebSocket gateway and pub/sub message broker.",
            "priority": "high",
        },
    )
    assert plan_res.status_code == 201
    plan_id = plan_res.json()["id"]

    # 5. Delegate CEO Plan
    delegate_plan_res = await app_client.post(
        f"/api/v1/companies/{company_id}/ceo/plans/{plan_id}/delegate",
        json={"project_name": "Notifications System"},
    )
    assert delegate_plan_res.status_code == 201
    plan_result = delegate_plan_res.json()
    assert plan_result["project_id"] is not None
    assert plan_result["parent_task_id"] is not None
    assert plan_result["child_tasks_count"] > 0
    assert plan_result["delegations_count"] > 0

    # 6. Create a standalone task and delegate it: CEO -> CTO -> Architect
    task_res = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks",
        json={
            "title": "Audit Database Connection Pooling",
            "description": "Inspect asyncpg pool limits and timeout configurations",
            "project_id": plan_result["project_id"],
        },
    )
    task_id = task_res.json()["id"]

    # Delegate to CTO
    del_res1 = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks/{task_id}/delegate",
        json={
            "target_agent_id": cto["id"],
            "delegator_agent_id": ceo["id"],
            "reason": "CTO lead oversight",
            "scope": "Infrastructure and database",
        },
    )
    assert del_res1.status_code == 201
    assert del_res1.json()["depth"] == 1
    assert del_res1.json()["delegated_to_agent_id"] == cto["id"]

    # Delegate from CTO to Software Architect
    del_res2 = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks/{task_id}/delegate",
        json={
            "target_agent_id": architect["id"],
            "delegator_agent_id": cto["id"],
            "reason": "Specialist execution",
            "scope": "Performance profiling",
        },
    )
    assert del_res2.status_code == 201
    assert del_res2.json()["depth"] == 2
    assert del_res2.json()["delegated_to_agent_id"] == architect["id"]

    # 7. Get Task Delegation Lineage
    lineage_res = await app_client.get(
        f"/api/v1/companies/{company_id}/tasks/{task_id}/delegations"
    )
    assert lineage_res.status_code == 200
    lineage = lineage_res.json()
    assert len(lineage) == 2
    assert lineage[0]["depth"] == 1
    assert lineage[1]["depth"] == 2

    # 8. List Company Delegations
    all_del_res = await app_client.get(f"/api/v1/companies/{company_id}/delegations")
    assert all_del_res.status_code == 200
    assert all_del_res.json()["total"] >= 3

    # 9. Multi-tenant isolation check: Register User Beta in Company Beta
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Beta",
            "email": "beta@delegation.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "beta@delegation.os", "password": "Password123!"},
    )
    beta_comp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Beta Corp"},
    )
    assert beta_comp.status_code == 201

    # User Beta attempting to delegate Company Alpha's task must receive 403 Forbidden
    cross_res = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks/{task_id}/delegate",
        json={
            "target_agent_id": cto["id"],
            "reason": "Cross-company breach attempt",
        },
    )
    assert cross_res.status_code == 403
