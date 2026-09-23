"""API schemas for Agent Presence adhering to docs/Phases.md Section 18."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from domain.presence.schemas import PresenceStatus, PresenceSummaryResponse


class AgentPresenceItemResponse(BaseModel):
    """API response model for an individual agent presence record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_id: str
    agent_name: str
    agent_role: str
    department_id: str | None = None
    department_name: str | None = None
    company_id: str
    status: PresenceStatus
    current_task_id: str | None = None
    current_task_title: str | None = None
    current_project_id: str | None = None
    current_project_name: str | None = None
    current_activity: str | None = None
    current_step: str | None = None
    last_heartbeat_at: datetime
    started_at: datetime | None = None
    updated_at: datetime
    duration_seconds: int = 0
    is_stale: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class PresenceListResponse(BaseModel):
    """API response for listing all agent presences for a company."""

    items: list[AgentPresenceItemResponse]
    total: int


class HeartbeatApiRequest(BaseModel):
    """Payload for agent heartbeat check-in."""

    current_step: str | None = None
    current_activity: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class PresenceUpdateApiRequest(BaseModel):
    """Payload for manual or operator presence status override."""

    status: PresenceStatus
    current_activity: str | None = None
    current_step: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "AgentPresenceItemResponse",
    "HeartbeatApiRequest",
    "PresenceListResponse",
    "PresenceStatus",
    "PresenceSummaryResponse",
    "PresenceUpdateApiRequest",
]
