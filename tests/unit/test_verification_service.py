"""Unit tests for VerificationService adhering to docs/Phases.md Section 26, docs/Architecture.md Sections 71-72, and docs/Rules.md Sections 17 & 146."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.verification_service import VerificationService
from domain.verification.exceptions import (
    VerificationAccessDeniedError,
    VerificationNotFoundError,
)
from domain.verification.schemas import (
    BenchmarkCategory,
    BenchmarkRunRequest,
    PipelineStage,
    VerificationStatus,
)
from infrastructure.database.base import Base
from infrastructure.database.models import (
    Agent,
    Artifact,
    Company,
    CompanyMember,
    Project,
    Task,
    TaskFileChange,
    ToolExecutionRecord,
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
    """Seed test company, user, project, agent, tasks, executions, and artifacts."""
    user = User(
        id="usr-vrf-001",
        email="evaluator@company.os",
        password_hash="hashed_secret",
        name="Lead AI Evaluator",
    )
    unauthorized_user = User(
        id="usr-vrf-999",
        email="outsider@external.os",
        password_hash="hashed_secret",
        name="External Observer",
    )
    company = Company(
        id="cmp-vrf-001",
        name="Reliability Labs Inc",
        description="Company testing autonomous verification harnesses",
    )
    member = CompanyMember(
        id="mem-vrf-001",
        company_id=company.id,
        user_id=user.id,
        role="OWNER",
        status="active",
    )
    project = Project(
        id="prj-vrf-001",
        company_id=company.id,
        name="Verification Pipeline Engine",
        description="Core evaluation engine",
        status="ACTIVE",
    )
    agent = Agent(
        id="agt-vrf-001",
        company_id=company.id,
        name="Engineering Specialist",
        role="Engineering",
        mission="Build robust software",
        status="ACTIVE",
    )

    # Valid task with evidence and tool execution
    task_valid = Task(
        id="tsk-vrf-001",
        company_id=company.id,
        project_id=project.id,
        title="Implement Rate Limiting Algorithm",
        description="Write sliding window token rate limiter with comprehensive unit tests.",
        status="COMPLETED",
        priority="HIGH",
        assigned_to_agent_id=agent.id,
        created_by_user_id=user.id,
    )

    # Incomplete / failing task
    task_incomplete = Task(
        id="tsk-vrf-002",
        company_id=company.id,
        project_id=project.id,
        title="Unverified Task",
        description="Missing implementation deliverables.",
        status="PLANNED",
        priority="LOW",
        assigned_to_agent_id=agent.id,
        created_by_user_id=user.id,
    )

    # Artifact adhering to Rule 146 (references sources & evidence)
    artifact_grounded = Artifact(
        id="art-vrf-001",
        company_id=company.id,
        project_id=project.id,
        task_id=task_valid.id,
        creator_name="Lead AI Evaluator",
        name="Rate Limiter Verification Report",
        artifact_type="REPORT",
        content="## Empirical Findings\nTested with 1,000 req/sec across 10 concurrent threads.\nSource: Load benchmark tests.",
        change_summary="Empirical evaluation report with verified benchmarks.",
        version=1,
        created_by_agent_id=agent.id,
    )

    tool_exec = ToolExecutionRecord(
        id="ter-vrf-001",
        company_id=company.id,
        task_id=task_valid.id,
        agent_id=agent.id,
        tool_name="pytest_runner",
        action="execute_tests",
        input_params={"suite": "tests/unit"},
        output_data={"passed": 24, "failed": 0},
        status="SUCCESS",
    )

    file_change = TaskFileChange(
        id="tfc-vrf-001",
        company_id=company.id,
        task_id=task_valid.id,
        file_path="infrastructure/security/rate_limiter.py",
        agent_id=agent.id,
        agent_name=agent.name,
        change_type="MODIFIED",
        additions=45,
        deletions=2,
    )

    db_session.add_all(
        [
            user,
            unauthorized_user,
            company,
            member,
            project,
            agent,
            task_valid,
            task_incomplete,
            artifact_grounded,
            tool_exec,
            file_change,
        ]
    )
    await db_session.commit()

    return {
        "company_id": company.id,
        "user_id": user.id,
        "unauthorized_user_id": unauthorized_user.id,
        "task_valid_id": task_valid.id,
        "task_incomplete_id": task_incomplete.id,
        "artifact_id": artifact_grounded.id,
        "agent_id": agent.id,
    }


@pytest.mark.asyncio
async def test_verify_task_passing_completion_rule(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify task passes 5-stage pipeline and Rule 17 completion rule transitions status to VERIFIED."""
    service = VerificationService(db_session)

    run = await service.verify_task(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        task_id=test_data["task_valid_id"],
    )

    assert run.target_type == "TASK"
    assert run.target_id == test_data["task_valid_id"]
    assert run.status == VerificationStatus.PASSED
    assert run.pipeline_stage == PipelineStage.COMPLETED
    assert run.overall_score >= 80.0
    assert len(run.criterion_scores) == 8  # All 8 canonical dimensions

    # Verify task status was transitioned to VERIFIED in database (Rule 17)
    task = await db_session.get(Task, test_data["task_valid_id"])
    assert task is not None
    assert task.status == "VERIFIED"


@pytest.mark.asyncio
async def test_verify_task_failing_rule_17(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify incomplete task with no evidence fails verification and does not transition to VERIFIED."""
    service = VerificationService(db_session)

    run = await service.verify_task(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        task_id=test_data["task_incomplete_id"],
    )

    assert run.target_type == "TASK"
    assert run.status == VerificationStatus.FAILED
    assert run.overall_score < 80.0

    # Ensure task did NOT become VERIFIED
    task = await db_session.get(Task, test_data["task_incomplete_id"])
    assert task is not None
    assert task.status != "VERIFIED"


@pytest.mark.asyncio
async def test_verify_artifact_evidence_rule_146(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify artifact is checked for schema completeness and evidence citations (Rule 146)."""
    service = VerificationService(db_session)

    run = await service.verify_artifact(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        artifact_id=test_data["artifact_id"],
    )

    assert run.target_type == "ARTIFACT"
    assert run.status == VerificationStatus.PASSED
    assert run.overall_score >= 75.0
    assert run.completed_at is not None


@pytest.mark.asyncio
async def test_run_benchmarks_and_list(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Test representative benchmark execution across Section 26 categories."""
    service = VerificationService(db_session)

    # 1. Run CEO benchmark
    ceo_res = await service.run_benchmark(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=BenchmarkRunRequest(category=BenchmarkCategory.CEO),
    )
    assert ceo_res.category == BenchmarkCategory.CEO
    assert ceo_res.passed is True
    assert ceo_res.overall_score >= 85.0
    assert ceo_res.run_id.startswith("vrf-bmk-")

    # 2. List all seeded benchmarks
    benchmarks = await service.list_benchmarks(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
    )
    assert len(benchmarks) == 8
    categories = {b.category for b in benchmarks}
    assert BenchmarkCategory.CEO in categories
    assert BenchmarkCategory.MARKETING in categories
    assert BenchmarkCategory.ENGINEERING in categories
    assert BenchmarkCategory.TOOL in categories
    assert BenchmarkCategory.APPROVAL in categories
    assert BenchmarkCategory.FAILURE in categories
    assert BenchmarkCategory.RECOVERY in categories


@pytest.mark.asyncio
async def test_verification_runs_and_telemetry(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test retrieving verification runs and calculating aggregated telemetry."""
    service = VerificationService(db_session)

    # Run verification to produce data
    await service.verify_task(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        task_id=test_data["task_valid_id"],
    )

    # List runs
    runs_res = await service.list_runs(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
    )
    assert runs_res.total >= 1
    assert len(runs_res.items) >= 1

    first_run = runs_res.items[0]
    detail = await service.get_run(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        run_id=first_run.id,
    )
    assert detail.id == first_run.id
    assert len(detail.criterion_scores) > 0

    # Telemetry
    telem = await service.get_telemetry(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
    )
    assert telem.company_id == test_data["company_id"]
    assert telem.total_runs >= 1
    assert telem.passed_runs >= 1
    assert telem.pass_rate > 0.0
    assert telem.avg_overall_score > 0.0


@pytest.mark.asyncio
async def test_verification_tenant_isolation_and_errors(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test cross-tenant access rejection and missing target error handling."""
    service = VerificationService(db_session)

    # Unauthorized user
    with pytest.raises(VerificationAccessDeniedError):
        await service.verify_task(
            company_id=test_data["company_id"],
            user_id=test_data["unauthorized_user_id"],
            task_id=test_data["task_valid_id"],
        )

    # Non-existent task
    with pytest.raises(VerificationNotFoundError):
        await service.verify_task(
            company_id=test_data["company_id"],
            user_id=test_data["user_id"],
            task_id="tsk-non-existent",
        )
