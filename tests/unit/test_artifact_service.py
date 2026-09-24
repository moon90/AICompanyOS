"""Unit tests for ArtifactService adhering to docs/Phases.md Section 22 and docs/Memory.md Section 31."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.artifact_service import ArtifactService
from domain.artifacts.exceptions import (
    ArtifactAccessDeniedError,
    ArtifactNotFoundError,
)
from domain.artifacts.schemas import (
    ArtifactCreatePayload,
    ArtifactType,
    ArtifactUpdatePayload,
    ArtifactVersionCreatePayload,
)
from domain.work.exceptions import ProjectNotFoundError, TaskNotFoundError
from infrastructure.database.base import Base
from infrastructure.database.models import (
    ActivityEvent,
    Agent,
    Company,
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
    """Seed test company, user, agent, project, and task."""
    user = User(
        id="usr-art-001",
        email="operator@test.os",
        name="Lead Operator",
        password_hash="hash",
    )
    db_session.add(user)

    company = Company(
        id="cmp-art-001",
        name="Artifacts Test Corp",
        status="active",
    )
    db_session.add(company)

    member = CompanyMember(
        id="mem-art-001",
        company_id=company.id,
        user_id=user.id,
        role="owner",
        status="active",
    )
    db_session.add(member)

    agent = Agent(
        id="agt-art-001",
        company_id=company.id,
        name="Architect Agent",
        role="System Architect",
        status="idle",
    )
    db_session.add(agent)

    project = Project(
        id="prj-art-001",
        company_id=company.id,
        name="AI Infrastructure Revamp",
        status="active",
    )
    db_session.add(project)

    task = Task(
        id="tsk-art-001",
        company_id=company.id,
        project_id=project.id,
        title="Draft Architectural Specs",
        status="IN_PROGRESS",
    )
    db_session.add(task)

    await db_session.commit()

    return {
        "company_id": company.id,
        "user_id": user.id,
        "agent_id": agent.id,
        "project_id": project.id,
        "task_id": task.id,
    }


@pytest.mark.asyncio
async def test_create_artifact_success(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    service = ArtifactService(db_session)
    payload = ArtifactCreatePayload(
        name="System Architecture Document",
        artifact_type=ArtifactType.MARKDOWN,
        project_id=test_data["project_id"],
        task_id=test_data["task_id"],
        content="# System Architecture\n\nDetailed specifications here.",
        location="docs/architecture.md",
        metadata={"tags": ["architecture", "spec"]},
    )

    result = await service.create_artifact(
        company_id=test_data["company_id"],
        payload=payload,
        user_id=test_data["user_id"],
    )

    assert result.id is not None
    assert result.name == "System Architecture Document"
    assert result.artifact_type == "MARKDOWN"
    assert result.version == 1
    assert result.parent_artifact_id is None
    assert payload.content is not None
    assert result.file_size_bytes == len(payload.content.encode("utf-8"))
    assert result.creator_name == "Lead Operator"
    assert result.metadata == {"tags": ["architecture", "spec"]}

    # Verify Activity Event
    events = (
        (
            await db_session.execute(
                select(ActivityEvent).where(
                    ActivityEvent.company_id == test_data["company_id"],
                    ActivityEvent.event_type == "artifact.created",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 1
    assert "System Architecture Document" in events[0].message


@pytest.mark.asyncio
async def test_create_artifact_agent_attribution(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    service = ArtifactService(db_session)
    payload = ArtifactCreatePayload(
        name="Performance Benchmark Report",
        artifact_type=ArtifactType.REPORT,
        created_by_agent_id=test_data["agent_id"],
        content="Benchmark Results: 10k ops/sec",
    )

    result = await service.create_artifact(
        company_id=test_data["company_id"],
        payload=payload,
    )

    assert result.creator_name == "Architect Agent"
    assert result.created_by_agent_id == test_data["agent_id"]


@pytest.mark.asyncio
async def test_create_artifact_access_denied(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    service = ArtifactService(db_session)
    payload = ArtifactCreatePayload(name="Unauthorized Doc")

    with pytest.raises(ArtifactAccessDeniedError):
        await service.create_artifact(
            company_id=test_data["company_id"],
            payload=payload,
            user_id="usr-foreign-999",
        )


@pytest.mark.asyncio
async def test_create_artifact_invalid_references(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    service = ArtifactService(db_session)

    # Invalid project
    with pytest.raises(ProjectNotFoundError):
        await service.create_artifact(
            company_id=test_data["company_id"],
            payload=ArtifactCreatePayload(name="Doc", project_id="prj-invalid-999"),
            user_id=test_data["user_id"],
        )

    # Invalid task
    with pytest.raises(TaskNotFoundError):
        await service.create_artifact(
            company_id=test_data["company_id"],
            payload=ArtifactCreatePayload(name="Doc", task_id="tsk-invalid-999"),
            user_id=test_data["user_id"],
        )


@pytest.mark.asyncio
async def test_get_and_list_artifacts(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    service = ArtifactService(db_session)

    doc1 = await service.create_artifact(
        company_id=test_data["company_id"],
        payload=ArtifactCreatePayload(
            name="Alpha Doc",
            artifact_type=ArtifactType.MARKDOWN,
            project_id=test_data["project_id"],
            content="Alpha content",
        ),
        user_id=test_data["user_id"],
    )

    await service.create_artifact(
        company_id=test_data["company_id"],
        payload=ArtifactCreatePayload(
            name="Beta Dataset",
            artifact_type=ArtifactType.CSV,
            content="id,metric\n1,100",
        ),
        user_id=test_data["user_id"],
    )

    # Get single
    fetched = await service.get_artifact(
        company_id=test_data["company_id"],
        artifact_id=doc1.id,
        user_id=test_data["user_id"],
    )
    assert fetched.id == doc1.id
    assert fetched.name == "Alpha Doc"

    # List all
    all_docs = await service.list_artifacts(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
    )
    assert all_docs.total == 2

    # Filter by type
    csv_docs = await service.list_artifacts(
        company_id=test_data["company_id"],
        artifact_type="CSV",
        user_id=test_data["user_id"],
    )
    assert csv_docs.total == 1
    assert csv_docs.items[0].name == "Beta Dataset"

    # Search filter
    search_res = await service.list_artifacts(
        company_id=test_data["company_id"],
        search="Alpha",
        user_id=test_data["user_id"],
    )
    assert search_res.total == 1
    assert search_res.items[0].name == "Alpha Doc"


@pytest.mark.asyncio
async def test_update_artifact(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    service = ArtifactService(db_session)

    doc = await service.create_artifact(
        company_id=test_data["company_id"],
        payload=ArtifactCreatePayload(
            name="Draft Doc",
            artifact_type=ArtifactType.TEXT,
            content="Initial",
        ),
        user_id=test_data["user_id"],
    )

    updated = await service.update_artifact(
        company_id=test_data["company_id"],
        artifact_id=doc.id,
        payload=ArtifactUpdatePayload(
            name="Final Document",
            content="Updated content with more detail.",
            metadata={"status": "reviewed"},
        ),
        user_id=test_data["user_id"],
    )

    assert updated.name == "Final Document"
    assert updated.content == "Updated content with more detail."
    assert updated.file_size_bytes == len(b"Updated content with more detail.")
    assert updated.metadata == {"status": "reviewed"}


@pytest.mark.asyncio
async def test_versioning_lineage(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    service = ArtifactService(db_session)

    # v1
    v1 = await service.create_artifact(
        company_id=test_data["company_id"],
        payload=ArtifactCreatePayload(
            name="API Spec",
            artifact_type=ArtifactType.JSON,
            content='{"version": 1}',
            change_summary="Initial spec",
        ),
        user_id=test_data["user_id"],
    )
    assert v1.version == 1
    assert v1.parent_artifact_id is None

    # v2 created from v1
    v2 = await service.create_new_version(
        company_id=test_data["company_id"],
        artifact_id=v1.id,
        payload=ArtifactVersionCreatePayload(
            content='{"version": 2, "endpoints": ["/api/v1/artifacts"]}',
            change_summary="Added artifacts endpoint",
            creator_name="API Lead",
        ),
        user_id=test_data["user_id"],
    )
    assert v2.version == 2
    assert v2.parent_artifact_id == v1.id
    assert v2.name == "API Spec"
    assert v2.creator_name == "API Lead"
    assert v2.change_summary == "Added artifacts endpoint"

    # v3 created from v2 (should link to root v1)
    v3 = await service.create_new_version(
        company_id=test_data["company_id"],
        artifact_id=v2.id,
        payload=ArtifactVersionCreatePayload(
            content='{"version": 3, "endpoints": ["/api/v1/artifacts", "/api/v1/realtime"]}',
            change_summary="Added realtime endpoints",
        ),
        user_id=test_data["user_id"],
    )
    assert v3.version == 3
    assert v3.parent_artifact_id == v1.id
    assert v3.change_summary == "Added realtime endpoints"

    # Verify lineage history
    history = await service.get_version_history(
        company_id=test_data["company_id"],
        artifact_id=v3.id,
        user_id=test_data["user_id"],
    )
    assert len(history) == 3
    assert [h.version for h in history] == [1, 2, 3]


@pytest.mark.asyncio
async def test_delete_artifact(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    service = ArtifactService(db_session)

    doc = await service.create_artifact(
        company_id=test_data["company_id"],
        payload=ArtifactCreatePayload(
            name="Temporary Artifact",
            content="Delete me",
        ),
        user_id=test_data["user_id"],
    )

    deleted = await service.delete_artifact(
        company_id=test_data["company_id"],
        artifact_id=doc.id,
        user_id=test_data["user_id"],
    )
    assert deleted is True

    with pytest.raises(ArtifactNotFoundError):
        await service.get_artifact(
            company_id=test_data["company_id"],
            artifact_id=doc.id,
            user_id=test_data["user_id"],
        )
