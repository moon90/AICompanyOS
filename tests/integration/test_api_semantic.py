"""Integration tests for Semantic / Vector Memory API endpoints adhering to docs/Phases.md Section 24 and docs/Memory.md Section 40."""

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
async def test_semantic_requires_auth(app_client: AsyncClient) -> None:
    """Verify unauthenticated requests to semantic memory endpoints return 401."""
    resp_stats = await app_client.get("/api/v1/companies/cmp-123/semantic/stats")
    assert resp_stats.status_code == 401

    resp_search = await app_client.post(
        "/api/v1/companies/cmp-123/semantic/search",
        json={"query": "test inquiry"},
    )
    assert resp_search.status_code == 401

    resp_ctx = await app_client.post(
        "/api/v1/companies/cmp-123/semantic/context",
        json={"query": "test prompt"},
    )
    assert resp_ctx.status_code == 401

    resp_index = await app_client.post(
        "/api/v1/companies/cmp-123/semantic/index",
        json={},
    )
    assert resp_index.status_code == 401


@pytest.mark.asyncio
async def test_semantic_lifecycle_and_retrieval(app_client: AsyncClient) -> None:
    """Verify end-to-end vector indexing, stats, semantic search, and context generation."""
    # 1. Register & login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Vector Lead",
            "email": "lead@vector.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_resp = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "lead@vector.test", "password": "Password123!"},
    )
    assert login_resp.status_code == 200

    # 2. Create Company
    comp_resp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Hyperion Vector Labs", "description": "AI Operations"},
    )
    assert comp_resp.status_code == 201
    company_id = comp_resp.json()["id"]

    # 3. Create Project & Task
    proj_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/projects",
        json={"name": "Semantic Gateway", "description": "Vector indexing gateway"},
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    task_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks",
        json={
            "project_id": project_id,
            "title": "Calibrate HNSW Cosine Index",
            "description": "Configure m=16 and ef_construction=64 for high accuracy cosine search.",
            "priority": "HIGH",
        },
    )
    assert task_resp.status_code == 201

    # 4. Create Knowledge Item
    kn_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/knowledge",
        json={
            "title": "pgvector Cosine Operations",
            "content": "Using the <=> cosine distance operator allows PostgreSQL to execute sub-millisecond similarity scans.",
            "category": "PROCEDURE",
            "confidence": "HIGH",
        },
    )
    assert kn_resp.status_code == 201

    # 5. Index memory
    index_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/semantic/index",
        json={"force_reindex": True},
    )
    assert index_resp.status_code == 200
    index_data = index_resp.json()
    assert index_data["company_id"] == company_id
    assert index_data["indexed_count"] >= 2  # Task + Knowledge

    # 6. Retrieve vector stats
    stats_resp = await app_client.get(f"/api/v1/companies/{company_id}/semantic/stats")
    assert stats_resp.status_code == 200
    stats_data = stats_resp.json()
    assert stats_data["total_embeddings"] >= 2
    assert stats_data["dimension"] == 768
    assert stats_data["index_type"] in ("HNSW", "Exact Cosine Scan")

    # 7. Perform Semantic Search
    search_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/semantic/search",
        json={
            "query": "How does cosine similarity operator work in pgvector?",
            "limit": 5,
            "min_similarity": -1.0,
        },
    )
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total_matches"] > 0
    assert len(search_data["results"]) > 0
    assert "similarity_score" in search_data["results"][0]

    # 8. Build Agent Semantic Context
    context_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/semantic/context",
        json={
            "query": "Configure database indexing for fast cosine search",
            "limit": 3,
            "min_similarity": -1.0,
        },
    )
    assert context_resp.status_code == 200
    context_data = context_resp.json()
    assert "### Semantic Company Context" in context_data["synthesized_context"]
    assert context_data["total_items"] > 0


@pytest.mark.asyncio
async def test_semantic_multi_tenant_isolation(app_client: AsyncClient) -> None:
    """Verify unauthorized users cannot access another company's semantic memory."""
    # 1. Register user A and company A
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Owner A",
            "email": "userA@semantic.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "userA@semantic.test", "password": "Password123!"},
    )
    comp_a_resp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Company Alpha", "description": "First Company"},
    )
    company_a_id = comp_a_resp.json()["id"]

    # 2. Register user B
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Owner B",
            "email": "userB@semantic.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    await app_client.post(
        "/api/v1/auth/login",
        json={"email": "userB@semantic.test", "password": "Password123!"},
    )

    # 3. User B tries to search or get stats of Company A -> 403 Forbidden
    resp_stats = await app_client.get(f"/api/v1/companies/{company_a_id}/semantic/stats")
    assert resp_stats.status_code == 403

    resp_search = await app_client.post(
        f"/api/v1/companies/{company_a_id}/semantic/search",
        json={"query": "test inquiry"},
    )
    assert resp_search.status_code == 403

    resp_ctx = await app_client.post(
        f"/api/v1/companies/{company_a_id}/semantic/context",
        json={"query": "test query"},
    )
    assert resp_ctx.status_code == 403

    resp_index = await app_client.post(
        f"/api/v1/companies/{company_a_id}/semantic/index",
        json={},
    )
    assert resp_index.status_code == 403
