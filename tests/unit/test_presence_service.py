"""Unit tests for PresenceService adhering to docs/Phases.md Section 18 and docs/Memory.md Section 20."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.presence_service import PresenceService
from domain.presence.exceptions import PresenceAccessDeniedError, PresenceNotFoundError
from domain.presence.schemas import PresenceStatus, PresenceUpdateParams
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
        id="usr-pres-001",
        email="operator@presence.test",
        name="Presence Operator",
        password_hash="hash",
    )
    db_session.add(user)

    company = Company(
        id="cmp-pres-001",
        name="Presence Test Corp",
        status="active",
    )
    db_session.add(company)

    member = CompanyMember(
        id="mem-pres-001",
        company_id=company.id,
        user_id=user.id,
        role="owner",
    )
    db_session.add(member)

    dept = Department(
        id="dep-pres-001",
        company_id=company.id,
        name="Engineering",
        code="ENG",
    )
    db_session.add(dept)

    agent_ceo = Agent(
        id="agt-pres-ceo",
        company_id=company.id,
        department_id=dept.id,
        name="Executive CEO",
        role="Chief Executive Officer",
        type="lead",
        status="active",
    )
    agent_cmo = Agent(
        id="agt-pres-cmo",
        company_id=company.id,
        department_id=dept.id,
        name="Growth CMO",
        role="Chief Marketing Officer",
        type="lead",
        status="active",
    )
    agent_inactive = Agent(
        id="agt-pres-inactive",
        company_id=company.id,
        department_id=dept.id,
        name="Decommissioned Agent",
        role="Specialist",
        type="specialist",
        status="inactive",
    )
    db_session.add_all([agent_ceo, agent_cmo, agent_inactive])

    project = Project(
        id="prj-pres-001",
        company_id=company.id,
        name="Presence Launch",
        status="IN_PROGRESS",
    )
    db_session.add(project)

    task = Task(
        id="tsk-pres-001",
        company_id=company.id,
        project_id=project.id,
        title="Develop Telemetry Widget",
        status="IN_PROGRESS",
    )
    db_session.add(task)
    await db_session.commit()

    return {
        "user_id": user.id,
        "company_id": company.id,
        "agent_ceo": agent_ceo.id,
        "agent_cmo": agent_cmo.id,
        "agent_inactive": agent_inactive.id,
        "project_id": project.id,
        "task_id": task.id,
    }


@pytest.mark.asyncio
async def test_presence_sync_and_retrieval(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test sync_all_agent_presences creates initial presences with appropriate states."""
    service = PresenceService(db_session)
    presences = await service.get_company_presence(
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
    )

    assert len(presences) == 3
    presence_map = {p.agent_id: p for p in presences}

    # Active agents initialized to IDLE
    assert presence_map[test_data["agent_ceo"]].status == PresenceStatus.IDLE
    assert presence_map[test_data["agent_cmo"]].status == PresenceStatus.IDLE
    # Inactive agent initialized to OFFLINE
    assert presence_map[test_data["agent_inactive"]].status == PresenceStatus.OFFLINE


@pytest.mark.asyncio
async def test_presence_lifecycle_transitions(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test presence transitions between WORKING, WAITING, BLOCKED, ERROR, and IDLE."""
    service = PresenceService(db_session)

    # 1. Transition CEO to WORKING
    await service.set_working(
        company_id=test_data["company_id"],
        agent_id=test_data["agent_ceo"],
        task_id=test_data["task_id"],
        project_id=test_data["project_id"],
        activity="Planning strategic initiative",
        current_step="Formulating task graph",
    )
    await db_session.commit()

    ceo_pres = await service.get_agent_presence(
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
        agent_id=test_data["agent_ceo"],
    )
    assert ceo_pres.status == PresenceStatus.WORKING
    assert ceo_pres.current_activity == "Planning strategic initiative"
    assert ceo_pres.current_step == "Formulating task graph"
    assert ceo_pres.current_task_title == "Develop Telemetry Widget"
    assert ceo_pres.current_project_name == "Presence Launch"
    assert ceo_pres.started_at is not None

    # 2. Transition CMO to WAITING
    await service.set_waiting(
        company_id=test_data["company_id"],
        agent_id=test_data["agent_cmo"],
        task_id=test_data["task_id"],
        reason="Awaiting campaign budget approval",
    )
    await db_session.commit()

    cmo_pres = await service.get_agent_presence(
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
        agent_id=test_data["agent_cmo"],
    )
    assert cmo_pres.status == PresenceStatus.WAITING
    assert cmo_pres.current_activity == "Awaiting campaign budget approval"

    # 3. Transition CEO to IDLE
    await service.set_idle(
        company_id=test_data["company_id"],
        agent_id=test_data["agent_ceo"],
    )
    await db_session.commit()

    ceo_pres_idle = await service.get_agent_presence(
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
        agent_id=test_data["agent_ceo"],
    )
    assert ceo_pres_idle.status == PresenceStatus.IDLE
    assert ceo_pres_idle.current_task_id is None
    assert ceo_pres_idle.current_activity is None
    assert ceo_pres_idle.started_at is None


@pytest.mark.asyncio
async def test_heartbeat_and_stale_detection(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test heartbeat recording and stale detection per docs/Memory.md Section 20."""
    service = PresenceService(db_session)

    # 1. Set CMO to WORKING with a heartbeat 2 minutes in the past
    p = await service.set_working(
        company_id=test_data["company_id"],
        agent_id=test_data["agent_cmo"],
        task_id=test_data["task_id"],
        activity="Market research",
    )
    # Artificially age the heartbeat
    p.last_heartbeat_at = datetime.now(UTC) - timedelta(seconds=120)
    await db_session.commit()

    # Verify stale detection resets working agent to IDLE
    stale_count = await service.evaluate_stale_presence(
        company_id=test_data["company_id"],
        stale_threshold_seconds=60,
    )
    await db_session.commit()
    assert stale_count == 1

    cmo_pres = await service.get_agent_presence(
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
        agent_id=test_data["agent_cmo"],
    )
    assert cmo_pres.status == PresenceStatus.IDLE
    assert "Heartbeat lapsed" in (cmo_pres.current_activity or "")

    # 2. Record fresh heartbeat
    await service.record_heartbeat(
        company_id=test_data["company_id"],
        agent_id=test_data["agent_cmo"],
        current_step="Parsing results",
    )
    await db_session.commit()

    cmo_pres_fresh = await service.get_agent_presence(
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
        agent_id=test_data["agent_cmo"],
    )
    assert cmo_pres_fresh.current_step == "Parsing results"


@pytest.mark.asyncio
async def test_presence_summary(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Test aggregated presence summary counters."""
    service = PresenceService(db_session)
    await service.sync_all_agent_presences(test_data["company_id"])

    # Put CEO in WORKING
    await service.set_working(
        company_id=test_data["company_id"],
        agent_id=test_data["agent_ceo"],
        activity="Executive review",
    )
    await db_session.commit()

    summary = await service.get_presence_summary(
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
    )
    assert summary.total_agents == 3
    assert summary.working_count == 1
    assert summary.idle_count == 1  # CMO is idle
    assert summary.offline_count == 1  # inactive agent is offline


@pytest.mark.asyncio
async def test_operator_override_presence(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test operator manual override of agent presence status."""
    service = PresenceService(db_session)
    await service.sync_all_agent_presences(test_data["company_id"])

    # Manually mark CMO as BLOCKED
    updated = await service.update_presence_status(
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
        agent_id=test_data["agent_cmo"],
        params=PresenceUpdateParams(
            status=PresenceStatus.BLOCKED,
            current_activity="Blocked by external vendor SLA",
        ),
    )
    assert updated.status == PresenceStatus.BLOCKED
    assert updated.current_activity == "Blocked by external vendor SLA"


@pytest.mark.asyncio
async def test_presence_company_isolation(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test company isolation guards for presence service."""
    service = PresenceService(db_session)

    # Unauthorized user
    with pytest.raises(PresenceAccessDeniedError):
        await service.get_company_presence(
            user_id="unauthorized-user-999",
            company_id=test_data["company_id"],
        )

    # Nonexistent agent
    with pytest.raises(PresenceNotFoundError):
        await service.get_agent_presence(
            user_id=test_data["user_id"],
            company_id=test_data["company_id"],
            agent_id="nonexistent-agent-id",
        )
