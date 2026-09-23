"""Integration tests for Project Kanban Board API endpoints and status transitions."""

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
async def test_get_project_board_api(app_client: AsyncClient) -> None:
    """Verify GET /api/v1/companies/{company_id}/projects/{project_id}/board returns complete board payload."""
    # 1. Register & Login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Board User",
            "email": "board.user@test.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_res = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "board.user@test.os", "password": "Password123!"},
    )
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Company & Project
    comp_res = await app_client.post(
        "/api/v1/companies",
        json={"name": "Kanban Enterprises"},
        headers=headers,
    )
    company_id = comp_res.json()["id"]

    proj_res = await app_client.post(
        f"/api/v1/companies/{company_id}/projects",
        json={
            "name": "Cloud Native Platform",
            "description": "Enterprise cloud deployment",
            "priority": "high",
        },
        headers=headers,
    )
    project_id = proj_res.json()["id"]

    # 3. Create Tasks
    await app_client.post(
        f"/api/v1/companies/{company_id}/tasks",
        json={
            "project_id": project_id,
            "title": "Design Infrastructure Architecture",
            "priority": "critical",
            "status": "READY",
        },
        headers=headers,
    )
    await app_client.post(
        f"/api/v1/companies/{company_id}/tasks",
        json={
            "project_id": project_id,
            "title": "Provision Kubernetes Cluster",
            "priority": "high",
            "status": "IN_PROGRESS",
        },
        headers=headers,
    )
    await app_client.post(
        f"/api/v1/companies/{company_id}/tasks",
        json={
            "project_id": project_id,
            "title": "Configure Cloud Firewall",
            "priority": "medium",
            "status": "BLOCKED",
        },
        headers=headers,
    )

    # 4. Fetch Board
    board_res = await app_client.get(
        f"/api/v1/companies/{company_id}/projects/{project_id}/board",
        headers=headers,
    )
    assert board_res.status_code == 200
    data = board_res.json()

    assert data["project"]["id"] == project_id
    assert data["project"]["name"] == "Cloud Native Platform"
    assert len(data["columns"]) == 7
    assert len(data["tasks"]) == 3
    assert data["summary"]["total_tasks"] == 3
    assert data["summary"]["blocked_tasks"] == 1
    assert data["summary"]["in_progress_tasks"] == 1
    assert data["summary"]["completed_tasks"] == 0

    # Verify column task count
    col_map = {c["id"]: c["task_count"] for c in data["columns"]}
    assert col_map["READY"] == 1
    assert col_map["IN_PROGRESS"] == 1
    assert col_map["BLOCKED"] == 1

    # Verify allowed transitions
    assert "READY" in data["allowed_transitions"]
    assert "IN_PROGRESS" in data["allowed_transitions"]["READY"]


@pytest.mark.asyncio
async def test_kanban_drag_drop_status_transition(app_client: AsyncClient) -> None:
    """Verify task transition triggered by drag-and-drop on the Kanban board."""
    # 1. Register & Login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator",
            "email": "operator@test.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_res = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "operator@test.os", "password": "Password123!"},
    )
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Company & Project
    comp_res = await app_client.post(
        "/api/v1/companies",
        json={"name": "Agile Dynamics"},
        headers=headers,
    )
    company_id = comp_res.json()["id"]

    proj_res = await app_client.post(
        f"/api/v1/companies/{company_id}/projects",
        json={"name": "Workflow Pipeline"},
        headers=headers,
    )
    project_id = proj_res.json()["id"]

    # 3. Create task in READY
    task_res = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks",
        json={
            "project_id": project_id,
            "title": "Process Incoming Batch",
            "status": "READY",
        },
        headers=headers,
    )
    task_id = task_res.json()["id"]

    # 4. Drag task to IN_PROGRESS: PATCH status
    advance_res = await app_client.patch(
        f"/api/v1/companies/{company_id}/tasks/{task_id}/status",
        json={"status": "IN_PROGRESS"},
        headers=headers,
    )
    assert advance_res.status_code == 200
    assert advance_res.json()["status"] == "IN_PROGRESS"
    assert advance_res.json()["started_at"] is not None

    # 5. Drag task to VERIFYING: PATCH status
    verifying_res = await app_client.patch(
        f"/api/v1/companies/{company_id}/tasks/{task_id}/status",
        json={"status": "VERIFYING"},
        headers=headers,
    )
    assert verifying_res.status_code == 200
    assert verifying_res.json()["status"] == "VERIFYING"

    # 6. Drag task to COMPLETED: PATCH status
    complete_res = await app_client.patch(
        f"/api/v1/companies/{company_id}/tasks/{task_id}/status",
        json={"status": "COMPLETED", "output": "Batch successfully processed with zero errors."},
        headers=headers,
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "COMPLETED"
    assert complete_res.json()["completed_at"] is not None
    assert complete_res.json()["output"] == "Batch successfully processed with zero errors."

    # 7. Check Board reflects COMPLETED
    board_res = await app_client.get(
        f"/api/v1/companies/{company_id}/projects/{project_id}/board",
        headers=headers,
    )
    data = board_res.json()
    assert data["summary"]["completed_tasks"] == 1
    assert data["summary"]["completion_rate"] == 100.0


@pytest.mark.asyncio
async def test_kanban_invalid_transition_rejected(app_client: AsyncClient) -> None:
    """Verify backend enforces State Machine rules and rejects invalid drag-and-drop transitions."""
    # 1. Register & Login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Strict Officer",
            "email": "strict@test.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_res = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "strict@test.os", "password": "Password123!"},
    )
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Company & Project
    comp_res = await app_client.post(
        "/api/v1/companies",
        json={"name": "Governance Corp"},
        headers=headers,
    )
    company_id = comp_res.json()["id"]

    proj_res = await app_client.post(
        f"/api/v1/companies/{company_id}/projects",
        json={"name": "Strict Protocol"},
        headers=headers,
    )
    project_id = proj_res.json()["id"]

    # 3. Create task in CREATED
    task_res = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks",
        json={
            "project_id": project_id,
            "title": "Raw Idea",
            "status": "CREATED",
        },
        headers=headers,
    )
    task_id = task_res.json()["id"]

    # 4. Attempt illegal jump from CREATED directly to COMPLETED
    illegal_res = await app_client.patch(
        f"/api/v1/companies/{company_id}/tasks/{task_id}/status",
        json={"status": "COMPLETED"},
        headers=headers,
    )
    assert illegal_res.status_code == 400
    assert "Cannot transition task from 'CREATED' to 'COMPLETED'" in illegal_res.json()["detail"]


@pytest.mark.asyncio
async def test_get_project_board_unauthenticated_and_cross_company(app_client: AsyncClient) -> None:
    """Verify security boundaries: 401 unauthenticated, 403 cross-company, 404 not found."""
    # 1. Register User 1 & Company 1
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "User One",
            "email": "user1@board.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login1 = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "user1@board.os", "password": "Password123!"},
    )
    token1 = login1.json()["token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    c1_res = await app_client.post(
        "/api/v1/companies",
        json={"name": "Company One"},
        headers=headers1,
    )
    c1_id = c1_res.json()["id"]

    p1_res = await app_client.post(
        f"/api/v1/companies/{c1_id}/projects",
        json={"name": "Project One"},
        headers=headers1,
    )
    p1_id = p1_res.json()["id"]

    # 2. Register User 2 & Company 2
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "User Two",
            "email": "user2@board.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login2 = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "user2@board.os", "password": "Password123!"},
    )
    token2 = login2.json()["token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Unauthenticated request (clear cookies first) -> 401
    app_client.cookies.clear()
    unauth_res = await app_client.get(
        f"/api/v1/companies/{c1_id}/projects/{p1_id}/board",
    )
    assert unauth_res.status_code == 401

    # Cross-company request by User 2 -> 403
    forbidden_res = await app_client.get(
        f"/api/v1/companies/{c1_id}/projects/{p1_id}/board",
        headers=headers2,
    )
    assert forbidden_res.status_code == 403

    # Non-existent project -> 404
    not_found_res = await app_client.get(
        f"/api/v1/companies/{c1_id}/projects/non-existent-id/board",
        headers=headers1,
    )
    assert not_found_res.status_code == 404
