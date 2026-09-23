"""Integration tests for Company Activity History API endpoints."""

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
async def test_activity_requires_auth(app_client: AsyncClient) -> None:
    """Verify unauthenticated requests to activity endpoint are rejected with 401."""
    resp = await app_client.get("/api/v1/companies/some-company-id/activity")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_activity_multi_tenant_isolation(app_client: AsyncClient) -> None:
    """Verify operators cannot view activity of a foreign company."""
    # Register and login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator One",
            "email": "op1@activity.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_resp = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "op1@activity.os", "password": "Password123!"},
    )
    assert login_resp.status_code == 200

    resp = await app_client.get("/api/v1/companies/unauthorized-company-id/activity")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_company_activity_with_lifecycle_events(app_client: AsyncClient) -> None:
    """Verify operational events emitted during project & task lifecycle appear in activity stream."""
    # 1. Register & Login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Audit Manager",
            "email": "manager@activity.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "manager@activity.os", "password": "Password123!"},
    )

    # 2. Create Company
    comp_resp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Timeline Corp", "description": "Operational tracking corp"},
    )
    assert comp_resp.status_code == 201
    company_id = comp_resp.json()["id"]

    # 3. Create Project
    proj_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/projects",
        json={"name": "Infrastructure Rollout", "priority": "high"},
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 4. Create Task
    task_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks",
        json={
            "project_id": project_id,
            "title": "Configure Database Pools",
            "priority": "critical",
            "status": "READY",
        },
    )
    assert task_resp.status_code == 201
    task_id = task_resp.json()["id"]

    # 5. Transition Task Status
    patch_resp = await app_client.patch(
        f"/api/v1/companies/{company_id}/tasks/{task_id}/status",
        json={"status": "IN_PROGRESS"},
    )
    assert patch_resp.status_code == 200

    # 6. Query Company Activity
    activity_resp = await app_client.get(f"/api/v1/companies/{company_id}/activity")
    assert activity_resp.status_code == 200
    data = activity_resp.json()
    assert data["total"] >= 3
    event_types = [e["event_type"] for e in data["items"]]
    assert "PROJECT_CREATED" in event_types
    assert "TASK_CREATED" in event_types
    assert "TASK_STATUS_CHANGED" in event_types

    # 7. Query Project Scoped Activity
    proj_activity_resp = await app_client.get(
        f"/api/v1/companies/{company_id}/projects/{project_id}/activity"
    )
    assert proj_activity_resp.status_code == 200
    proj_data = proj_activity_resp.json()
    assert proj_data["total"] >= 1
    for item in proj_data["items"]:
        assert item["project_id"] == project_id

    # 8. Query Task Scoped Activity
    task_activity_resp = await app_client.get(
        f"/api/v1/companies/{company_id}/tasks/{task_id}/activity"
    )
    assert task_activity_resp.status_code == 200
    task_data = task_activity_resp.json()
    assert task_data["total"] >= 2
    for item in task_data["items"]:
        assert item["task_id"] == task_id
