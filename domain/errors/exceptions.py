"""Domain exceptions for error and bug management adhering to docs/Phases.md Section 19."""


class ErrorRecordError(Exception):
    """Base exception for all error record domain exceptions."""


class ErrorNotFoundError(ErrorRecordError):
    """Raised when an error record is not found."""


class ErrorAccessDeniedError(ErrorRecordError):
    """Raised when unauthorized access to an error record is attempted across tenants."""


class InvalidErrorTransitionError(ErrorRecordError):
    """Raised when an invalid lifecycle transition is attempted on an error record."""


class MissingResolutionError(ErrorRecordError):
    """Raised when attempting to mark an error resolved without resolution details."""


class MissingEvidenceError(ErrorRecordError):
    """Raised when attempting to mark an error verified without resolution evidence."""
