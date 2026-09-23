"""Domain exceptions for Company Memory and Decisions."""


class MemoryError(Exception):
    """Base exception for all memory and company state operations."""


class DecisionNotFoundError(MemoryError):
    """Raised when a referenced decision cannot be found within company scope."""


class DecisionAlreadySupersededError(MemoryError):
    """Raised when attempting to supersede a decision that has already been superseded or revoked."""


class MemoryAccessDeniedError(MemoryError):
    """Raised when a user attempts to access or mutate company memory outside their tenancy."""


class InvalidDecisionStateError(MemoryError):
    """Raised when a decision mutation violates domain state machine invariants."""
