"""Domain exceptions for Verification & AI Evaluation adhering to docs/Phases.md Section 26 and docs/Rules.md Section 17."""


class VerificationError(Exception):
    """Base exception for all verification and evaluation errors."""


class VerificationAccessDeniedError(VerificationError):
    """Raised when an operator or user does not have permission to verify resources in a company."""


class VerificationNotFoundError(VerificationError):
    """Raised when a verification run, target task, artifact, or benchmark is not found."""


class InvalidVerificationCriteriaError(VerificationError):
    """Raised when evaluation criteria or scores are malformed."""


class VerificationPipelineFailureError(VerificationError):
    """Raised when an internal stage of the verification pipeline fails unrecoverably."""
