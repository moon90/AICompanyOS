"""Unit tests for SemanticService adhering to docs/Phases.md Section 24 and docs/Memory.md Section 40."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.semantic_service import SemanticService
from domain.semantic.exceptions import (
    SemanticAccessDeniedError,
    SemanticMemoryNotFoundError,
)
from domain.semantic.schemas import (
    BatchIndexRequest,
    SemanticContextBuildRequest,
    SemanticSearchRequest,
)
from infrastructure.database.base import Base
from infrastructure.database.models import (
    Agent,
    Artifact,
    Company,
    CompanyDecision,
    CompanyKnowledge,
    CompanyMember,
    Project,
    Task,
    User,
)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated, in-memory SQLite session with all models created."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_data(db_session: AsyncSession) -> dict[str, str]:
    """Seed test company, user, project, task, decision, artifact, and knowledge items."""
    user = User(
        id="usr-sem-001",
        email="architect@company.os",
        password_hash="hashed_secret",
        name="Software Architect",
    )
    unauthorized_user = User(
        id="usr-sem-999",
        email="stranger@external.os",
        password_hash="hashed_secret",
        name="External Hacker",
    )
    company = Company(
        id="cmp-sem-001",
        name="Vector AI Systems Inc",
        status="active",
    )
    other_company = Company(
        id="cmp-sem-002",
        name="Other Corp",
        status="active",
    )
    membership = CompanyMember(
        id="mem-sem-001",
        company_id=company.id,
        user_id=user.id,
        role="owner",
        status="active",
    )
    other_membership = CompanyMember(
        id="mem-sem-002",
        company_id=other_company.id,
        user_id=unauthorized_user.id,
        role="owner",
        status="active",
    )
    project = Project(
        id="prj-sem-001",
        company_id=company.id,
        name="Autonomous Memory Core",
        status="active",
    )
    agent = Agent(
        id="agt-sem-001",
        company_id=company.id,
        name="Chief Architect",
        role="ARCHITECT",
        status="idle",
    )
    task = Task(
        id="tsk-sem-001",
        company_id=company.id,
        project_id=project.id,
        created_by_agent_id=agent.id,
        assigned_to_agent_id=agent.id,
        title="Deploy Vector Search Subsystem",
        description="Configure pgvector HNSW indexing and semantic retrieval pipelines for the company.",
        status="IN_PROGRESS",
    )
    decision = CompanyDecision(
        id="dec-sem-001",
        company_id=company.id,
        project_id=project.id,
        task_id=task.id,
        title="Standardize on pgvector with 768-dim embeddings",
        decision="Adopt pgvector on PostgreSQL 16 with 768-dim embeddings",
        rationale="HNSW indexing in PostgreSQL avoids data silos while delivering sub-millisecond retrieval.",
        status="ACTIVE",
    )
    artifact = Artifact(
        id="art-sem-001",
        company_id=company.id,
        project_id=project.id,
        task_id=task.id,
        creator_name="Lead Architect",
        name="Vector Architecture Specification",
        version=1,
        artifact_type="SPEC",
        location="docs/vector-spec.md",
        content="All company knowledge, decisions, artifacts, and tasks must be semantically searchable.",
    )
    knowledge = CompanyKnowledge(
        id="kn-sem-001",
        company_id=company.id,
        title="PostgreSQL pgvector Deployment Standard",
        content="PostgreSQL pgvector provides vector similarity search with HNSW indexes for high throughput.",
        category="PROCEDURE",
        confidence="HIGH",
        source_type="USER",
        author_name="Software Architect",
    )

    db_session.add_all(
        [
            user,
            unauthorized_user,
            company,
            other_company,
            membership,
            other_membership,
            project,
            agent,
            task,
            decision,
            artifact,
            knowledge,
        ]
    )
    await db_session.commit()

    return {
        "company_id": company.id,
        "other_company_id": other_company.id,
        "user_id": user.id,
        "unauthorized_user_id": unauthorized_user.id,
        "project_id": project.id,
        "task_id": task.id,
        "decision_id": decision.id,
        "artifact_id": artifact.id,
        "knowledge_id": knowledge.id,
    }


@pytest.mark.asyncio
async def test_index_company_knowledge(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Test batch indexing across knowledge, decisions, artifacts, and tasks."""
    service = SemanticService(db_session)
    request = BatchIndexRequest(force_reindex=True)

    response = await service.index_company_knowledge(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=request,
    )

    assert response.company_id == test_data["company_id"]
    assert response.indexed_count >= 4  # Knowledge, Decision, Artifact, Task
    assert response.duration_ms >= 0.0

    # Query vector stats to verify persisted embeddings
    stats = await service.get_vector_stats(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
    )
    assert stats.total_embeddings >= 4
    assert stats.dimension == 768
    assert "KNOWLEDGE" in stats.count_by_source
    assert "DECISION" in stats.count_by_source
    assert "ARTIFACT" in stats.count_by_source
    assert "TASK" in stats.count_by_source


@pytest.mark.asyncio
async def test_semantic_search_retrieval(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test semantic search retrieval with relevance ranking and filters."""
    service = SemanticService(db_session)
    # First index the company
    await service.index_company_knowledge(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=BatchIndexRequest(force_reindex=True),
    )

    # Search for pgvector architectural info
    search_req = SemanticSearchRequest(
        query="PostgreSQL pgvector HNSW indexing deployment",
        limit=5,
        min_similarity=-1.0,
    )
    search_resp = await service.search_semantic(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=search_req,
    )

    assert search_resp.total_matches > 0
    top_match = search_resp.results[0]
    assert top_match.similarity_score > 0.0
    assert len(top_match.content_chunk) > 0


@pytest.mark.asyncio
async def test_semantic_search_source_type_filter(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test semantic search filtering strictly by source type."""
    service = SemanticService(db_session)
    await service.index_company_knowledge(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=BatchIndexRequest(force_reindex=True),
    )

    # Filter only DECISION
    search_req = SemanticSearchRequest(
        query="standardize on embeddings",
        source_types=["DECISION"],
        limit=5,
    )
    response = await service.search_semantic(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=search_req,
    )

    for item in response.results:
        assert item.source_type == "DECISION"


@pytest.mark.asyncio
async def test_build_semantic_context(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Test synthesizing selective bounded context for agent execution."""
    service = SemanticService(db_session)
    await service.index_company_knowledge(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=BatchIndexRequest(force_reindex=True),
    )

    context_req = SemanticContextBuildRequest(
        query="How should the agent implement vector search in PostgreSQL?",
        limit=3,
        min_similarity=-1.0,
    )
    context_resp = await service.build_semantic_context(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=context_req,
    )

    assert context_resp.company_id == test_data["company_id"]
    assert "### Semantic Company Context" in context_resp.synthesized_context
    assert len(context_resp.items_used) > 0


@pytest.mark.asyncio
async def test_build_semantic_context_no_matches(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test bounded context when no matching vectors meet minimum similarity."""
    service = SemanticService(db_session)

    context_req = SemanticContextBuildRequest(
        query="completely unmatched non-existent query",
        limit=3,
        min_similarity=0.9999,  # Impossibly high threshold
    )
    context_resp = await service.build_semantic_context(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=context_req,
    )

    assert context_resp.total_items == 0
    assert (
        "No semantic knowledge chunks exceeded the relevance threshold"
        in context_resp.synthesized_context
    )


@pytest.mark.asyncio
async def test_access_denied_isolation(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Test multi-tenant isolation prevents unauthorized company access."""
    service = SemanticService(db_session)

    with pytest.raises(SemanticAccessDeniedError):
        await service.get_vector_stats(
            company_id=test_data["company_id"],
            user_id=test_data["unauthorized_user_id"],
        )

    with pytest.raises(SemanticAccessDeniedError):
        await service.search_semantic(
            company_id=test_data["company_id"],
            user_id=test_data["unauthorized_user_id"],
            request=SemanticSearchRequest(query="test"),
        )


@pytest.mark.asyncio
async def test_vector_stats_company_not_found(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test get_vector_stats on non-existent company raises SemanticMemoryNotFoundError."""
    service = SemanticService(db_session)

    with pytest.raises(SemanticMemoryNotFoundError):
        await service.get_vector_stats(
            company_id="cmp-non-existent",
            user_id=test_data["user_id"],
        )
