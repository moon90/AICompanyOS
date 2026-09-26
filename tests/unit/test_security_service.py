"""Unit tests for SecurityService adhering to docs/Phases.md § 27 and docs/Rules.md § 185."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.security_service import SecurityService
from domain.security.enums import (
    ActorType,
    AgentCapability,
    SecurityEventType,
    SecurityPosture,
    SecuritySeverity,
)
from domain.security.exceptions import (
    AgentQuarantinedError,
    CapabilityDeniedError,
    CrossTenantAccessError,
)
from domain.security.schemas import AgentPolicyUpdateRequest
from infrastructure.database.base import Base
from infrastructure.database.models import Agent, Company, CompanyMember, User


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
async def seed_data(db_session: AsyncSession) -> dict[str, str]:
    """Seed test company, user, member, and agent."""
    user = User(
        id="usr-sec-001",
        email="security@company.os",
        password_hash="hashed_secret",
        name="Security Auditor",
    )
    foreign_user = User(
        id="usr-sec-999",
        email="attacker@external.os",
        password_hash="hashed_secret",
        name="Malicious Actor",
    )
    company = Company(
        id="cmp-sec-001",
        name="Secure Systems Inc",
        description="Hardened enterprise test company",
    )
    member = CompanyMember(
        id="mem-sec-001",
        company_id=company.id,
        user_id=user.id,
        role="OWNER",
    )
    agent = Agent(
        id="agt-sec-001",
        company_id=company.id,
        name="Engineering Co-Pilot",
        role="DEVELOPER",
        status="IDLE",
    )

    db_session.add_all([user, foreign_user, company, member, agent])
    await db_session.commit()

    return {
        "user_id": user.id,
        "foreign_user_id": foreign_user.id,
        "company_id": company.id,
        "agent_id": agent.id,
    }


async def test_log_and_query_security_events(
    db_session: AsyncSession, seed_data: dict[str, str]
) -> None:
    service = SecurityService(db_session)
    comp_id = seed_data["company_id"]
    usr_id = seed_data["user_id"]

    log = await service.log_security_event(
        event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
        severity=SecuritySeverity.HIGH,
        company_id=comp_id,
        user_id=usr_id,
        actor_type=ActorType.USER,
        resource_type="PROJECT",
        resource_id="prj-secret",
        is_blocked=True,
    )
    assert log.id is not None
    assert log.event_type == SecurityEventType.UNAUTHORIZED_ACCESS.value
    assert log.is_blocked is True

    items, total = await service.get_security_logs(company_id=comp_id)
    assert total >= 1
    assert items[0].resource_type == "PROJECT"


async def test_security_summary_aggregation(
    db_session: AsyncSession, seed_data: dict[str, str]
) -> None:
    service = SecurityService(db_session)
    comp_id = seed_data["company_id"]

    await service.log_security_event(
        event_type=SecurityEventType.PROMPT_INJECTION_DETECTED,
        severity=SecuritySeverity.CRITICAL,
        company_id=comp_id,
        is_blocked=True,
    )
    await service.log_security_event(
        event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
        severity=SecuritySeverity.MEDIUM,
        company_id=comp_id,
        is_blocked=True,
    )

    summary = await service.get_security_summary(comp_id)
    assert summary.company_id == comp_id
    assert summary.default_posture == SecurityPosture.DENY
    assert summary.total_events >= 2
    assert summary.critical_events >= 1
    assert summary.blocked_threats >= 2


async def test_agent_policy_default_deny(
    db_session: AsyncSession, seed_data: dict[str, str]
) -> None:
    service = SecurityService(db_session)
    comp_id = seed_data["company_id"]
    agt_id = seed_data["agent_id"]

    # Retrieve policy (auto-provisions Default-DENY)
    policy = await service.get_agent_policy(comp_id, agt_id)
    assert policy.default_posture == SecurityPosture.DENY.value
    assert policy.allowed_capabilities == []
    assert policy.is_quarantined is False

    # Default-DENY must block capability not explicitly granted
    with pytest.raises(CapabilityDeniedError) as exc_info:
        await service.evaluate_agent_capability(comp_id, agt_id, AgentCapability.CODE_WRITE.value)
    assert "Default-DENY" in str(exc_info.value)

    # Now explicitly grant CODE_WRITE
    await service.update_agent_policy(
        comp_id,
        agt_id,
        AgentPolicyUpdateRequest(allowed_capabilities=[AgentCapability.CODE_WRITE.value]),
    )

    # Evaluation should now pass
    is_allowed = await service.evaluate_agent_capability(
        comp_id, agt_id, AgentCapability.CODE_WRITE.value
    )
    assert is_allowed is True


async def test_explicit_denied_capability(
    db_session: AsyncSession, seed_data: dict[str, str]
) -> None:
    service = SecurityService(db_session)
    comp_id = seed_data["company_id"]
    agt_id = seed_data["agent_id"]

    # Even with ALLOW posture, denied_capabilities takes precedence
    await service.update_agent_policy(
        comp_id,
        agt_id,
        AgentPolicyUpdateRequest(
            default_posture=SecurityPosture.ALLOW,
            denied_capabilities=[AgentCapability.DESTRUCTIVE_TOOL.value],
        ),
    )

    with pytest.raises(CapabilityDeniedError):
        await service.evaluate_agent_capability(
            comp_id, agt_id, AgentCapability.DESTRUCTIVE_TOOL.value
        )


async def test_quarantine_blocks_all_capabilities(
    db_session: AsyncSession, seed_data: dict[str, str]
) -> None:
    service = SecurityService(db_session)
    comp_id = seed_data["company_id"]
    agt_id = seed_data["agent_id"]

    # Grant CODE_READ
    await service.update_agent_policy(
        comp_id,
        agt_id,
        AgentPolicyUpdateRequest(allowed_capabilities=[AgentCapability.CODE_READ.value]),
    )

    # Quarantine agent
    quarantined_policy = await service.quarantine_agent(
        comp_id, agt_id, reason="Anomalous network egress detected"
    )
    assert quarantined_policy.is_quarantined is True
    assert "Anomalous" in (quarantined_policy.quarantine_reason or "")

    # Capability must now be blocked
    with pytest.raises(AgentQuarantinedError):
        await service.evaluate_agent_capability(comp_id, agt_id, AgentCapability.CODE_READ.value)

    # Unquarantine agent
    restored = await service.unquarantine_agent(comp_id, agt_id)
    assert restored.is_quarantined is False
    assert (
        await service.evaluate_agent_capability(comp_id, agt_id, AgentCapability.CODE_READ.value)
        is True
    )


async def test_tenant_boundary_enforcement(
    db_session: AsyncSession, seed_data: dict[str, str]
) -> None:
    service = SecurityService(db_session)
    comp_id = seed_data["company_id"]
    valid_user = seed_data["user_id"]
    foreign_user = seed_data["foreign_user_id"]

    # Valid user passes
    await service.verify_tenant_boundary(valid_user, comp_id)

    # Foreign user must raise CrossTenantAccessError and log critical event
    with pytest.raises(CrossTenantAccessError):
        await service.verify_tenant_boundary(foreign_user, comp_id)

    # Verify critical security audit log was recorded
    logs, count = await service.get_security_logs(
        comp_id, event_type=SecurityEventType.CROSS_TENANT_ATTEMPT.value
    )
    assert count >= 1
    assert logs[0].severity == SecuritySeverity.CRITICAL.value
