"""Integration tests for Company Knowledge API endpoints adhering to docs/Phases.md Section 23 and docs/Memory.md Sections 31-39."""

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
async def test_knowledge_requires_auth(app_client: AsyncClient) -> None:
    """Verify unauthenticated requests to knowledge endpoints return 401."""
    resp = await app_client.get("/api/v1/companies/cmp-123/knowledge")
    assert resp.status_code == 401

    resp_post = await app_client.post(
        "/api/v1/companies/cmp-123/knowledge",
        json={"title": "Unauthorized Note", "content": "Sample"},
    )
    assert resp_post.status_code == 401

    resp_query = await app_client.post(
        "/api/v1/companies/cmp-123/knowledge/query",
        json={"question": "Why did we make this decision?"},
    )
    assert resp_query.status_code == 401

    resp_ctx = await app_client.post(
        "/api/v1/companies/cmp-123/knowledge/context",
        json={},
    )
    assert resp_ctx.status_code == 401


@pytest.mark.asyncio
async def test_knowledge_lifecycle_and_inquiries(app_client: AsyncClient) -> None:
    """Verify end-to-end knowledge CRUD, canonical inquiries, and selective context synthesis."""
    # 1. Register and login
    await app_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Knowledge Lead",
            "email": "lead@knowledge.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_resp = await app_client.post(
        "/api/v1/auth/login",
        json={"email": "lead@knowledge.test", "password": "Password123!"},
    )
    assert login_resp.status_code == 200

    # 2. Create Company
    comp_resp = await app_client.post(
        "/api/v1/companies",
        json={"name": "Quantum Knowledge Corp", "description": "AI Operations"},
    )
    assert comp_resp.status_code == 201
    company_id = comp_resp.json()["id"]

    # 3. Create Project & Task
    proj_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/projects",
        json={"name": "Knowledge Graph Engine", "description": "Enterprise graph pipeline"},
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    task_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/tasks",
        json={
            "project_id": project_id,
            "title": "Construct Entity Resolution Model",
            "description": "Evaluate spaCy vs HuggingFace models.",
            "priority": "HIGH",
        },
    )
    assert task_resp.status_code == 201
    task_id = task_resp.json()["id"]

    # 4. Create Decision
    dec_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/memory/decisions",
        json={
            "title": "Entity Linking Approach",
            "decision": "Use fine-tuned modern BERT embedding with cosine similarity",
            "rationale": "Superior accuracy in disambiguating homonyms in company context.",
            "project_id": project_id,
            "task_id": task_id,
        },
    )
    assert dec_resp.status_code == 201
    decision_id = dec_resp.json()["id"]

    # 5. Create Artifact
    art_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/artifacts",
        json={
            "name": "Entity Benchmark Report",
            "artifact_type": "REPORT",
            "project_id": project_id,
            "task_id": task_id,
            "location": "docs/entity_eval.md",
            "content": "# Evaluation Summary\nBERT achieved 94.2% F1 score.",
        },
    )
    assert art_resp.status_code == 201
    artifact_id = art_resp.json()["id"]

    # 6. Create Knowledge Records
    k1_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/knowledge",
        json={
            "title": "Entity Resolution Standard",
            "category": "STRATEGY",
            "content": "All pipelines must standardize on 768-dim embeddings.",
            "project_id": project_id,
            "task_id": task_id,
            "decision_id": decision_id,
            "artifact_id": artifact_id,
            "source_type": "RESEARCH",
            "confidence": "HIGH",
            "tags": ["ml", "nlp", "standards"],
            "metadata": {"approved_by": "Architect Council"},
        },
    )
    assert k1_resp.status_code == 201
    k1 = k1_resp.json()
    assert k1["title"] == "Entity Resolution Standard"
    assert k1["category"] == "STRATEGY"
    assert k1["decision_id"] == decision_id
    knowledge_id = k1["id"]

    k2_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/knowledge",
        json={
            "title": "Model Serving Latency Policy",
            "category": "POLICY",
            "content": "Inference latency must remain below 40ms p95.",
            "confidence": "HIGH",
        },
    )
    assert k2_resp.status_code == 201

    # 7. Get single knowledge item
    get_resp = await app_client.get(f"/api/v1/companies/{company_id}/knowledge/{knowledge_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == knowledge_id

    # 8. List knowledge items
    list_resp = await app_client.get(f"/api/v1/companies/{company_id}/knowledge")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 2

    # Filter by category
    filter_resp = await app_client.get(f"/api/v1/companies/{company_id}/knowledge?category=POLICY")
    assert filter_resp.status_code == 200
    assert filter_resp.json()["total"] == 1
    assert filter_resp.json()["items"][0]["title"] == "Model Serving Latency Policy"

    # Search
    search_resp = await app_client.get(f"/api/v1/companies/{company_id}/knowledge?search=768-dim")
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] == 1
    assert search_resp.json()["items"][0]["id"] == knowledge_id

    # 9. Update knowledge item
    update_resp = await app_client.put(
        f"/api/v1/companies/{company_id}/knowledge/{knowledge_id}",
        json={
            "title": "Entity Resolution Standard v2",
            "content": "All pipelines must standardize on 768-dim embeddings with normalized vectors.",
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Entity Resolution Standard v2"

    # 10. Canonical Questions Testing
    q_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/knowledge/query",
        json={"question": "Why did we make this decision?"},
    )
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert q_data["canonical_topic"] == "Why did we make this decision?"
    assert len(q_data["citations"]) >= 1
    assert "BERT" in q_data["answer"] or "Entity Linking" in q_data["answer"]

    q_doc_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/knowledge/query",
        json={"question": "Which documents contain relevant information?"},
    )
    assert q_doc_resp.status_code == 200
    doc_data = q_doc_resp.json()
    assert doc_data["canonical_topic"] == "Which documents contain relevant information?"
    assert len(doc_data["citations"]) >= 1

    # 11. Selective Context Synthesis (Section 23 Acceptance Criteria)
    ctx_resp = await app_client.post(
        f"/api/v1/companies/{company_id}/knowledge/context",
        json={
            "project_id": project_id,
            "task_id": task_id,
            "intent_keywords": ["BERT", "embedding", "latency"],
            "max_items": 5,
        },
    )
    assert ctx_resp.status_code == 200
    ctx_data = ctx_resp.json()
    assert ctx_data["company_id"] == company_id
    assert ctx_data["project"]["name"] == "Knowledge Graph Engine"
    assert ctx_data["task"]["title"] == "Construct Entity Resolution Model"
    assert len(ctx_data["relevant_decisions"]) >= 1
    assert len(ctx_data["relevant_knowledge"]) >= 1
    assert "Selective Company Knowledge" in ctx_data["synthesized_context"]

    # 12. Delete knowledge item
    del_resp = await app_client.delete(f"/api/v1/companies/{company_id}/knowledge/{knowledge_id}")
    assert del_resp.status_code == 204

    # Confirm 404 after delete
    get_del = await app_client.get(f"/api/v1/companies/{company_id}/knowledge/{knowledge_id}")
    assert get_del.status_code == 404
