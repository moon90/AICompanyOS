"""Domain exceptions for projects, tasks, and work management."""


class WorkDomainError(Exception):
    """Base exception for work management domain errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProjectNotFoundError(WorkDomainError):
    """Raised when a project is not found or does not belong to the company."""


class TaskNotFoundError(WorkDomainError):
    """Raised when a task is not found or does not belong to the company."""


class WorkAccessDeniedError(WorkDomainError):
    """Raised when access to project or task is denied due to company isolation."""


class InvalidStatusTransitionError(WorkDomainError):
    """Raised when an invalid task or project status transition is attempted."""


class CircularDependencyError(WorkDomainError):
    """Raised when adding a task dependency would produce a cycle."""


class SelfDependencyError(WorkDomainError):
    """Raised when a task is set to depend on itself."""


class InvalidWorkAssignmentError(WorkDomainError):
    """Raised when assigning a task to an agent or user outside the company."""
