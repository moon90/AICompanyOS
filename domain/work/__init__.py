"""Work domain package for projects, tasks, and state machine validation."""

from domain.work.exceptions import (
    CircularDependencyError,
    InvalidStatusTransitionError,
    InvalidWorkAssignmentError,
    ProjectNotFoundError,
    SelfDependencyError,
    TaskNotFoundError,
    WorkAccessDeniedError,
    WorkDomainError,
)
from domain.work.state_machine import (
    ProjectPriority,
    ProjectStatus,
    TaskPriority,
    TaskStateMachine,
    TaskStatus,
)

__all__ = [
    "WorkDomainError",
    "ProjectNotFoundError",
    "TaskNotFoundError",
    "WorkAccessDeniedError",
    "InvalidStatusTransitionError",
    "CircularDependencyError",
    "SelfDependencyError",
    "InvalidWorkAssignmentError",
    "ProjectStatus",
    "ProjectPriority",
    "TaskStatus",
    "TaskPriority",
    "TaskStateMachine",
]
