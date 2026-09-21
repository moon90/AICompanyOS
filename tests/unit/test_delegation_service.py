"""Unit tests for DelegationService managing task delegation, hierarchy, and audit logs."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.agent_service import AgentService
from application.services.company_service import CompanyService
from application.services.delegation_service import DelegationService
from application.services.project_service import ProjectService
from application.services.task_service import TaskService
from domain.delegation.exceptions import (
    CircularDelegationError,
    DelegationAccessDeniedError,
)
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
async def test_delegate_task_success(db_session: AsyncSession) -> None:
    """Verify task delegation updates task assignment, advances status, and persists DelegationRecord."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    project_service = ProjectService(db_session)
    task_service = TaskService(db_session)
    delegation_service = DelegationService(db_session)

    user = User(name="Founder", email="founder@alpha.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Alpha Corp")
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)
    agents = await agent_service.get_company_agents(company_id=company.id, user_id=user.id)

    ceo = next(
        a
        for a in agents
        if a.role.lower() in ("ceo", "chief executive officer") or a.name.lower() == "ceo"
    )
    cto = next(a for a in agents if a.role == "Chief Technology Officer")
    architect = next(a for a in agents if a.role == "Software Architect")

    project = await project_service.create_project(
        user_id=user.id,
        company_id=company.id,
        name="Platform Foundation",
    )

    task = await task_service.create_task(
        user_id=user.id,
        company_id=company.id,
        title="Design Microservice Architecture",
        description="Create detailed architecture specification",
        project_id=project.id,
    )
    assert task.status == "CREATED"

    # 1. CEO delegates task to CTO
    record1 = await delegation_service.delegate_task(
        company_id=company.id,
        task_id=task.id,
        user_id=user.id,
        target_agent_id=cto.id,
        delegator_agent_id=ceo.id,
        reason="CTO oversight requested for architecture design",
        scope="Technical architecture and scalability",
    )

    assert record1.depth == 1
    assert record1.delegated_to_agent_id == cto.id
    assert record1.delegated_by_agent_id == ceo.id
    assert task.assigned_to_agent_id == cto.id
    assert task.status == "ASSIGNED"

    # 2. CTO delegates to Software Architect
    record2 = await delegation_service.delegate_task(
        company_id=company.id,
        task_id=task.id,
        user_id=user.id,
        target_agent_id=architect.id,
        delegator_agent_id=cto.id,
        reason="Specialist execution assigned to Software Architect",
        scope="Component diagram and database schema",
    )

    assert record2.depth == 2
    assert record2.delegated_to_agent_id == architect.id
    assert record2.delegated_by_agent_id == cto.id
    assert task.assigned_to_agent_id == architect.id

    # 3. Retrieve task delegation history
    history = await delegation_service.get_task_delegations(
        company_id=company.id,
        user_id=user.id,
        task_id=task.id,
    )
    assert len(history) == 2
    assert history[0].delegated_to_agent_id == cto.id
    assert history[1].delegated_to_agent_id == architect.id

    # 4. List all company delegations
    all_del, total = await delegation_service.list_company_delegations(
        company_id=company.id,
        user_id=user.id,
    )
    assert total == 2
    assert len(all_del) == 2


@pytest.mark.asyncio
async def test_circular_delegation_rejection_in_service(db_session: AsyncSession) -> None:
    """Verify DelegationService rejects circular delegation attempts."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    task_service = TaskService(db_session)
    delegation_service = DelegationService(db_session)

    user = User(name="Founder", email="founder2@alpha.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Beta Corp")
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)
    agents = await agent_service.get_company_agents(company_id=company.id, user_id=user.id)

    ceo = next(
        a
        for a in agents
        if a.role.lower() in ("ceo", "chief executive officer") or a.name.lower() == "ceo"
    )
    cto = next(a for a in agents if a.role == "Chief Technology Officer")

    task = await task_service.create_task(
        user_id=user.id,
        company_id=company.id,
        title="Loop Task",
    )

    # CEO delegates to CTO
    await delegation_service.delegate_task(
        company_id=company.id,
        task_id=task.id,
        user_id=user.id,
        target_agent_id=cto.id,
        delegator_agent_id=ceo.id,
        reason="First hop",
    )

    # CTO tries to delegate back to CEO
    with pytest.raises(CircularDelegationError):
        await delegation_service.delegate_task(
            company_id=company.id,
            task_id=task.id,
            user_id=user.id,
            target_agent_id=ceo.id,
            delegator_agent_id=cto.id,
            reason="Back to CEO",
        )


@pytest.mark.asyncio
async def test_delegation_access_denied_for_non_member(db_session: AsyncSession) -> None:
    """Verify unauthorized user cannot delegate tasks."""
    company_service = CompanyService(db_session)
    delegation_service = DelegationService(db_session)

    user1 = User(name="Owner", email="owner@corp.com", password_hash="hash")
    user2 = User(name="Attacker", email="attacker@evil.com", password_hash="hash")
    db_session.add_all([user1, user2])
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user1.id, name="Secure Corp")

    with pytest.raises(DelegationAccessDeniedError):
        await delegation_service.delegate_task(
            company_id=company.id,
            task_id="non-existent",
            user_id=user2.id,
            target_agent_id="any",
            reason="Unauthorized",
        )
