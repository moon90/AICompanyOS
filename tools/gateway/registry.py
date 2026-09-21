"""Tool Registry managing available tool declarations adhering to docs/Phases.md Section 13."""

from collections.abc import Callable
from typing import Any

from domain.tools.exceptions import ToolNotFoundError
from domain.tools.schemas import ToolDefinition, ToolRiskLevel
from tools.documents.reader import DocumentsTool
from tools.github.inspector import GitHubTool
from tools.web.search import WebSearchTool


class ToolRegistry:
    """Central registry of all authorized tools accessible via the Tool Gateway."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register the 3 foundational Phase 9 tools: web_search, documents, github."""
        # 1. Web Search
        web_tool = WebSearchTool()
        self.register(
            definition=ToolDefinition(
                name=web_tool.NAME,
                provider=web_tool.PROVIDER,
                description=web_tool.DESCRIPTION,
                version=web_tool.VERSION,
                risk_level=ToolRiskLevel.LOW,
                requires_approval=False,
                allowed_roles=["*"],  # All agents
                input_schema=web_tool.INPUT_SCHEMA,
                output_schema=web_tool.OUTPUT_SCHEMA,
            ),
            handler=web_tool.execute,
        )

        # 2. Documents
        doc_tool = DocumentsTool()
        self.register(
            definition=ToolDefinition(
                name=doc_tool.NAME,
                provider=doc_tool.PROVIDER,
                description=doc_tool.DESCRIPTION,
                version=doc_tool.VERSION,
                risk_level=ToolRiskLevel.LOW,
                requires_approval=False,
                allowed_roles=["*"],  # All agents
                input_schema=doc_tool.INPUT_SCHEMA,
                output_schema=doc_tool.OUTPUT_SCHEMA,
            ),
            handler=doc_tool.execute,
        )

        # 3. GitHub
        gh_tool = GitHubTool()
        self.register(
            definition=ToolDefinition(
                name=gh_tool.NAME,
                provider=gh_tool.PROVIDER,
                description=gh_tool.DESCRIPTION,
                version=gh_tool.VERSION,
                risk_level=ToolRiskLevel.MEDIUM,
                requires_approval=False,  # Inspection is medium, write actions escalate to high
                allowed_roles=gh_tool.ALLOWED_ROLES,
                input_schema=gh_tool.INPUT_SCHEMA,
                output_schema=gh_tool.OUTPUT_SCHEMA,
            ),
            handler=gh_tool.execute,
        )

    def register(self, definition: ToolDefinition, handler: Callable[..., Any]) -> None:
        """Register a tool definition and its execution handler."""
        self._tools[definition.name] = definition
        self._handlers[definition.name] = handler

    def get_tool(self, name: str) -> ToolDefinition:
        """Retrieve tool definition by name."""
        clean_name = name.strip().lower()
        if clean_name not in self._tools:
            raise ToolNotFoundError(clean_name)
        return self._tools[clean_name]

    def get_handler(self, name: str) -> Callable[..., Any]:
        """Retrieve tool execution handler by name."""
        clean_name = name.strip().lower()
        if clean_name not in self._handlers:
            raise ToolNotFoundError(clean_name)
        return self._handlers[clean_name]

    def list_tools(self) -> list[ToolDefinition]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_tools_for_role(self, role: str) -> list[ToolDefinition]:
        """Return subset of tools permissible for a specific agent role."""
        clean_role = role.strip().lower()
        result: list[ToolDefinition] = []
        for tool in self._tools.values():
            if "*" in tool.allowed_roles or any(
                r.lower() == clean_role or r.lower() in clean_role for r in tool.allowed_roles
            ):
                result.append(tool)
        return result
