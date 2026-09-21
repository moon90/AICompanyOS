from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.agent_service import AgentService
from application.services.company_service import CompanyService
from domain.agents.exceptions import (
    AgentAccessDeniedError,
    DuplicateAgentVersionError,
    InvalidAgentDataError,
    InvalidAgentDepartmentError,
    InvalidAgentHierarchyError,
)
from infrastructure.database.base import Base
from infrastructure.database.models import User


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create in-memory SQLite database session for testing AgentService."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_agent_registration_lifecycle(db_session: AsyncSession) -> None:
    """Verify agent creation, default definition v1.0, and retrieval."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)

    # 1. Create User & Company
    user = User(name="Founder", email="founder@agency.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(
        user_id=user.id,
        name="Apex Intelligence",
    )
    depts = await company_service.get_departments(user_id=user.id, company_id=company.id)
    cto_dept = next(d for d in depts if d.code.upper() == "CTO")

    # 2. Register Agent
    agent = await agent_service.create_agent(
        company_id=company.id,
        user_id=user.id,
        name="Lead AI Engineer",
        role="Principal AI Architect",
        type="specialist",
        department_id=cto_dept.id,
        mission="Build robust cognitive systems.",
        authority_level="specialist",
        system_prompt="You are the Principal AI Architect.",
        model="gemini-1.5-pro",
        capabilities=["architecture", "codegen"],
        tools=["web_search"],
    )

    assert agent.id is not None
    assert agent.name == "Lead AI Engineer"
    assert agent.role == "Principal AI Architect"
    assert agent.department_id == cto_dept.id
    assert agent.status == "active"
    assert len(agent.definitions) == 1
    assert agent.definitions[0].version == "1.0"
    assert agent.definitions[0].is_current is True
    assert agent.definitions[0].capabilities == ["architecture", "codegen"]

    # 3. Retrieve Agent
    retrieved = await agent_service.get_agent(company.id, agent.id, user.id)
    assert retrieved.id == agent.id
    assert retrieved.department is not None
    assert retrieved.department.code.upper() == "CTO"


@pytest.mark.asyncio
async def test_agent_validation_failures(db_session: AsyncSession) -> None:
    """Verify input validation rules for agent registration."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)

    user = User(name="Founder", email="validator@agency.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Valid Co")

    # Empty name fails
    with pytest.raises(InvalidAgentDataError, match="Agent name cannot be empty"):
        await agent_service.create_agent(
            company_id=company.id,
            user_id=user.id,
            name="   ",
            role="Specialist",
        )

    # Empty role fails
    with pytest.raises(InvalidAgentDataError, match="Agent role cannot be empty"):
        await agent_service.create_agent(
            company_id=company.id,
            user_id=user.id,
            name="Specialist Alpha",
            role="   ",
        )


@pytest.mark.asyncio
async def test_cross_company_isolation(db_session: AsyncSession) -> None:
    """Verify tenant isolation: non-member cannot list, view, or create agents."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)

    # User A and Company A
    user_a = User(name="User A", email="usera@corp.os", password_hash="hash")
    # User B (different tenant)
    user_b = User(name="User B", email="userb@rival.os", password_hash="hash")
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    company_a, _ = await company_service.create_company(user_id=user_a.id, name="Company A")

    # User A creates Agent in Company A
    agent_a = await agent_service.create_agent(
        company_id=company_a.id,
        user_id=user_a.id,
        name="Agent Alpha",
        role="Strategist",
    )

    # User B attempts to access Company A's agent list
    with pytest.raises(AgentAccessDeniedError):
        await agent_service.get_company_agents(company_a.id, user_b.id)

    # User B attempts to view Agent A
    with pytest.raises(AgentAccessDeniedError):
        await agent_service.get_agent(company_a.id, agent_a.id, user_b.id)

    # User B attempts to create agent in Company A
    with pytest.raises(AgentAccessDeniedError):
        await agent_service.create_agent(
            company_id=company_a.id,
            user_id=user_b.id,
            name="Intruder Agent",
            role="Spy",
        )


@pytest.mark.asyncio
async def test_cross_company_department_rejection(db_session: AsyncSession) -> None:
    """Verify an agent cannot be assigned to a department belonging to another company."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)

    user_a = User(name="Owner A", email="owner_a@tenant.os", password_hash="hash")
    user_b = User(name="Owner B", email="owner_b@tenant.os", password_hash="hash")
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    company_a, _ = await company_service.create_company(user_id=user_a.id, name="Tenant A")
    company_b, _ = await company_service.create_company(user_id=user_b.id, name="Tenant B")

    depts_b = await company_service.get_departments(user_id=user_b.id, company_id=company_b.id)
    dept_b = depts_b[0]

    # Attempt to assign Company A agent to Company B department
    with pytest.raises(InvalidAgentDepartmentError, match="belongs to another company"):
        await agent_service.create_agent(
            company_id=company_a.id,
            user_id=user_a.id,
            name="Confused Agent",
            role="Engineer",
            department_id=dept_b.id,
        )


@pytest.mark.asyncio
async def test_hierarchy_validation_and_cycle_prevention(db_session: AsyncSession) -> None:
    """Verify hierarchy rules: no self-reporting, no cross-company manager, no circular cycles."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)

    user_a = User(name="Owner Org", email="org_owner@tenant.os", password_hash="hash")
    user_b = User(name="Owner Other", email="other_owner@tenant.os", password_hash="hash")
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    company_a, _ = await company_service.create_company(user_id=user_a.id, name="Org Company")
    company_b, _ = await company_service.create_company(user_id=user_b.id, name="Other Company")

    # Create Agent 1 and Agent 2 in Company A
    agent_1 = await agent_service.create_agent(
        company_id=company_a.id,
        user_id=user_a.id,
        name="Director",
        role="Director",
    )
    agent_2 = await agent_service.create_agent(
        company_id=company_a.id,
        user_id=user_a.id,
        name="Manager",
        role="Manager",
        reports_to=agent_1.id,
    )
    agent_3 = await agent_service.create_agent(
        company_id=company_a.id,
        user_id=user_a.id,
        name="Individual Contributor",
        role="Specialist",
        reports_to=agent_2.id,
    )

    # 1. Self-reporting rejected
    with pytest.raises(InvalidAgentHierarchyError, match="cannot report to itself"):
        await agent_service.update_agent(
            company_id=company_a.id,
            agent_id=agent_1.id,
            user_id=user_a.id,
            reports_to=agent_1.id,
        )

    # 2. Cross-company manager rejected
    agent_foreign = await agent_service.create_agent(
        company_id=company_b.id,
        user_id=user_b.id,
        name="Foreign Executive",
        role="Foreign CEO",
    )
    with pytest.raises(InvalidAgentHierarchyError, match="belongs to another company"):
        await agent_service.update_agent(
            company_id=company_a.id,
            agent_id=agent_1.id,
            user_id=user_a.id,
            reports_to=agent_foreign.id,
        )

    # 3. Two-agent direct cycle rejected (Agent 1 reports to Agent 2 while Agent 2 reports to Agent 1)
    with pytest.raises(InvalidAgentHierarchyError, match="Circular reporting relationship"):
        await agent_service.update_agent(
            company_id=company_a.id,
            agent_id=agent_1.id,
            user_id=user_a.id,
            reports_to=agent_2.id,
        )

    # 4. Multi-agent cycle rejected (Agent 1 -> Agent 3, while chain is 1 -> 2 -> 3)
    with pytest.raises(InvalidAgentHierarchyError, match="Circular reporting relationship"):
        await agent_service.update_agent(
            company_id=company_a.id,
            agent_id=agent_1.id,
            user_id=user_a.id,
            reports_to=agent_3.id,
        )


@pytest.mark.asyncio
async def test_agent_definition_versioning(db_session: AsyncSession) -> None:
    """Verify versioned definitions, history preservation, and duplicate rejection."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)

    user = User(name="Founder", email="versions@agency.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Versioned Co")

    agent = await agent_service.create_agent(
        company_id=company.id,
        user_id=user.id,
        name="Analyst",
        role="Data Analyst",
        system_prompt="Initial prompt v1.0",
    )

    # 1. Add version 1.1
    def_1_1 = await agent_service.create_agent_definition(
        company_id=company.id,
        agent_id=agent.id,
        user_id=user.id,
        version="1.1",
        system_prompt="Updated prompt v1.1",
        model="claude-3-5-sonnet",
        capabilities=["sql_query", "chart_gen"],
    )

    assert def_1_1.version == "1.1"
    assert def_1_1.is_current is True

    # Check history
    defs = await agent_service.get_agent_definitions(company.id, agent.id, user.id)
    assert len(defs) == 2
    # v1.1 is current, v1.0 is not current
    current_def = next(d for d in defs if d.is_current)
    old_def = next(d for d in defs if not d.is_current)
    assert current_def.version == "1.1"
    assert old_def.version == "1.0"

    # 2. Duplicate version rejected
    with pytest.raises(DuplicateAgentVersionError, match="Version 1.1 already exists"):
        await agent_service.create_agent_definition(
            company_id=company.id,
            agent_id=agent.id,
            user_id=user.id,
            version="1.1",
        )


@pytest.mark.asyncio
async def test_provision_default_agents(db_session: AsyncSession) -> None:
    """Verify provisioning of the foundational initial agents according to docs/Phases.md Section 8."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)

    user = User(name="Founder", email="defaults@agency.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Autonomous Enterprise")

    agents = await agent_service.provision_default_agents(company.id, user.id)
    assert len(agents) == 11

    # Map by name for inspection
    agent_map = {a.name: a for a in agents}

    # Verify CEO
    ceo = agent_map["CEO"]
    assert ceo.type == "executive"
    assert ceo.reports_to is None
    assert ceo.authority_level == "executive"

    # Verify CTO and subordinates
    cto = agent_map["CTO"]
    assert cto.reports_to == ceo.id
    assert agent_map["Software Architect"].reports_to == cto.id
    assert agent_map["Full Stack Engineer"].reports_to == cto.id

    # Verify CMO and subordinates
    cmo = agent_map["CMO"]
    assert cmo.reports_to == ceo.id
    assert agent_map["Marketing Strategist"].reports_to == cmo.id
    assert agent_map["Copywriter"].reports_to == cmo.id

    # Verify Sales Director and subordinates
    sales_dir = agent_map["Sales Director"]
    assert sales_dir.reports_to == ceo.id
    assert agent_map["Lead Researcher"].reports_to == sales_dir.id
    assert agent_map["Sales Analyst"].reports_to == sales_dir.id

    # Verify Executive Assistant
    ea = agent_map["Executive Assistant"]
    assert ea.reports_to == ceo.id

    # Calling provision again returns existing agents without duplicates
    agents_again = await agent_service.provision_default_agents(company.id, user.id)
    assert len(agents_again) == 11
