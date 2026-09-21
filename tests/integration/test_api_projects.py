"""Integration tests for Project API endpoints and multi-company isolation."""

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
async def test_project_api_lifecycle_and_isolation(app_client: AsyncClient) -> None:
    """Verify project creation, retrieval, update, deletion, and cross-company isolation."""
    # 1. Register User A and create Company A
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "User Alpha",
            "email": "alpha@projects.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "alpha@projects.os", "password": "Password123!"},
    )
    comp_a_resp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Alpha Technologies"},
    )
    assert comp_a_resp.status_code == 201
    comp_a_id = comp_a_resp.json()["id"]

    # 2. Create Project in Company A
    proj_resp = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/projects",
        json={
            "name": "Cloud Migration",
            "description": "Migrate on-prem services to AWS",
            "objective": "Zero downtime cloud shift",
            "priority": "high",
        },
    )
    assert proj_resp.status_code == 201
    proj_data = proj_resp.json()
    assert proj_data["name"] == "Cloud Migration"
    assert proj_data["status"] == "PLANNED"
    assert proj_data["priority"] == "high"
    assert proj_data["stats"]["total_tasks"] == 0
    proj_id = proj_data["id"]

    # 3. List Projects
    list_resp = await app_client.get(f"/api/v1/companies/{comp_a_id}/projects")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["id"] == proj_id

    # 4. Update Project
    patch_resp = await app_client.patch(
        f"/api/v1/companies/{comp_a_id}/projects/{proj_id}",
        json={"status": "ACTIVE", "priority": "critical"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "ACTIVE"
    assert patch_resp.json()["priority"] == "critical"

    # 5. Register User B and Company B
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "User Beta",
            "email": "beta@projects.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "beta@projects.os", "password": "Password123!"},
    )
    comp_b_resp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Beta Enterprises"},
    )
    assert comp_b_resp.status_code == 201

    # User B cannot access Company A's projects
    unauth_list = await app_client.get(f"/api/v1/companies/{comp_a_id}/projects")
    assert unauth_list.status_code == 403

    unauth_detail = await app_client.get(f"/api/v1/companies/{comp_a_id}/projects/{proj_id}")
    assert unauth_detail.status_code == 403

    # 6. Log back in as User A and delete project
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "alpha@projects.os", "password": "Password123!"},
    )
    del_resp = await app_client.delete(f"/api/v1/companies/{comp_a_id}/projects/{proj_id}")
    assert del_resp.status_code == 204

    # Verify deleted
    get_del = await app_client.get(f"/api/v1/companies/{comp_a_id}/projects/{proj_id}")
    assert get_del.status_code == 404
