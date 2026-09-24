"""Domain exceptions for semantic / vector memory adhering to docs/Phases.md Section 24 and docs/Memory.md Section 40."""


class SemanticMemoryError(Exception):
    """Base exception for all semantic memory domain exceptions."""


class SemanticMemoryNotFoundError(SemanticMemoryError):
    """Raised when an embedding or semantic entity is not found."""


class SemanticAccessDeniedError(SemanticMemoryError):
    """Raised when access to semantic memory of another company/tenant is attempted."""


class EmbeddingDimensionMismatchError(SemanticMemoryError):
    """Raised when an embedding vector does not match the configured model dimensions."""


class InvalidSemanticOperationError(SemanticMemoryError):
    """Raised when a semantic memory operation is malformed or invalid."""
