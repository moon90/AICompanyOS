"""Semantic / Vector Memory domain package adhering to docs/Phases.md Section 24 and docs/Memory.md Section 40."""

from domain.semantic.exceptions import (
    EmbeddingDimensionMismatchError,
    InvalidSemanticOperationError,
    SemanticAccessDeniedError,
    SemanticMemoryError,
    SemanticMemoryNotFoundError,
)
from domain.semantic.schemas import (
    BatchIndexRequest,
    BatchIndexResponse,
    SemanticContextBuildRequest,
    SemanticContextBuildResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResultItem,
    VectorEmbeddingResponse,
    VectorMemoryStatsResponse,
)

__all__ = [
    "BatchIndexRequest",
    "BatchIndexResponse",
    "EmbeddingDimensionMismatchError",
    "InvalidSemanticOperationError",
    "SemanticAccessDeniedError",
    "SemanticContextBuildRequest",
    "SemanticContextBuildResponse",
    "SemanticMemoryError",
    "SemanticMemoryNotFoundError",
    "SemanticSearchRequest",
    "SemanticSearchResponse",
    "SemanticSearchResultItem",
    "VectorEmbeddingResponse",
    "VectorMemoryStatsResponse",
]
