"""Domain schemas for Real-Time Operations per docs/Phases.md Section 21."""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RealtimeEventType(StrEnum):
    """Authoritative real-time event taxonomy per docs/Phases.md Section 21."""

    CEO_PLANNING = "ceo.planning"
    AGENT_STARTED = "agent.started"
    TASK_ASSIGNED = "task.assigned"
    AGENT_WORKING = "agent.working"
    TOOL_CALLED = "tool.called"
    TOOL_COMPLETED = "tool.completed"
    TASK_BLOCKED = "task.blocked"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"
    ERROR_DETECTED = "error.detected"
    ERROR_RESOLVED = "error.resolved"
    TASK_COMPLETED = "task.completed"
    TASK_STATUS_CHANGED = "task.status_changed"
    PRESENCE_UPDATED = "presence.updated"
    ENGINEERING_VERIFIED = "engineering.verified"
    ENGINEERING_UPDATED = "engineering.updated"
    SYSTEM_HEARTBEAT = "system.heartbeat"
    TEST_PULSE = "test.pulse"


class RealtimeEventPayload(BaseModel):
    """Event payload dispatched over real-time SSE stream."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    event_type: str
    message: str
    actor_type: str = "system"
    actor_id: str | None = None
    actor_name: str | None = None
    project_id: str | None = None
    task_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_sse_data(self) -> str:
        """Serialize model to JSON string suitable for SSE data frame."""
        return self.model_dump_json()


class RealtimeEmitRequest(BaseModel):
    """Request payload to manually emit an operational event for testing or operator pulses."""

    event_type: str
    message: str
    actor_type: str = "user"
    actor_id: str | None = None
    actor_name: str | None = None
    project_id: str | None = None
    task_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RealtimeStatusResponse(BaseModel):
    """Status telemetry for company's real-time operations channel."""

    company_id: str
    active_subscribers: int
    channel_status: str
    events_dispatched: int
    timestamp: datetime
