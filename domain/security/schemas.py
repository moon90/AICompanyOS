"""Pydantic schemas for Security Hardening domain operations."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from domain.security.enums import (
    ActorType,
    SecurityEventType,
    SecurityPosture,
    SecuritySeverity,
)


class SecurityLogItem(BaseModel):
    """Authoritative representation of a security audit log event."""

    id: str
    company_id: str | None = None
    user_id: str | None = None
    actor_type: ActorType
    event_type: SecurityEventType
    severity: SecuritySeverity
    resource_type: str
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    action_details: dict[str, Any] = Field(default_factory=dict)
    is_blocked: bool
    created_at: datetime


class SecurityLogListResponse(BaseModel):
    """Paginated list of security audit logs."""

    items: list[SecurityLogItem]
    total: int
    limit: int
    offset: int


class SecurityLogCreateRequest(BaseModel):
    """Payload to record a security audit event."""

    user_id: str | None = None
    actor_type: ActorType = ActorType.USER
    event_type: SecurityEventType
    severity: SecuritySeverity = SecuritySeverity.LOW
    resource_type: str = "GENERAL"
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    action_details: dict[str, Any] = Field(default_factory=dict)
    is_blocked: bool = True


class AgentPolicyResponse(BaseModel):
    """Authoritative agent capability security policy."""

    id: str
    company_id: str
    agent_id: str
    default_posture: SecurityPosture = SecurityPosture.DENY
    allowed_capabilities: list[str] = Field(default_factory=list)
    denied_capabilities: list[str] = Field(default_factory=list)
    rate_limit_rpm: int = 60
    max_daily_budget: float = 50.0
    can_execute_destructive_tools: bool = False
    requires_human_approval_for_tools: bool = True
    is_quarantined: bool = False
    quarantine_reason: str | None = None
    quarantined_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AgentPolicyUpdateRequest(BaseModel):
    """Payload to update agent capability boundaries and sandboxing flags."""

    default_posture: SecurityPosture | None = None
    allowed_capabilities: list[str] | None = None
    denied_capabilities: list[str] | None = None
    rate_limit_rpm: int | None = None
    max_daily_budget: float | None = None
    can_execute_destructive_tools: bool | None = None
    requires_human_approval_for_tools: bool | None = None


class AgentQuarantineRequest(BaseModel):
    """Payload to quarantine an agent."""

    reason: str = Field(min_length=3, max_length=500)


class PromptScanRequest(BaseModel):
    """Payload to scan an untrusted prompt or tool result for security threats."""

    content: str = Field(min_length=1)
    source_type: str = "EXTERNAL"


class PromptScanResponse(BaseModel):
    """Result of prompt security analysis."""

    is_safe: bool
    injection_detected: bool
    injection_indicators: list[str]
    redacted_content: str
    redacted_secrets_count: int
    data_tagged_content: str


class SecuritySummaryResponse(BaseModel):
    """Aggregated security posture and operational threat telemetry."""

    company_id: str
    default_posture: SecurityPosture = SecurityPosture.DENY
    total_events: int
    blocked_threats: int
    critical_events: int
    high_events: int
    active_agent_policies: int
    quarantined_agents_count: int
    last_event_timestamp: datetime | None = None
