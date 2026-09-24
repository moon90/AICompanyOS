"""Unit tests for EngineeringService adhering to docs/Phases.md Section 20 and docs/Memory.md Section 61."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.engineering_service import EngineeringService
from domain.engineering.exceptions import (
    EngineeringAccessDeniedError,
)
from domain.engineering.schemas import (
    EngineeringContextUpsertPayload,
    FileChangeBulkCreatePayload,
    FileChangeCreatePayload,
    FileChangeType,
    TestStatus,
    VerificationState,
)
from domain.work.exceptions import TaskNotFoundError
from infrastructure.database.base import Base
from infrastructure.database.models import (
    ActivityEvent,
    Agent,
    Company,
    CompanyMember,
    Department,
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
    """Seed test company, user, department, agents, project, and task."""
    user = User(
        id="usr-eng-001",
        email="engineer@test.os",
        name="Lead Engineer",
        password_hash="hash",
    )
    db_session.add(user)

    company = Company(
        id="cmp-eng-001",
        name="Engineering Test Corp",
        status="active",
    )
    db_session.add(company)

    member = CompanyMember(
        id="mem-eng-001",
        company_id=company.id,
        user_id=user.id,
        role="owner",
        status="active",
    )
    db_session.add(member)

    dept = Department(
        id="dep-eng-001",
        company_id=company.id,
        name="Core Engineering",
        code="ENG",
    )
    db_session.add(dept)

    agent = Agent(
        id="agt-eng-001",
        company_id=company.id,
        name="Frontend Dev Agent",
        role="Frontend Engineer",
        status="idle",
    )
    db_session.add(agent)

    project = Project(
        id="prj-eng-001",
        company_id=company.id,
        name="Company Portal Redesign",
        status="active",
    )
    db_session.add(project)

    task = Task(
        id="tsk-eng-001",
        company_id=company.id,
        project_id=project.id,
        title="Implement Task Drawer Code Inspection",
        description="Add tab to view tracked files and commit context",
        status="in_progress",
        assigned_to_agent_id=agent.id,
    )
    db_session.add(task)

    await db_session.commit()

    return {
        "user_id": user.id,
        "company_id": company.id,
        "agent_id": agent.id,
        "project_id": project.id,
        "task_id": task.id,
    }


@pytest.mark.asyncio
async def test_get_task_engineering_view_empty(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify task engineering view returns empty context and file changes initially."""
    service = EngineeringService(db_session)
    view = await service.get_task_engineering_view(
        company_id=test_data["company_id"],
        task_id=test_data["task_id"],
        user_id=test_data["user_id"],
    )

    assert view.task_id == test_data["task_id"]
    assert view.company_id == test_data["company_id"]
    assert view.context is None
    assert view.file_changes == []
    assert view.total_files_changed == 0
    assert view.total_additions == 0
    assert view.total_deletions == 0


@pytest.mark.asyncio
async def test_upsert_engineering_context_and_verify(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify creating and updating engineering context with verification events."""
    service = EngineeringService(db_session)

    # 1. Initialize context
    payload = EngineeringContextUpsertPayload(
        repository="moon90/AICompanyOS",
        branch="feat/task-drawer-engineering",
        pull_request_number="42",
        pull_request_url="https://github.com/moon90/AICompanyOS/pull/42",
        pull_request_title="feat: engineering file tracking drawer",
        commit_count=3,
        test_status=TestStatus.RUNNING,
        test_output_summary="Running pytest & vitest suites...",
        verification_state=VerificationState.IN_REVIEW,
    )

    context = await service.upsert_engineering_context(
        company_id=test_data["company_id"],
        task_id=test_data["task_id"],
        payload=payload,
        user_id=test_data["user_id"],
    )

    assert context.task_id == test_data["task_id"]
    assert context.branch == "feat/task-drawer-engineering"
    assert context.pull_request_number == "42"
    assert context.commit_count == 3
    assert context.test_status == "RUNNING"
    assert context.verification_state == "IN_REVIEW"

    # 2. Update to VERIFIED
    update_payload = EngineeringContextUpsertPayload(
        test_status=TestStatus.PASSED,
        test_output_summary="All 100% tests passed. Clean lints.",
        verification_state=VerificationState.VERIFIED,
        verification_notes="Code reviewed and verified by QA agent.",
    )
    updated_context = await service.upsert_engineering_context(
        company_id=test_data["company_id"],
        task_id=test_data["task_id"],
        payload=update_payload,
        user_id=test_data["user_id"],
    )

    assert updated_context.test_status == "PASSED"
    assert updated_context.verification_state == "VERIFIED"
    assert updated_context.verification_notes == "Code reviewed and verified by QA agent."
    assert updated_context.branch == "feat/task-drawer-engineering"

    # Verify activity events recorded
    events_res = await db_session.execute(
        select(ActivityEvent).where(ActivityEvent.company_id == test_data["company_id"])
    )
    events = list(events_res.scalars().all())
    event_types = [e.event_type for e in events]
    assert "engineering.context_created" in event_types
    assert "engineering.verified" in event_types


@pytest.mark.asyncio
async def test_record_file_changes_and_history(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify recording batch file changes and aggregating company file history."""
    service = EngineeringService(db_session)

    payload = FileChangeBulkCreatePayload(
        changes=[
            FileChangeCreatePayload(
                file_path="apps/web/app/tasks/page.tsx",
                repository="moon90/AICompanyOS",
                branch="feat/task-drawer-engineering",
                agent_id=test_data["agent_id"],
                change_type=FileChangeType.MODIFIED,
                commit_hash="a1b2c3d4",
                commit_message="feat(web): add engineering tab to task drawer",
                additions=85,
                deletions=12,
                change_summary="Added EngineeringCodeTab with branch and diff preview",
            ),
            FileChangeCreatePayload(
                file_path="apps/web/lib/api.ts",
                repository="moon90/AICompanyOS",
                branch="feat/task-drawer-engineering",
                agent_id=test_data["agent_id"],
                change_type=FileChangeType.MODIFIED,
                commit_hash="a1b2c3d4",
                commit_message="feat(web): add engineering tab to task drawer",
                additions=40,
                deletions=0,
                change_summary="Added getTaskEngineeringView and upsertEngineeringContext",
            ),
        ]
    )

    results = await service.record_file_changes(
        company_id=test_data["company_id"],
        task_id=test_data["task_id"],
        payload=payload,
        user_id=test_data["user_id"],
    )

    assert len(results) == 2
    assert results[0].file_path == "apps/web/app/tasks/page.tsx"
    assert results[0].additions == 85
    assert results[0].deletions == 12
    assert results[0].agent_id == test_data["agent_id"]
    assert results[1].file_path == "apps/web/lib/api.ts"

    # Query view
    view = await service.get_task_engineering_view(
        company_id=test_data["company_id"],
        task_id=test_data["task_id"],
        user_id=test_data["user_id"],
    )
    assert view.total_files_changed == 2
    assert view.total_additions == 125
    assert view.total_deletions == 12
    assert view.context is not None
    assert view.context.branch == "feat/task-drawer-engineering"

    # Query company file history
    history = await service.get_company_file_history(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
    )
    assert len(history) == 2
    file_paths = [h.file_path for h in history]
    assert "apps/web/app/tasks/page.tsx" in file_paths
    assert "apps/web/lib/api.ts" in file_paths


@pytest.mark.asyncio
async def test_engineering_access_denied(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify unauthorized users cannot access engineering context."""
    service = EngineeringService(db_session)

    with pytest.raises(EngineeringAccessDeniedError):
        await service.get_task_engineering_view(
            company_id=test_data["company_id"],
            task_id=test_data["task_id"],
            user_id="usr-rogue-999",
        )


@pytest.mark.asyncio
async def test_engineering_task_not_found(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify querying non-existent task raises TaskNotFoundError."""
    service = EngineeringService(db_session)

    with pytest.raises(TaskNotFoundError):
        await service.get_task_engineering_view(
            company_id=test_data["company_id"],
            task_id="tsk-does-not-exist",
            user_id=test_data["user_id"],
        )
