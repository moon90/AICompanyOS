"""Unit tests for ToolService adhering to docs/Phases.md Section 13."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.agent_service import AgentService
from application.services.company_service import CompanyService
from application.services.tool_service import ToolService
from domain.runtime.exceptions import AgentInactiveError
from domain.tools.exceptions import (
    ToolAccessDeniedError,
    ToolExecutionNotFoundError,
)
from domain.tools.schemas import (
    ToolCallRequest,
    ToolExecutionStatus,
    ToolRiskLevel,
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
async def test_tool_service_list_tools(db_session: AsyncSession) -> None:
    """Verify listing tools with role filtering through ToolService."""
    company_service = CompanyService(db_session)
    tool_service = ToolService(db_session)

    user = User(name="Founder", email="founder@tools.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Tool Corp")

    # List all tools
    all_tools = await tool_service.list_tools(company_id=company.id, user_id=user.id)
    assert len(all_tools) == 3

    # Filter by role
    eng_tools = await tool_service.list_tools(
        company_id=company.id, user_id=user.id, role="software_engineer"
    )
    assert any(t.name == "github" for t in eng_tools)

    hr_tools = await tool_service.list_tools(
        company_id=company.id, user_id=user.id, role="hr_specialist"
    )
    assert not any(t.name == "github" for t in hr_tools)


@pytest.mark.asyncio
async def test_tool_service_execute_web_search(db_session: AsyncSession) -> None:
    """Verify executing tool persists ToolExecutionRecord in database."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    tool_service = ToolService(db_session)

    user = User(name="Founder", email="founder2@tools.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Search Corp")
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)
    agents = await agent_service.get_company_agents(company_id=company.id, user_id=user.id)
    agent = agents[0]

    request = ToolCallRequest(
        agent_id=agent.id,
        tool_name="web_search",
        action="search",
        parameters={"query": "python concurrency"},
    )

    record = await tool_service.execute_tool(
        company_id=company.id,
        user_id=user.id,
        request=request,
    )

    assert record.id is not None
    assert record.company_id == company.id
    assert record.agent_id == agent.id
    assert record.tool_name == "web_search"
    assert record.status == ToolExecutionStatus.SUCCESS.value
    assert record.risk_level == ToolRiskLevel.LOW.value
    assert record.requires_approval is False
    assert "results" in record.output_data


@pytest.mark.asyncio
async def test_tool_service_execute_approval_required(db_session: AsyncSession) -> None:
    """Verify high-risk actions halt with APPROVAL_REQUIRED and persist audit log."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    tool_service = ToolService(db_session)

    user = User(name="Founder", email="founder3@tools.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Risk Corp")
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)
    agents = await agent_service.get_company_agents(company_id=company.id, user_id=user.id)
    eng_agent = next(
        a for a in agents if "engineer" in a.role.lower() or "backend" in a.role.lower()
    )

    request = ToolCallRequest(
        agent_id=eng_agent.id,
        tool_name="github",
        action="create_pr",
        parameters={"repository": "moon90/AICompanyOS", "action": "create_pr", "branch": "main"},
    )

    record = await tool_service.execute_tool(
        company_id=company.id,
        user_id=user.id,
        request=request,
    )

    assert record.status == ToolExecutionStatus.APPROVAL_REQUIRED.value
    assert record.requires_approval is True
    assert record.risk_level in (ToolRiskLevel.HIGH.value, ToolRiskLevel.CRITICAL.value)
    assert record.error_details is not None
    assert "requires human operator approval" in record.error_details


@pytest.mark.asyncio
async def test_tool_service_membership_access_denied(db_session: AsyncSession) -> None:
    """Verify unauthorized users cannot execute tools or view records."""
    company_service = CompanyService(db_session)
    tool_service = ToolService(db_session)

    user1 = User(name="Owner", email="owner@tools.os", password_hash="hash")
    user2 = User(name="Intruder", email="intruder@tools.os", password_hash="hash")
    db_session.add_all([user1, user2])
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user1.id, name="Private Corp")

    with pytest.raises(ToolAccessDeniedError):
        await tool_service.list_tools(company_id=company.id, user_id=user2.id)


@pytest.mark.asyncio
async def test_tool_service_inactive_agent_rejected(db_session: AsyncSession) -> None:
    """Verify inactive agents cannot invoke tools."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    tool_service = ToolService(db_session)

    user = User(name="Founder", email="founder4@tools.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Inactive Corp")
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)
    agents = await agent_service.get_company_agents(company_id=company.id, user_id=user.id)
    agent = agents[0]

    # Deactivate agent
    agent.status = "inactive"
    await db_session.commit()

    request = ToolCallRequest(
        agent_id=agent.id,
        tool_name="web_search",
        action="search",
        parameters={"query": "test"},
    )

    with pytest.raises(AgentInactiveError):
        await tool_service.execute_tool(
            company_id=company.id,
            user_id=user.id,
            request=request,
        )


@pytest.mark.asyncio
async def test_tool_service_list_and_get_executions(db_session: AsyncSession) -> None:
    """Verify listing and retrieving specific tool execution records."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    tool_service = ToolService(db_session)

    user = User(name="Founder", email="founder5@tools.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Query Corp")
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)
    agents = await agent_service.get_company_agents(company_id=company.id, user_id=user.id)
    agent = agents[0]

    req1 = ToolCallRequest(
        agent_id=agent.id,
        tool_name="web_search",
        action="search",
        parameters={"query": "query 1"},
    )
    req2 = ToolCallRequest(
        agent_id=agent.id,
        tool_name="documents",
        action="read",
        parameters={"document_id": "architecture_spec"},
    )

    rec1 = await tool_service.execute_tool(company.id, user.id, req1)
    await tool_service.execute_tool(company.id, user.id, req2)

    records, total = await tool_service.list_tool_executions(
        company_id=company.id,
        user_id=user.id,
    )
    assert total == 2
    assert len(records) == 2

    # Get single
    fetched = await tool_service.get_tool_execution(
        company_id=company.id,
        user_id=user.id,
        execution_id=rec1.id,
    )
    assert fetched.id == rec1.id
    assert fetched.tool_name == "web_search"

    # Non-existent raises ToolExecutionNotFoundError
    with pytest.raises(ToolExecutionNotFoundError):
        await tool_service.get_tool_execution(
            company_id=company.id,
            user_id=user.id,
            execution_id="non-existent-id",
        )
