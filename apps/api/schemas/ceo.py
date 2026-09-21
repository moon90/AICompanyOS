"""Pydantic schemas for the CEO Orchestrator API endpoints."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PlanCreateRequest(BaseModel):
    """Request payload for submitting a goal to the CEO orchestrator."""

    objective: str = Field(
        ..., min_length=3, max_length=2000, description="Primary goal to plan and decompose"
    )
    requested_outcome: str | None = Field(
        default=None, max_length=2000, description="Desired final outcome or deliverable"
    )
    constraints: list[str] = Field(default_factory=list, description="User or policy constraints")
    priority: Literal["low", "medium", "high", "critical"] = Field(
        default="medium", description="Goal priority"
    )
    requirements: list[str] = Field(
        default_factory=list, description="Specific user-provided requirements"
    )


class CeoContextResponse(BaseModel):
    """Authoritative company context snapshot available to the CEO."""

    company: dict[str, Any]
    ceo_agent: dict[str, Any] | None
    departments: list[dict[str, Any]]
    agents: list[dict[str, Any]]
    agent_count: int
    department_count: int


class PlanSummaryResponse(BaseModel):
    """Compact summary of a generated CEO plan."""

    id: str
    company_id: str
    user_id: str
    ceo_agent_id: str | None
    goal: str
    requested_outcome: str | None
    priority: str
    status: str
    reasoning_summary: str
    step_count: int
    created_at: datetime
    updated_at: datetime


class PlanDetailResponse(BaseModel):
    """Full detail of a generated CEO plan proposal with DAG and delegation proposals."""

    id: str
    company_id: str
    user_id: str
    ceo_agent_id: str | None
    goal: str
    requested_outcome: str | None
    priority: str
    status: str
    reasoning_summary: str
    context_snapshot: dict[str, Any]
    plan_steps: list[dict[str, Any]]
    delegation_proposals: list[dict[str, Any]]
    approval_requirements: list[dict[str, Any]]
    risks: list[dict[str, Any]]
    assumptions: list[str]
    created_at: datetime
    updated_at: datetime
