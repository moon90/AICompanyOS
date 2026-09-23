"""Domain exceptions for agent presence adhering to docs/Phases.md Section 18."""


class PresenceError(Exception):
    """Base exception for all presence domain errors."""


class PresenceNotFoundError(PresenceError):
    """Raised when presence record for an agent is not found."""


class PresenceAccessDeniedError(PresenceError):
    """Raised when a user attempts to access presence in an unauthorized company."""


class InvalidPresenceStateError(PresenceError):
    """Raised when an invalid presence status transition is attempted."""
