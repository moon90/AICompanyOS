"""Domain exceptions for engineering file tracking adhering to docs/Phases.md Section 20."""


class EngineeringError(Exception):
    """Base exception for all engineering domain exceptions."""


class EngineeringContextNotFoundError(EngineeringError):
    """Raised when an engineering context is not found."""


class EngineeringAccessDeniedError(EngineeringError):
    """Raised when access to engineering resources of another tenant is attempted."""


class InvalidEngineeringOperationError(EngineeringError):
    """Raised when an engineering operation is invalid or malformed."""
