"""Unit tests for ErrorService adhering to docs/Phases.md Section 19 and docs/Memory.md Section 20."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.error_service import ErrorService
from domain.errors.exceptions import (
    ErrorAccessDeniedError,
    MissingEvidenceError,
    MissingResolutionError,
)
from domain.errors.schemas import (
    ErrorAssignPayload,
    ErrorCreatePayload,
    ErrorResolvePayload,
    ErrorSeverity,
    ErrorStatus,
    ErrorVerifyPayload,
)
from infrastructure.database.base import Base
from infrastructure.database.models import (
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
        id="usr-err-001",
        email="operator@errors.test",
        name="Bug Lead",
        password_hash="hash",
    )
    db_session.add(user)

    company = Company(
        id="cmp-err-001",
        name="Error Test Corp",
        status="active",
    )
    db_session.add(company)

    member = CompanyMember(
        id="mem-err-001",
        company_id=company.id,
        user_id=user.id,
        role="owner",
        status="active",
    )
    db_session.add(member)

    dept = Department(
        id="dep-err-001",
        company_id=company.id,
        name="Engineering",
        code="ENG",
    )
    db_session.add(dept)

    agent = Agent(
        id="agt-err-001",
        company_id=company.id,
        department_id=dept.id,
        name="Coder Agent",
        role="Backend Engineer",
        type="specialist",
        status="active",
        authority_level="specialist",
    )
    db_session.add(agent)

    proj = Project(
        id="prj-err-001",
        company_id=company.id,
        name="Core Platform",
        status="ACTIVE",
    )
    db_session.add(proj)

    task = Task(
        id="tsk-err-001",
        company_id=company.id,
        project_id=proj.id,
        title="Implement Auth",
        status="FAILED",
    )
    db_session.add(task)

    # Secondary company for tenant isolation tests
    company2 = Company(
        id="cmp-err-002",
        name="Other Corp",
        status="active",
    )
    db_session.add(company2)

    await db_session.commit()

    return {
        "company_id": company.id,
        "company2_id": company2.id,
        "user_id": user.id,
        "agent_id": agent.id,
        "project_id": proj.id,
        "task_id": task.id,
    }


@pytest.mark.asyncio
async def test_create_error_success(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Verify an error can be created answering discovery questions."""
    service = ErrorService(db_session)
    payload = ErrorCreatePayload(
        title="Uncaught NullPointerException in payment flow",
        description="Payment webhook crashed on empty payload",
        severity=ErrorSeverity.HIGH,
        detected_by="agent:Coder Agent",
        project_id=test_data["project_id"],
        task_id=test_data["task_id"],
        evidence={"traceback": "NullPointerException at line 42"},
    )
    error = await service.create_error(
        company_id=test_data["company_id"],
        payload=payload,
        user_id=test_data["user_id"],
    )

    assert error.id is not None
    assert error.title == "Uncaught NullPointerException in payment flow"
    assert error.severity == ErrorSeverity.HIGH
    assert error.status == ErrorStatus.OPEN
    assert error.detected_by == "agent:Coder Agent"
    assert error.project_name == "Core Platform"
    assert error.task_title == "Implement Auth"
    assert error.evidence["traceback"] == "NullPointerException at line 42"


@pytest.mark.asyncio
async def test_create_error_with_assignee(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify error created with assignee initializes to ASSIGNED status."""
    service = ErrorService(db_session)
    payload = ErrorCreatePayload(
        title="Database deadlock in order processing",
        severity=ErrorSeverity.CRITICAL,
        detected_by="user:Bug Lead",
        assigned_to="Coder Agent",
        assigned_agent_id=test_data["agent_id"],
    )
    error = await service.create_error(
        company_id=test_data["company_id"],
        payload=payload,
        user_id=test_data["user_id"],
    )

    assert error.status == ErrorStatus.ASSIGNED
    assert error.assigned_to == "Coder Agent"
    assert error.assigned_agent_name == "Coder Agent"


@pytest.mark.asyncio
async def test_assign_error(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Verify assigning an error transitions status to ASSIGNED."""
    service = ErrorService(db_session)
    error = await service.create_error(
        company_id=test_data["company_id"],
        payload=ErrorCreatePayload(
            title="CSS overflow on mobile viewport",
            severity=ErrorSeverity.LOW,
            detected_by="QA Agent",
        ),
        user_id=test_data["user_id"],
    )
    assert error.status == ErrorStatus.OPEN

    assigned = await service.assign_error(
        company_id=test_data["company_id"],
        error_id=error.id,
        payload=ErrorAssignPayload(
            assigned_to="Coder Agent", assigned_agent_id=test_data["agent_id"]
        ),
        user_id=test_data["user_id"],
    )
    assert assigned.status == ErrorStatus.ASSIGNED
    assert assigned.assigned_to == "Coder Agent"
    assert assigned.assigned_agent_name == "Coder Agent"


@pytest.mark.asyncio
async def test_start_investigation(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Verify starting investigation updates status and investigator."""
    service = ErrorService(db_session)
    error = await service.create_error(
        company_id=test_data["company_id"],
        payload=ErrorCreatePayload(
            title="Slow query on analytics",
            severity=ErrorSeverity.MEDIUM,
            detected_by="Monitoring",
        ),
        user_id=test_data["user_id"],
    )

    investigating = await service.start_investigation(
        company_id=test_data["company_id"],
        error_id=error.id,
        investigated_by="Coder Agent",
        user_id=test_data["user_id"],
    )
    assert investigating.status == ErrorStatus.INVESTIGATING
    assert investigating.investigated_by == "Coder Agent"


@pytest.mark.asyncio
async def test_resolve_error_success(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Verify resolving error updates status, root cause, and resolved_at."""
    service = ErrorService(db_session)
    error = await service.create_error(
        company_id=test_data["company_id"],
        payload=ErrorCreatePayload(
            title="Memory leak in socket handler",
            severity=ErrorSeverity.CRITICAL,
            detected_by="Observability",
        ),
        user_id=test_data["user_id"],
    )

    resolved = await service.resolve_error(
        company_id=test_data["company_id"],
        error_id=error.id,
        payload=ErrorResolvePayload(
            resolved_by="Coder Agent",
            resolution="Closed unhandled socket connections in finally block",
            root_cause="Event listener retained references to terminated sockets",
            evidence={"commit": "abc1234"},
        ),
        user_id=test_data["user_id"],
    )
    assert resolved.status == ErrorStatus.RESOLVED
    assert resolved.resolved_by == "Coder Agent"
    assert resolved.resolution == "Closed unhandled socket connections in finally block"
    assert resolved.root_cause == "Event listener retained references to terminated sockets"
    assert resolved.resolved_at is not None
    assert resolved.evidence["commit"] == "abc1234"


@pytest.mark.asyncio
async def test_resolve_error_missing_resolution(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify resolving an error without resolution details raises an error."""
    service = ErrorService(db_session)
    error = await service.create_error(
        company_id=test_data["company_id"],
        payload=ErrorCreatePayload(
            title="Typo in landing page",
            severity=ErrorSeverity.LOW,
            detected_by="User",
        ),
        user_id=test_data["user_id"],
    )

    with pytest.raises(MissingResolutionError):
        await service.resolve_error(
            company_id=test_data["company_id"],
            error_id=error.id,
            payload=ErrorResolvePayload(
                resolved_by="Coder Agent",
                resolution="   ",
            ),
            user_id=test_data["user_id"],
        )


@pytest.mark.asyncio
async def test_verify_error_success(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Verify error verification requires evidence and updates status to VERIFIED or CLOSED."""
    service = ErrorService(db_session)
    error = await service.create_error(
        company_id=test_data["company_id"],
        payload=ErrorCreatePayload(
            title="API rate limiter bypass",
            severity=ErrorSeverity.HIGH,
            detected_by="Security Audit",
        ),
        user_id=test_data["user_id"],
    )
    await service.resolve_error(
        company_id=test_data["company_id"],
        error_id=error.id,
        payload=ErrorResolvePayload(
            resolved_by="Security Engineer",
            resolution="Added IP validation header parsing check",
        ),
        user_id=test_data["user_id"],
    )

    verified = await service.verify_error(
        company_id=test_data["company_id"],
        error_id=error.id,
        payload=ErrorVerifyPayload(
            verified_by="QA Team",
            evidence={"automated_tests": "passed", "test_run_id": "tr-9988"},
            close_immediately=False,
        ),
        user_id=test_data["user_id"],
    )
    assert verified.status == ErrorStatus.VERIFIED
    assert verified.verified_by == "QA Team"
    assert verified.verified_at is not None
    assert verified.evidence["test_run_id"] == "tr-9988"


@pytest.mark.asyncio
async def test_verify_error_missing_evidence(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify error verification without evidence raises MissingEvidenceError."""
    service = ErrorService(db_session)
    error = await service.create_error(
        company_id=test_data["company_id"],
        payload=ErrorCreatePayload(
            title="Broken button",
            severity=ErrorSeverity.LOW,
            detected_by="Manual QA",
        ),
        user_id=test_data["user_id"],
    )

    with pytest.raises(MissingEvidenceError):
        await service.verify_error(
            company_id=test_data["company_id"],
            error_id=error.id,
            payload=ErrorVerifyPayload(
                verified_by="QA Team",
                evidence={},
            ),
            user_id=test_data["user_id"],
        )


@pytest.mark.asyncio
async def test_reopen_and_close_error(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Verify lifecycle transitions for reopen and close."""
    service = ErrorService(db_session)
    error = await service.create_error(
        company_id=test_data["company_id"],
        payload=ErrorCreatePayload(
            title="Transient 504 Gateway Timeout",
            severity=ErrorSeverity.MEDIUM,
            detected_by="SRE",
        ),
        user_id=test_data["user_id"],
    )
    await service.resolve_error(
        company_id=test_data["company_id"],
        error_id=error.id,
        payload=ErrorResolvePayload(
            resolved_by="SRE",
            resolution="Increased upstream timeout",
        ),
        user_id=test_data["user_id"],
    )

    # Reopen
    reopened = await service.reopen_error(
        company_id=test_data["company_id"],
        error_id=error.id,
        reason="Timeouts reproduced during load test",
        actor="Load Test Agent",
        user_id=test_data["user_id"],
    )
    assert reopened.status == ErrorStatus.REOPENED
    assert reopened.resolved_at is None
    assert reopened.evidence["reopened_reason"] == "Timeouts reproduced during load test"

    # Close
    closed = await service.close_error(
        company_id=test_data["company_id"],
        error_id=error.id,
        actor="Bug Lead",
        user_id=test_data["user_id"],
    )
    assert closed.status == ErrorStatus.CLOSED


@pytest.mark.asyncio
async def test_get_error_summary_and_filtering(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify aggregated summary metrics and list filtering."""
    service = ErrorService(db_session)
    # Create critical open error
    await service.create_error(
        company_id=test_data["company_id"],
        payload=ErrorCreatePayload(
            title="Critical Error 1",
            severity=ErrorSeverity.CRITICAL,
            detected_by="Monitoring",
        ),
        user_id=test_data["user_id"],
    )
    # Create low resolved error
    e2 = await service.create_error(
        company_id=test_data["company_id"],
        payload=ErrorCreatePayload(
            title="Low Error 2",
            severity=ErrorSeverity.LOW,
            detected_by="User",
        ),
        user_id=test_data["user_id"],
    )
    await service.resolve_error(
        company_id=test_data["company_id"],
        error_id=e2.id,
        payload=ErrorResolvePayload(
            resolved_by="Agent",
            resolution="Resolved quickly",
        ),
        user_id=test_data["user_id"],
    )

    summary = await service.get_error_summary(
        company_id=test_data["company_id"], user_id=test_data["user_id"]
    )
    assert summary.total_errors == 2
    assert summary.open_count == 1
    assert summary.resolved_count == 1
    assert summary.critical_count == 1
    assert summary.low_count == 1

    # Filter by severity
    crit_list = await service.get_errors(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        severity=ErrorSeverity.CRITICAL,
    )
    assert len(crit_list.items) == 1
    assert crit_list.items[0].title == "Critical Error 1"


@pytest.mark.asyncio
async def test_multi_tenant_isolation(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Verify unauthorized company access is rejected with ErrorAccessDeniedError."""
    service = ErrorService(db_session)
    payload = ErrorCreatePayload(
        title="Unauthorized error",
        detected_by="Attacker",
    )
    with pytest.raises(ErrorAccessDeniedError):
        await service.create_error(
            company_id=test_data["company2_id"],
            payload=payload,
            user_id=test_data["user_id"],
        )
