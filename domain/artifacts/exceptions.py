"""Domain exceptions for artifacts and documents adhering to docs/Phases.md Section 22."""


class ArtifactError(Exception):
    """Base exception for all artifact domain exceptions."""


class ArtifactNotFoundError(ArtifactError):
    """Raised when an artifact or document is not found."""


class ArtifactAccessDeniedError(ArtifactError):
    """Raised when access to an artifact of another company/tenant is attempted."""


class InvalidArtifactOperationError(ArtifactError):
    """Raised when an artifact operation is invalid or malformed."""
