"""Unit tests for CEO plan decomposition into Project, Tasks, and Delegations per docs/Phases.md Section 11."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.agent_service import AgentService
from application.services.ceo_service import CeoService
from application.services.company_service import CompanyService
from infrastructure.database.base import Base
from infrastructure.database.models import Task, User
from orchestration.planner.schemas import GoalIntake


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
async def test_ceo_plan_decomposition_into_task_dag(db_session: AsyncSession) -> None:
    """Verify that delegating a CEO plan creates 1 parent task, multiple child tasks, DAG dependencies, and delegations."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    ceo_service = CeoService(db=db_session)

    user = User(name="Founder", email="founder@apex.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Apex Ventures")
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)

    # 1. Generate a proposed CEO plan
    goal = GoalIntake(
        objective="Enter European enterprise market with localized marketing and technical compliance.",
        requested_outcome="Full regulatory audit and launch marketing strategy.",
        priority="high",
    )
    plan = await ceo_service.generate_plan(
        user_id=user.id,
        company_id=company.id,
        goal=goal,
    )
    assert plan.status == "proposed"
    assert len(plan.plan_steps) >= 3

    # 2. Delegate the CEO plan
    result = await ceo_service.delegate_plan(
        user_id=user.id,
        company_id=company.id,
        plan_id=plan.id,
        project_name="European Enterprise Expansion",
    )

    assert result["project_id"] is not None
    assert result["project_name"] == "European Enterprise Expansion"
    assert result["parent_task_id"] is not None
    assert result["child_tasks_count"] == len(plan.plan_steps)
    assert result["delegations_count"] > 0

    # 3. Check plan status updated
    updated_plan = await ceo_service.get_plan(
        user_id=user.id, company_id=company.id, plan_id=plan.id
    )
    assert updated_plan.status == "delegated"
    assert updated_plan.project_id == result["project_id"]

    # 4. Check parent-child relationships in database
    parent_task = await db_session.get(Task, result["parent_task_id"])
    assert parent_task is not None
    assert parent_task.parent_task_id is None

    for child_id in result["child_task_ids"]:
        child_task = await db_session.get(Task, child_id)
        assert child_task is not None
        assert child_task.parent_task_id == parent_task.id
        assert child_task.project_id == result["project_id"]

    # 5. Attempting to re-delegate raises ValueError
    with pytest.raises(ValueError, match="already been delegated"):
        await ceo_service.delegate_plan(
            user_id=user.id,
            company_id=company.id,
            plan_id=plan.id,
        )
