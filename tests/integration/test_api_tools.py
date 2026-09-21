"""Integration tests for Tool Gateway API endpoints, audit logging, and tenant isolation."""

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
        app_name="AI Company OS Tool Test",
        app_env="test",
        session_cookie_name="ai_company_session_tool_test",
        cookie_secure=False,
    )
    app = create_application(settings=settings)
    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await engine.dispose()


@pytest.mark.asyncio
async def test_tool_gateway_endpoints_and_isolation(app_client: AsyncClient) -> None:
    """Verify tool listing, execution, approval interception, and multi-tenant isolation."""
    # 1. Register and Login User Alpha
    reg_res = await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Alpha",
            "email": "alpha@toolgate.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert reg_res.status_code == 201

    login_res = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "alpha@toolgate.os", "password": "Password123!"},
    )
    assert login_res.status_code == 200

    # 2. Create Company Alpha & Provision Agents
    comp_res = await app_client.post(
        "/api/v1/companies",
        json={"name": "Alpha Tool Technologies", "industry": "Testing tools"},
    )
    assert comp_res.status_code == 201
    comp_alpha_id = comp_res.json()["id"]

    prov_res = await app_client.post(f"/api/v1/companies/{comp_alpha_id}/agents/provision-defaults")
    assert prov_res.status_code == 201

    agents_res = await app_client.get(f"/api/v1/companies/{comp_alpha_id}/agents")
    assert agents_res.status_code == 200
    agents = agents_res.json()
    eng_agent = next(
        a for a in agents if "engineer" in a["role"].lower() or "backend" in a["role"].lower()
    )

    # 3. Test GET /tools
    tools_res = await app_client.get(f"/api/v1/companies/{comp_alpha_id}/tools")
    assert tools_res.status_code == 200
    tools_data = tools_res.json()
    assert tools_data["total"] == 3
    tool_names = [t["name"] for t in tools_data["items"]]
    assert "web_search" in tool_names
    assert "documents" in tool_names
    assert "github" in tool_names

    # 4. Test GET /tools with role filtering
    filtered_res = await app_client.get(
        f"/api/v1/companies/{comp_alpha_id}/tools?role=hr_specialist"
    )
    assert filtered_res.status_code == 200
    filtered_names = [t["name"] for t in filtered_res.json()["items"]]
    assert "github" not in filtered_names

    # 5. Test GET /tools/definitions/{tool_name}
    doc_def = await app_client.get(f"/api/v1/companies/{comp_alpha_id}/tools/definitions/documents")
    assert doc_def.status_code == 200
    assert doc_def.json()["name"] == "documents"

    not_found = await app_client.get(
        f"/api/v1/companies/{comp_alpha_id}/tools/definitions/ghost_tool"
    )
    assert not_found.status_code == 404

    # 6. Test POST /tools/execute (web_search)
    exec_res = await app_client.post(
        f"/api/v1/companies/{comp_alpha_id}/tools/execute",
        json={
            "agent_id": eng_agent["id"],
            "tool_name": "web_search",
            "action": "search",
            "parameters": {"query": "system architecture patterns"},
        },
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "SUCCESS"
    assert exec_data["tool_name"] == "web_search"
    assert exec_data["risk_level"] == "LOW"
    assert exec_data["requires_approval"] is False
    assert "results" in exec_data["output_data"]
    execution_id = exec_data["id"]

    # 7. Test POST /tools/execute (Approval Interception for HIGH risk action)
    approval_res = await app_client.post(
        f"/api/v1/companies/{comp_alpha_id}/tools/execute",
        json={
            "agent_id": eng_agent["id"],
            "tool_name": "github",
            "action": "create_pr",
            "parameters": {
                "repository": "moon90/AICompanyOS",
                "action": "create_pr",
                "branch": "main",
            },
        },
    )
    assert approval_res.status_code == 200
    approval_data = approval_res.json()
    assert approval_data["status"] == "APPROVAL_REQUIRED"
    assert approval_data["requires_approval"] is True
    assert "requires human operator approval" in approval_data["error_details"]

    # 8. Test Schema Validation Error (missing query)
    val_res = await app_client.post(
        f"/api/v1/companies/{comp_alpha_id}/tools/execute",
        json={
            "agent_id": eng_agent["id"],
            "tool_name": "web_search",
            "action": "search",
            "parameters": {},
        },
    )
    assert val_res.status_code == 422

    # 9. Test GET /tools/executions
    logs_res = await app_client.get(f"/api/v1/companies/{comp_alpha_id}/tools/executions")
    assert logs_res.status_code == 200
    logs_data = logs_res.json()
    assert logs_data["total"] >= 2

    # 10. Test GET /tools/executions/{execution_id}
    single_res = await app_client.get(
        f"/api/v1/companies/{comp_alpha_id}/tools/executions/{execution_id}"
    )
    assert single_res.status_code == 200
    assert single_res.json()["id"] == execution_id

    # 11. Multi-Tenant Company Isolation: User Beta cannot access Company Alpha's tools
    reg_beta = await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Operator Beta",
            "email": "beta@toolgate.os",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert reg_beta.status_code == 201

    login_beta = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "beta@toolgate.os", "password": "Password123!"},
    )
    assert login_beta.status_code == 200

    # Attempt cross-company access
    cross_res = await app_client.get(f"/api/v1/companies/{comp_alpha_id}/tools")
    assert cross_res.status_code == 403

    cross_exec = await app_client.post(
        f"/api/v1/companies/{comp_alpha_id}/tools/execute",
        json={
            "agent_id": eng_agent["id"],
            "tool_name": "web_search",
            "action": "search",
            "parameters": {"query": "hack"},
        },
    )
    assert cross_exec.status_code == 403
