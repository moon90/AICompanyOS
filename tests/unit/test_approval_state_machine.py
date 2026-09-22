"""Unit tests for ApprovalStateMachine adhering to docs/Phases.md Section 14."""

import pytest

from domain.approvals.exceptions import (
    ApprovalAlreadyProcessedError,
    InvalidApprovalTransitionError,
)
from domain.approvals.schemas import ApprovalStatus
from domain.approvals.state_machine import ApprovalStateMachine


def test_valid_transitions_from_pending() -> None:
    """Verify PENDING can transition to APPROVED, REJECTED, and CANCELLED."""
    assert (
        ApprovalStateMachine.can_transition(ApprovalStatus.PENDING, ApprovalStatus.APPROVED) is True
    )
    assert (
        ApprovalStateMachine.can_transition(ApprovalStatus.PENDING, ApprovalStatus.REJECTED) is True
    )
    assert (
        ApprovalStateMachine.can_transition(ApprovalStatus.PENDING, ApprovalStatus.CANCELLED)
        is True
    )
    assert (
        ApprovalStateMachine.can_transition(ApprovalStatus.PENDING, ApprovalStatus.PENDING) is True
    )

    # Validate transition does not raise
    ApprovalStateMachine.validate_transition(ApprovalStatus.PENDING, ApprovalStatus.APPROVED)
    ApprovalStateMachine.validate_transition(ApprovalStatus.PENDING, ApprovalStatus.REJECTED)
    ApprovalStateMachine.validate_transition(ApprovalStatus.PENDING, ApprovalStatus.CANCELLED)


def test_terminal_states_cannot_transition() -> None:
    """Verify terminal statuses (APPROVED, REJECTED, CANCELLED) cannot transition to any other status."""
    terminal_states = [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.CANCELLED]

    for term in terminal_states:
        for target in [
            ApprovalStatus.PENDING,
            ApprovalStatus.APPROVED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.CANCELLED,
        ]:
            if target != term:
                assert ApprovalStateMachine.can_transition(term, target) is False
                with pytest.raises(ApprovalAlreadyProcessedError) as exc_info:
                    ApprovalStateMachine.validate_transition(term, target)
                assert "already in terminal state" in str(exc_info.value)


def test_invalid_arbitrary_transition() -> None:
    """Verify invalid transition from unrecognized state raises InvalidApprovalTransitionError."""
    with pytest.raises(InvalidApprovalTransitionError) as exc_info:
        ApprovalStateMachine.validate_transition("UNKNOWN_STATE", ApprovalStatus.APPROVED)
    assert "Cannot transition approval request" in str(exc_info.value)
