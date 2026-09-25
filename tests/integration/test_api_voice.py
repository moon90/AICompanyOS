"""Integration tests for Voice Interface API endpoints adhering to docs/Phases.md Section 25 and docs/Memory.md Section 60."""

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
async def test_voice_requires_auth(app_client: AsyncClient) -> None:
    """Verify unauthenticated requests to voice endpoints return 401."""
    resp_sess = await app_client.get("/api/v1/companies/cmp-123/voice/sessions")
    assert resp_sess.status_code == 401

    resp_cmd = await app_client.post(
        "/api/v1/companies/cmp-123/voice/command",
        json={"transcript": "CEO, what's happening?"},
    )
    assert resp_cmd.status_code == 401

    resp_synth = await app_client.post(
        "/api/v1/companies/cmp-123/voice/synthesize",
        json={"text": "System ready."},
    )
    assert resp_synth.status_code == 401

    resp_telem = await app_client.get("/api/v1/companies/cmp-123/voice/telemetry")
    assert resp_telem.status_code == 401


@pytest.mark.asyncio
async def test_voice_session_and_command_lifecycle(app_client: AsyncClient) -> None:
    """Verify end-to-end voice session creation, execution of Section 25 commands, and telemetry."""
    # 1. Register and login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Voice Commander",
            "email": "commander@voice.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_resp = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "commander@voice.test", "password": "Password123!"},
    )
    assert login_resp.status_code == 200

    # 2. Create Company & Project
    comp_resp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Aether Dynamics", "description": "Autonomous voice control"},
    )
    assert comp_resp.status_code == 201
    company_id = comp_resp.json()["id"]

    proj_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/projects",
        json={"name": "Voice Core", "description": "Core interface"},
    )
    assert proj_resp.status_code == 201

    # 3. Create Voice Session
    create_sess_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/voice/sessions",
        json={"title": "Executive Voice Console"},
    )
    assert create_sess_resp.status_code == 201
    session_data = create_sess_resp.json()
    session_id = session_data["id"]
    assert session_data["title"] == "Executive Voice Console"
    assert session_data["state"] == "IDLE"

    # 4. List Voice Sessions
    list_sess_resp = await app_client.get(f"/api/v1/companies/{company_id}/voice/sessions")
    assert list_sess_resp.status_code == 200
    assert list_sess_resp.json()["total"] >= 1

    # 5. Execute Section 25 status briefing command: "CEO, what's happening?"
    cmd_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/voice/command",
        json={
            "session_id": session_id,
            "transcript": "CEO, what's happening?",
        },
    )
    assert cmd_resp.status_code == 200
    cmd_data = cmd_resp.json()
    assert cmd_data["intent"] == "STATUS_QUERY"
    assert cmd_data["state"] == "SPEAKING"
    assert "active projects" in cmd_data["spoken_response"].lower()
    assert cmd_data["action_taken"] == "FETCH_EXECUTIVE_BRIEFING"

    # 6. Execute task creation voice command: "Ask marketing to draft release notes"
    create_task_cmd = await app_client.post(
        f"/api/v1/companies/{company_id}/voice/command",
        json={
            "session_id": session_id,
            "transcript": "Ask marketing to draft release notes",
        },
    )
    assert create_task_cmd.status_code == 200
    task_cmd_data = create_task_cmd.json()
    assert task_cmd_data["action_taken"] == "CREATE_TASK"
    assert task_cmd_data["action_entity_id"] is not None
    created_task_id = task_cmd_data["action_entity_id"]

    # Verify task in task endpoint
    get_task_resp = await app_client.get(f"/api/v1/companies/{company_id}/tasks/{created_task_id}")
    assert get_task_resp.status_code == 200
    assert "draft release notes" in get_task_resp.json()["title"].lower()

    # 7. Execute task control voice command: "Stop the task"
    stop_cmd = await app_client.post(
        f"/api/v1/companies/{company_id}/voice/command",
        json={
            "session_id": session_id,
            "transcript": "Stop the task",
            "context_task_id": created_task_id,
        },
    )
    assert stop_cmd.status_code == 200
    assert stop_cmd.json()["action_taken"] == "STOP_TASK"

    # Verify task cancelled
    get_stopped_task = await app_client.get(
        f"/api/v1/companies/{company_id}/tasks/{created_task_id}"
    )
    assert get_stopped_task.json()["status"] == "CANCELLED"

    # 8. Test synthesize endpoint
    synth_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/voice/synthesize",
        json={"text": "Task has been stopped successfully."},
    )
    assert synth_resp.status_code == 200
    assert synth_resp.json()["audio_format"] == "browser-tts/pcm"

    # 9. Test telemetry endpoint
    telem_resp = await app_client.get(f"/api/v1/companies/{company_id}/voice/telemetry")
    assert telem_resp.status_code == 200
    telem_data = telem_resp.json()
    assert telem_data["total_sessions"] >= 1
    assert telem_data["total_interactions"] >= 3


@pytest.mark.asyncio
async def test_voice_tenant_isolation(app_client: AsyncClient) -> None:
    """Verify tenant isolation prevents cross-company voice access."""
    # User 1 registers and creates Company 1
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Tenant One",
            "email": "t1@voice.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "t1@voice.test", "password": "Password123!"},
    )
    c1_resp = await app_client.post("/api/v1/companies", json={"name": "Company One"})
    c1_id = c1_resp.json()["id"]

    # User 2 registers and creates Company 2
    await app_client.post("/api/v1/auth/logout")
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Tenant Two",
            "email": "t2@voice.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "t2@voice.test", "password": "Password123!"},
    )

    # User 2 attempts to send voice command to Company 1
    illegal_cmd = await app_client.post(
        f"/api/v1/companies/{c1_id}/voice/command",
        json={"transcript": "CEO, what's happening?"},
    )
    assert illegal_cmd.status_code == 403
