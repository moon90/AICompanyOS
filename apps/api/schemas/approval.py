"""Pydantic API schemas for Human Approval & Oversight System."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApprovalRequestResponse(BaseModel):
    """API response model for an approval request."""

    id: str
    company_id: str
    task_id: str | None = None
    agent_id: str | None = None
    execution_id: str | None = None
    tool_execution_id: str | None = None
    action_type: str
    description: str
    payload: dict[str, Any] = Field(default_factory=dict)
    risk_level: str
    status: str
    reviewed_by_user_id: str | None = None
    reviewed_at: datetime | None = None
    decision_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    # Denormalized / enriched relationship attributes for UI presentation
    agent_name: str | None = None
    task_title: str | None = None
    reviewer_name: str | None = None
    tool_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalListResponse(BaseModel):
    """API response model for paginated approval request list."""

    items: list[ApprovalRequestResponse]
    total: int


class ApprovalDecisionRequest(BaseModel):
    """Payload for submitting an approval or rejection decision."""

    decision_reason: str | None = Field(
        default=None,
        description="Optional human reviewer explanation or rationale",
    )
