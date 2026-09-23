"""Domain schemas and data contracts for Company Memory & Operational State.

Adheres to docs/Phases.md Section 15 and docs/Memory.md Sections 33-34.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DecisionStatus(StrEnum):
    """Authoritative decision statuses per docs/Memory.md Section 33."""

    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"


class CompanyDecisionCreate(BaseModel):
    """Data contract for recording a new authoritative company decision."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255, description="Brief title or question")
    decision: str = Field(min_length=1, description="Authoritative outcome or decision statement")
    rationale: str = Field(min_length=1, description="Justification and explanation")
    evidence: dict[str, Any] = Field(
        default_factory=dict,
        description="References, metrics, or linked documents supporting this decision",
    )
    project_id: str | None = Field(default=None, description="Optional associated project ID")
    task_id: str | None = Field(default=None, description="Optional associated task ID")
    decided_by_agent_id: str | None = Field(
        default=None, description="Optional deciding agent ID (if formulated by an agent)"
    )


class CompanyDecisionResponse(BaseModel):
    """Data contract representing a persisted company decision."""

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


class CompanyDecisionFilter(BaseModel):
    """Filter criteria for querying company decisions."""

    model_config = ConfigDict(extra="forbid")

    status: DecisionStatus | None = None
    project_id: str | None = None
    task_id: str | None = None


class CompanyContextPacket(BaseModel):
    """Authoritative operational state memory packet.

    Aggregates live state across companies, departments, agents, projects, tasks,
    approvals, and decisions into a single ground truth structure.
    """

    model_config = ConfigDict(extra="forbid")

    company: dict[str, Any]
    departments: list[dict[str, Any]] = Field(default_factory=list)
    agents: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    tasks_summary: dict[str, Any] = Field(default_factory=dict)
    recent_approvals: list[dict[str, Any]] = Field(default_factory=list)
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime


class CeoInquiryCitation(BaseModel):
    """Provenance citation linking CEO response to an authoritative record."""

    model_config = ConfigDict(extra="forbid")

    source_type: str = Field(
        description="Type of entity: COMPANY, DEPARTMENT, AGENT, PROJECT, TASK, APPROVAL, DECISION"
    )
    source_id: str = Field(description="Unique ID of the entity cited")
    reference: str = Field(description="Human readable name or summary of the record")


class CeoInquiryRequest(BaseModel):
    """Request payload for querying the CEO grounded in persistent company state."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        min_length=1,
        description="The inquiry or question for the CEO regarding company state or operations",
    )


class CeoInquiryResponse(BaseModel):
    """Response payload containing CEO answer grounded in persistent company memory."""

    model_config = ConfigDict(extra="forbid")

    answer: str = Field(description="Authoritative, factual answer strictly grounded in memory")
    citations: list[CeoInquiryCitation] = Field(
        default_factory=list, description="Authoritative sources cited in answering"
    )
    grounded_state_timestamp: datetime = Field(
        description="Timestamp of the company memory snapshot used"
    )
