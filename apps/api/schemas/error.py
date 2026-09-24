"""API schemas for Error & Bug Management adhering to docs/Phases.md Section 19."""

from pydantic import BaseModel, Field

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


class ErrorReopenApiRequest(BaseModel):
    """Payload to reopen a resolved/verified error."""

    reason: str = Field(..., min_length=1, max_length=1000)


__all__ = [
    "ErrorAssignPayload",
    "ErrorCreatePayload",
    "ErrorListResponse",
    "ErrorRecordResponse",
    "ErrorReopenApiRequest",
    "ErrorResolvePayload",
    "ErrorSeverity",
    "ErrorStatus",
    "ErrorSummaryResponse",
    "ErrorUpdatePayload",
    "ErrorVerifyPayload",
]
