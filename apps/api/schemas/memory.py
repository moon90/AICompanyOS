"""API request and response schemas for Memory, Decisions, and Company State."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CompanyDecisionCreateRequest(BaseModel):
    """Payload to record a new company decision."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255, description="Brief title or question")
    decision: str = Field(min_length=1, description="Authoritative decision statement")
    rationale: str = Field(min_length=1, description="Justification and explanation")
    evidence: dict[str, Any] = Field(default_factory=dict, description="Supporting evidence data")
    project_id: str | None = Field(default=None, description="Optional associated project ID")
    task_id: str | None = Field(default=None, description="Optional associated task ID")
    decided_by_agent_id: str | None = Field(
        default=None, description="Optional associated agent ID"
    )


class CompanyDecisionItemResponse(BaseModel):
    """Schema representing an authoritative company decision record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    project_id: str | None = None
    task_id: str | None = None
    title: str
    decision: str
    rationale: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    status: str
    decided_by_user_id: str | None = None
    decided_by_agent_id: str | None = None
    superseded_by_decision_id: str | None = None
    created_at: datetime
    updated_at: datetime


class CompanyDecisionListResponse(BaseModel):
    """Paginated or listed decisions response."""

    items: list[CompanyDecisionItemResponse]
    total: int


class CompanyStateResponse(BaseModel):
    """Authoritative operational state memory response."""

    company: dict[str, Any]
    departments: list[dict[str, Any]]
    agents: list[dict[str, Any]]
    projects: list[dict[str, Any]]
    tasks_summary: dict[str, Any]
    recent_approvals: list[dict[str, Any]]
    decisions: list[dict[str, Any]]
    generated_at: datetime


class TaskContextResponse(BaseModel):
    """Context response scoped to a task."""

    task: dict[str, Any]
    project: dict[str, Any] | None
    company: dict[str, Any]
    decisions: list[dict[str, Any]]
    execution_history: list[dict[str, Any]]
    synthesized_prompt: str


class CeoInquiryCitationItem(BaseModel):
    """Source reference cited by CEO."""

    source_type: str
    source_id: str
    reference: str


class CeoInquiryApiRequest(BaseModel):
    """Inquiry submitted to the CEO."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, description="Question for the CEO regarding company state")


class CeoInquiryApiResponse(BaseModel):
    """Grounded answer from CEO."""

    answer: str
    citations: list[CeoInquiryCitationItem]
    grounded_state_timestamp: datetime
