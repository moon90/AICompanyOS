"""Unit tests for Company Decisions and Immutability Chain adhering to docs/Memory.md § 33."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.memory_service import MemoryService
from domain.memory.exceptions import (
    DecisionAlreadySupersededError,
    DecisionNotFoundError,
    MemoryAccessDeniedError,
)
from domain.memory.schemas import (
    CompanyDecisionCreate,
    CompanyDecisionFilter,
    DecisionStatus,
)
from domain.work.exceptions import ProjectNotFoundError, TaskNotFoundError
from infrastructure.database.base import Base
from infrastructure.database.models import Company, CompanyMember, Project, Task, User


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an in-memory SQLite async database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def seeded_entities(async_session: AsyncSession) -> dict[str, str]:
    """Seed test user, company, project, and task."""
    user = User(
        id=str(uuid.uuid4()),
        name="Lead Architect",
        email="architect@company.os",
        password_hash="hashed_pw",
        status="active",
    )
    unauthorized_user = User(
        id=str(uuid.uuid4()),
        name="Outsider",
        email="outsider@external.com",
        password_hash="hashed_pw",
        status="active",
    )
    company = Company(
        id=str(uuid.uuid4()),
        name="Acme Quantum",
        mission="Build quantum microservices",
        description="Pioneering enterprise AI systems",
    )
    member = CompanyMember(
        id=str(uuid.uuid4()),
        company_id=company.id,
        user_id=user.id,
        role="owner",
        status="active",
    )
    project = Project(
        id=str(uuid.uuid4()),
        company_id=company.id,
        name="Project Chronos",
        description="Temporal database engine",
        objective="Achieve sub-millisecond queries",
        status="ACTIVE",
    )
    task = Task(
        id=str(uuid.uuid4()),
        company_id=company.id,
        project_id=project.id,
        title="Design Storage Layer",
        description="Select immutable log structure",
        status="READY",
    )

    async_session.add_all([user, unauthorized_user, company, member, project, task])
    await async_session.commit()

    return {
        "user_id": user.id,
        "unauthorized_user_id": unauthorized_user.id,
        "company_id": company.id,
        "project_id": project.id,
        "task_id": task.id,
    }


@pytest.mark.asyncio
async def test_record_decision_success(
    async_session: AsyncSession,
    seeded_entities: dict[str, str],
) -> None:
    """Verify that a decision is durably recorded with ACTIVE status."""
    service = MemoryService(db=async_session)

    decision_dto = CompanyDecisionCreate(
        title="Adopt PostgreSQL for State Memory",
        decision="All state memory must reside in PostgreSQL with ACID guarantees.",
        rationale="Guarantees auditability and prevents hallucinated state.",
        evidence={"benchmarks": "pg_stat_activity", "concurrency": 1000},
        project_id=seeded_entities["project_id"],
        task_id=seeded_entities["task_id"],
    )

    created = await service.record_decision(
        company_id=seeded_entities["company_id"],
        user_id=seeded_entities["user_id"],
        data=decision_dto,
    )

    assert created.id is not None
    assert created.status == DecisionStatus.ACTIVE.value
    assert created.title == "Adopt PostgreSQL for State Memory"
    assert created.superseded_by_decision_id is None
    assert created.decided_by_user_id == seeded_entities["user_id"]
    assert created.evidence["concurrency"] == 1000


@pytest.mark.asyncio
async def test_supersede_decision_creates_audit_chain(
    async_session: AsyncSession,
    seeded_entities: dict[str, str],
) -> None:
    """Verify decision supersedence links the old decision to the new one and marks it SUPERSEDED."""
    service = MemoryService(db=async_session)

    # 1. Initial decision
    initial_dto = CompanyDecisionCreate(
        title="Database Choice V1",
        decision="Use SQLite for all environments.",
        rationale="Lightweight and file-based.",
    )
    initial_dec = await service.record_decision(
        company_id=seeded_entities["company_id"],
        user_id=seeded_entities["user_id"],
        data=initial_dto,
    )

    # 2. Superseding decision
    superseding_dto = CompanyDecisionCreate(
        title="Database Choice V2 (PostgreSQL Upgrade)",
        decision="Migrate to PostgreSQL 16 for production multi-tenant concurrency.",
        rationale="SQLite lacks multi-connection write scalability under load.",
        evidence={"scalability_report": "passed"},
    )
    new_dec = await service.supersede_decision(
        company_id=seeded_entities["company_id"],
        user_id=seeded_entities["user_id"],
        old_decision_id=initial_dec.id,
        data=superseding_dto,
    )

    # Verify new decision is ACTIVE and un-superseded
    assert new_dec.status == DecisionStatus.ACTIVE.value
    assert new_dec.superseded_by_decision_id is None
    assert new_dec.id != initial_dec.id

    # Verify old decision is now SUPERSEDED and links to new decision ID
    old_reloaded = await service.get_decision(
        company_id=seeded_entities["company_id"],
        user_id=seeded_entities["user_id"],
        decision_id=initial_dec.id,
    )
    assert old_reloaded.status == DecisionStatus.SUPERSEDED.value
    assert old_reloaded.superseded_by_decision_id == new_dec.id


@pytest.mark.asyncio
async def test_superseding_already_superseded_decision_fails(
    async_session: AsyncSession,
    seeded_entities: dict[str, str],
) -> None:
    """Verify attempting to supersede an already superseded decision raises DecisionAlreadySupersededError."""
    service = MemoryService(db=async_session)

    d1 = await service.record_decision(
        company_id=seeded_entities["company_id"],
        user_id=seeded_entities["user_id"],
        data=CompanyDecisionCreate(
            title="Arch V1",
            decision="Monolith",
            rationale="Fast start",
        ),
    )
    await service.supersede_decision(
        company_id=seeded_entities["company_id"],
        user_id=seeded_entities["user_id"],
        old_decision_id=d1.id,
        data=CompanyDecisionCreate(
            title="Arch V2",
            decision="Modular Core",
            rationale="Clean boundaries",
        ),
    )

    # Attempting to supersede V1 again should fail
    with pytest.raises(DecisionAlreadySupersededError):
        await service.supersede_decision(
            company_id=seeded_entities["company_id"],
            user_id=seeded_entities["user_id"],
            old_decision_id=d1.id,
            data=CompanyDecisionCreate(
                title="Arch V3",
                decision="Microservices",
                rationale="Scale",
            ),
        )


@pytest.mark.asyncio
async def test_record_decision_invalid_project(
    async_session: AsyncSession,
    seeded_entities: dict[str, str],
) -> None:
    """Verify linking a decision to an invalid project raises ProjectNotFoundError."""
    service = MemoryService(db=async_session)

    with pytest.raises(ProjectNotFoundError):
        await service.record_decision(
            company_id=seeded_entities["company_id"],
            user_id=seeded_entities["user_id"],
            data=CompanyDecisionCreate(
                title="Invalid Project Link",
                decision="Outcome",
                rationale="Rationale",
                project_id=str(uuid.uuid4()),
            ),
        )


@pytest.mark.asyncio
async def test_record_decision_invalid_task(
    async_session: AsyncSession,
    seeded_entities: dict[str, str],
) -> None:
    """Verify linking a decision to an invalid task raises TaskNotFoundError."""
    service = MemoryService(db=async_session)

    with pytest.raises(TaskNotFoundError):
        await service.record_decision(
            company_id=seeded_entities["company_id"],
            user_id=seeded_entities["user_id"],
            data=CompanyDecisionCreate(
                title="Invalid Task Link",
                decision="Outcome",
                rationale="Rationale",
                task_id=str(uuid.uuid4()),
            ),
        )


@pytest.mark.asyncio
async def test_decision_access_denied_for_non_member(
    async_session: AsyncSession,
    seeded_entities: dict[str, str],
) -> None:
    """Verify non-members are blocked from recording or viewing decisions."""
    service = MemoryService(db=async_session)

    with pytest.raises(MemoryAccessDeniedError):
        await service.record_decision(
            company_id=seeded_entities["company_id"],
            user_id=seeded_entities["unauthorized_user_id"],
            data=CompanyDecisionCreate(
                title="Intruder Decision",
                decision="Hacked",
                rationale="Malicious",
            ),
        )


@pytest.mark.asyncio
async def test_list_decisions_with_filter(
    async_session: AsyncSession,
    seeded_entities: dict[str, str],
) -> None:
    """Verify listing decisions supports filtering by status."""
    service = MemoryService(db=async_session)

    d1 = await service.record_decision(
        company_id=seeded_entities["company_id"],
        user_id=seeded_entities["user_id"],
        data=CompanyDecisionCreate(title="Decision 1", decision="D1", rationale="R1"),
    )
    await service.record_decision(
        company_id=seeded_entities["company_id"],
        user_id=seeded_entities["user_id"],
        data=CompanyDecisionCreate(title="Decision 2", decision="D2", rationale="R2"),
    )
    await service.supersede_decision(
        company_id=seeded_entities["company_id"],
        user_id=seeded_entities["user_id"],
        old_decision_id=d1.id,
        data=CompanyDecisionCreate(title="Decision 1B", decision="D1B", rationale="R1B"),
    )

    all_decisions = await service.list_decisions(
        company_id=seeded_entities["company_id"],
        user_id=seeded_entities["user_id"],
    )
    assert len(all_decisions) == 3

    active_decisions = await service.list_decisions(
        company_id=seeded_entities["company_id"],
        user_id=seeded_entities["user_id"],
        filter_params=CompanyDecisionFilter(status=DecisionStatus.ACTIVE),
    )
    assert len(active_decisions) == 2

    superseded_decisions = await service.list_decisions(
        company_id=seeded_entities["company_id"],
        user_id=seeded_entities["user_id"],
        filter_params=CompanyDecisionFilter(status=DecisionStatus.SUPERSEDED),
    )
    assert len(superseded_decisions) == 1
    assert superseded_decisions[0].id == d1.id


@pytest.mark.asyncio
async def test_get_decision_not_found(
    async_session: AsyncSession,
    seeded_entities: dict[str, str],
) -> None:
    """Verify querying a non-existent decision raises DecisionNotFoundError."""
    service = MemoryService(db=async_session)

    with pytest.raises(DecisionNotFoundError):
        await service.get_decision(
            company_id=seeded_entities["company_id"],
            user_id=seeded_entities["user_id"],
            decision_id=str(uuid.uuid4()),
        )
