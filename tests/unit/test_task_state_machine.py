"""Unit tests for TaskStateMachine and status transitions."""

import pytest

from domain.work.exceptions import InvalidStatusTransitionError
from domain.work.state_machine import TaskStateMachine, TaskStatus


def test_task_state_machine_self_transition_allowed() -> None:
    """Verify that transitioning to the same status is always a no-op allowed transition."""
    for status in TaskStatus:
        assert TaskStateMachine.can_transition(status.value, status.value) is True


def test_task_state_machine_valid_forward_flow() -> None:
    """Verify standard happy-path lifecycle transitions."""
    flow = [
        TaskStatus.CREATED,
        TaskStatus.PLANNED,
        TaskStatus.READY,
        TaskStatus.ASSIGNED,
        TaskStatus.IN_PROGRESS,
        TaskStatus.VERIFYING,
        TaskStatus.COMPLETED,
    ]
    for i in range(len(flow) - 1):
        source = flow[i].value
        target = flow[i + 1].value
        assert TaskStateMachine.can_transition(source, target) is True, (
            f"Failed: {source} -> {target}"
        )
        TaskStateMachine.validate_transition(source, target)


def test_task_state_machine_invalid_skips() -> None:
    """Verify invalid leaps in state are rejected."""
    # Cannot jump directly from CREATED to COMPLETED
    assert (
        TaskStateMachine.can_transition(TaskStatus.CREATED.value, TaskStatus.COMPLETED.value)
        is False
    )
    with pytest.raises(InvalidStatusTransitionError) as exc_info:
        TaskStateMachine.validate_transition(TaskStatus.CREATED.value, TaskStatus.COMPLETED.value)
    assert "Cannot transition task from 'CREATED' to 'COMPLETED'" in str(exc_info.value)

    # Cannot jump from COMPLETED to CANCELLED directly
    assert (
        TaskStateMachine.can_transition(TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value)
        is False
    )
    with pytest.raises(InvalidStatusTransitionError):
        TaskStateMachine.validate_transition(TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value)


def test_task_state_machine_reopen_transitions() -> None:
    """Verify failed or cancelled tasks can be re-opened to planned or created."""
    assert TaskStateMachine.can_transition(TaskStatus.FAILED.value, TaskStatus.READY.value) is True
    assert (
        TaskStateMachine.can_transition(TaskStatus.CANCELLED.value, TaskStatus.PLANNED.value)
        is True
    )
    assert (
        TaskStateMachine.can_transition(TaskStatus.COMPLETED.value, TaskStatus.IN_PROGRESS.value)
        is True
    )


def test_task_state_machine_timestamp_calculations() -> None:
    """Verify started_at and completed_at timestamps are recorded and cleared appropriately."""
    # 1. Entering IN_PROGRESS records started_at
    s1, c1 = TaskStateMachine.calculate_timestamps(TaskStatus.IN_PROGRESS.value, None, None)
    assert s1 is not None
    assert c1 is None

    # 2. Re-entering IN_PROGRESS preserves original started_at
    s2, c2 = TaskStateMachine.calculate_timestamps(TaskStatus.IN_PROGRESS.value, s1, None)
    assert s2 == s1

    # 3. Entering COMPLETED records completed_at
    s3, c3 = TaskStateMachine.calculate_timestamps(TaskStatus.COMPLETED.value, s1, None)
    assert s3 == s1
    assert c3 is not None

    # 4. Re-opening task clears completed_at
    s4, c4 = TaskStateMachine.calculate_timestamps(TaskStatus.READY.value, s1, c3)
    assert s4 == s1
    assert c4 is None
