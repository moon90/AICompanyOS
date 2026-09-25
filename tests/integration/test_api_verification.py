"""Integration tests for Verification & AI Evaluation API endpoints adhering to docs/Phases.md Section 26, docs/Architecture.md Section 71, and docs/Rules.md Section 17."""

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
async def test_verification_requires_auth(app_client: AsyncClient) -> None:
    """Verify unauthenticated requests to verification endpoints return 401."""
    resp_task = await app_client.post("/api/v1/companies/cmp-123/verification/verify/task/tsk-123")
    assert resp_task.status_code == 401

    resp_art = await app_client.post(
        "/api/v1/companies/cmp-123/verification/verify/artifact/art-123"
    )
    assert resp_art.status_code == 401

    resp_bench = await app_client.post(
        "/api/v1/companies/cmp-123/verification/benchmarks/run", json={}
    )
    assert resp_bench.status_code == 401

    resp_runs = await app_client.get("/api/v1/companies/cmp-123/verification/runs")
    assert resp_runs.status_code == 401

    resp_telem = await app_client.get("/api/v1/companies/cmp-123/verification/telemetry")
    assert resp_telem.status_code == 401


@pytest.mark.asyncio
async def test_verification_lifecycle(app_client: AsyncClient) -> None:
    """Verify full verification lifecycle: task verification, benchmark suite run, and telemetry."""
    # 1. Register & Login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Verification Admin",
            "email": "admin@eval.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_resp = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@eval.test", "password": "Password123!"},
    )
    assert login_resp.status_code == 200

    # 2. Create Company & Project & Task
    comp_resp = await app_client.post(
        "/api/v1/companies",
        json={
            "name": "Synthetica AI Labs",
            "description": "Verification and evaluation operations",
        },
    )
    assert comp_resp.status_code == 201
    company_id = comp_resp.json()["id"]

    proj_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/projects",
        json={"name": "Benchmark Harness", "description": "Continuous evaluation harness"},
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    task_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks",
        json={
            "project_id": project_id,
            "title": "Validate Distributed Consensus Algorithm",
            "description": "Run Raft consensus simulation under 30% node churn.",
            "priority": "HIGH",
        },
    )
    assert task_resp.status_code == 201
    task_id = task_resp.json()["id"]

    # 3. Verify Task
    vrf_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/verification/verify/task/{task_id}"
    )
    assert vrf_resp.status_code == 201
    vrf_data = vrf_resp.json()
    assert vrf_data["target_type"] == "TASK"
    assert vrf_data["target_id"] == task_id
    assert vrf_data["pipeline_stage"] == "COMPLETED"
    assert len(vrf_data["criterion_scores"]) == 8
    run_id = vrf_data["id"]

    # 4. Get Verification Run Detail
    run_detail_resp = await app_client.get(
        f"/api/v1/companies/{company_id}/verification/runs/{run_id}"
    )
    assert run_detail_resp.status_code == 200
    assert run_detail_resp.json()["id"] == run_id

    # 5. Run Representative Benchmark Suite (CEO)
    bench_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/verification/benchmarks/run",
        json={"category": "CEO"},
    )
    assert bench_resp.status_code == 200
    bench_data = bench_resp.json()
    assert bench_data["category"] == "CEO"
    assert bench_data["passed"] is True

    # 6. List Benchmark Suites
    list_bench_resp = await app_client.get(
        f"/api/v1/companies/{company_id}/verification/benchmarks"
    )
    assert list_bench_resp.status_code == 200
    bench_list = list_bench_resp.json()
    assert len(bench_list) == 8

    # 7. List Verification Runs
    runs_resp = await app_client.get(f"/api/v1/companies/{company_id}/verification/runs")
    assert runs_resp.status_code == 200
    assert runs_resp.json()["total"] >= 2

    # 8. Check Telemetry
    telem_resp = await app_client.get(f"/api/v1/companies/{company_id}/verification/telemetry")
    assert telem_resp.status_code == 200
    telem_data = telem_resp.json()
    assert telem_data["total_runs"] >= 2
    assert telem_data["avg_overall_score"] > 0.0


@pytest.mark.asyncio
async def test_verification_tenant_isolation(app_client: AsyncClient) -> None:
    """Verify tenant isolation blocks cross-company verification operations."""
    # Tenant 1 registers and creates company 1
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Tenant One",
            "email": "t1@eval.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "t1@eval.test", "password": "Password123!"},
    )
    c1_resp = await app_client.post("/api/v1/companies", json={"name": "Company One"})
    c1_id = c1_resp.json()["id"]

    # Tenant 2 registers
    await app_client.post("/api/v1/auth/logout")
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Tenant Two",
            "email": "t2@eval.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "t2@eval.test", "password": "Password123!"},
    )

    # Tenant 2 attempts to query Tenant 1's verification runs
    illegal_resp = await app_client.get(f"/api/v1/companies/{c1_id}/verification/runs")
    assert illegal_resp.status_code == 403
