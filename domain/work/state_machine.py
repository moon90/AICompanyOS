"""State machine rules and status enumerations for projects and tasks."""

from datetime import UTC, datetime
from enum import StrEnum

from domain.work.exceptions import InvalidStatusTransitionError


class ProjectStatus(StrEnum):
    """Authoritative project statuses from docs/Phases.md Section 10."""

    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ProjectPriority(StrEnum):
    """Project priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(StrEnum):
    """Authoritative task statuses from docs/Phases.md Section 10."""

    CREATED = "CREATED"
    PLANNED = "PLANNED"
    READY = "READY"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class TaskPriority(StrEnum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStateMachine:
    """Manages valid state transitions and lifecycle timestamps for tasks."""

    # Explicit transition map
    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        TaskStatus.CREATED: {
            TaskStatus.PLANNED,
            TaskStatus.READY,
            TaskStatus.ASSIGNED,
            TaskStatus.CANCELLED,
        },
        TaskStatus.PLANNED: {
            TaskStatus.READY,
            TaskStatus.ASSIGNED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.CANCELLED,
        },
        TaskStatus.READY: {
            TaskStatus.ASSIGNED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.BLOCKED,
            TaskStatus.CANCELLED,
        },
        TaskStatus.ASSIGNED: {
            TaskStatus.READY,
            TaskStatus.IN_PROGRESS,
            TaskStatus.WAITING,
            TaskStatus.BLOCKED,
            TaskStatus.CANCELLED,
        },
        TaskStatus.IN_PROGRESS: {
            TaskStatus.WAITING,
            TaskStatus.BLOCKED,
            TaskStatus.VERIFYING,
            TaskStatus.APPROVAL_REQUIRED,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        },
        TaskStatus.WAITING: {
            TaskStatus.READY,
            TaskStatus.ASSIGNED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.BLOCKED,
            TaskStatus.CANCELLED,
        },
        TaskStatus.BLOCKED: {
            TaskStatus.READY,
            TaskStatus.ASSIGNED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.CANCELLED,
        },
        TaskStatus.APPROVAL_REQUIRED: {
            TaskStatus.READY,
            TaskStatus.ASSIGNED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.CANCELLED,
        },
        TaskStatus.VERIFYING: {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.APPROVAL_REQUIRED,
        },
        TaskStatus.COMPLETED: {
            TaskStatus.READY,
            TaskStatus.IN_PROGRESS,
        },
        TaskStatus.FAILED: {
            TaskStatus.CREATED,
            TaskStatus.PLANNED,
            TaskStatus.READY,
            TaskStatus.IN_PROGRESS,
        },
        TaskStatus.CANCELLED: {
            TaskStatus.CREATED,
            TaskStatus.PLANNED,
            TaskStatus.READY,
        },
    }

    TERMINAL_STATUSES: set[str] = {
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
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
        """Validate status transition or raise InvalidStatusTransitionError."""
        if not cls.can_transition(current_status, new_status):
            allowed = sorted(cls.ALLOWED_TRANSITIONS.get(current_status, set()))
            raise InvalidStatusTransitionError(
                f"Cannot transition task from '{current_status}' to '{new_status}'. "
                f"Allowed target statuses: {allowed}"
            )

    @classmethod
    def calculate_timestamps(
        cls,
        new_status: str,
        current_started_at: datetime | None,
        current_completed_at: datetime | None,
    ) -> tuple[datetime | None, datetime | None]:
        """Calculate updated started_at and completed_at timestamps based on the new status."""
        now = datetime.now(UTC)
        started_at = current_started_at
        completed_at = current_completed_at

        # If entering IN_PROGRESS for the first time, record started_at
        if new_status == TaskStatus.IN_PROGRESS and started_at is None:
            started_at = now

        # If entering a terminal status, record completed_at
        if new_status in cls.TERMINAL_STATUSES:
            completed_at = now
        # If moving out of terminal status (re-opening), clear completed_at
        elif current_completed_at is not None:
            completed_at = None

        return started_at, completed_at
