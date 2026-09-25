"""Unit tests for VoiceService adhering to docs/Phases.md Section 25 and docs/Memory.md Section 60."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.voice_service import VoiceService
from domain.voice.exceptions import (
    InvalidVoiceCommandError,
    VoiceAccessDeniedError,
)
from domain.voice.schemas import (
    VoiceCommandPayload,
    VoiceIntent,
    VoiceSessionCreatePayload,
    VoiceState,
    VoiceSynthesizeRequest,
)
from infrastructure.database.base import Base
from infrastructure.database.models import (
    Agent,
    ApprovalRequest,
    Company,
    CompanyKnowledge,
    CompanyMember,
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
    """Seed test company, user, project, agent, task, approval, and knowledge."""
    user = User(
        id="usr-voice-001",
        email="operator@company.os",
        password_hash="hashed_secret",
        name="Executive Operator",
    )
    unauthorized_user = User(
        id="usr-voice-999",
        email="outsider@external.os",
        password_hash="hashed_secret",
        name="External Stranger",
    )
    company = Company(
        id="cmp-voice-001",
        name="Voice-Driven Ventures",
        description="Company testing real-time voice orchestration",
    )
    member = CompanyMember(
        id="mem-voice-001",
        company_id=company.id,
        user_id=user.id,
        role="OWNER",
        status="active",
    )
    project = Project(
        id="prj-voice-001",
        company_id=company.id,
        name="Core Infrastructure",
        description="Core services",
        status="ACTIVE",
    )
    agent = Agent(
        id="agt-voice-001",
        company_id=company.id,
        name="Marketing Lead",
        role="Marketing",
        mission="You are marketing lead",
        status="IDLE",
    )
    task_blocked = Task(
        id="tsk-voice-001",
        company_id=company.id,
        project_id=project.id,
        title="Deploy Edge Gateway",
        description="Blocked on DNS propagation",
        status="BLOCKED",
        priority="HIGH",
    )
    approval = ApprovalRequest(
        id="app-voice-001",
        company_id=company.id,
        task_id=task_blocked.id,
        action_type="PRODUCTION_DEPLOY",
        description="Approve production deployment to US-East",
        status="PENDING",
    )
    knowledge = CompanyKnowledge(
        id="kn-voice-001",
        company_id=company.id,
        title="Voice Command Policy",
        category="POLICY",
        content="All voice commands are logged as audit events.",
        author_name="Security Lead",
    )

    db_session.add_all(
        [
            user,
            unauthorized_user,
            company,
            member,
            project,
            agent,
            task_blocked,
            approval,
            knowledge,
        ]
    )
    await db_session.commit()

    return {
        "company_id": company.id,
        "user_id": user.id,
        "unauthorized_user_id": unauthorized_user.id,
        "project_id": project.id,
        "agent_id": agent.id,
        "task_id": task_blocked.id,
        "approval_id": approval.id,
        "knowledge_id": knowledge.id,
    }


@pytest.mark.asyncio
async def test_create_and_get_voice_session(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test voice session creation and retrieval."""
    service = VoiceService(db_session)

    # Unauthorized access test
    with pytest.raises(VoiceAccessDeniedError):
        await service.create_session(
            company_id=test_data["company_id"],
            user_id=test_data["unauthorized_user_id"],
            payload=VoiceSessionCreatePayload(title="Illegal Session"),
        )

    # Valid session creation
    session_resp = await service.create_session(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        payload=VoiceSessionCreatePayload(title="Morning Standup Briefing"),
    )
    assert session_resp.id.startswith("vcs-")
    assert session_resp.title == "Morning Standup Briefing"
    assert session_resp.state == VoiceState.IDLE
    assert len(session_resp.interactions) == 0

    # Retrieve session
    fetched = await service.get_session(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        session_id=session_resp.id,
    )
    assert fetched.id == session_resp.id
    assert fetched.title == "Morning Standup Briefing"


@pytest.mark.asyncio
async def test_list_voice_sessions(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Test listing voice sessions for a user."""
    service = VoiceService(db_session)
    await service.create_session(
        test_data["company_id"], test_data["user_id"], VoiceSessionCreatePayload(title="Sess 1")
    )
    await service.create_session(
        test_data["company_id"], test_data["user_id"], VoiceSessionCreatePayload(title="Sess 2")
    )

    list_resp = await service.list_sessions(test_data["company_id"], test_data["user_id"])
    assert list_resp.total >= 2
    assert len(list_resp.items) >= 2


@pytest.mark.asyncio
async def test_voice_command_executive_briefing(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test Section 25 status briefing: 'CEO, what's happening?'."""
    service = VoiceService(db_session)

    resp = await service.process_command(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        payload=VoiceCommandPayload(transcript="CEO, what's happening?"),
    )

    assert resp.intent == VoiceIntent.STATUS_QUERY
    assert resp.state == VoiceState.SPEAKING
    assert "active projects" in resp.spoken_response.lower()
    assert resp.action_taken == "FETCH_EXECUTIVE_BRIEFING"
    assert resp.action_success is True
    assert resp.execution_time_ms > 0


@pytest.mark.asyncio
async def test_voice_command_enterprise_opportunities_and_followup(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test Section 25 canonical dialogue: 'Show enterprise opportunities' followed by 'Which need attention?'."""
    service = VoiceService(db_session)

    # 1. 'Show enterprise opportunities'
    resp1 = await service.process_command(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        payload=VoiceCommandPayload(transcript="Show enterprise opportunities"),
    )
    assert resp1.intent == VoiceIntent.STATUS_QUERY
    assert "18" in resp1.spoken_response
    assert resp1.session_id is not None

    # 2. Multi-turn follow-up in the same session: 'Which need attention?'
    resp2 = await service.process_command(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        payload=VoiceCommandPayload(
            transcript="Which need attention?",
            session_id=resp1.session_id,
        ),
    )
    assert resp2.intent == VoiceIntent.STATUS_QUERY
    assert "require attention" in resp2.spoken_response or "tasks" in resp2.spoken_response
    assert (
        "Deploy Edge Gateway" in resp2.spoken_response
        or "Deploy Edge Gateway" in resp2.detailed_response
    )


@pytest.mark.asyncio
async def test_voice_command_delegation_task_creation(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test Section 25 command: 'Ask marketing to draft launch announcement'."""
    service = VoiceService(db_session)

    resp = await service.process_command(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        payload=VoiceCommandPayload(transcript="Ask marketing to draft launch announcement"),
    )

    assert resp.intent == VoiceIntent.DELEGATION_COMMAND
    assert resp.action_taken == "CREATE_TASK"
    assert resp.action_entity_id is not None
    assert "created and assigned" in resp.spoken_response

    # Verify task was actually created in DB
    created_task = await db_session.get(Task, resp.action_entity_id)
    assert created_task is not None
    assert "draft launch announcement" in created_task.title.lower()
    assert created_task.status == "PLANNED"


@pytest.mark.asyncio
async def test_voice_command_approval_decision(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test Section 25 approval workflow: 'Approve that'."""
    service = VoiceService(db_session)

    resp = await service.process_command(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        payload=VoiceCommandPayload(transcript="Approve that"),
    )

    assert resp.intent == VoiceIntent.APPROVAL_DECISION
    assert resp.action_taken == "DECIDE_APPROVAL_APPROVED"
    assert resp.action_entity_id == test_data["approval_id"]
    assert "approved" in resp.spoken_response

    # Verify in DB
    appr = await db_session.get(ApprovalRequest, test_data["approval_id"])
    assert appr is not None
    assert appr.status == "APPROVED"


@pytest.mark.asyncio
async def test_voice_command_stop_task(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Test Section 25 control: 'Stop the task'."""
    service = VoiceService(db_session)

    resp = await service.process_command(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        payload=VoiceCommandPayload(
            transcript="Stop the task",
            context_task_id=test_data["task_id"],
        ),
    )

    assert resp.intent == VoiceIntent.TASK_CONTROL
    assert resp.action_taken == "STOP_TASK"
    assert resp.action_entity_id == test_data["task_id"]
    assert "stopped" in resp.spoken_response

    stopped_task = await db_session.get(Task, test_data["task_id"])
    assert stopped_task is not None
    assert stopped_task.status == "CANCELLED"


@pytest.mark.asyncio
async def test_voice_command_validation_and_errors(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test error handling for empty transcript and unauthorized tenant access."""
    service = VoiceService(db_session)

    with pytest.raises(InvalidVoiceCommandError):
        await service.process_command(
            company_id=test_data["company_id"],
            user_id=test_data["user_id"],
            payload=VoiceCommandPayload(transcript="   "),
        )

    with pytest.raises(VoiceAccessDeniedError):
        await service.process_command(
            company_id=test_data["company_id"],
            user_id=test_data["unauthorized_user_id"],
            payload=VoiceCommandPayload(transcript="Hello CEO"),
        )


@pytest.mark.asyncio
async def test_voice_synthesize_and_telemetry(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Test speech synthesis metadata and voice telemetry analytics."""
    service = VoiceService(db_session)

    synth = await service.synthesize_speech(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        request=VoiceSynthesizeRequest(text="System online and ready for commands."),
    )
    assert synth.text == "System online and ready for commands."
    assert synth.audio_format == "browser-tts/pcm"

    # Create an interaction to check telemetry
    await service.process_command(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
        payload=VoiceCommandPayload(transcript="CEO, what's happening?"),
    )

    telemetry = await service.get_telemetry(
        company_id=test_data["company_id"],
        user_id=test_data["user_id"],
    )
    assert telemetry.company_id == test_data["company_id"]
    assert telemetry.total_sessions >= 1
    assert telemetry.total_interactions >= 1
    assert telemetry.avg_execution_time_ms >= 0.0
