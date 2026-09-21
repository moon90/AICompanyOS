"""Domain-level exceptions for Agent Registry operations."""


class AgentNotFoundError(Exception):
    """Raised when the requested agent cannot be found."""


class AgentAccessDeniedError(Exception):
    """Raised when a user lacks permission or tenant membership for the agent."""


class InvalidAgentHierarchyError(Exception):
    """Raised when an organizational hierarchy relationship is invalid (e.g. self-report, cross-company, or cycle)."""


class InvalidAgentDepartmentError(Exception):
    """Raised when an agent is assigned to an invalid or cross-company department."""


class DuplicateAgentVersionError(Exception):
    """Raised when attempting to register a duplicate agent definition version."""


class InvalidAgentDataError(Exception):
    """Raised when provided agent payload data violates domain validation rules."""
