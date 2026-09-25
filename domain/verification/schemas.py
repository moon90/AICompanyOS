"""Domain schemas for Verification & AI Evaluation adhering to docs/Phases.md Section 26, docs/Architecture.md Sections 71-72, and docs/Rules.md Sections 17 & 146."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CriterionType(StrEnum):
    """The 8 canonical evaluation dimensions per docs/Phases.md Section 26."""

    CORRECTNESS = "CORRECTNESS"
    COMPLETENESS = "COMPLETENESS"
    TOOL_USAGE = "TOOL_USAGE"
    PERMISSION_COMPLIANCE = "PERMISSION_COMPLIANCE"
    HALLUCINATION_RATE = "HALLUCINATION_RATE"
    INSTRUCTION_FOLLOWING = "INSTRUCTION_FOLLOWING"
    TASK_COMPLETION = "TASK_COMPLETION"
    EVIDENCE_QUALITY = "EVIDENCE_QUALITY"


class VerificationStatus(StrEnum):
    """Terminal and intermediate verification statuses."""

    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"


class PipelineStage(StrEnum):
    """The 5-stage verification pipeline per docs/Architecture.md Section 71."""

    SCHEMA_VALIDATION = "SCHEMA_VALIDATION"
    EVIDENCE_CHECK = "EVIDENCE_CHECK"
    TASK_VERIFICATION = "TASK_VERIFICATION"
    EVALUATION = "EVALUATION"
    COMPLETED = "COMPLETED"


class BenchmarkCategory(StrEnum):
    """Representative task categories for agent evaluation per docs/Phases.md Section 26."""

    CEO = "CEO"
    MARKETING = "MARKETING"
    ENGINEERING = "ENGINEERING"
    SALES = "SALES"
    TOOL = "TOOL"
    APPROVAL = "APPROVAL"
    FAILURE = "FAILURE"
    RECOVERY = "RECOVERY"


class CriterionScoreItem(BaseModel):
    """Individual score and evidence for an evaluation criterion."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    criterion: CriterionType
    score: float = Field(ge=0.0, le=100.0)
    status: VerificationStatus
    details: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)


class VerificationRunResponse(BaseModel):
    """Full detail of a verification pipeline execution."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    target_type: str
    target_id: str
    agent_id: str | None = None
    status: VerificationStatus
    overall_score: float = Field(ge=0.0, le=100.0)
    pipeline_stage: PipelineStage
    summary: str = ""
    created_at: datetime
    completed_at: datetime | None = None
    criterion_scores: list[CriterionScoreItem] = Field(default_factory=list)


class VerificationRunListResponse(BaseModel):
    """Paginated list of verification pipeline executions."""

    items: list[VerificationRunResponse]
    total: int


class TaskVerificationRequest(BaseModel):
    """Request to verify an agent task execution."""

    force_reverify: bool = False
    custom_criteria: list[CriterionType] | None = None


class ArtifactVerificationRequest(BaseModel):
    """Request to verify an artifact against schema and evidence rules."""

    require_evidence: bool = True


class BenchmarkRunRequest(BaseModel):
    """Request to execute a representative evaluation benchmark suite."""

    category: BenchmarkCategory | None = None
    benchmark_id: str | None = None


class BenchmarkRunResponse(BaseModel):
    """Result of an evaluation benchmark run."""

    benchmark_id: str
    name: str
    category: BenchmarkCategory
    run_id: str
    overall_score: float
    status: VerificationStatus
    passed: bool
    duration_ms: float
    timestamp: datetime


class BenchmarkDefinitionResponse(BaseModel):
    """Configured evaluation benchmark suite or task."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    category: BenchmarkCategory
    name: str
    description: str
    task_prompt: str
    target_role: str
    min_passing_score: float
    is_active: bool


class VerificationTelemetryResponse(BaseModel):
    """Telemetry on verification pipeline passes, failures, and criterion scores."""

    company_id: str
    total_runs: int
    passed_runs: int
    failed_runs: int
    pass_rate: float
    avg_overall_score: float
    avg_scores_by_criterion: dict[str, float]
    runs_by_target_type: dict[str, int]
    last_run_at: datetime | None = None
    timestamp: datetime
