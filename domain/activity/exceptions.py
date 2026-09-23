"""Domain exceptions for activity history per docs/Phases.md Section 17."""


class ActivityError(Exception):
    """Base exception for all activity domain errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ActivityNotFoundError(ActivityError):
    """Raised when an activity event is not found."""

    def __init__(self, event_id: str) -> None:
        super().__init__(f"Activity event '{event_id}' was not found.")
        self.event_id = event_id


class ActivityAccessDeniedError(ActivityError):
    """Raised when an actor is not authorized to access an activity event or company feed."""

    def __init__(self, message: str = "Access to activity event history was denied.") -> None:
        super().__init__(message)
