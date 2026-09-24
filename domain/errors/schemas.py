"""Domain schemas for error and bug management adhering to docs/Phases.md Section 19 and docs/Memory.md Section 20."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorSeverity(StrEnum):
    """Error severity levels adhering to docs/Phases.md Section 19."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ErrorStatus(StrEnum):
    """Lifecycle states for error management adhering to docs/Phases.md Section 19."""

    OPEN = "OPEN"
    TRIAGED = "TRIAGED"
    ASSIGNED = "ASSIGNED"
    INVESTIGATING = "INVESTIGATING"
    BLOCKED = "BLOCKED"
    RESOLVED = "RESOLVED"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    REOPENED = "REOPENED"
    CLOSED = "CLOSED"


class ErrorCreatePayload(BaseModel):
    """Payload to record a new error or bug."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    detected_by: str = Field(..., min_length=1, max_length=255)
    project_id: str | None = None
    task_id: str | None = None
    assigned_to: str | None = None
    assigned_agent_id: str | None = None
    assigned_user_id: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class ErrorUpdatePayload(BaseModel):
    """Payload to update an existing error record."""

    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    severity: ErrorSeverity | None = None
    status: ErrorStatus | None = None
    assigned_to: str | None = None
    assigned_agent_id: str | None = None
    assigned_user_id: str | None = None
    investigated_by: str | None = None
    resolved_by: str | None = None
    verified_by: str | None = None
    root_cause: str | None = None
    resolution: str | None = None
    evidence: dict[str, Any] | None = None


class ErrorAssignPayload(BaseModel):
    """Payload to assign an error to an agent or user."""

    assigned_to: str = Field(..., min_length=1, max_length=255)
    assigned_agent_id: str | None = None
    assigned_user_id: str | None = None


class ErrorResolvePayload(BaseModel):
    """Payload to mark an error resolved."""

    resolved_by: str = Field(..., min_length=1, max_length=255)
    resolution: str = Field(..., min_length=1)
    root_cause: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class ErrorVerifyPayload(BaseModel):
    """Payload to verify an error resolution with proof/evidence."""

    verified_by: str = Field(..., min_length=1, max_length=255)
    evidence: dict[str, Any] = Field(default_factory=dict)
    close_immediately: bool = False


class ErrorRecordResponse(BaseModel):
    """Authoritative error response model answering all 8 operational bug questions."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    project_id: str | None = None
    project_name: str | None = None
    task_id: str | None = None
    task_title: str | None = None
    title: str
    description: str | None = None
    severity: ErrorSeverity
    status: ErrorStatus
    detected_by: str
    assigned_to: str | None = None
    investigated_by: str | None = None
    resolved_by: str | None = None
    verified_by: str | None = None
    assigned_agent_id: str | None = None
    assigned_agent_name: str | None = None
    assigned_user_id: str | None = None
    assigned_user_name: str | None = None
    root_cause: str | None = None
    resolution: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    resolved_at: datetime | None = None
    verified_at: datetime | None = None


class ErrorListResponse(BaseModel):
    """Paginated or listed collection of error records with state counters."""

    items: list[ErrorRecordResponse]
    total: int
    open_count: int = 0
    investigating_count: int = 0
    resolved_count: int = 0
    verified_count: int = 0


class ErrorSummaryResponse(BaseModel):
    """Lightweight aggregated metrics for executive dashboards."""

    total_errors: int = 0
    open_count: int = 0
    triaged_count: int = 0
    assigned_count: int = 0
    investigating_count: int = 0
    blocked_count: int = 0
    resolved_count: int = 0
    verifying_count: int = 0
    verified_count: int = 0
    reopened_count: int = 0
    closed_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
