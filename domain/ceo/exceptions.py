"""Domain exceptions for the CEO Orchestration layer."""


class CeoDomainError(Exception):
    """Base exception for CEO domain errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class CeoNotFoundError(CeoDomainError):
    """Raised when no active CEO agent is registered for the company."""


class CeoAccessDeniedError(CeoDomainError):
    """Raised when a user attempts to access CEO functions for a company they do not belong to."""


class PlanNotFoundError(CeoDomainError):
    """Raised when a requested CEO plan does not exist or does not belong to the company."""


class InvalidGoalError(CeoDomainError):
    """Raised when an input goal is empty, invalid, or violates length constraints."""


class InvalidPlanGraphError(CeoDomainError):
    """Raised when a generated plan has an invalid DAG structure (cycles, self-dependencies, invalid references)."""


class PlanDepthExceededError(CeoDomainError):
    """Raised when a plan exceeds safety depth or step bounds."""
