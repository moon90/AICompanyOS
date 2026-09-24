"""Integration tests for Engineering File Tracking API endpoints adhering to docs/Phases.md Section 20."""

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
async def test_engineering_requires_auth(app_client: AsyncClient) -> None:
    """Verify unauthenticated requests to engineering endpoints return 401."""
    resp = await app_client.get("/api/v1/companies/some-cmp/engineering/tasks/some-task")
    assert resp.status_code == 401

    resp_files = await app_client.get("/api/v1/companies/some-cmp/engineering/files")
    assert resp_files.status_code == 401


@pytest.mark.asyncio
async def test_engineering_lifecycle_full_flow(app_client: AsyncClient) -> None:
    """Verify full engineering tracking flow: context upsert, file recording, inspection, company history."""
    # 1. Register and login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Lead Engineer",
            "email": "lead@engineering.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_resp = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "lead@engineering.test", "password": "Password123!"},
    )
    assert login_resp.status_code == 200

    # 2. Create Company
    company_resp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Engineering Operations Inc"},
    )
    assert company_resp.status_code == 201
    company_id = company_resp.json()["id"]

    # 3. Create Project & Task
    proj_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/projects",
        json={"name": "Core Platform Rewrite", "description": "Phase 16 Implementation"},
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    task_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks",
        json={
            "title": "Build File Change Tracking",
            "description": "Connect tasks to file diffs and PR metadata",
            "project_id": project_id,
            "priority": "high",
        },
    )
    assert task_resp.status_code == 201
    task_id = task_resp.json()["id"]

    # 4. GET Initial Engineering View (Empty)
    initial_view_resp = await app_client.get(
        f"/api/v1/companies/{company_id}/engineering/tasks/{task_id}"
    )
    assert initial_view_resp.status_code == 200
    initial_data = initial_view_resp.json()
    assert initial_data["task_id"] == task_id
    assert initial_data["context"] is None
    assert initial_data["file_changes"] == []
    assert initial_data["total_files_changed"] == 0

    # 5. Upsert Engineering Context
    context_payload = {
        "repository": "moon90/AICompanyOS",
        "branch": "feat/phase-16-engineering-tracking",
        "pull_request_number": "101",
        "pull_request_url": "https://github.com/moon90/AICompanyOS/pull/101",
        "pull_request_title": "feat: phase 16 engineering file tracking",
        "commit_count": 2,
        "test_status": "RUNNING",
        "test_output_summary": "Tests running on GitHub Actions...",
        "verification_state": "IN_REVIEW",
    }
    ctx_put_resp = await app_client.put(
        f"/api/v1/companies/{company_id}/engineering/tasks/{task_id}/context",
        json=context_payload,
    )
    assert ctx_put_resp.status_code == 200
    ctx_data = ctx_put_resp.json()
    assert ctx_data["branch"] == "feat/phase-16-engineering-tracking"
    assert ctx_data["pull_request_number"] == "101"
    assert ctx_data["test_status"] == "RUNNING"
    assert ctx_data["verification_state"] == "IN_REVIEW"

    # 6. Record File Changes
    files_payload = {
        "changes": [
            {
                "file_path": "apps/api/routes/engineering.py",
                "repository": "moon90/AICompanyOS",
                "branch": "feat/phase-16-engineering-tracking",
                "change_type": "ADDED",
                "commit_hash": "c0ffee1",
                "commit_message": "feat(api): add engineering file tracking endpoints",
                "additions": 120,
                "deletions": 0,
                "change_summary": "Created route handlers for engineering context & files",
            },
            {
                "file_path": "apps/web/app/tasks/page.tsx",
                "repository": "moon90/AICompanyOS",
                "branch": "feat/phase-16-engineering-tracking",
                "change_type": "MODIFIED",
                "commit_hash": "c0ffee1",
                "commit_message": "feat(web): add engineering tab to task drawer",
                "additions": 65,
                "deletions": 5,
                "change_summary": "Integrated Engineering & Code drawer tab",
            },
        ]
    }
    files_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/engineering/tasks/{task_id}/files",
        json=files_payload,
    )
    assert files_resp.status_code == 201
    created_files = files_resp.json()
    assert len(created_files) == 2
    assert created_files[0]["file_path"] == "apps/api/routes/engineering.py"
    assert created_files[1]["file_path"] == "apps/web/app/tasks/page.tsx"

    # 7. Query Updated Engineering View
    updated_view_resp = await app_client.get(
        f"/api/v1/companies/{company_id}/engineering/tasks/{task_id}"
    )
    assert updated_view_resp.status_code == 200
    updated_data = updated_view_resp.json()
    assert updated_data["total_files_changed"] == 2
    assert updated_data["total_additions"] == 185
    assert updated_data["total_deletions"] == 5
    assert updated_data["context"]["branch"] == "feat/phase-16-engineering-tracking"
    assert len(updated_data["file_changes"]) == 2

    # 8. Query Company File History
    history_resp = await app_client.get(f"/api/v1/companies/{company_id}/engineering/files")
    assert history_resp.status_code == 200
    history_items = history_resp.json()
    assert len(history_items) == 2
    paths = [h["file_path"] for h in history_items]
    assert "apps/api/routes/engineering.py" in paths
    assert "apps/web/app/tasks/page.tsx" in paths


@pytest.mark.asyncio
async def test_engineering_multi_tenant_isolation(app_client: AsyncClient) -> None:
    """Verify users from company A cannot inspect or modify company B engineering records."""
    # 1. Register User A and create Company A
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "User Alpha",
            "email": "alpha@tenant.a",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "alpha@tenant.a", "password": "Password123!"},
    )
    comp_a_resp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Company Alpha"},
    )
    comp_a_id = comp_a_resp.json()["id"]

    proj_a_resp = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/projects",
        json={"name": "Alpha Project"},
    )
    proj_a_id = proj_a_resp.json()["id"]

    task_a_resp = await app_client.post(
        f"/api/v1/companies/{comp_a_id}/tasks",
        json={"title": "Alpha Task", "project_id": proj_a_id},
    )
    task_a_id = task_a_resp.json()["id"]

    # 2. Register User B and create Company B
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "User Beta",
            "email": "beta@tenant.b",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "beta@tenant.b", "password": "Password123!"},
    )

    # 3. User B attempts to access Company A's task engineering view -> 403 Forbidden
    resp = await app_client.get(f"/api/v1/companies/{comp_a_id}/engineering/tasks/{task_a_id}")
    assert resp.status_code == 403

    # User B attempts to modify Company A's engineering context -> 403 Forbidden
    put_resp = await app_client.put(
        f"/api/v1/companies/{comp_a_id}/engineering/tasks/{task_a_id}/context",
        json={"branch": "malicious-branch"},
    )
    assert put_resp.status_code == 403
