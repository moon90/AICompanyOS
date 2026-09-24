"""Unit tests for KnowledgeService adhering to docs/Phases.md Section 23 and docs/Memory.md Sections 31-39."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.knowledge_service import KnowledgeService
from domain.artifacts.exceptions import ArtifactNotFoundError
from domain.knowledge.exceptions import (
    KnowledgeAccessDeniedError,
    KnowledgeNotFoundError,
)
from domain.knowledge.schemas import (
    KnowledgeCategory,
    KnowledgeConfidence,
    KnowledgeCreatePayload,
    KnowledgeQueryRequest,
    KnowledgeSourceType,
    KnowledgeUpdatePayload,
    SelectiveContextRequest,
)
from domain.memory.exceptions import DecisionNotFoundError
from domain.work.exceptions import ProjectNotFoundError, TaskNotFoundError
from infrastructure.database.base import Base
from infrastructure.database.models import (
    ActivityEvent,
    Agent,
    Artifact,
    Company,
    CompanyDecision,
    CompanyMember,
    ExecutionRecord,
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
    """Seed test company, user, project, task, decision, and artifact."""
    user = User(
        id="usr-kn-001",
        email="lead@company.os",
        name="Lead Architect",
        password_hash="hash",
    )
    db_session.add(user)

    company = Company(
        id="cmp-kn-001",
        name="Knowledge Corp",
        status="active",
    )
    db_session.add(company)

    other_company = Company(
        id="cmp-kn-other",
        name="Other Corp",
        status="active",
    )
    db_session.add(other_company)

    member = CompanyMember(
        id="mem-kn-001",
        company_id=company.id,
        user_id=user.id,
        role="owner",
        status="active",
    )
    db_session.add(member)

    agent = Agent(
        id="agt-kn-001",
        company_id=company.id,
        name="Researcher Agent",
        role="Research Assistant",
        status="idle",
    )
    db_session.add(agent)

    project = Project(
        id="prj-kn-001",
        company_id=company.id,
        name="Vector Architecture",
        status="active",
    )
    db_session.add(project)

    task = Task(
        id="tsk-kn-001",
        company_id=company.id,
        project_id=project.id,
        title="Benchmark Embedding Models",
        status="IN_PROGRESS",
    )
    db_session.add(task)

    decision = CompanyDecision(
        id="dec-kn-001",
        company_id=company.id,
        project_id=project.id,
        task_id=task.id,
        title="Vector DB Selection",
        decision="Adopt pgvector on PostgreSQL 16",
        rationale="Eliminates extra infrastructure footprint while providing sub-50ms latency.",
        status="ACTIVE",
    )
    db_session.add(decision)

    artifact = Artifact(
        id="art-kn-001",
        company_id=company.id,
        project_id=project.id,
        task_id=task.id,
        creator_name="Lead Architect",
        name="Benchmark Report",
        artifact_type="REPORT",
        version=1,
        location="docs/benchmarks.md",
        content="# Benchmarks\npgvector vs Qdrant vs Milvus.",
    )
    db_session.add(artifact)

    execution = ExecutionRecord(
        id="exec-kn-001",
        company_id=company.id,
        task_id=task.id,
        agent_id=agent.id,
        status="SUCCESS",
        step_count=5,
        duration_ms=4200,
        result_summary="Successfully completed pgvector load benchmarks.",
    )
    db_session.add(execution)

    await db_session.commit()

    return {
        "company_id": company.id,
        "other_company_id": other_company.id,
        "user_id": user.id,
        "project_id": project.id,
        "task_id": task.id,
        "decision_id": decision.id,
        "artifact_id": artifact.id,
        "execution_id": execution.id,
    }


@pytest.mark.asyncio
async def test_create_knowledge_item_success(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    service = KnowledgeService(db_session)
    payload = KnowledgeCreatePayload(
        title="Microservices Boundary Guidelines",
        category=KnowledgeCategory.POLICY,
        content="All service communications must be synchronous HTTP or transactional events.",
        project_id=test_data["project_id"],
        task_id=test_data["task_id"],
        decision_id=test_data["decision_id"],
        artifact_id=test_data["artifact_id"],
        source_type=KnowledgeSourceType.RESEARCH,
        confidence=KnowledgeConfidence.HIGH,
        tags=["architecture", "guidelines"],
        metadata={"review_cycle": "quarterly"},
    )

    item = await service.create_knowledge_item(
        company_id=test_data["company_id"],
        payload=payload,
        user_id=test_data["user_id"],
    )

    assert item.id is not None
    assert item.company_id == test_data["company_id"]
    assert item.title == "Microservices Boundary Guidelines"
    assert item.category == "POLICY"
    assert item.project_id == test_data["project_id"]
    assert item.decision_id == test_data["decision_id"]
    assert item.tags == ["architecture", "guidelines"]
    assert item.metadata == {"review_cycle": "quarterly"}

    # Verify activity event logged
    ev_res = await db_session.execute(
        select(ActivityEvent).where(
            ActivityEvent.company_id == test_data["company_id"],
            ActivityEvent.event_type == "knowledge.created",
        )
    )
    event = ev_res.scalar_one_or_none()
    assert event is not None
    assert "Microservices Boundary Guidelines" in event.message


@pytest.mark.asyncio
async def test_create_knowledge_validation_errors(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    service = KnowledgeService(db_session)

    # 1. Non-member access denied
    with pytest.raises(KnowledgeAccessDeniedError):
        await service.create_knowledge_item(
            company_id=test_data["other_company_id"],
            payload=KnowledgeCreatePayload(title="T", content="C"),
            user_id=test_data["user_id"],
        )

    # 2. Non-existent project
    with pytest.raises(ProjectNotFoundError):
        await service.create_knowledge_item(
            company_id=test_data["company_id"],
            payload=KnowledgeCreatePayload(title="T", content="C", project_id="non-existent"),
            user_id=test_data["user_id"],
        )

    # 3. Non-existent task
    with pytest.raises(TaskNotFoundError):
        await service.create_knowledge_item(
            company_id=test_data["company_id"],
            payload=KnowledgeCreatePayload(title="T", content="C", task_id="non-existent"),
            user_id=test_data["user_id"],
        )

    # 4. Non-existent decision
    with pytest.raises(DecisionNotFoundError):
        await service.create_knowledge_item(
            company_id=test_data["company_id"],
            payload=KnowledgeCreatePayload(title="T", content="C", decision_id="non-existent"),
            user_id=test_data["user_id"],
        )

    # 5. Non-existent artifact
    with pytest.raises(ArtifactNotFoundError):
        await service.create_knowledge_item(
            company_id=test_data["company_id"],
            payload=KnowledgeCreatePayload(title="T", content="C", artifact_id="non-existent"),
            user_id=test_data["user_id"],
        )


@pytest.mark.asyncio
async def test_get_and_list_knowledge_items(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    service = KnowledgeService(db_session)

    item1 = await service.create_knowledge_item(
        company_id=test_data["company_id"],
        payload=KnowledgeCreatePayload(
            title="Postgres Indexing Strategies",
            category=KnowledgeCategory.PROCEDURE,
            content="Use BRIN for time series and HNSW for vector search.",
        ),
        user_id=test_data["user_id"],
    )

    item2 = await service.create_knowledge_item(
        company_id=test_data["company_id"],
        payload=KnowledgeCreatePayload(
            title="Q3 Security Protocol",
            category=KnowledgeCategory.POLICY,
            content="Enforce strict TLS 1.3 across internal gateways.",
        ),
        user_id=test_data["user_id"],
    )

    # Get single item
    fetched = await service.get_knowledge_item(
        company_id=test_data["company_id"],
        item_id=item1.id,
        user_id=test_data["user_id"],
    )
    assert fetched.id == item1.id
    assert fetched.title == "Postgres Indexing Strategies"

    # Cross-tenant get fails
    with pytest.raises(KnowledgeAccessDeniedError):
        await service.get_knowledge_item(
            company_id=test_data["other_company_id"],
            item_id=item1.id,
        )

    # Non-existent item
    with pytest.raises(KnowledgeNotFoundError):
        await service.get_knowledge_item(
            company_id=test_data["company_id"],
            item_id="missing-id",
            user_id=test_data["user_id"],
        )

    # List all
    all_items = await service.list_knowledge_items(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
    )
    assert all_items.total == 2
    assert len(all_items.items) == 2

    # Filter by category
    filtered = await service.list_knowledge_items(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        category="POLICY",
    )
    assert filtered.total == 1
    assert filtered.items[0].id == item2.id

    # Search filter
    search_res = await service.list_knowledge_items(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        search="HNSW",
    )
    assert search_res.total == 1
    assert search_res.items[0].id == item1.id


@pytest.mark.asyncio
async def test_update_and_delete_knowledge_item(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    service = KnowledgeService(db_session)

    item = await service.create_knowledge_item(
        company_id=test_data["company_id"],
        payload=KnowledgeCreatePayload(
            title="Initial Draft Policy",
            category=KnowledgeCategory.POLICY,
            content="Initial thoughts.",
        ),
        user_id=test_data["user_id"],
    )

    # Update item
    updated = await service.update_knowledge_item(
        company_id=test_data["company_id"],
        item_id=item.id,
        payload=KnowledgeUpdatePayload(
            title="Finalized Security Policy",
            content="Mandatory 2FA across all administrative accounts.",
            confidence=KnowledgeConfidence.HIGH,
        ),
        user_id=test_data["user_id"],
    )
    assert updated.title == "Finalized Security Policy"
    assert "Mandatory 2FA" in updated.content

    # Delete item
    await service.delete_knowledge_item(
        company_id=test_data["company_id"],
        item_id=item.id,
        user_id=test_data["user_id"],
    )

    # Confirm deletion
    with pytest.raises(KnowledgeNotFoundError):
        await service.get_knowledge_item(
            company_id=test_data["company_id"],
            item_id=item.id,
            user_id=test_data["user_id"],
        )


@pytest.mark.asyncio
async def test_canonical_knowledge_inquiries(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify Section 23 canonical questions are answered with grounded citations."""
    service = KnowledgeService(db_session)

    # Seed supporting knowledge
    await service.create_knowledge_item(
        company_id=test_data["company_id"],
        payload=KnowledgeCreatePayload(
            title="pgvector Benchmark Findings",
            category=KnowledgeCategory.RESEARCH,
            content="pgvector handles 10M embeddings with HNSW indexing at 28ms query response.",
            source_type=KnowledgeSourceType.RESEARCH,
            confidence=KnowledgeConfidence.HIGH,
        ),
        user_id=test_data["user_id"],
    )

    await service.create_knowledge_item(
        company_id=test_data["company_id"],
        payload=KnowledgeCreatePayload(
            title="Deployment Run Post-Mortem",
            category=KnowledgeCategory.HISTORICAL_RESULT,
            content="Previous rollout completed with zero downtime and 4.2s benchmark duration.",
            source_type=KnowledgeSourceType.POST_MORTEM,
            confidence=KnowledgeConfidence.HIGH,
        ),
        user_id=test_data["user_id"],
    )

    # Canonical Question 1: "Why did we make this decision?"
    q1_resp = await service.query_knowledge(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=KnowledgeQueryRequest(question="Why did we make this decision?"),
    )
    assert q1_resp.canonical_topic == "Why did we make this decision?"
    assert len(q1_resp.citations) >= 1
    assert any(c.source_type == "DECISION" for c in q1_resp.citations)
    assert "pgvector" in q1_resp.answer

    # Canonical Question 2: "What research supports it?"
    q2_resp = await service.query_knowledge(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=KnowledgeQueryRequest(question="What research supports it?"),
    )
    assert q2_resp.canonical_topic == "What research supports it?"
    assert len(q2_resp.citations) >= 1
    assert "Benchmark" in q2_resp.answer

    # Canonical Question 3: "What happened last time?"
    q3_resp = await service.query_knowledge(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=KnowledgeQueryRequest(question="What happened last time?"),
    )
    assert q3_resp.canonical_topic == "What happened last time?"
    assert len(q3_resp.citations) >= 1
    assert "Execution" in q3_resp.answer or "Post-Mortem" in q3_resp.answer

    # Canonical Question 4: "Which projects depend on this decision?"
    q4_resp = await service.query_knowledge(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=KnowledgeQueryRequest(question="Which projects depend on this decision?"),
    )
    assert q4_resp.canonical_topic == "Which projects depend on this decision?"
    assert len(q4_resp.citations) >= 1
    assert "Vector Architecture" in q4_resp.answer or "Decision" in q4_resp.answer

    # Canonical Question 5: "Which documents contain relevant information?"
    q5_resp = await service.query_knowledge(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=KnowledgeQueryRequest(question="Which documents contain relevant information?"),
    )
    assert q5_resp.canonical_topic == "Which documents contain relevant information?"
    assert len(q5_resp.citations) >= 1
    assert any(c.source_type == "ARTIFACT" for c in q5_resp.citations)


@pytest.mark.asyncio
async def test_get_selective_context_acceptance_criteria(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify Section 23 Acceptance Criteria:
    'Agents can retrieve relevant historical company context without loading the entire database.'
    """
    service = KnowledgeService(db_session)

    # Seed 5 knowledge entries
    for i in range(5):
        await service.create_knowledge_item(
            company_id=test_data["company_id"],
            payload=KnowledgeCreatePayload(
                title=f"Architecture Note {i}",
                category=KnowledgeCategory.STRATEGY,
                content=f"Guideline detail number {i} regarding database queries and indexing.",
                project_id=test_data["project_id"],
            ),
            user_id=test_data["user_id"],
        )

    # Request selective context bounded to project and keywords
    resp = await service.get_selective_context(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=SelectiveContextRequest(
            project_id=test_data["project_id"],
            task_id=test_data["task_id"],
            intent_keywords=["indexing", "database"],
            max_items=3,
        ),
    )

    assert resp.company_id == test_data["company_id"]
    assert resp.project is not None
    assert resp.project["name"] == "Vector Architecture"
    assert resp.task is not None
    assert resp.task["title"] == "Benchmark Embedding Models"
    assert len(resp.relevant_decisions) >= 1
    assert len(resp.relevant_knowledge) <= 3
    assert len(resp.relevant_artifacts) >= 1
    assert len(resp.historical_results_summary) >= 1
    assert "### Selective Company Knowledge & Precedents" in resp.synthesized_context
    assert resp.item_count > 0
