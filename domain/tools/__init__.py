"""Domain Tool Gateway schemas and exceptions."""

from domain.tools.exceptions import (
    ToolAccessDeniedError,
    ToolApprovalRequiredError,
    ToolError,
    ToolExecutionFailedError,
    ToolNotFoundError,
    ToolPermissionDeniedError,
    ToolValidationError,
)
from domain.tools.schemas import (
    DocumentContent,
    GitHubResult,
    SearchResult,
    SearchResultItem,
    ToolCallRequest,
    ToolCallResult,
    ToolDefinition,
    ToolExecutionStatus,
    ToolRiskLevel,
)

__all__ = [
    "DocumentContent",
    "GitHubResult",
    "SearchResult",
    "SearchResultItem",
    "ToolAccessDeniedError",
    "ToolApprovalRequiredError",
    "ToolCallRequest",
    "ToolCallResult",
    "ToolDefinition",
    "ToolError",
    "ToolExecutionFailedError",
    "ToolExecutionNotFoundError",
    "ToolExecutionStatus",
    "ToolNotFoundError",
    "ToolPermissionDeniedError",
    "ToolRiskLevel",
    "ToolValidationError",
]
