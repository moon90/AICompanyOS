"""Canonical security enums adhering to docs/Phases.md § 27 and docs/Rules.md § 185."""

from enum import StrEnum


class ActorType(StrEnum):
    """Categorization of actors attempting or performing operations."""

    USER = "USER"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"
    ANONYMOUS = "ANONYMOUS"


class SecurityEventType(StrEnum):
    """Canonical security event and threat types."""

    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    CROSS_TENANT_ATTEMPT = "CROSS_TENANT_ATTEMPT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    PROMPT_INJECTION_DETECTED = "PROMPT_INJECTION_DETECTED"
    TOOL_ABUSE_DETECTED = "TOOL_ABUSE_DETECTED"
    CREDENTIAL_LEAK_PREVENTED = "CREDENTIAL_LEAK_PREVENTED"
    PRIVILEGE_ESCALATION_ATTEMPT = "PRIVILEGE_ESCALATION_ATTEMPT"
    AGENT_QUARANTINED = "AGENT_QUARANTINED"
    AGENT_UNQUARANTINED = "AGENT_UNQUARANTINED"
    CAPABILITY_DENIED = "CAPABILITY_DENIED"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    SESSION_REVOKED = "SESSION_REVOKED"
    POLICY_UPDATED = "POLICY_UPDATED"


class SecuritySeverity(StrEnum):
    """Severity ratings for security events."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityPosture(StrEnum):
    """Default-DENY vs explicit capability posture per Rule 185."""

    DENY = "DENY"
    ALLOW = "ALLOW"


class AgentCapability(StrEnum):
    """Granular agent capability designations defaulting to DENY."""

    TASK_READ = "TASK_READ"
    TASK_CREATE = "TASK_CREATE"
    TASK_UPDATE = "TASK_UPDATE"
    PROJECT_READ = "PROJECT_READ"
    PROJECT_MANAGE = "PROJECT_MANAGE"
    CODE_READ = "CODE_READ"
    CODE_WRITE = "CODE_WRITE"
    TOOL_EXECUTE = "TOOL_EXECUTE"
    APPROVAL_REQUEST = "APPROVAL_REQUEST"
    KNOWLEDGE_ACCESS = "KNOWLEDGE_ACCESS"
    VOICE_INTERACT = "VOICE_INTERACT"
    DESTRUCTIVE_TOOL = "DESTRUCTIVE_TOOL"
