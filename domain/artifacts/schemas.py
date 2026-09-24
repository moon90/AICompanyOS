"""Domain schemas for artifacts and documents adhering to docs/Phases.md Section 22 and docs/Memory.md Section 31."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ArtifactType(StrEnum):
    """Supported artifact and document types."""

    MARKDOWN = "MARKDOWN"
    TEXT = "TEXT"
    PDF = "PDF"
    CSV = "CSV"
    JSON = "JSON"
    IMAGE = "IMAGE"
    CODE = "CODE"
    REPORT = "REPORT"
    DOCUMENT = "DOCUMENT"


class ArtifactCreatePayload(BaseModel):
    """Payload to create a new artifact or document."""

    name: str = Field(..., min_length=1, max_length=255)
    artifact_type: ArtifactType = ArtifactType.MARKDOWN
    project_id: str | None = None
    task_id: str | None = None
    creator_name: str | None = Field(default=None, max_length=255)
    created_by_agent_id: str | None = None
    created_by_user_id: str | None = None
    location: str | None = Field(default=None, max_length=1024)
    content: str | None = None
    file_size_bytes: int | None = Field(default=None, ge=0)
    change_summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactUpdatePayload(BaseModel):
    """Payload to update an artifact's metadata or mutable details."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    artifact_type: ArtifactType | None = None
    project_id: str | None = None
    task_id: str | None = None
    location: str | None = Field(default=None, max_length=1024)
    content: str | None = None
    file_size_bytes: int | None = Field(default=None, ge=0)
    change_summary: str | None = None
    metadata: dict[str, Any] | None = None


class ArtifactVersionCreatePayload(BaseModel):
    """Payload to create a new version of an existing artifact."""

    content: str | None = None
    location: str | None = Field(default=None, max_length=1024)
    change_summary: str = Field(..., min_length=1)
    creator_name: str | None = Field(default=None, max_length=255)
    created_by_agent_id: str | None = None
    created_by_user_id: str | None = None
    file_size_bytes: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactResponse(BaseModel):
    """Authoritative response representation of an artifact."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    company_id: str
    project_id: str | None = None
    task_id: str | None = None
    created_by_agent_id: str | None = None
    created_by_user_id: str | None = None
    creator_name: str
    name: str
    artifact_type: str
    version: int
    parent_artifact_id: str | None = None
    location: str | None = None
    content: str | None = None
    file_size_bytes: int
    change_summary: str | None = None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("metadata", "artifact_metadata"),
    )
    created_at: datetime
    updated_at: datetime


class ArtifactVersionItem(BaseModel):
    """Lightweight lineage item for version history."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    version: int
    creator_name: str
    change_summary: str | None = None
    file_size_bytes: int
    created_at: datetime
    parent_artifact_id: str | None = None


class ArtifactListResponse(BaseModel):
    """Paginated list of artifacts."""

    items: list[ArtifactResponse]
    total: int
    page: int
    page_size: int
