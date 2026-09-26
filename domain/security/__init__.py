"""Domain layer for Phase 23 Security Hardening."""

from domain.security.enums import (
    ActorType,
    AgentCapability,
    SecurityEventType,
    SecurityPosture,
    SecuritySeverity,
)
from domain.security.exceptions import (
    AgentQuarantinedError,
    CapabilityDeniedError,
    CredentialLeakError,
    CrossTenantAccessError,
    PromptInjectionDetectedError,
    RateLimitExceededError,
    SecurityError,
    SecurityPolicyNotFoundError,
)
from domain.security.prompt_guard import PromptGuard, PromptScanResult
from domain.security.schemas import (
    AgentPolicyResponse,
    AgentPolicyUpdateRequest,
    AgentQuarantineRequest,
    PromptScanRequest,
    PromptScanResponse,
    SecurityLogCreateRequest,
    SecurityLogItem,
    SecurityLogListResponse,
    SecuritySummaryResponse,
)

__all__ = [
    "ActorType",
    "AgentCapability",
    "SecurityEventType",
    "SecurityPosture",
    "SecuritySeverity",
    "SecurityError",
    "CrossTenantAccessError",
    "CapabilityDeniedError",
    "PromptInjectionDetectedError",
    "AgentQuarantinedError",
    "RateLimitExceededError",
    "CredentialLeakError",
    "SecurityPolicyNotFoundError",
    "PromptGuard",
    "PromptScanResult",
    "SecurityLogItem",
    "SecurityLogListResponse",
    "SecurityLogCreateRequest",
    "AgentPolicyResponse",
    "AgentPolicyUpdateRequest",
    "AgentQuarantineRequest",
    "PromptScanRequest",
    "PromptScanResponse",
    "SecuritySummaryResponse",
]
