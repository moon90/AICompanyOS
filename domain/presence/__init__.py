"""Domain presence package adhering to docs/Phases.md Section 18."""

from domain.presence.exceptions import (
    InvalidPresenceStateError,
    PresenceAccessDeniedError,
    PresenceError,
    PresenceNotFoundError,
)
from domain.presence.schemas import (
    AgentPresenceResponse,
    HeartbeatRequest,
    PresenceStatus,
    PresenceSummaryResponse,
    PresenceUpdateParams,
)

__all__ = [
    "AgentPresenceResponse",
    "HeartbeatRequest",
    "InvalidPresenceStateError",
    "PresenceAccessDeniedError",
    "PresenceError",
    "PresenceNotFoundError",
    "PresenceStatus",
    "PresenceSummaryResponse",
    "PresenceUpdateParams",
]
