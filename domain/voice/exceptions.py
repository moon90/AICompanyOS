"""Domain exceptions for Voice Interface adhering to docs/Phases.md Section 25 and docs/Memory.md Section 60."""


class VoiceError(Exception):
    """Base exception for all voice interface operations."""


class VoiceSessionNotFoundError(VoiceError):
    """Raised when target voice session does not exist."""


class VoiceAccessDeniedError(VoiceError):
    """Raised when user lacks active membership to operate company voice interface."""


class InvalidVoiceCommandError(VoiceError):
    """Raised when a voice command or transcript cannot be parsed or lacks required context."""


class VoiceActionExecutionError(VoiceError):
    """Raised when the underlying action triggered by a voice command fails."""
