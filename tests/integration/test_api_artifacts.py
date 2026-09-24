"""Integration tests for Documents & Artifacts API endpoints adhering to docs/Phases.md Section 22 and docs/Memory.md Section 31."""

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
async def test_artifacts_requires_auth(app_client: AsyncClient) -> None:
    """Verify unauthenticated requests to artifacts endpoints return 401."""
    resp = await app_client.get("/api/v1/companies/cmp-123/artifacts")
    assert resp.status_code == 401

    resp_post = await app_client.post(
        "/api/v1/companies/cmp-123/artifacts",
        json={"name": "Test Doc"},
    )
    assert resp_post.status_code == 401


@pytest.mark.asyncio
async def test_artifacts_lifecycle_full_flow(app_client: AsyncClient) -> None:
    """Verify end-to-end artifact creation, versioning, inspection, updates, and deletion."""
    # 1. Register and login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Artifacts Manager",
            "email": "manager@artifacts.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_resp = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "manager@artifacts.test", "password": "Password123!"},
    )
    assert login_resp.status_code == 200

    # 2. Create Company
    company_resp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Artifact Corp"},
    )
    assert company_resp.status_code == 201
    company_id = company_resp.json()["id"]

    # 3. Create Project
    proj_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/projects",
        json={"name": "Core Docs Redesign"},
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 4. Create root artifact (v1)
    create_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/artifacts",
        json={
            "name": "Phase 18 Technical Specification",
            "artifact_type": "MARKDOWN",
            "project_id": project_id,
            "content": "# Phase 18\n\nTechnical specifications for documents and artifacts.",
            "location": "docs/Phases.md",
            "change_summary": "Initial draft",
            "metadata": {"status": "DRAFT", "format": "markdown"},
        },
    )
    assert create_resp.status_code == 201
    artifact_v1 = create_resp.json()
    assert artifact_v1["name"] == "Phase 18 Technical Specification"
    assert artifact_v1["version"] == 1
    assert artifact_v1["parent_artifact_id"] is None
    assert artifact_v1["metadata"]["status"] == "DRAFT"
    art_id = artifact_v1["id"]

    # 5. List artifacts
    list_resp = await app_client.get(f"/api/v1/companies/{company_id}/artifacts")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["id"] == art_id

    # 6. Get single artifact
    get_resp = await app_client.get(f"/api/v1/companies/{company_id}/artifacts/{art_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Phase 18 Technical Specification"

    # 7. Update artifact
    patch_resp = await app_client.patch(
        f"/api/v1/companies/{company_id}/artifacts/{art_id}",
        json={
            "name": "Phase 18 Architecture Specification",
            "metadata": {"status": "IN_REVIEW"},
        },
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Phase 18 Architecture Specification"
    assert patch_resp.json()["metadata"]["status"] == "IN_REVIEW"

    # 8. Create new version (v2)
    v2_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/artifacts/{art_id}/versions",
        json={
            "content": "# Phase 18 v2\n\nApproved technical specifications.",
            "change_summary": "Approved by Architecture Board",
            "creator_name": "Lead Architect",
            "metadata": {"status": "APPROVED"},
        },
    )
    assert v2_resp.status_code == 201
    v2_data = v2_resp.json()
    assert v2_data["version"] == 2
    assert v2_data["parent_artifact_id"] == art_id
    assert v2_data["creator_name"] == "Lead Architect"
    assert v2_data["change_summary"] == "Approved by Architecture Board"

    # 9. Get lineage versions
    versions_resp = await app_client.get(
        f"/api/v1/companies/{company_id}/artifacts/{art_id}/versions"
    )
    assert versions_resp.status_code == 200
    versions = versions_resp.json()
    assert len(versions) == 2
    assert versions[0]["version"] == 1
    assert versions[1]["version"] == 2

    # 10. Delete v2
    del_resp = await app_client.delete(f"/api/v1/companies/{company_id}/artifacts/{v2_data['id']}")
    assert del_resp.status_code == 204

    # 11. Verify v2 is gone
    v2_check = await app_client.get(f"/api/v1/companies/{company_id}/artifacts/{v2_data['id']}")
    assert v2_check.status_code == 404


@pytest.mark.asyncio
async def test_artifacts_multi_tenant_isolation(app_client: AsyncClient) -> None:
    """Verify tenant isolation prevents cross-company artifact access."""
    # User 1
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "User One",
            "email": "u1@tenant.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "u1@tenant.test", "password": "Password123!"},
    )
    cmp1_resp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Tenant One Corp"},
    )
    cmp1_id = cmp1_resp.json()["id"]

    art_resp = await app_client.post(
        f"/api/v1/companies/{cmp1_id}/artifacts",
        json={"name": "Secret Roadmap", "content": "Confidential plan"},
    )
    art_id = art_resp.json()["id"]

    # User 2 in Tenant Two
    await app_client.post("/api/v1/auth/logout")
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "User Two",
            "email": "u2@tenant.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "u2@tenant.test", "password": "Password123!"},
    )

    # Attempt to access User 1's company artifact
    resp_get = await app_client.get(f"/api/v1/companies/{cmp1_id}/artifacts/{art_id}")
    assert resp_get.status_code == 403

    resp_list = await app_client.get(f"/api/v1/companies/{cmp1_id}/artifacts")
    assert resp_list.status_code == 403
