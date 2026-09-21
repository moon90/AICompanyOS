"""Integration tests for Task API endpoints, dependencies, and state transitions."""

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
async def test_task_api_complete_lifecycle(app_client: AsyncClient) -> None:
    """Verify task creation, assignment, status advancement, dependency linking, and isolation."""
    # 1. Register User A and create Company A
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Alpha",
            "email": "alpha@tasks.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "alpha@tasks.os", "password": "Password123!"},
    )
    comp_a_resp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Alpha Works"},
    )
    comp_a_id = comp_a_resp.json()["id"]

    # Provision agents
    prov_resp = await app_client.post(f"/api/v1/companies/{comp_a_id}/agents/provision-defaults")
    assert prov_resp.status_code == 201

    agents_resp = await app_client.get(f"/api/v1/companies/{comp_a_id}/agents")
    agents = agents_resp.json()
    engineer = next(a for a in agents if a["role"] == "Full Stack Engineer")

    # Create project
    proj_resp = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/projects",
        json={"name": "SaaS Platform"},
    )
    proj_id = proj_resp.json()["id"]

    # 2. Create Task 1
    t1_resp = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/tasks",
        json={
            "title": "Design Database Schema",
            "project_id": proj_id,
            "status": "CREATED",
            "priority": "high",
        },
    )
    assert t1_resp.status_code == 201
    t1_id = t1_resp.json()["id"]
    assert t1_resp.json()["status"] == "CREATED"

    # 3. Create Task 2 assigned to engineer
    t2_resp = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/tasks",
        json={
            "title": "Implement ORM Models",
            "project_id": proj_id,
            "assigned_to_agent_id": engineer["id"],
            "status": "CREATED",
        },
    )
    assert t2_resp.status_code == 201
    t2_id = t2_resp.json()["id"]
    # Should automatically advance to ASSIGNED
    assert t2_resp.json()["status"] == "ASSIGNED"
    assert t2_resp.json()["assigned_agent_name"] == engineer["name"]

    # 4. Add dependency: Task 2 depends on Task 1
    dep_resp = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/tasks/{t2_id}/dependencies",
        json={"depends_on_task_id": t1_id},
    )
    assert dep_resp.status_code == 201
    assert dep_resp.json()["depends_on_task_id"] == t1_id

    # 5. Adding circular dependency: Task 1 depends on Task 2 must fail (400)
    cycle_resp = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/tasks/{t1_id}/dependencies",
        json={"depends_on_task_id": t2_id},
    )
    assert cycle_resp.status_code == 400
    assert "Circular dependency detected" in cycle_resp.json()["detail"]

    # 6. Advance Task 1 to IN_PROGRESS, then COMPLETED
    s_resp1 = await app_client.patch(
        f"/api/v1/companies/{comp_a_id}/tasks/{t1_id}/status",
        json={"status": "READY"},
    )
    assert s_resp1.status_code == 200

    s_resp2 = await app_client.patch(
        f"/api/v1/companies/{comp_a_id}/tasks/{t1_id}/status",
        json={"status": "IN_PROGRESS"},
    )
    assert s_resp2.status_code == 200
    assert s_resp2.json()["started_at"] is not None

    s_resp3 = await app_client.patch(
        f"/api/v1/companies/{comp_a_id}/tasks/{t1_id}/status",
        json={"status": "COMPLETED", "output": "Schema approved and merged."},
    )
    assert s_resp3.status_code == 200
    assert s_resp3.json()["completed_at"] is not None

    # Check project stats updated
    proj_check = await app_client.get(f"/api/v1/companies/{comp_a_id}/projects/{proj_id}")
    assert proj_check.json()["stats"]["completed_tasks"] == 1
    assert proj_check.json()["stats"]["total_tasks"] == 2

    # 7. Remove dependency
    del_dep = await app_client.delete(
        f"/api/v1/companies/{comp_a_id}/tasks/{t2_id}/dependencies/{t1_id}"
    )
    assert del_dep.status_code == 204

    # 8. Multi-tenant isolation: User B cannot access Task 1
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Beta",
            "email": "beta@tasks.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "beta@tasks.os", "password": "Password123!"},
    )
    comp_b_resp = await app_client.post("/api/v1/companies", json={"name": "Beta Co"})
    assert comp_b_resp.status_code == 201

    unauth_task = await app_client.get(f"/api/v1/companies/{comp_a_id}/tasks/{t1_id}")
    assert unauth_task.status_code == 403
