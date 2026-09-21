"""Unit tests for ToolGateway adhering to docs/Architecture.md Sections 30-36."""

import pytest

from domain.tools.exceptions import ToolPermissionDeniedError, ToolValidationError
from domain.tools.schemas import (
    ToolCallRequest,
    ToolExecutionStatus,
    ToolRiskLevel,
)
from tools.gateway.gateway import ToolGateway


@pytest.mark.asyncio
async def test_tool_gateway_web_search_success() -> None:
    """Verify standard web_search execution through Tool Gateway."""
    gateway = ToolGateway()
    request = ToolCallRequest(
        agent_id="agent-123",
        tool_name="web_search",
        action="search",
        parameters={"query": "fastapi architecture", "max_results": 3},
    )

    result = await gateway.invoke(
        request=request,
        agent_role="research_specialist",
        agent_authority_level="specialist",
    )

    assert result.status == ToolExecutionStatus.SUCCESS.value
    assert result.tool_name == "web_search"
    assert result.risk_level == ToolRiskLevel.LOW.value
    assert result.requires_approval is False
    assert result.duration_ms > 0
    assert "results" in result.output
    assert len(result.output["results"]) > 0


@pytest.mark.asyncio
async def test_tool_gateway_documents_success() -> None:
    """Verify documents tool access through Tool Gateway."""
    gateway = ToolGateway()
    request = ToolCallRequest(
        agent_id="agent-123",
        tool_name="documents",
        action="read",
        parameters={"document_id": "architecture_spec"},
    )

    result = await gateway.invoke(
        request=request,
        agent_role="backend_specialist",
        agent_authority_level="specialist",
    )

    assert result.status == ToolExecutionStatus.SUCCESS.value
    assert result.tool_name == "documents"
    assert "Autonomous Operating Architecture" in result.output["title"]
    assert result.output["word_count"] > 0


@pytest.mark.asyncio
async def test_tool_gateway_github_inspect_success() -> None:
    """Verify GitHub read inspection succeeds for engineering roles."""
    gateway = ToolGateway()
    request = ToolCallRequest(
        agent_id="agent-eng",
        tool_name="github",
        action="inspect_repo",
        parameters={"repository": "moon90/AICompanyOS", "action": "inspect_repo"},
    )

    result = await gateway.invoke(
        request=request,
        agent_role="software_engineer",
        agent_authority_level="specialist",
    )

    assert result.status == ToolExecutionStatus.SUCCESS.value
    assert result.tool_name == "github"
    assert result.risk_level == ToolRiskLevel.MEDIUM.value
    assert result.output["repository"] == "moon90/AICompanyOS"
    assert "latest_commit" in result.output["data"]


@pytest.mark.asyncio
async def test_tool_gateway_permission_denied() -> None:
    """Verify unauthorized role cannot execute restricted tool."""
    gateway = ToolGateway()
    request = ToolCallRequest(
        agent_id="agent-hr",
        tool_name="github",
        action="inspect_repo",
        parameters={"repository": "moon90/AICompanyOS", "action": "inspect_repo"},
    )

    with pytest.raises(ToolPermissionDeniedError) as exc_info:
        await gateway.invoke(
            request=request,
            agent_role="hr_specialist",
            agent_authority_level="specialist",
        )
    assert "not authorized to invoke tool 'github'" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tool_gateway_schema_validation_failure() -> None:
    """Verify invalid parameters fail schema validation at step 3."""
    gateway = ToolGateway()
    request = ToolCallRequest(
        agent_id="agent-123",
        tool_name="web_search",
        action="search",
        parameters={},  # Missing required 'query'
    )

    with pytest.raises(ToolValidationError):
        await gateway.invoke(
            request=request,
            agent_role="specialist",
            agent_authority_level="specialist",
        )


@pytest.mark.asyncio
async def test_tool_gateway_approval_gate_intercepts_high_risk() -> None:
    """Verify actions with HIGH/CRITICAL risk or write actions halt with APPROVAL_REQUIRED."""
    gateway = ToolGateway()
    request = ToolCallRequest(
        agent_id="agent-eng",
        tool_name="github",
        action="create_pr",  # HIGH risk write action
        parameters={
            "repository": "moon90/AICompanyOS",
            "action": "create_pr",
            "branch": "feature/tools",
        },
    )

    result = await gateway.invoke(
        request=request,
        agent_role="lead_engineer",
        agent_authority_level="lead",
    )

    assert result.status == ToolExecutionStatus.APPROVAL_REQUIRED.value
    assert result.requires_approval is True
    assert result.risk_level in (ToolRiskLevel.HIGH.value, ToolRiskLevel.CRITICAL.value)
    assert "requires human operator approval" in (result.error_details or "")
