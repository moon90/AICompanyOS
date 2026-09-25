"""API schemas for Voice Interface adhering to docs/Phases.md Section 25 and docs/Memory.md Section 60."""

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
    "VoiceCommandPayload",
    "VoiceCommandResponse",
    "VoiceIntent",
    "VoiceInteractionItem",
    "VoiceSessionCreatePayload",
    "VoiceSessionListResponse",
    "VoiceSessionResponse",
    "VoiceState",
    "VoiceSynthesizeRequest",
    "VoiceSynthesizeResponse",
    "VoiceTelemetryResponse",
]
