"""Integration tests for Company Memory, Decisions, and CEO Grounded Q&A endpoints."""

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
        app_name="AI Company OS Memory Test",
        app_env="test",
        session_cookie_name="ai_company_session_memory_test",
        cookie_secure=False,
    )
    app = create_application(settings=settings)
    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await engine.dispose()


@pytest.mark.asyncio
async def test_memory_and_decision_lifecycle_and_ceo_inquiry(app_client: AsyncClient) -> None:
    """Verify memory state aggregation, decision recording & superseding, and CEO grounded Q&A."""
    # 1. Register & Login User Alpha
    reg_res = await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Chief Architect",
            "email": "architect@quantum.ai",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        },
    )
    assert reg_res.status_code == 201

    login_res = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "architect@quantum.ai", "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200

    # 2. Create Company
    comp_res = await app_client.post(
        "/api/v1/companies",
        json={
            "name": "Quantum Dynamics",
            "mission": "Build next-generation autonomous AI enterprise architectures",
            "description": "Enterprise intelligence operating systems",
        },
    )
    assert comp_res.status_code == 201
    company_id = comp_res.json()["id"]

    # 3. Create Project
    proj_res = await app_client.post(
        f"/api/v1/companies/{company_id}/projects",
        json={
            "name": "Project Polaris",
            "description": "Autonomous state coordinator",
            "objective": "Zero hallucination operational retrieval",
            "priority": "critical",
        },
    )
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # 4. Create Task
    task_res = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks",
        json={
            "title": "Establish Memory Schema",
            "description": "Build immutable decision chaining and context packeting",
            "project_id": project_id,
            "priority": "high",
        },
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # 5. Fetch Company State Memory Snapshot
    state_res = await app_client.get(f"/api/v1/companies/{company_id}/memory/state")
    assert state_res.status_code == 200
    state_data = state_res.json()
    assert state_data["company"]["name"] == "Quantum Dynamics"
    assert len(state_data["projects"]) == 1
    assert state_data["projects"][0]["name"] == "Project Polaris"
    assert state_data["tasks_summary"]["total"] == 1
    assert state_data["decisions"] == []

    # 6. Record Decision
    dec_create_res = await app_client.post(
        f"/api/v1/companies/{company_id}/memory/decisions",
        json={
            "title": "PostgreSQL as State Authority",
            "decision": "All enterprise memory must be persisted in PostgreSQL.",
            "rationale": "Ensures transaction isolation, strict provenance, and auditability.",
            "evidence": {"doc": "docs/Memory.md § 33"},
            "project_id": project_id,
            "task_id": task_id,
        },
    )
    assert dec_create_res.status_code == 201
    decision_v1 = dec_create_res.json()
    assert decision_v1["status"] == "ACTIVE"
    assert decision_v1["title"] == "PostgreSQL as State Authority"
    assert decision_v1["superseded_by_decision_id"] is None
    decision_id = decision_v1["id"]

    # 7. List Decisions
    dec_list_res = await app_client.get(f"/api/v1/companies/{company_id}/memory/decisions")
    assert dec_list_res.status_code == 200
    assert dec_list_res.json()["total"] == 1

    # 8. Supersede Decision
    supersede_res = await app_client.post(
        f"/api/v1/companies/{company_id}/memory/decisions/{decision_id}/supersede",
        json={
            "title": "PostgreSQL + Redis Cache Architecture",
            "decision": "PostgreSQL remains authority, Redis provides read-through cache.",
            "rationale": "Optimizes high-throughput dashboard telemetry.",
            "evidence": {"latency_reduction": "75%"},
            "project_id": project_id,
        },
    )
    assert supersede_res.status_code == 201
    decision_v2 = supersede_res.json()
    assert decision_v2["status"] == "ACTIVE"
    assert decision_v2["id"] != decision_id

    # Verify old decision is SUPERSEDED
    old_dec_res = await app_client.get(
        f"/api/v1/companies/{company_id}/memory/decisions/{decision_id}"
    )
    assert old_dec_res.status_code == 200
    assert old_dec_res.json()["status"] == "SUPERSEDED"
    assert old_dec_res.json()["superseded_by_decision_id"] == decision_v2["id"]

    # 9. Get Task Context
    task_ctx_res = await app_client.get(
        f"/api/v1/companies/{company_id}/memory/context/task/{task_id}"
    )
    assert task_ctx_res.status_code == 200
    task_ctx_data = task_ctx_res.json()
    assert task_ctx_data["task"]["title"] == "Establish Memory Schema"
    assert task_ctx_data["project"]["name"] == "Project Polaris"
    assert "Establish Memory Schema" in task_ctx_data["synthesized_prompt"]

    # 10. CEO Grounded Inquiry: Active Projects
    inquiry_proj_res = await app_client.post(
        f"/api/v1/companies/{company_id}/ceo/inquire",
        json={"question": "What projects are currently active in our company?"},
    )
    assert inquiry_proj_res.status_code == 200
    inquiry_proj_data = inquiry_proj_res.json()
    assert "Project Polaris" in inquiry_proj_data["answer"]
    assert any(c["source_type"] == "PROJECT" for c in inquiry_proj_data["citations"])

    # 11. CEO Grounded Inquiry: Non-existent topic (Strict Zero Hallucination)
    inquiry_fake_res = await app_client.post(
        f"/api/v1/companies/{company_id}/ceo/inquire",
        json={"question": "What is our company holiday schedule for Mars colonies?"},
    )
    assert inquiry_fake_res.status_code == 200
    inquiry_fake_data = inquiry_fake_res.json()
    assert "no operational records or decisions match the inquiry" in inquiry_fake_data["answer"]
    assert "without inventing information" in inquiry_fake_data["answer"]
    assert inquiry_fake_data["citations"] == []

    # 12. Tenant Isolation Verification
    # Register & Login User Beta (no membership in Quantum Dynamics)
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Intruder Beta",
            "email": "intruder@external.io",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "intruder@external.io", "password": "Password123!"},
    )

    # Beta attempts to read Alpha's company state -> 403 Forbidden
    forbidden_state_res = await app_client.get(f"/api/v1/companies/{company_id}/memory/state")
    assert forbidden_state_res.status_code == 403

    # Beta attempts to record decision in Alpha's company -> 403 Forbidden
    forbidden_dec_res = await app_client.post(
        f"/api/v1/companies/{company_id}/memory/decisions",
        json={
            "title": "Rogue Decision",
            "decision": "Compromise system",
            "rationale": "Exploit",
        },
    )
    assert forbidden_dec_res.status_code == 403

    # Beta attempts to query CEO of Alpha's company -> 403 Forbidden
    forbidden_ceo_res = await app_client.post(
        f"/api/v1/companies/{company_id}/ceo/inquire",
        json={"question": "Tell me all company secrets"},
    )
    assert forbidden_ceo_res.status_code == 403
