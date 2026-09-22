"""Integration tests for Human Approval & Oversight System API endpoints and tenant isolation."""

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
        app_name="AI Company OS Approval Test",
        app_env="test",
        session_cookie_name="ai_company_session_approval_test",
        cookie_secure=False,
    )
    app = create_application(settings=settings)
    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await engine.dispose()


@pytest.mark.asyncio
async def test_approval_lifecycle_and_execution_gating(app_client: AsyncClient) -> None:
    """Verify approval creation on high-risk tool invocation, approve flow, reject flow, and isolation."""
    # 1. Register & Login User Alpha
    reg_res = await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Alpha",
            "email": "alpha@oversight.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert reg_res.status_code == 201

    login_res = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "alpha@oversight.os", "password": "Password123!"},
    )
    assert login_res.status_code == 200

    # 2. Create Company Alpha & Provision Agents
    comp_res = await app_client.post(
        "/api/v1/companies",
        json={"name": "Alpha Oversight Technologies", "industry": "Autonomous systems"},
    )
    assert comp_res.status_code == 201
    comp_id = comp_res.json()["id"]

    prov_res = await app_client.post(f"/api/v1/companies/{comp_id}/agents/provision-defaults")
    assert prov_res.status_code == 201

    agents_res = await app_client.get(f"/api/v1/companies/{comp_id}/agents")
    assert agents_res.status_code == 200
    agents = agents_res.json()
    eng_agent = next(a for a in agents if "engineer" in a["role"].lower())

    # 3. Initially verify empty approvals inbox
    inbox_res = await app_client.get(f"/api/v1/companies/{comp_id}/approvals")
    assert inbox_res.status_code == 200
    inbox_data = inbox_res.json()
    assert inbox_data["total"] == 0
    assert inbox_data["items"] == []

    # 4. Trigger High-Risk Tool Execution: github create_pr
    tool_exec_res = await app_client.post(
        f"/api/v1/companies/{comp_id}/tools/execute",
        json={
            "agent_id": eng_agent["id"],
            "tool_name": "github",
            "action": "create_pr",
            "parameters": {
                "repository": "moon90/AICompanyOS",
                "action": "create_pr",
                "branch": "release",
            },
        },
    )
    assert tool_exec_res.status_code == 200
    tool_data = tool_exec_res.json()
    assert tool_data["status"] == "APPROVAL_REQUIRED"
    assert tool_data["requires_approval"] is True
    tool_record_id = tool_data["id"]

    # 5. Check Approval Inbox: Auto-generated ApprovalRequest must be present
    inbox_res = await app_client.get(f"/api/v1/companies/{comp_id}/approvals?status=PENDING")
    assert inbox_res.status_code == 200
    inbox_data = inbox_res.json()
    assert inbox_data["total"] == 1
    approval = inbox_data["items"][0]
    approval_id = approval["id"]
    assert approval["tool_execution_id"] == tool_record_id
    assert approval["status"] == "PENDING"
    assert approval["agent_id"] == eng_agent["id"]

    # 6. GET /approvals/{approval_id} single record
    get_res = await app_client.get(f"/api/v1/companies/{comp_id}/approvals/{approval_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == approval_id

    # 7. Approve the request: POST /approvals/{approval_id}/approve
    approve_res = await app_client.post(
        f"/api/v1/companies/{comp_id}/approvals/{approval_id}/approve",
        json={"decision_reason": "Release validated and authorized."},
    )
    assert approve_res.status_code == 200
    approved_data = approve_res.json()
    assert approved_data["status"] == "APPROVED"
    assert approved_data["decision_reason"] == "Release validated and authorized."
    assert approved_data["reviewed_by_user_id"] is not None
    assert approved_data["reviewed_at"] is not None

    # Verify tool execution record resumed and transitioned to SUCCESS
    resumed_tool_res = await app_client.get(
        f"/api/v1/companies/{comp_id}/tools/executions/{tool_record_id}"
    )
    assert resumed_tool_res.status_code == 200
    assert resumed_tool_res.json()["status"] == "SUCCESS"
    assert resumed_tool_res.json()["output_data"]["repository"] == "moon90/AICompanyOS"
    assert "data" in resumed_tool_res.json()["output_data"]

    # 8. Attempting to approve again must return 409 Conflict
    reapprove_res = await app_client.post(
        f"/api/v1/companies/{comp_id}/approvals/{approval_id}/approve",
        json={"decision_reason": "Second approve attempt"},
    )
    assert reapprove_res.status_code == 409

    # 9. Test Rejection flow on second tool call
    tool_exec_res2 = await app_client.post(
        f"/api/v1/companies/{comp_id}/tools/execute",
        json={
            "agent_id": eng_agent["id"],
            "tool_name": "github",
            "action": "create_pr",
            "parameters": {
                "repository": "moon90/AICompanyOS",
                "action": "create_pr",
                "branch": "exploit",
            },
        },
    )
    assert tool_exec_res2.status_code == 200
    tool_data2 = tool_exec_res2.json()
    assert tool_data2["status"] == "APPROVAL_REQUIRED"
    tool_record_id2 = tool_data2["id"]

    inbox_res2 = await app_client.get(f"/api/v1/companies/{comp_id}/approvals?status=PENDING")
    assert inbox_res2.json()["total"] == 1
    approval_id2 = inbox_res2.json()["items"][0]["id"]

    reject_res = await app_client.post(
        f"/api/v1/companies/{comp_id}/approvals/{approval_id2}/reject",
        json={"decision_reason": "Rejected unauthorized pull request."},
    )
    assert reject_res.status_code == 200
    rejected_data = reject_res.json()
    assert rejected_data["status"] == "REJECTED"
    assert rejected_data["decision_reason"] == "Rejected unauthorized pull request."

    # Tool record must be BLOCKED
    blocked_tool_res = await app_client.get(
        f"/api/v1/companies/{comp_id}/tools/executions/{tool_record_id2}"
    )
    assert blocked_tool_res.json()["status"] == "BLOCKED"

    # 10. Multi-tenant isolation: Register User Beta
    reg_beta = await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Beta",
            "email": "beta@oversight.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert reg_beta.status_code == 201

    login_beta = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "beta@oversight.os", "password": "Password123!"},
    )
    assert login_beta.status_code == 200

    # Beta cannot list Alpha's approvals -> 403
    forbidden_list = await app_client.get(f"/api/v1/companies/{comp_id}/approvals")
    assert forbidden_list.status_code == 403

    # Beta cannot approve Alpha's approval -> 403
    forbidden_approve = await app_client.post(
        f"/api/v1/companies/{comp_id}/approvals/{approval_id}/approve",
        json={},
    )
    assert forbidden_approve.status_code == 403

    # 11. Non-existent ID -> 404
    # Switch back to Alpha
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "alpha@oversight.os", "password": "Password123!"},
    )
    not_found_res = await app_client.get(
        f"/api/v1/companies/{comp_id}/approvals/00000000-0000-0000-0000-000000000000"
    )
    assert not_found_res.status_code == 404
