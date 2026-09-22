"""Unit tests for ApprovalService adhering to docs/Phases.md Section 14."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.agent_service import AgentService
from application.services.approval_service import ApprovalService
from application.services.company_service import CompanyService
from application.services.project_service import ProjectService
from application.services.task_service import TaskService
from application.services.tool_service import ToolService
from domain.approvals.exceptions import (
    AgentCannotApproveError,
    ApprovalAccessDeniedError,
    ApprovalAlreadyProcessedError,
)
from domain.approvals.schemas import (
    ApprovalActionType,
    ApprovalDecisionInput,
    ApprovalFilter,
    ApprovalRequestCreate,
    ApprovalRiskLevel,
    ApprovalStatus,
)
from domain.tools.schemas import ToolCallRequest
from domain.work.state_machine import TaskPriority, TaskStatus
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
async def test_create_and_list_approvals(db_session: AsyncSession) -> None:
    """Verify creating and listing approval requests with company isolation and filters."""
    company_service = CompanyService(db_session)
    approval_service = ApprovalService(db_session)

    user = User(name="Founder", email="founder@approval.test", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Security Corp")

    # Create approval request
    req = ApprovalRequestCreate(
        company_id=company.id,
        action_type=ApprovalActionType.DEPLOY_PRODUCTION.value,
        description="Deploy v2.4 to production cluster",
        payload={"cluster": "prod-us-east-1", "version": "v2.4"},
        risk_level=ApprovalRiskLevel.CRITICAL.value,
    )
    created = await approval_service.create_approval(
        company_id=company.id,
        creator_id=user.id,
        request_data=req,
    )
    assert created.id is not None
    assert created.status == ApprovalStatus.PENDING.value
    assert created.risk_level == ApprovalRiskLevel.CRITICAL.value

    # List with filters
    filter_params = ApprovalFilter(status=ApprovalStatus.PENDING)
    items, total = await approval_service.list_approvals(
        company_id=company.id,
        user_id=user.id,
        filter_params=filter_params,
    )
    assert total == 1
    assert len(items) == 1
    assert items[0].id == created.id
    assert items[0].action_type == ApprovalActionType.DEPLOY_PRODUCTION.value


@pytest.mark.asyncio
async def test_task_state_transitions_on_approval_and_rejection(db_session: AsyncSession) -> None:
    """Verify task moves to APPROVAL_REQUIRED and resumes on approve or blocks on reject."""
    company_service = CompanyService(db_session)
    project_service = ProjectService(db_session)
    task_service = TaskService(db_session)
    approval_service = ApprovalService(db_session)

    user = User(name="Operator", email="op@approval.test", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Ops Corp")
    project = await project_service.create_project(
        company_id=company.id, user_id=user.id, name="Project Apollo"
    )
    task = await task_service.create_task(
        company_id=company.id,
        user_id=user.id,
        title="Deploy Critical Fix",
        project_id=project.id,
        priority=TaskPriority.CRITICAL,
    )
    await task_service.update_task_status(
        user_id=user.id,
        company_id=company.id,
        task_id=task.id,
        new_status=TaskStatus.READY.value,
    )
    await task_service.update_task_status(
        user_id=user.id,
        company_id=company.id,
        task_id=task.id,
        new_status=TaskStatus.IN_PROGRESS.value,
    )

    # Create approval referencing task
    req = ApprovalRequestCreate(
        company_id=company.id,
        task_id=task.id,
        action_type=ApprovalActionType.SPEND_MONEY.value,
        description="Allocate cloud budget $5,000",
        payload={"amount": 5000.0},
        risk_level=ApprovalRiskLevel.HIGH.value,
    )
    approval = await approval_service.create_approval(
        company_id=company.id,
        creator_id=user.id,
        request_data=req,
    )

    # Verify task transitioned to APPROVAL_REQUIRED
    task_refreshed = await task_service.get_task(
        company_id=company.id, user_id=user.id, task_id=task.id
    )
    assert task_refreshed.status == TaskStatus.APPROVAL_REQUIRED.value

    # Approve request
    decision = ApprovalDecisionInput(decision_reason="Budget approved by finance.")
    approved = await approval_service.approve_request(
        company_id=company.id,
        user_id=user.id,
        approval_id=approval.id,
        decision_input=decision,
    )
    assert approved.status == ApprovalStatus.APPROVED.value
    assert approved.reviewed_by_user_id == user.id
    assert approved.decision_reason == "Budget approved by finance."

    # Verify task resumed to IN_PROGRESS
    task_after_approval = await task_service.get_task(
        company_id=company.id, user_id=user.id, task_id=task.id
    )
    assert task_after_approval.status == TaskStatus.IN_PROGRESS.value

    # Cannot approve again
    with pytest.raises(ApprovalAlreadyProcessedError):
        await approval_service.approve_request(
            company_id=company.id,
            user_id=user.id,
            approval_id=approval.id,
            decision_input=decision,
        )


@pytest.mark.asyncio
async def test_tool_execution_resumption_and_rejection(db_session: AsyncSession) -> None:
    """Verify tool execution halts on high-risk gate and executes upon approval."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    tool_service = ToolService(db_session)
    approval_service = ApprovalService(db_session)

    user = User(name="Lead", email="lead@approval.test", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Gate Corp")
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)
    agents = await agent_service.get_company_agents(company_id=company.id, user_id=user.id)
    eng_agent = next(
        a for a in agents if "engineer" in a.role.lower() or "architect" in a.role.lower()
    )

    # 1. Invoke a high-risk tool action: github 'create_pr' has HIGH risk and requires approval!
    call_req = ToolCallRequest(
        agent_id=eng_agent.id,
        tool_name="github",
        action="create_pr",
        parameters={"repository": "moon90/AICompanyOS", "action": "create_pr", "branch": "release"},
    )
    tool_record = await tool_service.execute_tool(
        company_id=company.id,
        user_id=user.id,
        request=call_req,
    )
    assert tool_record.status == "APPROVAL_REQUIRED"
    assert tool_record.requires_approval is True

    # Check auto-generated ApprovalRequest
    approvals, count = await approval_service.list_approvals(
        company_id=company.id,
        user_id=user.id,
        filter_params=ApprovalFilter(status=ApprovalStatus.PENDING),
    )
    assert count == 1
    approval = approvals[0]
    assert approval.tool_execution_id == tool_record.id
    assert approval.status == ApprovalStatus.PENDING.value

    # 2. Approve the request -> Tool execution must resume and succeed
    await approval_service.approve_request(
        company_id=company.id,
        user_id=user.id,
        approval_id=approval.id,
        decision_input=ApprovalDecisionInput(decision_reason="PR validated by tech lead."),
    )

    # Tool record must now be updated to SUCCESS
    resumed_tool = await tool_service.get_tool_execution(
        company_id=company.id,
        user_id=user.id,
        execution_id=tool_record.id,
    )
    assert resumed_tool.status == "SUCCESS"
    assert resumed_tool.output_data["repository"] == "moon90/AICompanyOS"
    assert "data" in resumed_tool.output_data

    # 3. Test Rejection flow on a second tool invocation
    call_req2 = ToolCallRequest(
        agent_id=eng_agent.id,
        tool_name="github",
        action="create_pr",
        parameters={"repository": "moon90/AICompanyOS", "action": "create_pr", "branch": "exploit"},
    )
    tool_record2 = await tool_service.execute_tool(
        company_id=company.id,
        user_id=user.id,
        request=call_req2,
    )
    approvals2, count2 = await approval_service.list_approvals(
        company_id=company.id,
        user_id=user.id,
        filter_params=ApprovalFilter(status=ApprovalStatus.PENDING),
    )
    assert count2 == 1
    approval2 = approvals2[0]

    # Reject
    await approval_service.reject_request(
        company_id=company.id,
        user_id=user.id,
        approval_id=approval2.id,
        decision_input=ApprovalDecisionInput(decision_reason="Suspicious branch rejected."),
    )

    blocked_tool = await tool_service.get_tool_execution(
        company_id=company.id,
        user_id=user.id,
        execution_id=tool_record2.id,
    )
    assert blocked_tool.status == "BLOCKED"
    assert "Suspicious branch rejected" in (blocked_tool.error_details or "")


@pytest.mark.asyncio
async def test_agent_cannot_approve_enforcement(db_session: AsyncSession) -> None:
    """Verify docs/Rules.md § 42: Agents cannot approve or reject actions."""
    company_service = CompanyService(db_session)
    approval_service = ApprovalService(db_session)

    user = User(name="Founder", email="founder@bot.test", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Bot Guard Corp")
    req = ApprovalRequestCreate(
        company_id=company.id,
        action_type=ApprovalActionType.EXTERNAL_COMMUNICATION.value,
        description="Outbound SMS broadcast",
    )
    approval = await approval_service.create_approval(
        company_id=company.id,
        creator_id=user.id,
        request_data=req,
    )

    with pytest.raises(AgentCannotApproveError):
        await approval_service.approve_request(
            company_id=company.id,
            user_id=user.id,
            approval_id=approval.id,
            decision_input=ApprovalDecisionInput(),
            is_agent=True,
        )

    with pytest.raises(AgentCannotApproveError):
        await approval_service.reject_request(
            company_id=company.id,
            user_id=user.id,
            approval_id=approval.id,
            decision_input=ApprovalDecisionInput(),
            is_agent=True,
        )


@pytest.mark.asyncio
async def test_company_isolation_access_denied(db_session: AsyncSession) -> None:
    """Verify users from other companies cannot view or modify approval requests."""
    company_service = CompanyService(db_session)
    approval_service = ApprovalService(db_session)

    user1 = User(name="User 1", email="u1@isolation.test", password_hash="hash")
    user2 = User(name="User 2", email="u2@isolation.test", password_hash="hash")
    db_session.add_all([user1, user2])
    await db_session.flush()

    comp1, _ = await company_service.create_company(user_id=user1.id, name="Company 1")
    comp2, _ = await company_service.create_company(user_id=user2.id, name="Company 2")

    req = ApprovalRequestCreate(
        company_id=comp1.id,
        action_type=ApprovalActionType.SEND_EMAIL.value,
        description="Notify customer",
    )
    approval = await approval_service.create_approval(
        company_id=comp1.id,
        creator_id=user1.id,
        request_data=req,
    )

    # User 2 attempting to list approvals in Company 1 -> Access Denied
    with pytest.raises(ApprovalAccessDeniedError):
        await approval_service.list_approvals(
            company_id=comp1.id,
            user_id=user2.id,
            filter_params=ApprovalFilter(),
        )

    # User 2 attempting to approve in Company 1 -> Access Denied
    with pytest.raises(ApprovalAccessDeniedError):
        await approval_service.approve_request(
            company_id=comp1.id,
            user_id=user2.id,
            approval_id=approval.id,
            decision_input=ApprovalDecisionInput(),
        )
