"""Domain schemas for Agent Runtime adhering to docs/Phases.md Section 12."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuntimeLimits(BaseModel):
    """Runtime limits and safety bounds per docs/Phases.md Section 12."""

    max_steps: int = Field(default=5, ge=1, le=20, description="Maximum reasoning steps")
    max_duration_seconds: int = Field(
        default=60, ge=1, le=300, description="Execution timeout in seconds"
    )
    max_tokens: int = Field(default=8000, ge=100, le=128000, description="Maximum token budget")
    max_cost: float = Field(default=0.50, ge=0.0, description="Maximum monetary cost budget")


class ExecutionStep(BaseModel):
    """Individual step executed during an agent's reasoning loop."""

    step_number: int
    thought: str
    action_type: str = Field(
        default="REASON", description="Type of action: REASON, DRAFT, CODE, VERIFY, FINALIZE"
    )
    observation: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Deliverable(BaseModel):
    """Structured work product produced by an agent."""

    title: str
    format: str = Field(default="markdown", description="Content format: markdown, python, text")
    content: str
    summary: str


class ExecutionResult(BaseModel):
    """Authoritative structured output produced by the Agent Runtime."""

    status: str = Field(default="SUCCESS", description="SUCCESS, FAILED, TIMED_OUT")
    summary: str
    deliverable: Deliverable
    steps: list[ExecutionStep] = Field(default_factory=list)
    self_assessment_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Agent confidence score (0.0 - 1.0)"
    )
    verification_notes: str = Field(
        default="Ready for operator/system verification",
        description="Notes for the verification stage",
    )
    step_count: int = 0
    duration_ms: int = 0
    tokens_used: int = 0
    estimated_cost: float = 0.0
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AgentExecutionContext(BaseModel):
    """Authoritative context packet gathered for executing an agent on a task."""

    company_id: str
    company_name: str
    company_mission: str | None = None
    company_industry: str | None = None
    department_name: str | None = None
    department_code: str | None = None
    task_id: str
    task_title: str
    task_objective: str | None = None
    task_description: str | None = None
    task_priority: str
    prerequisite_outputs: list[dict[str, Any]] = Field(default_factory=list)
    agent_id: str
    agent_name: str
    agent_role: str
    agent_authority_level: str | int = "specialist"
    system_prompt: str | None = None
    model: str
    capabilities: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
