"""Domain schemas for activity history per docs/Phases.md Section 17."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ActorType(StrEnum):
    """Types of actors responsible for an activity event."""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class ActivityEventType(StrEnum):
    """Categorical types of operational activity events."""

    # Company lifecycle
    COMPANY_CREATED = "COMPANY_CREATED"
    COMPANY_UPDATED = "COMPANY_UPDATED"

    # Project lifecycle
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_STATUS_CHANGED = "PROJECT_STATUS_CHANGED"

    # Task lifecycle
    TASK_CREATED = "TASK_CREATED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_STATUS_CHANGED = "TASK_STATUS_CHANGED"
    TASK_DELEGATED = "TASK_DELEGATED"

    # Execution lifecycle
    EXECUTION_STARTED = "EXECUTION_STARTED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    TASK_RECOVERED = "TASK_RECOVERED"

    # Governance & Approvals
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    APPROVAL_RESOLVED = "APPROVAL_RESOLVED"

    # Memory & Strategic Decisions
    DECISION_RECORDED = "DECISION_RECORDED"
    DECISION_SUPERSEDED = "DECISION_SUPERSEDED"

    # Tools
    TOOL_EXECUTED = "TOOL_EXECUTED"


class ActivityEventCreate(BaseModel):
    """Payload to create an authoritative activity event."""

    model_config = ConfigDict(extra="forbid")

    company_id: str
    event_type: str
    message: str
    actor_type: str = ActorType.SYSTEM.value
    actor_id: str | None = None
    project_id: str | None = None
    task_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActivityEventResponse(BaseModel):
    """Serialized representation of an activity event."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    project_id: str | None = None
    task_id: str | None = None
    actor_type: str
    actor_id: str | None = None
    event_type: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ActivityFilterParams(BaseModel):
    """Filter parameters for querying operational activity history."""

    model_config = ConfigDict(extra="forbid")

    project_id: str | None = None
    task_id: str | None = None
    actor_type: str | None = None
    actor_id: str | None = None
    event_type: str | None = None
    search: str | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
