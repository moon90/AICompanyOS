"""Unit tests for Tool Registry adhering to docs/Phases.md Section 13."""

import pytest

from domain.tools.exceptions import ToolNotFoundError
from domain.tools.schemas import ToolDefinition, ToolRiskLevel
from tools.gateway.registry import ToolRegistry


def test_default_tools_registration() -> None:
    """Verify foundational tools (web_search, documents, github) are registered by default."""
    registry = ToolRegistry()
    tools = registry.list_tools()
    tool_names = [t.name for t in tools]

    assert "web_search" in tool_names
    assert "documents" in tool_names
    assert "github" in tool_names
    assert len(tools) == 3


def test_get_tool_success() -> None:
    """Verify get_tool retrieves declared definitions accurately."""
    registry = ToolRegistry()
    web_tool = registry.get_tool("web_search")
    assert web_tool.name == "web_search"
    assert web_tool.risk_level == ToolRiskLevel.LOW
    assert "*" in web_tool.allowed_roles

    gh_tool = registry.get_tool("github")
    assert gh_tool.name == "github"
    assert gh_tool.risk_level == ToolRiskLevel.MEDIUM
    assert "software_engineer" in gh_tool.allowed_roles


def test_get_tool_not_found() -> None:
    """Verify get_tool raises ToolNotFoundError for unregistered tools."""
    registry = ToolRegistry()
    with pytest.raises(ToolNotFoundError) as exc_info:
        registry.get_tool("unregistered_tool")
    assert "unregistered_tool" in str(exc_info.value)


def test_get_tools_for_role() -> None:
    """Verify role-based tool visibility."""
    registry = ToolRegistry()

    # Engineer role should see all 3 tools
    engineer_tools = registry.get_tools_for_role("software_engineer")
    eng_names = [t.name for t in engineer_tools]
    assert "web_search" in eng_names
    assert "documents" in eng_names
    assert "github" in eng_names

    # HR role should only see wildcard tools, not github
    hr_tools = registry.get_tools_for_role("hr_specialist")
    hr_names = [t.name for t in hr_tools]
    assert "web_search" in hr_names
    assert "documents" in hr_names
    assert "github" not in hr_names


def test_custom_tool_registration() -> None:
    """Verify custom tool definitions can be registered dynamically."""
    registry = ToolRegistry()
    custom_def = ToolDefinition(
        name="custom_calc",
        provider="internal_math",
        description="Math calculator",
        version="1.0.0",
        risk_level=ToolRiskLevel.LOW,
        requires_approval=False,
        allowed_roles=["*"],
    )

    async def calc_handler(action: str, parameters: dict) -> dict:
        return {"result": 42}

    registry.register(custom_def, calc_handler)
    assert registry.get_tool("custom_calc").name == "custom_calc"
    assert registry.get_handler("custom_calc") is calc_handler
