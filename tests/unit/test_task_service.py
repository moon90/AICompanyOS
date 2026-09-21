"""Unit tests for TaskService managing tasks, assignments, dependencies, and cycle prevention."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.agent_service import AgentService
from application.services.company_service import CompanyService
from application.services.project_service import ProjectService
from application.services.task_service import TaskService
from domain.work.exceptions import (
    CircularDependencyError,
    InvalidStatusTransitionError,
    SelfDependencyError,
    WorkAccessDeniedError,
)
from domain.work.state_machine import TaskStatus
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
async def test_task_creation_and_agent_assignment(db_session: AsyncSession) -> None:
    """Verify task creation, project linking, and automatic promotion to ASSIGNED on agent assignment."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    project_service = ProjectService(db_session)
    task_service = TaskService(db_session)

    user = User(name="Leader", email="leader@apex.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Apex Systems")
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)
    agents = await agent_service.get_company_agents(company_id=company.id, user_id=user.id)
    engineer = next(a for a in agents if a.role == "Full Stack Engineer")

    project = await project_service.create_project(
        user_id=user.id,
        company_id=company.id,
        name="Core Infrastructure",
    )

    # 1. Create task assigned to engineer
    task = await task_service.create_task(
        user_id=user.id,
        company_id=company.id,
        title="Setup Redis Cache",
        description="Provision Redis cluster and wire connection pool",
        project_id=project.id,
        assigned_to_agent_id=engineer.id,
        status="CREATED",
    )

    # Assigned task should automatically advance from CREATED to ASSIGNED
    assert task.status == TaskStatus.ASSIGNED.value
    assert task.assigned_to_agent_id == engineer.id
    assert task.project_id == project.id
    assert task.department_id == engineer.department_id

    # 2. Advance task to IN_PROGRESS
    task = await task_service.update_task_status(
        user_id=user.id,
        company_id=company.id,
        task_id=task.id,
        new_status=TaskStatus.IN_PROGRESS.value,
    )
    assert task.status == TaskStatus.IN_PROGRESS.value
    assert task.started_at is not None
    assert task.completed_at is None

    # 3. Complete task
    task = await task_service.update_task_status(
        user_id=user.id,
        company_id=company.id,
        task_id=task.id,
        new_status=TaskStatus.COMPLETED.value,
        output="Redis cluster provisioned with 3 nodes and TLS enabled.",
    )
    assert task.status == TaskStatus.COMPLETED.value
    assert task.completed_at is not None
    assert "Redis cluster provisioned" in (task.output or "")


@pytest.mark.asyncio
async def test_task_invalid_status_transition(db_session: AsyncSession) -> None:
    """Verify invalid state transitions are blocked by the service."""
    company_service = CompanyService(db_session)
    task_service = TaskService(db_session)

    user = User(name="User", email="user@test.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Test Co")

    task = await task_service.create_task(
        user_id=user.id,
        company_id=company.id,
        title="Draft Architecture",
        status=TaskStatus.CREATED.value,
    )

    # Cannot transition directly from CREATED to COMPLETED
    with pytest.raises(InvalidStatusTransitionError):
        await task_service.update_task_status(
            user_id=user.id,
            company_id=company.id,
            task_id=task.id,
            new_status=TaskStatus.COMPLETED.value,
        )


@pytest.mark.asyncio
async def test_task_dependency_cycle_detection(db_session: AsyncSession) -> None:
    """Verify self-dependencies and cyclic dependencies are detected and rejected."""
    company_service = CompanyService(db_session)
    task_service = TaskService(db_session)

    user = User(name="User", email="user2@test.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Graph Co")

    task_a = await task_service.create_task(user_id=user.id, company_id=company.id, title="Task A")
    task_b = await task_service.create_task(user_id=user.id, company_id=company.id, title="Task B")
    task_c = await task_service.create_task(user_id=user.id, company_id=company.id, title="Task C")

    # 1. Self dependency must fail
    with pytest.raises(SelfDependencyError):
        await task_service.add_dependency(
            user_id=user.id,
            company_id=company.id,
            task_id=task_a.id,
            depends_on_task_id=task_a.id,
        )

    # 2. Add valid chain: A depends on B, B depends on C
    await task_service.add_dependency(
        user_id=user.id,
        company_id=company.id,
        task_id=task_a.id,
        depends_on_task_id=task_b.id,
    )
    await task_service.add_dependency(
        user_id=user.id,
        company_id=company.id,
        task_id=task_b.id,
        depends_on_task_id=task_c.id,
    )

    # 3. Direct cycle: B cannot depend on A
    with pytest.raises(CircularDependencyError):
        await task_service.add_dependency(
            user_id=user.id,
            company_id=company.id,
            task_id=task_b.id,
            depends_on_task_id=task_a.id,
        )

    # 4. Transitive cycle: C cannot depend on A (because A -> B -> C -> A)
    with pytest.raises(CircularDependencyError):
        await task_service.add_dependency(
            user_id=user.id,
            company_id=company.id,
            task_id=task_c.id,
            depends_on_task_id=task_a.id,
        )


@pytest.mark.asyncio
async def test_task_multi_tenant_isolation(db_session: AsyncSession) -> None:
    """Verify tasks are strictly isolated between companies."""
    company_service = CompanyService(db_session)
    task_service = TaskService(db_session)

    user_a = User(name="User A", email="a@corp.os", password_hash="hash")
    user_b = User(name="User B", email="b@corp.os", password_hash="hash")
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    company_a, _ = await company_service.create_company(user_id=user_a.id, name="Company A")
    company_b, _ = await company_service.create_company(user_id=user_b.id, name="Company B")

    task_a = await task_service.create_task(
        user_id=user_a.id,
        company_id=company_a.id,
        title="Secret Task A",
    )

    # User B cannot read Task A
    with pytest.raises(WorkAccessDeniedError):
        await task_service.get_task(
            user_id=user_b.id,
            company_id=company_a.id,
            task_id=task_a.id,
        )

    # User B cannot update Task A
    with pytest.raises(WorkAccessDeniedError):
        await task_service.update_task_status(
            user_id=user_b.id,
            company_id=company_a.id,
            task_id=task_a.id,
            new_status=TaskStatus.IN_PROGRESS.value,
        )
