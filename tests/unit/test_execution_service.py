"""Unit tests for ExecutionService managing task execution runs and lifecycle transitions."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.agent_service import AgentService
from application.services.company_service import CompanyService
from application.services.execution_service import ExecutionService
from application.services.project_service import ProjectService
from application.services.task_service import TaskService
from domain.runtime.exceptions import (
    AgentInactiveError,
    ExecutionAccessDeniedError,
    InvalidTaskStateForExecutionError,
    UnassignedTaskError,
)
from domain.runtime.schemas import RuntimeLimits
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
async def test_execute_task_success(db_session: AsyncSession) -> None:
    """Verify executing an assigned task transitions it to VERIFYING and persists ExecutionRecord."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    project_service = ProjectService(db_session)
    task_service = TaskService(db_session)
    execution_service = ExecutionService(db_session)

    # 1. Setup user and company
    user = User(name="Founder", email="founder@alpha.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Alpha Corp")
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)
    agents = await agent_service.get_company_agents(company_id=company.id, user_id=user.id)
    backend_agent = next(
        a for a in agents if "backend" in a.role.lower() or "engineer" in a.role.lower()
    )

    # 2. Setup project and task
    project = await project_service.create_project(
        company_id=company.id,
        user_id=user.id,
        name="Core Infrastructure",
    )
    task = await task_service.create_task(
        company_id=company.id,
        user_id=user.id,
        title="Implement Redis caching layer",
        objective="Cache session state with 15-minute TTL",
        description="Write Redis client helper with fallback to PostgreSQL.",
        project_id=project.id,
        assigned_to_agent_id=backend_agent.id,
    )
    assert task.status == TaskStatus.ASSIGNED.value

    # 3. Execute task
    limits = RuntimeLimits(max_steps=4, max_duration_seconds=30)
    record = await execution_service.execute_task(
        company_id=company.id,
        task_id=task.id,
        user_id=user.id,
        limits=limits,
    )

    # 4. Verify ExecutionRecord
    assert record.id is not None
    assert record.status == "SUCCESS"
    assert record.agent_id == backend_agent.id
    assert record.task_id == task.id
    assert record.duration_ms > 0
    assert record.step_count > 0
    assert record.deliverable is not None
    assert len(record.steps_json) > 0

    # 5. Verify Task state: must be VERIFYING (Phase 8 Golden Rule: agent claiming
    #    'Task completed' does not make it COMPLETED; advances to VERIFYING).
    reloaded_task = await task_service.get_task(
        company_id=company.id, task_id=task.id, user_id=user.id
    )
    assert reloaded_task.status == TaskStatus.VERIFYING.value
    assert reloaded_task.output == record.deliverable
    assert reloaded_task.started_at is not None

    # 6. Verify list_task_executions
    history = await execution_service.list_task_executions(
        company_id=company.id,
        task_id=task.id,
        user_id=user.id,
    )
    assert len(history) == 1
    assert history[0].id == record.id

    # 7. Verify get_execution
    fetched = await execution_service.get_execution(
        company_id=company.id,
        execution_id=record.id,
        user_id=user.id,
    )
    assert fetched.id == record.id
    assert fetched.status == "SUCCESS"


@pytest.mark.asyncio
async def test_execute_task_validation_guards(db_session: AsyncSession) -> None:
    """Verify validation guards for unassigned tasks, inactive agents, and invalid statuses."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    task_service = TaskService(db_session)
    execution_service = ExecutionService(db_session)

    user = User(name="Founder", email="founder@alpha.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Alpha Corp")
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)
    agents = await agent_service.get_company_agents(company_id=company.id, user_id=user.id)
    agent = agents[0]

    # 1. Unassigned task error
    unassigned_task = await task_service.create_task(
        company_id=company.id,
        user_id=user.id,
        title="Unassigned Task",
    )
    with pytest.raises(UnassignedTaskError):
        await execution_service.execute_task(
            company_id=company.id,
            task_id=unassigned_task.id,
            user_id=user.id,
        )

    # 2. Inactive agent error
    inactive_task = await task_service.create_task(
        company_id=company.id,
        user_id=user.id,
        title="Task for Inactive Agent",
        assigned_to_agent_id=agent.id,
    )
    # Deactivate agent
    await agent_service.update_agent(
        company_id=company.id,
        agent_id=agent.id,
        user_id=user.id,
        status="inactive",
    )
    with pytest.raises(AgentInactiveError):
        await execution_service.execute_task(
            company_id=company.id,
            task_id=inactive_task.id,
            user_id=user.id,
        )

    # Re-activate agent
    await agent_service.update_agent(
        company_id=company.id,
        agent_id=agent.id,
        user_id=user.id,
        status="active",
    )

    # 3. Invalid status error (e.g. COMPLETED cannot be directly executed)
    valid_task = await task_service.create_task(
        company_id=company.id,
        user_id=user.id,
        title="Completed Task",
        assigned_to_agent_id=agent.id,
    )
    # Transition to COMPLETED
    await task_service.update_task_status(
        user_id=user.id,
        company_id=company.id,
        task_id=valid_task.id,
        new_status=TaskStatus.IN_PROGRESS.value,
    )
    await task_service.update_task_status(
        user_id=user.id,
        company_id=company.id,
        task_id=valid_task.id,
        new_status=TaskStatus.COMPLETED.value,
    )

    with pytest.raises(InvalidTaskStateForExecutionError):
        await execution_service.execute_task(
            company_id=company.id,
            task_id=valid_task.id,
            user_id=user.id,
        )


@pytest.mark.asyncio
async def test_execute_task_tenant_isolation(db_session: AsyncSession) -> None:
    """Verify that execution is blocked for non-member users across companies."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    task_service = TaskService(db_session)
    execution_service = ExecutionService(db_session)

    user1 = User(name="User 1", email="u1@alpha.os", password_hash="hash")
    user2 = User(name="User 2", email="u2@beta.os", password_hash="hash")
    db_session.add_all([user1, user2])
    await db_session.flush()

    company1, _ = await company_service.create_company(user_id=user1.id, name="Company 1")
    await agent_service.provision_default_agents(company_id=company1.id, user_id=user1.id)
    agents = await agent_service.get_company_agents(company_id=company1.id, user_id=user1.id)

    task1 = await task_service.create_task(
        company_id=company1.id,
        user_id=user1.id,
        title="Task in Company 1",
        assigned_to_agent_id=agents[0].id,
    )

    # Non-member user2 should be denied
    with pytest.raises(ExecutionAccessDeniedError):
        await execution_service.execute_task(
            company_id=company1.id,
            task_id=task1.id,
            user_id=user2.id,
        )
