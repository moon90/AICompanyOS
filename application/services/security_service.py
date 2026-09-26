"""Application service orchestrating Security Hardening, Default-DENY policies, and audit logging."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.security.enums import (
    ActorType,
    SecurityEventType,
    SecurityPosture,
    SecuritySeverity,
)
from domain.security.exceptions import (
    AgentQuarantinedError,
    CapabilityDeniedError,
    CrossTenantAccessError,
)
from domain.security.prompt_guard import PromptGuard, PromptScanResult
from domain.security.schemas import (
    AgentPolicyUpdateRequest,
    SecuritySummaryResponse,
)
from infrastructure.database.models import (
    AgentSecurityPolicy,
    CompanyMember,
    SecurityAuditLog,
)


class SecurityService:
    """Enterprise security service enforcing multi-tenancy, Default-DENY capability gates, and audit trails."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_security_event(
        self,
        event_type: SecurityEventType,
        severity: SecuritySeverity,
        company_id: str | None = None,
        user_id: str | None = None,
        actor_type: ActorType = ActorType.USER,
        resource_type: str = "GENERAL",
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        action_details: dict[str, Any] | None = None,
        is_blocked: bool = True,
    ) -> SecurityAuditLog:
        """Persist an immutable security audit event."""
        log = SecurityAuditLog(
            id=str(uuid.uuid4()),
            company_id=company_id,
            user_id=user_id,
            actor_type=actor_type.value,
            event_type=event_type.value,
            severity=severity.value,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            action_details=action_details or {},
            is_blocked=is_blocked,
            created_at=datetime.now(UTC),
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_security_logs(
        self,
        company_id: str,
        event_type: str | None = None,
        severity: str | None = None,
        is_blocked: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SecurityAuditLog], int]:
        """Fetch paginated audit logs for a company."""
        base_filter = [SecurityAuditLog.company_id == company_id]
        if event_type:
            base_filter.append(SecurityAuditLog.event_type == event_type)
        if severity:
            base_filter.append(SecurityAuditLog.severity == severity)
        if is_blocked is not None:
            base_filter.append(SecurityAuditLog.is_blocked == is_blocked)

        # Count total
        count_stmt = select(func.count(SecurityAuditLog.id)).where(*base_filter)
        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar() or 0

        # Query items
        stmt = (
            select(SecurityAuditLog)
            .where(*base_filter)
            .order_by(desc(SecurityAuditLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        items = list(res.scalars().all())

        return items, total

    async def get_security_summary(self, company_id: str) -> SecuritySummaryResponse:
        """Aggregate security metrics, posture, and active policy counts."""
        # Total events
        tot_stmt = select(func.count(SecurityAuditLog.id)).where(
            SecurityAuditLog.company_id == company_id
        )
        tot_res = await self.session.execute(tot_stmt)
        total_events = tot_res.scalar() or 0

        # Blocked threats
        blocked_stmt = select(func.count(SecurityAuditLog.id)).where(
            SecurityAuditLog.company_id == company_id,
            SecurityAuditLog.is_blocked == True,  # noqa: E712
        )
        blocked_res = await self.session.execute(blocked_stmt)
        blocked_threats = blocked_res.scalar() or 0

        # Critical events
        crit_stmt = select(func.count(SecurityAuditLog.id)).where(
            SecurityAuditLog.company_id == company_id,
            SecurityAuditLog.severity == SecuritySeverity.CRITICAL.value,
        )
        crit_res = await self.session.execute(crit_stmt)
        critical_events = crit_res.scalar() or 0

        # High events
        high_stmt = select(func.count(SecurityAuditLog.id)).where(
            SecurityAuditLog.company_id == company_id,
            SecurityAuditLog.severity == SecuritySeverity.HIGH.value,
        )
        high_res = await self.session.execute(high_stmt)
        high_events = high_res.scalar() or 0

        # Active agent policies
        pol_stmt = select(func.count(AgentSecurityPolicy.id)).where(
            AgentSecurityPolicy.company_id == company_id
        )
        pol_res = await self.session.execute(pol_stmt)
        active_agent_policies = pol_res.scalar() or 0

        # Quarantined agents
        quar_stmt = select(func.count(AgentSecurityPolicy.id)).where(
            AgentSecurityPolicy.company_id == company_id,
            AgentSecurityPolicy.is_quarantined == True,  # noqa: E712
        )
        quar_res = await self.session.execute(quar_stmt)
        quarantined_agents_count = quar_res.scalar() or 0

        # Last event timestamp
        last_stmt = (
            select(SecurityAuditLog.created_at)
            .where(SecurityAuditLog.company_id == company_id)
            .order_by(desc(SecurityAuditLog.created_at))
            .limit(1)
        )
        last_res = await self.session.execute(last_stmt)
        last_event_timestamp = last_res.scalar_one_or_none()

        return SecuritySummaryResponse(
            company_id=company_id,
            default_posture=SecurityPosture.DENY,
            total_events=total_events,
            blocked_threats=blocked_threats,
            critical_events=critical_events,
            high_events=high_events,
            active_agent_policies=active_agent_policies,
            quarantined_agents_count=quarantined_agents_count,
            last_event_timestamp=last_event_timestamp,
        )

    async def get_agent_policy(self, company_id: str, agent_id: str) -> AgentSecurityPolicy:
        """Fetch or initialize default-DENY security policy for an agent."""
        stmt = select(AgentSecurityPolicy).where(
            AgentSecurityPolicy.company_id == company_id,
            AgentSecurityPolicy.agent_id == agent_id,
        )
        res = await self.session.execute(stmt)
        policy = res.scalar_one_or_none()

        if not policy:
            # Auto-provision Default-DENY policy per Rule 185
            policy = AgentSecurityPolicy(
                id=str(uuid.uuid4()),
                company_id=company_id,
                agent_id=agent_id,
                default_posture=SecurityPosture.DENY.value,
                allowed_capabilities=[],
                denied_capabilities=[],
                rate_limit_rpm=60,
                max_daily_budget=50.0,
                can_execute_destructive_tools=False,
                requires_human_approval_for_tools=True,
                is_quarantined=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            self.session.add(policy)
            await self.session.commit()
            await self.session.refresh(policy)

        return policy

    async def list_agent_policies(self, company_id: str) -> list[AgentSecurityPolicy]:
        """List all agent security policies configured for a company."""
        stmt = (
            select(AgentSecurityPolicy)
            .where(AgentSecurityPolicy.company_id == company_id)
            .order_by(AgentSecurityPolicy.created_at)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def update_agent_policy(
        self,
        company_id: str,
        agent_id: str,
        update_data: AgentPolicyUpdateRequest,
    ) -> AgentSecurityPolicy:
        """Update an agent's capability constraints and execution flags."""
        policy = await self.get_agent_policy(company_id, agent_id)

        if update_data.default_posture is not None:
            policy.default_posture = update_data.default_posture.value
        if update_data.allowed_capabilities is not None:
            policy.allowed_capabilities = update_data.allowed_capabilities
        if update_data.denied_capabilities is not None:
            policy.denied_capabilities = update_data.denied_capabilities
        if update_data.rate_limit_rpm is not None:
            policy.rate_limit_rpm = update_data.rate_limit_rpm
        if update_data.max_daily_budget is not None:
            policy.max_daily_budget = update_data.max_daily_budget
        if update_data.can_execute_destructive_tools is not None:
            policy.can_execute_destructive_tools = update_data.can_execute_destructive_tools
        if update_data.requires_human_approval_for_tools is not None:
            policy.requires_human_approval_for_tools = update_data.requires_human_approval_for_tools

        policy.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(policy)

        # Audit policy change
        await self.log_security_event(
            event_type=SecurityEventType.POLICY_UPDATED,
            severity=SecuritySeverity.LOW,
            company_id=company_id,
            actor_type=ActorType.USER,
            resource_type="AGENT_POLICY",
            resource_id=agent_id,
            action_details={
                "allowed": policy.allowed_capabilities,
                "posture": policy.default_posture,
            },
            is_blocked=False,
        )

        return policy

    async def quarantine_agent(
        self, company_id: str, agent_id: str, reason: str
    ) -> AgentSecurityPolicy:
        """Quarantine an agent to block all operational capabilities."""
        policy = await self.get_agent_policy(company_id, agent_id)
        policy.is_quarantined = True
        policy.quarantine_reason = reason
        policy.quarantined_at = datetime.now(UTC)
        policy.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(policy)

        # Log High Severity Quarantine Event
        await self.log_security_event(
            event_type=SecurityEventType.AGENT_QUARANTINED,
            severity=SecuritySeverity.HIGH,
            company_id=company_id,
            actor_type=ActorType.SYSTEM,
            resource_type="AGENT",
            resource_id=agent_id,
            action_details={"reason": reason},
            is_blocked=True,
        )

        return policy

    async def unquarantine_agent(self, company_id: str, agent_id: str) -> AgentSecurityPolicy:
        """Restore an agent from quarantine."""
        policy = await self.get_agent_policy(company_id, agent_id)
        policy.is_quarantined = False
        policy.quarantine_reason = None
        policy.quarantined_at = None
        policy.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(policy)

        # Log Unquarantine event
        await self.log_security_event(
            event_type=SecurityEventType.AGENT_UNQUARANTINED,
            severity=SecuritySeverity.LOW,
            company_id=company_id,
            actor_type=ActorType.USER,
            resource_type="AGENT",
            resource_id=agent_id,
            action_details={"status": "restored"},
            is_blocked=False,
        )

        return policy

    async def evaluate_agent_capability(
        self,
        company_id: str,
        agent_id: str,
        capability: str,
    ) -> bool:
        """Evaluate if an agent is authorized to perform an action under Default-DENY."""
        policy = await self.get_agent_policy(company_id, agent_id)

        # 1. Check Quarantine
        if policy.is_quarantined:
            await self.log_security_event(
                event_type=SecurityEventType.CAPABILITY_DENIED,
                severity=SecuritySeverity.HIGH,
                company_id=company_id,
                actor_type=ActorType.AGENT,
                resource_type="CAPABILITY",
                resource_id=capability,
                action_details={
                    "agent_id": agent_id,
                    "reason": "Agent is quarantined",
                    "quarantine_reason": policy.quarantine_reason,
                },
                is_blocked=True,
            )
            raise AgentQuarantinedError(
                f"Agent {agent_id} is quarantined: {policy.quarantine_reason}"
            )

        # 2. Check explicit deny list
        if capability in (policy.denied_capabilities or []):
            await self.log_security_event(
                event_type=SecurityEventType.CAPABILITY_DENIED,
                severity=SecuritySeverity.MEDIUM,
                company_id=company_id,
                actor_type=ActorType.AGENT,
                resource_type="CAPABILITY",
                resource_id=capability,
                action_details={
                    "agent_id": agent_id,
                    "reason": "Explicitly in denied_capabilities",
                },
                is_blocked=True,
            )
            raise CapabilityDeniedError(
                f"Capability '{capability}' is explicitly denied for agent {agent_id}"
            )

        # 3. Default-DENY check
        if policy.default_posture == SecurityPosture.DENY.value and capability not in (
            policy.allowed_capabilities or []
        ):
            await self.log_security_event(
                event_type=SecurityEventType.CAPABILITY_DENIED,
                severity=SecuritySeverity.MEDIUM,
                company_id=company_id,
                actor_type=ActorType.AGENT,
                resource_type="CAPABILITY",
                resource_id=capability,
                action_details={
                    "agent_id": agent_id,
                    "reason": "Default-DENY: capability not in allowed list",
                },
                is_blocked=True,
            )
            raise CapabilityDeniedError(
                f"Default-DENY posture blocks unauthorized capability '{capability}' for agent {agent_id}"
            )

        return True

    async def scan_and_sanitize_prompt(
        self,
        company_id: str,
        content: str,
        source_type: str = "EXTERNAL",
        actor_id: str | None = None,
    ) -> PromptScanResult:
        """Scan untrusted input for prompt injections and redact credentials."""
        result = PromptGuard.scan_and_sanitize(content, source_type=source_type)

        if result.injection_detected:
            await self.log_security_event(
                event_type=SecurityEventType.PROMPT_INJECTION_DETECTED,
                severity=SecuritySeverity.HIGH,
                company_id=company_id,
                actor_type=ActorType.ANONYMOUS if not actor_id else ActorType.USER,
                resource_type="PROMPT",
                resource_id=source_type,
                action_details={
                    "indicators": result.injection_indicators,
                    "preview": content[:100],
                },
                is_blocked=True,
            )

        if result.redacted_secrets_count > 0:
            await self.log_security_event(
                event_type=SecurityEventType.CREDENTIAL_LEAK_PREVENTED,
                severity=SecuritySeverity.MEDIUM,
                company_id=company_id,
                actor_type=ActorType.SYSTEM,
                resource_type="PAYLOAD",
                action_details={"redacted_count": result.redacted_secrets_count},
                is_blocked=True,
            )

        return result

    async def verify_tenant_boundary(self, user_id: str, company_id: str) -> None:
        """Verify user is an authorized member of company; logs critical security event on violation."""
        stmt = select(CompanyMember).where(
            CompanyMember.user_id == user_id,
            CompanyMember.company_id == company_id,
        )
        res = await self.session.execute(stmt)
        membership = res.scalar_one_or_none()

        if not membership:
            # Audit cross-tenant attempt
            await self.log_security_event(
                event_type=SecurityEventType.CROSS_TENANT_ATTEMPT,
                severity=SecuritySeverity.CRITICAL,
                company_id=company_id,
                user_id=user_id,
                actor_type=ActorType.USER,
                resource_type="COMPANY",
                resource_id=company_id,
                action_details={"attempted_company_id": company_id, "user_id": user_id},
                is_blocked=True,
            )
            raise CrossTenantAccessError(
                f"User {user_id} does not have access to company {company_id}"
            )
