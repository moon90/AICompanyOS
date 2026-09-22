"""Approval and oversight domain exceptions."""


class ApprovalError(Exception):
    """Base exception for all approval domain errors."""


class ApprovalNotFoundError(ApprovalError):
    """Raised when an approval request cannot be located."""


class ApprovalAlreadyProcessedError(ApprovalError):
    """Raised when an approval request has already transitioned to a terminal status."""


class ApprovalAccessDeniedError(ApprovalError):
    """Raised when a user lacks company membership or permissions to act on an approval request."""


class InvalidApprovalTransitionError(ApprovalError):
    """Raised when an invalid state transition is attempted on an approval request."""


class AgentCannotApproveError(ApprovalError):
    """Raised when an automated agent attempts to approve an action per docs/Rules.md § 42."""
