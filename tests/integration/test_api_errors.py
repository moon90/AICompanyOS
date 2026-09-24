"""Integration tests for Error & Bug Management API endpoints adhering to docs/Phases.md Section 19."""

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
async def test_errors_requires_auth(app_client: AsyncClient) -> None:
    """Verify unauthenticated requests to error endpoints return 401."""
    resp = await app_client.get("/api/v1/companies/some-company-id/errors")
    assert resp.status_code == 401

    resp_summary = await app_client.get("/api/v1/companies/some-company-id/errors/summary")
    assert resp_summary.status_code == 401


@pytest.mark.asyncio
async def test_errors_multi_tenant_isolation(app_client: AsyncClient) -> None:
    """Verify users from company A cannot access errors in company B."""
    # Register & Login User 1
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "User One",
            "email": "user1@errors.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "user1@errors.test", "password": "Password123!"},
    )
    c1_res = await app_client.post(
        "/api/v1/companies",
        json={"name": "Company One", "mission": "First company"},
    )
    c1_id = c1_res.json()["id"]

    # Register & Login User 2
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "User Two",
            "email": "user2@errors.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "user2@errors.test", "password": "Password123!"},
    )

    # User 2 attempts to list or create errors in Company 1 -> 403 Forbidden
    resp = await app_client.get(f"/api/v1/companies/{c1_id}/errors")
    assert resp.status_code == 403

    create_resp = await app_client.post(
        f"/api/v1/companies/{c1_id}/errors",
        json={"title": "Hacked Error", "detected_by": "Attacker"},
    )
    assert create_resp.status_code == 403


@pytest.mark.asyncio
async def test_errors_full_lifecycle(app_client: AsyncClient) -> None:
    """Verify full error lifecycle: create -> assign -> investigate -> resolve -> verify -> reopen -> close."""
    # 1. Register & login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Bug Admin",
            "email": "admin@errors.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@errors.test", "password": "Password123!"},
    )
    c_res = await app_client.post(
        "/api/v1/companies",
        json={"name": "Software Corp", "mission": "Build quality systems"},
    )
    company_id = c_res.json()["id"]

    # 2. Record Error
    create_res = await app_client.post(
        f"/api/v1/companies/{company_id}/errors",
        json={
            "title": "Unhandled 500 in task checkout",
            "description": "Stripe webhook failed with invalid token",
            "severity": "CRITICAL",
            "detected_by": "Payment Monitor",
            "evidence": {"log_snippet": "WebhookSignatureVerificationError"},
        },
    )
    assert create_res.status_code == 201
    error = create_res.json()
    error_id = error["id"]
    assert error["status"] == "OPEN"
    assert error["severity"] == "CRITICAL"
    assert error["detected_by"] == "Payment Monitor"

    # 3. Check Summary
    sum_res = await app_client.get(f"/api/v1/companies/{company_id}/errors/summary")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["total_errors"] == 1
    assert sum_data["critical_count"] == 1
    assert sum_data["open_count"] == 1

    # 4. Assign Error
    assign_res = await app_client.post(
        f"/api/v1/companies/{company_id}/errors/{error_id}/assign",
        json={"assigned_to": "Billing Agent"},
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "ASSIGNED"
    assert assign_res.json()["assigned_to"] == "Billing Agent"

    # 5. Start Investigation
    inv_res = await app_client.post(
        f"/api/v1/companies/{company_id}/errors/{error_id}/investigate?investigated_by=Billing%20Agent"
    )
    assert inv_res.status_code == 200
    assert inv_res.json()["status"] == "INVESTIGATING"
    assert inv_res.json()["investigated_by"] == "Billing Agent"

    # 6. Resolve Error
    resolve_res = await app_client.post(
        f"/api/v1/companies/{company_id}/errors/{error_id}/resolve",
        json={
            "resolved_by": "Billing Agent",
            "root_cause": "Stripe secret key expired on rotating schedule",
            "resolution": "Updated secret in environment vault and rotated signing secret",
            "evidence": {"vault_version": "v3"},
        },
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"
    assert resolve_res.json()["root_cause"] == "Stripe secret key expired on rotating schedule"
    assert resolve_res.json()["resolved_at"] is not None

    # 7. Verify Error
    verify_res = await app_client.post(
        f"/api/v1/companies/{company_id}/errors/{error_id}/verify",
        json={
            "verified_by": "QA Auditor",
            "evidence": {"test_webhook_status": "200_OK"},
            "close_immediately": False,
        },
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "VERIFIED"
    assert verify_res.json()["verified_by"] == "QA Auditor"
    assert verify_res.json()["verified_at"] is not None

    # 8. Reopen Error
    reopen_res = await app_client.post(
        f"/api/v1/companies/{company_id}/errors/{error_id}/reopen",
        json={"reason": "Intermittent failure observed in stage environment"},
    )
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "REOPENED"
    assert reopen_res.json()["resolved_at"] is None

    # 9. Close Error
    close_res = await app_client.post(f"/api/v1/companies/{company_id}/errors/{error_id}/close")
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "CLOSED"

    # 10. List Errors
    list_res = await app_client.get(f"/api/v1/companies/{company_id}/errors")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["id"] == error_id
