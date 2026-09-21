"""Schemas and data models for Tool Gateway adhering to docs/Architecture.md Sections 30-36."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ToolRiskLevel(StrEnum):
    """Tool risk classification adhering to docs/Rules.md Section 36."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ToolExecutionStatus(StrEnum):
    """Tool execution status."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    BLOCKED = "BLOCKED"


class ToolDefinition(BaseModel):
    """Authoritative declaration of a tool in the Tool Registry per docs/Phases.md § 13."""

    name: str = Field(..., description="Unique tool identifier, e.g. web_search, documents, github")
    provider: str = Field(..., description="Backing provider/adapter name")
    description: str = Field(..., description="Capability description for planning & execution")
    version: str = Field(default="1.0.0", description="Semantic tool version")
    risk_level: ToolRiskLevel = Field(default=ToolRiskLevel.LOW, description="Declared risk tier")
    requires_approval: bool = Field(default=False, description="Flag if human approval is mandated")
    allowed_roles: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed agent roles or wildcard ['*']",
    )
    input_schema: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for input validation"
    )
    output_schema: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for normalized output"
    )


class ToolCallRequest(BaseModel):
    """Standard tool invocation payload from an agent."""

    agent_id: str = Field(..., description="Calling agent ID")
    tool_name: str = Field(..., description="Name of the registered tool to invoke")
    action: str = Field(default="default", description="Specific action/method to invoke")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Arguments for tool action"
    )
    task_id: str | None = Field(default=None, description="Optional task context ID")
    execution_id: str | None = Field(default=None, description="Optional execution run context ID")


class ToolCallResult(BaseModel):
    """Normalized output from Tool Gateway."""

    tool_name: str
    action: str
    status: str = ToolExecutionStatus.SUCCESS.value
    output: dict[str, Any] = Field(default_factory=dict)
    risk_level: str = ToolRiskLevel.LOW.value
    requires_approval: bool = False
    duration_ms: int = 0
    error_details: str | None = None


# Normalized Tool Output Domain Types (docs/Rules.md § 35)


class SearchResultItem(BaseModel):
    """Normalized search result entry."""

    title: str
    url: str
    snippet: str


class SearchResult(BaseModel):
    """Normalized web search response."""

    query: str
    total_results: int
    results: list[SearchResultItem] = Field(default_factory=list)


class DocumentContent(BaseModel):
    """Normalized document repository response."""

    document_id: str
    title: str
    content: str
    word_count: int
    format: str = "markdown"
    metadata: dict[str, Any] = Field(default_factory=dict)


class GitHubResult(BaseModel):
    """Normalized GitHub repository tool response."""

    repository: str
    action: str
    data: dict[str, Any] = Field(default_factory=dict)
