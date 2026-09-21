"""Pydantic schemas for agent task execution adhering to docs/Phases.md Section 12."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskExecuteRequest(BaseModel):
    """Payload for triggering agent task execution with optional limit overrides."""

    max_steps: int | None = Field(
        default=None, ge=1, le=20, description="Optional override for maximum reasoning steps"
    )
    max_duration_seconds: int | None = Field(
        default=None, ge=1, le=300, description="Optional override for execution timeout in seconds"
    )
    max_tokens: int | None = Field(
        default=None, ge=100, le=128000, description="Optional override for token budget"
    )


class ExecutionRecordResponse(BaseModel):
    """Response model for an individual agent execution run."""

    id: str
    company_id: str
    task_id: str
    agent_id: str
    executed_by_user_id: str | None = None
    status: str
    step_count: int
    duration_ms: int
    tokens_used: int
    estimated_cost: float
    result_summary: str | None = None
    deliverable: str | None = None
    steps_json: list[dict[str, Any]] = Field(default_factory=list)
    error_details: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    agent_name: str | None = None
    agent_role: str | None = None
    executed_by_user_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ExecutionListResponse(BaseModel):
    """List response for task execution history."""

    items: list[ExecutionRecordResponse]
    total: int
