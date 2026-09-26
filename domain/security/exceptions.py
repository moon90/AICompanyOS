"""Security domain exceptions."""


class SecurityError(Exception):
    """Base exception for all security and authorization domain errors."""


class CrossTenantAccessError(SecurityError):
    """Raised when an actor attempts to access resources belonging to a foreign company."""


class CapabilityDeniedError(SecurityError):
    """Raised when an agent attempts an action that is not in its allowed capabilities list (Default-DENY)."""


class PromptInjectionDetectedError(SecurityError):
    """Raised when an untrusted prompt or input contains known adversarial prompt injection patterns."""


class AgentQuarantinedError(SecurityError):
    """Raised when an agent is currently quarantined and prohibited from executing operations."""


class RateLimitExceededError(SecurityError):
    """Raised when an actor exceeds allowed requests per minute or daily budget."""


class CredentialLeakError(SecurityError):
    """Raised when sensitive secrets or unredacted credentials are detected in an outgoing or untrusted payload."""


class SecurityPolicyNotFoundError(SecurityError):
    """Raised when an agent security policy does not exist and cannot be loaded."""
