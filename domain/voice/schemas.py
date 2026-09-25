"""Domain schemas for Voice Interface adhering to docs/Phases.md Section 25 and docs/Memory.md Section 60."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VoiceState(StrEnum):
    """Canonical voice states adhering to docs/Phases.md Section 25."""

    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    SPEAKING = "SPEAKING"


class VoiceIntent(StrEnum):
    """Recognized intent categories for voice commands."""

    STATUS_QUERY = "STATUS_QUERY"
    TASK_CREATE = "TASK_CREATE"
    APPROVAL_DECISION = "APPROVAL_DECISION"
    TASK_CONTROL = "TASK_CONTROL"
    DELEGATION_COMMAND = "DELEGATION_COMMAND"
    GENERAL_INQUIRY = "GENERAL_INQUIRY"


class VoiceSessionCreatePayload(BaseModel):
    """Payload to initiate a conversational voice session."""

    title: str = Field(default="Voice Session", max_length=255)


class VoiceInteractionItem(BaseModel):
    """Representation of a single voice turn / command execution."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    company_id: str
    user_id: str
    transcript: str
    intent: str
    action_taken: str | None = None
    action_entity_id: str | None = None
    action_success: bool = True
    spoken_response: str
    detailed_response: str
    execution_time_ms: float
    created_at: datetime


class VoiceSessionResponse(BaseModel):
    """Representation of an active or historical voice session."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    user_id: str
    title: str
    state: str
    context_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    interactions: list[VoiceInteractionItem] = Field(default_factory=list)


class VoiceSessionListResponse(BaseModel):
    """Paginated list of company voice sessions."""

    items: list[VoiceSessionResponse]
    total: int


class VoiceCommandPayload(BaseModel):
    """Command payload representing a speech-to-text transcript or typed voice command."""

    transcript: str = Field(..., min_length=1, description="Recognized speech text or command")
    session_id: str | None = Field(
        default=None, description="Optional target voice session ID to resume"
    )
    project_id: str | None = Field(default=None, description="Optional scoped project ID")
    context_task_id: str | None = Field(
        default=None, description="Active task in context for follow-ups"
    )
    context_approval_id: str | None = Field(
        default=None, description="Active approval request in context"
    )


class VoiceCommandResponse(BaseModel):
    """Complete response returned after processing and executing a voice command."""

    session_id: str
    transcript: str
    intent: VoiceIntent
    state: VoiceState
    spoken_response: str
    detailed_response: str
    action_taken: str | None = None
    action_entity_id: str | None = None
    action_success: bool = True
    execution_time_ms: float
    timestamp: datetime


class VoiceSynthesizeRequest(BaseModel):
    """Request payload to synthesize speech audio from text."""

    text: str = Field(..., min_length=1, description="Text string to synthesize into speech")
    voice_persona: str = Field(default="CEO Executive", description="Synthetic voice personality")


class VoiceSynthesizeResponse(BaseModel):
    """Synthesized speech metadata and audio payload."""

    text: str
    audio_format: str = "wav/pcm"
    audio_b64: str | None = None
    phonemes: str | None = None


class VoiceTelemetryResponse(BaseModel):
    """Operational telemetry and usage distribution for voice interface."""

    company_id: str
    total_sessions: int
    total_interactions: int
    intent_distribution: dict[str, int]
    avg_execution_time_ms: float
    last_interaction_at: datetime | None
    timestamp: datetime
