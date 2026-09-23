"""Unit tests for ProjectService Kanban board generation."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.company_service import CompanyService
from application.services.project_service import ProjectService
from application.services.task_service import TaskService
from domain.work.exceptions import (
    ProjectNotFoundError,
    WorkAccessDeniedError,
)
from domain.work.state_machine import TaskStateMachine, TaskStatus
from infrastructure.database.base import Base
from infrastructure.database.models import User


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create in-memory SQLite database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_project_board_empty(db_session: AsyncSession) -> None:
    """Verify board generation for a project with no tasks."""
    company_service = CompanyService(db_session)
    project_service = ProjectService(db_session)

    user = User(name="Operator", email="op@company.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Cloud Systems")
    project = await project_service.create_project(
        user_id=user.id,
        company_id=company.id,
        name="Empty Project",
    )

    board = await project_service.get_project_board(
        user_id=user.id,
        company_id=company.id,
        project_id=project.id,
    )

    assert board["project"].id == project.id
    assert len(board["columns"]) == 7
    assert len(board["tasks"]) == 0
    assert board["summary"]["total_tasks"] == 0
    assert board["summary"]["completion_rate"] == 0.0

    # Verify column structures
    col_ids = [c["id"] for c in board["columns"]]
    assert col_ids == [
        "READY",
        "IN_PROGRESS",
        "WAITING",
        "BLOCKED",
        "VERIFYING",
        "COMPLETED",
        "ARCHIVED",
    ]


@pytest.mark.asyncio
async def test_get_project_board_with_tasks(db_session: AsyncSession) -> None:
    """Verify task grouping and rollup stats on the Kanban board."""
    company_service = CompanyService(db_session)
    project_service = ProjectService(db_session)
    task_service = TaskService(db_session)

    user = User(name="Leader", email="leader@company.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="FinTech OS")
    project = await project_service.create_project(
        user_id=user.id,
        company_id=company.id,
        name="Payment Engine v2",
    )

    # 1. Create a task in CREATED -> belongs in READY
    await task_service.create_task(
        user_id=user.id,
        company_id=company.id,
        project_id=project.id,
        title="Design Schemas",
        status=TaskStatus.CREATED.value,
    )

    # 2. Create a task in READY -> belongs in READY
    await task_service.create_task(
        user_id=user.id,
        company_id=company.id,
        project_id=project.id,
        title="Setup Migrations",
        status=TaskStatus.READY.value,
    )

    # 3. Create a task in IN_PROGRESS -> belongs in IN_PROGRESS
    await task_service.create_task(
        user_id=user.id,
        company_id=company.id,
        project_id=project.id,
        title="Implement Adapters",
        status=TaskStatus.IN_PROGRESS.value,
    )

    # 4. Create a task in WAITING -> belongs in WAITING
    await task_service.create_task(
        user_id=user.id,
        company_id=company.id,
        project_id=project.id,
        title="Vendor Clearance",
        status=TaskStatus.WAITING.value,
    )

    # 5. Create a task in BLOCKED -> belongs in BLOCKED
    await task_service.create_task(
        user_id=user.id,
        company_id=company.id,
        project_id=project.id,
        title="Security Audit Gate",
        status=TaskStatus.BLOCKED.value,
    )

    # 6. Create a task in COMPLETED -> belongs in COMPLETED
    await task_service.create_task(
        user_id=user.id,
        company_id=company.id,
        project_id=project.id,
        title="Architecture Document",
        status=TaskStatus.COMPLETED.value,
    )

    board = await project_service.get_project_board(
        user_id=user.id,
        company_id=company.id,
        project_id=project.id,
    )

    assert board["summary"]["total_tasks"] == 6
    assert board["summary"]["completed_tasks"] == 1
    assert board["summary"]["in_progress_tasks"] == 1
    assert board["summary"]["waiting_tasks"] == 1
    assert board["summary"]["blocked_tasks"] == 1
    # 1/6 = 16.7%
    assert board["summary"]["completion_rate"] == 16.7

    # Verify column task counts
    col_counts = {c["id"]: c["task_count"] for c in board["columns"]}
    assert col_counts["READY"] == 2
    assert col_counts["IN_PROGRESS"] == 1
    assert col_counts["WAITING"] == 1
    assert col_counts["BLOCKED"] == 1
    assert col_counts["VERIFYING"] == 0
    assert col_counts["COMPLETED"] == 1
    assert col_counts["ARCHIVED"] == 0


@pytest.mark.asyncio
async def test_get_project_board_allowed_transitions(db_session: AsyncSession) -> None:
    """Verify that allowed transitions map is completely populated from TaskStateMachine."""
    company_service = CompanyService(db_session)
    project_service = ProjectService(db_session)

    user = User(name="Admin", email="admin@company.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Test Enterprise")
    project = await project_service.create_project(
        user_id=user.id,
        company_id=company.id,
        name="Board Test",
    )

    board = await project_service.get_project_board(
        user_id=user.id,
        company_id=company.id,
        project_id=project.id,
    )

    allowed = board["allowed_transitions"]
    assert TaskStatus.READY.value in allowed
    assert TaskStatus.IN_PROGRESS.value in allowed[TaskStatus.READY.value]
    assert TaskStatus.BLOCKED.value in allowed[TaskStatus.READY.value]

    # Verify matching state machine definition
    for status, targets in TaskStateMachine.ALLOWED_TRANSITIONS.items():
        assert allowed[status] == sorted(targets)


@pytest.mark.asyncio
async def test_get_project_board_not_found(db_session: AsyncSession) -> None:
    """Verify ProjectNotFoundError when requesting non-existent project board."""
    company_service = CompanyService(db_session)
    project_service = ProjectService(db_session)

    user = User(name="User", email="user@company.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Lone Company")

    with pytest.raises(ProjectNotFoundError):
        await project_service.get_project_board(
            user_id=user.id,
            company_id=company.id,
            project_id="non-existent-uuid",
        )


@pytest.mark.asyncio
async def test_get_project_board_access_denied(db_session: AsyncSession) -> None:
    """Verify WorkAccessDeniedError when non-member requests a company's project board."""
    company_service = CompanyService(db_session)
    project_service = ProjectService(db_session)

    owner = User(name="Owner", email="owner@corp.os", password_hash="hash")
    outsider = User(name="Outsider", email="outsider@evil.os", password_hash="hash")
    db_session.add_all([owner, outsider])
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=owner.id, name="Secure Vault")
    project = await project_service.create_project(
        user_id=owner.id,
        company_id=company.id,
        name="Confidential Project",
    )

    with pytest.raises(WorkAccessDeniedError):
        await project_service.get_project_board(
            user_id=outsider.id,
            company_id=company.id,
            project_id=project.id,
        )
