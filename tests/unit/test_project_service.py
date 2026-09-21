"""Unit tests for ProjectService managing projects and tenant isolation."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.agent_service import AgentService
from application.services.company_service import CompanyService
from application.services.project_service import ProjectService
from domain.work.exceptions import (
    InvalidWorkAssignmentError,
    ProjectNotFoundError,
    WorkAccessDeniedError,
)
from domain.work.state_machine import ProjectStatus
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
async def test_project_crud_lifecycle(db_session: AsyncSession) -> None:
    """Verify standard project creation, update, retrieval, and deletion."""
    company_service = CompanyService(db_session)
    project_service = ProjectService(db_session)

    user = User(name="Owner", email="owner@test.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Omega Corp")

    # 1. Create project
    project = await project_service.create_project(
        user_id=user.id,
        company_id=company.id,
        name="Market Expansion",
        description="Expand market presence into Europe",
        objective="Achieve 10% market share",
        priority="high",
    )
    assert project.id is not None
    assert project.name == "Market Expansion"
    assert project.status == ProjectStatus.PLANNED.value
    assert project.priority == "high"
    assert project.owner_user_id == user.id

    # 2. Get project with stats
    fetched, stats = await project_service.get_project(
        user_id=user.id,
        company_id=company.id,
        project_id=project.id,
    )
    assert fetched.id == project.id
    assert stats["total_tasks"] == 0

    # 3. Update project status to COMPLETED
    updated = await project_service.update_project(
        user_id=user.id,
        company_id=company.id,
        project_id=project.id,
        status=ProjectStatus.COMPLETED.value,
    )
    assert updated.status == ProjectStatus.COMPLETED.value
    assert updated.completed_at is not None

    # 4. List projects
    items, total = await project_service.list_projects(
        user_id=user.id,
        company_id=company.id,
    )
    assert total == 1
    assert len(items) == 1

    # 5. Delete project
    await project_service.delete_project(
        user_id=user.id,
        company_id=company.id,
        project_id=project.id,
    )
    with pytest.raises(ProjectNotFoundError):
        await project_service.get_project(
            user_id=user.id,
            company_id=company.id,
            project_id=project.id,
        )


@pytest.mark.asyncio
async def test_project_cross_company_isolation(db_session: AsyncSession) -> None:
    """Verify projects cannot be accessed or created across company boundaries."""
    company_service = CompanyService(db_session)
    project_service = ProjectService(db_session)

    user_a = User(name="User A", email="a@test.os", password_hash="hash")
    user_b = User(name="User B", email="b@test.os", password_hash="hash")
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    company_a, _ = await company_service.create_company(user_id=user_a.id, name="Company A")
    company_b, _ = await company_service.create_company(user_id=user_b.id, name="Company B")

    proj_a = await project_service.create_project(
        user_id=user_a.id,
        company_id=company_a.id,
        name="Project A",
    )

    # User B cannot access Company A's project
    with pytest.raises(WorkAccessDeniedError):
        await project_service.get_project(
            user_id=user_b.id,
            company_id=company_a.id,
            project_id=proj_a.id,
        )

    # User A cannot access Project A through Company B
    with pytest.raises(WorkAccessDeniedError):
        await project_service.get_project(
            user_id=user_a.id,
            company_id=company_b.id,
            project_id=proj_a.id,
        )


@pytest.mark.asyncio
async def test_project_owner_agent_validation(db_session: AsyncSession) -> None:
    """Verify assigning foreign agent as owner is rejected."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    project_service = ProjectService(db_session)

    user = User(name="Founder", email="founder@test.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company_a, _ = await company_service.create_company(user_id=user.id, name="Company A")
    company_b, _ = await company_service.create_company(user_id=user.id, name="Company B")

    # Provision agents in Company B
    await agent_service.provision_default_agents(company_id=company_b.id, user_id=user.id)
    agents_b = await agent_service.get_company_agents(company_id=company_b.id, user_id=user.id)
    agent_b_id = agents_b[0].id

    # Trying to assign agent from Company B to a project in Company A must fail
    with pytest.raises(InvalidWorkAssignmentError, match="does not belong to company"):
        await project_service.create_project(
            user_id=user.id,
            company_id=company_a.id,
            name="Invalid Owner Project",
            owner_agent_id=agent_b_id,
        )
