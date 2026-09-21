"""Pydantic schemas for Tool Gateway adhering to docs/Phases.md Section 13 and docs/Architecture.md Section 30-36."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolDefinitionResponse(BaseModel):
    """Response model for a registered tool definition."""

    name: str
    provider: str
    description: str
    version: str
    risk_level: str
    requires_approval: bool
    allowed_roles: list[str] = Field(default_factory=list)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)


class ToolListResponse(BaseModel):
    """List response for available tool definitions in the gateway."""

    items: list[ToolDefinitionResponse]
    total: int


class ToolExecuteApiRequest(BaseModel):
    """Request payload for executing a tool through the Tool Gateway."""

    agent_id: str = Field(..., description="UUID of the agent invoking the tool")
    tool_name: str = Field(..., description="Target tool name in registry")
    action: str = Field(default="default", description="Specific tool action or command")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Input parameters matching tool schema"
    )
    task_id: str | None = Field(
        default=None, description="Optional Task UUID if invoked during a task"
    )
    execution_id: str | None = Field(
        default=None, description="Optional Execution Record UUID if part of runtime execution"
    )


class ToolExecutionResponse(BaseModel):
    """Response model for a persisted tool execution audit record."""

    id: str
    company_id: str
    agent_id: str
    task_id: str | None = None
    execution_id: str | None = None
    tool_name: str
    action: str
    risk_level: str
    requires_approval: bool
    status: str
    input_params: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    error_details: str | None = None
    duration_ms: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ToolExecutionListResponse(BaseModel):
    """List response for tool execution audit records with pagination metadata."""

    items: list[ToolExecutionResponse]
    total: int
