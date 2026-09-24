"""Domain schemas for semantic / vector memory adhering to docs/Phases.md Section 24 and docs/Memory.md Section 40."""

from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class SemanticSearchRequest(BaseModel):
    """Request payload to perform semantic similarity vector search."""

    query: str = Field(
        ..., min_length=1, description="Natural language search inquiry or task statement"
    )
    limit: int = Field(default=5, ge=1, le=50, description="Maximum candidate matches to retrieve")
    min_similarity: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Minimum cosine similarity threshold (-1.0 to 1.0)",
    )
    source_types: list[str] | None = Field(
        default=None,
        description="Optional source type filter (e.g. ['KNOWLEDGE', 'DECISION', 'ARTIFACT', 'TASK'])",
    )
    project_id: str | None = Field(
        default=None,
        description="Optional filter by associated project ID",
    )


class SemanticSearchResultItem(BaseModel):
    """Grounded semantic match item returned by pgvector similarity search."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    source_type: str
    source_id: str
    title: str
    content_chunk: str
    similarity_score: float
    distance: float
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("metadata", "embedding_metadata"),
    )


class SemanticSearchResponse(BaseModel):
    """Complete semantic search response with similarity rankings and metadata."""

    query: str
    results: list[SemanticSearchResultItem]
    total_matches: int
    execution_time_ms: float
    timestamp: datetime


class SemanticContextBuildRequest(BaseModel):
    """Request to synthesize bounded context for an agent based on semantic search."""

    query: str = Field(..., min_length=1, description="Task statement or agent prompt")
    task_id: str | None = Field(default=None, description="Optional target task ID")
    project_id: str | None = Field(default=None, description="Optional associated project ID")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum semantic chunks to inject")
    min_similarity: float = Field(
        default=0.05, ge=-1.0, le=1.0, description="Minimum cosine relevance threshold"
    )


class SemanticContextBuildResponse(BaseModel):
    """Selective, bounded context synthesized via vector embeddings for agent execution."""

    query: str
    company_id: str
    synthesized_context: str
    items_used: list[SemanticSearchResultItem]
    total_items: int
    timestamp: datetime


class VectorMemoryStatsResponse(BaseModel):
    """Telemetry metrics and health of company vector embeddings."""

    company_id: str
    total_embeddings: int
    count_by_source: dict[str, int]
    dimension: int
    vector_engine: str
    index_type: str
    timestamp: datetime


class BatchIndexRequest(BaseModel):
    """Request to index or re-index company structured state into vector memory."""

    source_types: list[str] | None = Field(
        default=None,
        description="Optional subset of sources to index (e.g. ['KNOWLEDGE', 'DECISION', 'ARTIFACT'])",
    )
    force_reindex: bool = Field(
        default=False,
        description="Whether to overwrite existing vector embeddings",
    )


class BatchIndexResponse(BaseModel):
    """Result of batch indexing operation."""

    company_id: str
    indexed_count: int
    updated_count: int
    skipped_count: int
    total_chunks: int
    duration_ms: float
    timestamp: datetime


class VectorEmbeddingResponse(BaseModel):
    """Direct representation of a stored vector embedding entity."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    company_id: str
    source_type: str
    source_id: str
    chunk_index: int
    content: str
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("metadata", "embedding_metadata"),
    )
    created_at: datetime
    updated_at: datetime
