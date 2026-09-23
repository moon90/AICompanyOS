"""Domain schemas for agent presence adhering to docs/Phases.md Section 18 and docs/Memory.md Section 20."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PresenceStatus(StrEnum):
    """Presence states adhering to docs/Phases.md Section 18."""

    ONLINE = "ONLINE"
    IDLE = "IDLE"
    WORKING = "WORKING"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"


class AgentPresenceResponse(BaseModel):
    """Authoritative agent presence model answering 'Who is working right now?'."""

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


class PresenceSummaryResponse(BaseModel):
    """Lightweight aggregated presence counters for executive telemetry."""

    total_agents: int = 0
    working_count: int = 0
    idle_count: int = 0
    waiting_count: int = 0
    blocked_count: int = 0
    error_count: int = 0
    offline_count: int = 0


class HeartbeatRequest(BaseModel):
    """Payload sent by an agent or worker checking in."""

    current_step: str | None = None
    current_activity: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class PresenceUpdateParams(BaseModel):
    """Payload for operator or manual presence override."""

    status: PresenceStatus
    current_activity: str | None = None
    current_step: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
