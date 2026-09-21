"""Domain exceptions for Tool Gateway adhering to docs/Architecture.md Sections 30-36."""

from typing import Any


class ToolError(Exception):
    """Base exception for tool-related domain errors."""


class ToolNotFoundError(ToolError):
    """Raised when a requested tool does not exist in the Tool Registry."""

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' is not registered in the Tool Gateway.")


class ToolValidationError(ToolError):
    """Raised when tool input or output schema validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.details = details or {}
        super().__init__(message)


class ToolPermissionDeniedError(ToolError):
    """Raised when calling agent lacks permission to execute the tool."""

    def __init__(self, agent_id: str, agent_role: str, tool_name: str) -> None:
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.tool_name = tool_name
        super().__init__(
            f"Agent '{agent_id}' with role '{agent_role}' is not authorized to invoke tool '{tool_name}'."
        )


class ToolApprovalRequiredError(ToolError):
    """Raised or intercepted when an action requires human approval before Phase 10 execution."""

    def __init__(self, tool_name: str, action: str, risk_level: str) -> None:
        self.tool_name = tool_name
        self.action = action
        self.risk_level = risk_level
        super().__init__(
            f"Action '{action}' on tool '{tool_name}' has risk level '{risk_level}' and requires operator approval."
        )


class ToolExecutionFailedError(ToolError):
    """Raised when external tool execution fails."""

    def __init__(self, tool_name: str, reason: str) -> None:
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Execution of tool '{tool_name}' failed: {reason}")


class ToolAccessDeniedError(ToolError):
    """Raised when user lacks active company membership to access tool capabilities."""


class ToolExecutionNotFoundError(ToolError):
    """Raised when a requested tool execution record is not found."""

    def __init__(self, execution_id: str) -> None:
        self.execution_id = execution_id
        super().__init__(f"Tool execution record '{execution_id}' was not found.")
