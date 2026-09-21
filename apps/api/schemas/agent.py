"""Pydantic schemas for Agent Registry API requests and responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentDefinitionResponse(BaseModel):
    """Schema for agent definition responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_id: str
    version: str
    system_prompt: str | None = None
    model: str
    capabilities: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
    is_current: bool
    created_at: datetime


class DepartmentSummary(BaseModel):
    """Summary of department assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str


class ManagerSummary(BaseModel):
    """Summary of reporting manager."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    role: str


class SubordinateSummary(BaseModel):
    """Summary of direct report."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    role: str
    status: str


class AgentResponse(BaseModel):
    """Schema for standard agent response in registry listings."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    department_id: str | None = None
    department: DepartmentSummary | None = None
    name: str
    role: str
    type: str
    reports_to: str | None = None
    manager: ManagerSummary | None = None
    mission: str | None = None
    status: str
    authority_level: str
    created_at: datetime
    updated_at: datetime
    current_definition: AgentDefinitionResponse | None = None


class AgentDetailResponse(AgentResponse):
    """Schema for comprehensive agent detail page."""

    definitions: list[AgentDefinitionResponse] = Field(default_factory=list)
    subordinates: list[SubordinateSummary] = Field(default_factory=list)


class AgentCreateRequest(BaseModel):
    """Payload for registering a new agent."""

    name: str = Field(..., min_length=1, max_length=255, description="Full agent display name")
    role: str = Field(..., min_length=1, max_length=128, description="Organizational title or role")
    type: str = Field(
        "specialist",
        max_length=64,
        description="Agent category (executive, department_head, specialist)",
    )
    department_id: str | None = Field(None, description="Department UUID if assigned")
    reports_to: str | None = Field(None, description="Manager agent UUID if reporting")
    mission: str | None = Field(None, description="Core objective and responsibility statement")
    authority_level: str = Field("specialist", max_length=64, description="Authorization tier")
    system_prompt: str | None = Field(None, description="Initial system prompt declaration")
    model: str = Field("gemini-1.5-pro", max_length=128, description="Target LLM model reference")
    capabilities: list[str] = Field(default_factory=list, description="Declared capabilities")
    tools: list[str] = Field(default_factory=list, description="Declared tools references")
    configuration: dict[str, Any] = Field(default_factory=dict, description="Model parameters")


class AgentUpdateRequest(BaseModel):
    """Payload for updating agent metadata."""

    name: str | None = Field(None, min_length=1, max_length=255)
    role: str | None = Field(None, min_length=1, max_length=128)
    type: str | None = Field(None, max_length=64)
    department_id: str | None = None
    reports_to: str | None = None
    mission: str | None = None
    status: str | None = Field(None, max_length=32)
    authority_level: str | None = Field(None, max_length=64)


class AgentDefinitionCreateRequest(BaseModel):
    """Payload for creating a new version of an agent definition."""

    version: str = Field(
        ..., min_length=1, max_length=32, description="Semantic version string (e.g. 1.1)"
    )
    system_prompt: str | None = Field(None, description="Updated prompt declaration")
    model: str = Field("gemini-1.5-pro", max_length=128)
    capabilities: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
