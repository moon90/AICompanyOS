"""Domain exceptions for agent task delegation adhering to docs/PRD.md Section 41 and docs/Rules.md §§ 58, 60, 61."""


class DelegationError(Exception):
    """Base domain exception for all delegation failures."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class CircularDelegationError(DelegationError):
    """Raised when delegation creates a cycle in the delegation chain."""


class MaxDelegationDepthExceededError(DelegationError):
    """Raised when delegation depth exceeds the configured threshold."""


class InvalidDelegationHierarchyError(DelegationError):
    """Raised when delegation violates organizational hierarchy (e.g. upward or unpermitted cross-department)."""


class DelegationAccessDeniedError(DelegationError):
    """Raised when user or agent lacks authority to delegate work within the tenant."""


class DelegationNotFoundError(DelegationError):
    """Raised when a referenced delegation record does not exist."""
