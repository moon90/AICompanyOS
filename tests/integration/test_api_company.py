"""Integration tests for Company and Organization API endpoints."""

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

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    await engine.dispose()


@pytest.mark.asyncio
async def test_company_api_complete_lifecycle_and_isolation(app_client: AsyncClient) -> None:
    """Verify complete HTTP company creation, departments inspection, and multi-tenant isolation."""
    # 1. Unauthenticated /api/v1/companies returns 401
    resp = await app_client.get("/api/v1/companies")
    assert resp.status_code == 401

    # 2. Register & login User A (Alice)
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Alice Founder",
            "email": "alice@company.os",
            "password": "alice-secure-password-1",
            "confirm_password": "alice-secure-password-1",
        },
    )
    login_resp = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@company.os", "password": "alice-secure-password-1"},
    )
    assert login_resp.status_code == 200

    # 3. User A creates Company A
    comp_payload = {
        "name": "Alpha Autonomous Labs",
        "description": "AI systems laboratory",
        "mission": "Automate company operating loops",
        "industry": "Artificial Intelligence",
    }
    create_resp = await app_client.post("/api/v1/companies", json=comp_payload)
    assert create_resp.status_code == 201
    company_a = create_resp.json()
    company_a_id = company_a["id"]
    assert company_a["name"] == "Alpha Autonomous Labs"
    assert company_a["user_role"] == "owner"

    # 4. User A retrieves company list
    list_resp = await app_client.get("/api/v1/companies")
    assert list_resp.status_code == 200
    companies_list = list_resp.json()
    assert len(companies_list) == 1
    assert companies_list[0]["id"] == company_a_id

    # 5. User A retrieves departments (should have 5 initial departments)
    dept_resp = await app_client.get(f"/api/v1/companies/{company_a_id}/departments")
    assert dept_resp.status_code == 200
    departments = dept_resp.json()
    assert len(departments) == 5
    dept_codes = {d["code"] for d in departments}
    assert dept_codes == {"cto", "cmo", "sales", "finance", "operations"}

    # 6. User A creates custom department
    new_dept_payload = {
        "name": "Product & Design",
        "code": "product",
        "lead_role": "Head of Product",
        "description": "Product strategy and UI/UX design",
    }
    custom_dept_resp = await app_client.post(
        f"/api/v1/companies/{company_a_id}/departments", json=new_dept_payload
    )
    assert custom_dept_resp.status_code == 201
    assert custom_dept_resp.json()["code"] == "product"

    # 7. User A retrieves members
    members_resp = await app_client.get(f"/api/v1/companies/{company_a_id}/members")
    assert members_resp.status_code == 200
    members = members_resp.json()
    assert len(members) == 1
    assert members[0]["user_email"] == "alice@company.os"
    assert members[0]["role"] == "owner"

    # 8. User A logs out
    await app_client.post("/api/v1/auth/logout")

    # 9. Register & login User B (Bob)
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Bob External",
            "email": "bob@other.os",
            "password": "bob-secure-password-2",
            "confirm_password": "bob-secure-password-2",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@other.os", "password": "bob-secure-password-2"},
    )

    # 10. User B lists companies -> empty list (isolation enforced)
    bob_list_resp = await app_client.get("/api/v1/companies")
    assert bob_list_resp.status_code == 200
    assert len(bob_list_resp.json()) == 0

    # 11. User B attempts to access Company A directly -> 403 Forbidden
    bob_get_resp = await app_client.get(f"/api/v1/companies/{company_a_id}")
    assert bob_get_resp.status_code == 403

    # 12. User B attempts to list Company A departments -> 403 Forbidden
    bob_dept_resp = await app_client.get(f"/api/v1/companies/{company_a_id}/departments")
    assert bob_dept_resp.status_code == 403

    # 13. User B attempts to create department in Company A -> 403 Forbidden
    bob_create_dept_resp = await app_client.post(
        f"/api/v1/companies/{company_a_id}/departments",
        json={"name": "Hacker Dept", "code": "hack"},
    )
    assert bob_create_dept_resp.status_code == 403
