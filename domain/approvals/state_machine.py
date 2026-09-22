"""State machine rules and status transitions for Approval & Oversight System."""

from domain.approvals.exceptions import (
    ApprovalAlreadyProcessedError,
    InvalidApprovalTransitionError,
)
from domain.approvals.schemas import ApprovalStatus


class ApprovalStateMachine:
    """Authoritative state machine governing approval request lifecycles."""

    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        ApprovalStatus.PENDING: {
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.CANCELLED,
        },
        ApprovalStatus.APPROVED: set(),
        ApprovalStatus.REJECTED: set(),
        ApprovalStatus.CANCELLED: set(),
    }

    TERMINAL_STATUSES: set[str] = {
        ApprovalStatus.APPROVED,
        ApprovalStatus.REJECTED,
        ApprovalStatus.CANCELLED,
    }

    @classmethod
    def can_transition(cls, current_status: str, new_status: str) -> bool:
        """Check if transition from current_status to new_status is allowed."""
        if current_status == new_status:
            return True
        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, set())
        return new_status in allowed

    @classmethod
    def validate_transition(cls, current_status: str, new_status: str) -> None:
        """Validate state transition or raise appropriate domain error."""
        if current_status in cls.TERMINAL_STATUSES:
            raise ApprovalAlreadyProcessedError(
                f"Approval request is already in terminal state '{current_status}' and cannot be modified."
            )

        if not cls.can_transition(current_status, new_status):
            allowed = sorted(cls.ALLOWED_TRANSITIONS.get(current_status, set()))
            raise InvalidApprovalTransitionError(
                f"Cannot transition approval request from '{current_status}' to '{new_status}'. "
                f"Allowed transitions: {allowed}"
            )
