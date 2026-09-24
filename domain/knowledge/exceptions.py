"""Domain exceptions for company knowledge adhering to docs/Phases.md Section 23."""


class KnowledgeError(Exception):
    """Base exception for all knowledge domain exceptions."""


class KnowledgeNotFoundError(KnowledgeError):
    """Raised when a company knowledge item is not found."""


class KnowledgeAccessDeniedError(KnowledgeError):
    """Raised when access to company knowledge of another company/tenant is attempted."""


class InvalidKnowledgeOperationError(KnowledgeError):
    """Raised when a knowledge operation is invalid or malformed."""
