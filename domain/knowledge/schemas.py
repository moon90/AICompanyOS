"""Domain schemas for advanced company knowledge adhering to docs/Phases.md Section 23 and docs/Memory.md Sections 31-39."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class KnowledgeCategory(StrEnum):
    """Canonical categories for company knowledge."""

    STRATEGY = "STRATEGY"
    RESEARCH = "RESEARCH"
    POLICY = "POLICY"
    DECISION_RATIONALE = "DECISION_RATIONALE"
    PROCEDURE = "PROCEDURE"
    MEETING_NOTE = "MEETING_NOTE"
    HISTORICAL_RESULT = "HISTORICAL_RESULT"
    GENERAL = "GENERAL"


class KnowledgeSourceType(StrEnum):
    """Provenance sources for knowledge items adhering to docs/Memory.md § 34."""

    USER = "USER"
    AGENT = "AGENT"
    DOCUMENT = "DOCUMENT"
    RESEARCH = "RESEARCH"
    MEETING = "MEETING"
    POST_MORTEM = "POST_MORTEM"
    EXTERNAL = "EXTERNAL"
    SYSTEM = "SYSTEM"


class KnowledgeConfidence(StrEnum):
    """Confidence levels for knowledge records adhering to docs/Memory.md § 36."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    ESTIMATED = "ESTIMATED"


class KnowledgeCreatePayload(BaseModel):
    """Payload to create a new persistent company knowledge item."""

    title: str = Field(..., min_length=1, max_length=255)
    category: KnowledgeCategory = KnowledgeCategory.GENERAL
    content: str = Field(..., min_length=1)
    project_id: str | None = None
    task_id: str | None = None
    decision_id: str | None = None
    artifact_id: str | None = None
    source_type: KnowledgeSourceType = KnowledgeSourceType.USER
    source_uri: str | None = Field(default=None, max_length=1024)
    author_name: str | None = Field(default=None, max_length=255)
    confidence: KnowledgeConfidence = KnowledgeConfidence.HIGH
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeUpdatePayload(BaseModel):
    """Payload to update an existing company knowledge item."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    category: KnowledgeCategory | None = None
    content: str | None = Field(default=None, min_length=1)
    project_id: str | None = None
    task_id: str | None = None
    decision_id: str | None = None
    artifact_id: str | None = None
    source_type: KnowledgeSourceType | None = None
    source_uri: str | None = Field(default=None, max_length=1024)
    author_name: str | None = Field(default=None, max_length=255)
    confidence: KnowledgeConfidence | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class KnowledgeResponse(BaseModel):
    """Authoritative representation of a company knowledge item."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    company_id: str
    project_id: str | None = None
    task_id: str | None = None
    decision_id: str | None = None
    artifact_id: str | None = None
    title: str
    category: str
    content: str
    source_type: str
    source_uri: str | None = None
    author_name: str
    confidence: str
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("metadata", "knowledge_metadata"),
    )
    created_at: datetime
    updated_at: datetime


class KnowledgeListResponse(BaseModel):
    """Paginated list of company knowledge items."""

    items: list[KnowledgeResponse]
    total: int
    page: int
    page_size: int


class KnowledgeQueryRequest(BaseModel):
    """Inquiry request for historical company knowledge."""

    question: str = Field(..., min_length=1)
    project_id: str | None = None
    categories: list[KnowledgeCategory] = Field(default_factory=list)


class KnowledgeQueryCitation(BaseModel):
    """Grounded citation for an answered knowledge question."""

    source_type: str
    source_id: str
    title: str
    reference: str
    confidence: str = "HIGH"


class KnowledgeQueryResponse(BaseModel):
    """Grounded answer with provenance citations answering Section 23 core questions."""

    question: str
    answer: str
    canonical_topic: str | None = None
    citations: list[KnowledgeQueryCitation] = Field(default_factory=list)
    related_decisions: list[dict[str, Any]] = Field(default_factory=list)
    related_artifacts: list[dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime


class SelectiveContextRequest(BaseModel):
    """Request to synthesize bounded context for an agent run without loading entire DB."""

    task_id: str | None = None
    project_id: str | None = None
    intent_keywords: list[str] = Field(default_factory=list)
    max_items: int = Field(default=15, ge=1, le=50)


class SelectiveContextResponse(BaseModel):
    """Selective, bounded context package fulfilling Section 23 acceptance criteria."""

    company_id: str
    project: dict[str, Any] | None = None
    task: dict[str, Any] | None = None
    relevant_decisions: list[dict[str, Any]] = Field(default_factory=list)
    relevant_knowledge: list[KnowledgeResponse] = Field(default_factory=list)
    relevant_artifacts: list[dict[str, Any]] = Field(default_factory=list)
    historical_results_summary: list[dict[str, Any]] = Field(default_factory=list)
    synthesized_context: str
    item_count: int
    timestamp: datetime
