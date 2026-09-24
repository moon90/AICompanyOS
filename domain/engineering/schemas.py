"""Domain schemas for engineering file tracking adhering to docs/Phases.md Section 20 and docs/Memory.md Section 61."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TestStatus(StrEnum):
    """Test execution status for engineering tasks."""

    __test__ = False
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class VerificationState(StrEnum):
    """Engineering code verification states."""

    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class FileChangeType(StrEnum):
    """File change operation types."""

    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    RENAMED = "RENAMED"


class EngineeringContextUpsertPayload(BaseModel):
    """Payload to create or update engineering task context."""

    repository: str | None = Field(default=None, max_length=255)
    branch: str | None = Field(default=None, max_length=255)
    pull_request_number: str | None = Field(default=None, max_length=64)
    pull_request_url: str | None = Field(default=None, max_length=512)
    pull_request_title: str | None = Field(default=None, max_length=255)
    commit_count: int | None = Field(default=None, ge=0)
    test_status: TestStatus | None = None
    test_output_summary: str | None = None
    verification_state: VerificationState | None = None
    verification_notes: str | None = None


class FileChangeCreatePayload(BaseModel):
    """Payload to record a file modification associated with a task."""

    file_path: str = Field(..., min_length=1, max_length=1024)
    repository: str = Field(default="main", max_length=255)
    branch: str = Field(default="main", max_length=255)
    agent_id: str | None = None
    agent_name: str | None = Field(default=None, max_length=255)
    change_type: FileChangeType = FileChangeType.MODIFIED
    commit_hash: str | None = Field(default=None, max_length=64)
    commit_message: str | None = Field(default=None, max_length=255)
    additions: int = Field(default=0, ge=0)
    deletions: int = Field(default=0, ge=0)
    change_summary: str | None = None


class FileChangeBulkCreatePayload(BaseModel):
    """Payload to record multiple file modifications in batch."""

    changes: list[FileChangeCreatePayload] = Field(..., min_length=1)


class EngineeringContextResponse(BaseModel):
    """Response model for task engineering context."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    task_id: str
    repository: str
    branch: str
    pull_request_number: str | None = None
    pull_request_url: str | None = None
    pull_request_title: str | None = None
    commit_count: int
    test_status: str
    test_output_summary: str | None = None
    verification_state: str
    verification_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class FileChangeResponse(BaseModel):
    """Response model for a task file change."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    task_id: str
    file_path: str
    repository: str
    branch: str
    agent_id: str | None = None
    agent_name: str
    change_type: str
    commit_hash: str | None = None
    commit_message: str | None = None
    additions: int
    deletions: int
    change_summary: str | None = None
    last_modified_at: datetime
    created_at: datetime


class EngineeringTaskViewResponse(BaseModel):
    """Comprehensive engineering view for a task: context + file changes."""

    model_config = ConfigDict(from_attributes=True)

    task_id: str
    company_id: str
    context: EngineeringContextResponse | None = None
    file_changes: list[FileChangeResponse] = Field(default_factory=list)
    total_files_changed: int = 0
    total_additions: int = 0
    total_deletions: int = 0


class CompanyFileHistoryItem(BaseModel):
    """Aggregated company-wide file touch record."""

    file_path: str
    repository: str
    branches: list[str]
    change_count: int
    last_modified_at: datetime
    last_commit_hash: str | None = None
    last_agent_id: str | None = None
    last_agent_name: str | None = None
