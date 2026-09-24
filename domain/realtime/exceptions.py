"""Domain exceptions for Real-Time Operations per docs/Phases.md Section 21."""


class RealtimeError(Exception):
    """Base exception for all real-time operational domain errors."""


class RealtimeAccessDeniedError(RealtimeError):
    """Raised when an actor lacks permission to access a company's real-time event stream."""


class InvalidRealtimeEventError(RealtimeError):
    """Raised when an emitted real-time event fails validation or contains invalid payload data."""
