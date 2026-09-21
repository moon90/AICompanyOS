"""Pydantic schemas for agent task delegation adhering to docs/Phases.md Section 11."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskDelegateRequest(BaseModel):
    """Payload for delegating a task to an agent."""

    target_agent_id: str = Field(
        ..., description="ID of the registered agent receiving the delegation"
    )
    reason: str = Field(
        ..., min_length=3, max_length=1000, description="Justification and rationale for delegation"
    )
    scope: str | None = Field(
        default=None, max_length=1000, description="Specific boundaries or verification scope"
    )
    delegator_agent_id: str | None = Field(
        default=None, description="ID of delegating agent if initiated by an agent"
    )


class DelegationRecordResponse(BaseModel):
    """Response model for an individual delegation record."""

    id: str
    company_id: str
    task_id: str
    delegated_by_user_id: str | None = None
    delegated_by_agent_id: str | None = None
    delegated_to_agent_id: str
    scope: str | None = None
    reason: str
    depth: int
    status: str
    created_at: datetime
    delegated_to_agent_name: str | None = None
    delegated_to_agent_role: str | None = None
    delegated_by_agent_name: str | None = None
    delegated_by_user_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DelegationListResponse(BaseModel):
    """Paginated list response for company delegations."""

    items: list[DelegationRecordResponse]
    total: int


class PlanDelegateRequest(BaseModel):
    """Optional configuration when delegating a proposed CEO plan."""

    project_id: str | None = Field(
        default=None, description="Optional existing project ID to attach delegated tasks to"
    )
    project_name: str | None = Field(
        default=None, description="Optional custom name for newly created project"
    )


class PlanDelegationResultResponse(BaseModel):
    """Structured result returned when a CEO plan is decomposed and delegated."""

    plan_id: str
    project_id: str
    project_name: str
    parent_task_id: str
    parent_task_title: str
    child_tasks_count: int
    child_task_ids: list[str]
    dependencies_count: int
    delegations_count: int
