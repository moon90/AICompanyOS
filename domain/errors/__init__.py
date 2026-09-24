"""Domain package for error and bug management adhering to docs/Phases.md Section 19."""

from domain.errors.exceptions import (
    ErrorAccessDeniedError,
    ErrorNotFoundError,
    ErrorRecordError,
    InvalidErrorTransitionError,
    MissingEvidenceError,
    MissingResolutionError,
)
from domain.errors.schemas import (
    ErrorAssignPayload,
    ErrorCreatePayload,
    ErrorListResponse,
    ErrorRecordResponse,
    ErrorResolvePayload,
    ErrorSeverity,
    ErrorStatus,
    ErrorSummaryResponse,
    ErrorUpdatePayload,
    ErrorVerifyPayload,
)

__all__ = [
    "ErrorAccessDeniedError",
    "ErrorAssignPayload",
    "ErrorCreatePayload",
    "ErrorListResponse",
    "ErrorNotFoundError",
    "ErrorRecordError",
    "ErrorRecordResponse",
    "ErrorResolvePayload",
    "ErrorSeverity",
    "ErrorStatus",
    "ErrorSummaryResponse",
    "ErrorUpdatePayload",
    "ErrorVerifyPayload",
    "InvalidErrorTransitionError",
    "MissingEvidenceError",
    "MissingResolutionError",
]
