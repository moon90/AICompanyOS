"""Domain module for Voice Interface adhering to docs/Phases.md Section 25 and docs/Memory.md Section 60."""

from domain.voice.exceptions import (
    InvalidVoiceCommandError,
    VoiceAccessDeniedError,
    VoiceActionExecutionError,
    VoiceError,
    VoiceSessionNotFoundError,
)
from domain.voice.schemas import (
    VoiceCommandPayload,
    VoiceCommandResponse,
    VoiceIntent,
    VoiceInteractionItem,
    VoiceSessionCreatePayload,
    VoiceSessionListResponse,
    VoiceSessionResponse,
    VoiceState,
    VoiceSynthesizeRequest,
    VoiceSynthesizeResponse,
    VoiceTelemetryResponse,
)

__all__ = [
    "InvalidVoiceCommandError",
    "VoiceAccessDeniedError",
    "VoiceActionExecutionError",
    "VoiceCommandPayload",
    "VoiceCommandResponse",
    "VoiceError",
    "VoiceIntent",
    "VoiceInteractionItem",
    "VoiceSessionCreatePayload",
    "VoiceSessionListResponse",
    "VoiceSessionNotFoundError",
    "VoiceSessionResponse",
    "VoiceState",
    "VoiceSynthesizeRequest",
    "VoiceSynthesizeResponse",
    "VoiceTelemetryResponse",
]
