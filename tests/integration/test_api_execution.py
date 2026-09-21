"""Integration tests for Agent Execution API endpoints, state transitions, and tenant isolation."""

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
async def test_agent_execution_complete_lifecycle(app_client: AsyncClient) -> None:
    """Verify executing a task transitions state to VERIFYING, stores deliverable, and enforces isolation."""
    # 1. Register and Login User Alpha
    reg_res = await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Alpha",
            "email": "alpha@executor.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert reg_res.status_code == 201

    login_res = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "alpha@executor.os", "password": "Password123!"},
    )
    assert login_res.status_code == 200

    # 2. Create Company & Provision Agents
    comp_res = await app_client.post(
        "/api/v1/companies",
        json={"name": "Alpha Autonomous Systems", "industry": "Enterprise Software"},
    )
    assert comp_res.status_code == 201
    company_id = comp_res.json()["id"]

    prov_res = await app_client.post(f"/api/v1/companies/{company_id}/agents/provision-defaults")
    assert prov_res.status_code == 201

    agents_res = await app_client.get(f"/api/v1/companies/{company_id}/agents")
    assert agents_res.status_code == 200
    agents = agents_res.json()
    backend_agent = next(
        a for a in agents if "backend" in a["role"].lower() or "engineer" in a["role"].lower()
    )

    # 3. Create Project & Assigned Task
    proj_res = await app_client.post(
        f"/api/v1/companies/{company_id}/projects",
        json={"name": "API Gateway Modernization", "priority": "high"},
    )
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    task_res = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks",
        json={
            "title": "Implement rate limiting middleware",
            "objective": "Prevent brute force attacks using sliding window algorithm",
            "description": "Create FastAPI dependency checking token rate limits with Redis.",
            "project_id": project_id,
            "assigned_to_agent_id": backend_agent["id"],
            "priority": "high",
        },
    )
    assert task_res.status_code == 201
    task = task_res.json()
    assert task["status"] == "ASSIGNED"

    # 4. Trigger Agent Task Execution
    exec_res = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks/{task['id']}/execute",
        json={"max_steps": 4, "max_duration_seconds": 30},
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "SUCCESS"
    assert exec_data["task_id"] == task["id"]
    assert exec_data["agent_id"] == backend_agent["id"]
    assert exec_data["duration_ms"] > 0
    assert exec_data["step_count"] > 0
    assert exec_data["deliverable"] is not None
    assert len(exec_data["steps_json"]) > 0
    execution_id = exec_data["id"]

    # 5. Verify Task State advanced to VERIFYING (Phase 8 Golden Rule)
    reloaded_task_res = await app_client.get(f"/api/v1/companies/{company_id}/tasks/{task['id']}")
    assert reloaded_task_res.status_code == 200
    reloaded_task = reloaded_task_res.json()
    assert reloaded_task["status"] == "VERIFYING"
    assert reloaded_task["output"] == exec_data["deliverable"]

    # 6. Verify Execution History
    history_res = await app_client.get(
        f"/api/v1/companies/{company_id}/tasks/{task['id']}/executions"
    )
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert history_data["total"] == 1
    assert history_data["items"][0]["id"] == execution_id

    # 7. Verify Get Individual Execution
    single_res = await app_client.get(f"/api/v1/companies/{company_id}/executions/{execution_id}")
    assert single_res.status_code == 200
    assert single_res.json()["id"] == execution_id

    # 8. Verify Tenant Isolation with User Beta
    # Register & Login Beta
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Beta",
            "email": "beta@executor.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "beta@executor.os", "password": "Password123!"},
    )

    # Beta attempts to execute Alpha's task -> 403 Forbidden
    forbidden_exec = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks/{task['id']}/execute",
        json={},
    )
    assert forbidden_exec.status_code == 403

    # Beta attempts to list Alpha's executions -> 403 Forbidden
    forbidden_history = await app_client.get(
        f"/api/v1/companies/{company_id}/tasks/{task['id']}/executions"
    )
    assert forbidden_history.status_code == 403
