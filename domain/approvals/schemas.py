"""Domain schemas and data contracts for Approval & Oversight System."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApprovalStatus(StrEnum):
    """Authoritative approval request statuses per docs/Phases.md Section 14."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ApprovalActionType(StrEnum):
    """Consequential action types requiring oversight per docs/Rules.md Section 40."""

    SEND_EMAIL = "SEND_EMAIL"
    PUBLISH_CONTENT = "PUBLISH_CONTENT"
    SPEND_MONEY = "SPEND_MONEY"
    DELETE_DATA = "DELETE_DATA"
    DEPLOY_PRODUCTION = "DEPLOY_PRODUCTION"
    MODIFY_CONFIGURATION = "MODIFY_CONFIGURATION"
    EXTERNAL_COMMUNICATION = "EXTERNAL_COMMUNICATION"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    DATABASE_MIGRATION = "DATABASE_MIGRATION"
    HIGH_RISK_ACTION = "HIGH_RISK_ACTION"


class ApprovalRiskLevel(StrEnum):
    """Risk tier classifications for approval requests."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalDecision(StrEnum):
    """Approval decision values submitted by human reviewer."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalRequestCreate(BaseModel):
    """Data contract for creating an approval request."""

    model_config = ConfigDict(extra="forbid")

    company_id: str
    task_id: str | None = None
    agent_id: str | None = None
    execution_id: str | None = None
    tool_execution_id: str | None = None
    action_type: str
    description: str
    payload: dict[str, Any] = Field(default_factory=dict)
    risk_level: str = ApprovalRiskLevel.MEDIUM.value


class ApprovalDecisionInput(BaseModel):
    """Payload for approving or rejecting an approval request."""

    model_config = ConfigDict(extra="forbid")

    decision_reason: str | None = Field(
        default=None,
        description="Optional justification or feedback provided by the human approver",
    )


class ApprovalFilter(BaseModel):
    """Filter criteria for querying approval requests."""

    model_config = ConfigDict(extra="forbid")

    status: ApprovalStatus | None = None
    risk_level: ApprovalRiskLevel | None = None
    action_type: str | None = None
    agent_id: str | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
