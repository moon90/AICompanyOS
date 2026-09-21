"""Tool Gateway implementing 8-step controlled execution flow per docs/Architecture.md Sections 30-31."""

import time
from typing import Any

from domain.tools.schemas import (
    ToolCallRequest,
    ToolCallResult,
    ToolExecutionStatus,
)
from tools.gateway.permissions import ToolPermissionChecker
from tools.gateway.registry import ToolRegistry
from tools.gateway.risk import ToolRiskEvaluator
from tools.gateway.validator import ToolValidator


class ToolGateway:
    """The central security gateway controlling all agent access to external tools."""

    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self.registry = registry or ToolRegistry()

    async def invoke(
        self,
        request: ToolCallRequest,
        agent_role: str = "specialist",
        agent_authority_level: str | int = "specialist",
    ) -> ToolCallResult:
        """Execute a tool request through the authoritative 8-step gateway pipeline.

        Pipeline:
        1. Sanitize input parameters (strip secrets)
        2. Tool Registry discovery
        3. Input schema validation
        4. Permission check (role & authority level)
        5. Risk classification
        6. Approval check (intercepts if approval required)
        7. Adapter execution with duration tracking
        8. Result packaging
        """
        start_time = time.perf_counter()

        # 1. Sanitize parameters
        sanitized_params = ToolValidator.sanitize_parameters(request.parameters)

        # 2. Lookup tool
        tool_def = self.registry.get_tool(request.tool_name)

        # 3. Validate input schema
        ToolValidator.validate_input(tool_def.name, tool_def.input_schema, sanitized_params)

        # 4. Check permissions
        ToolPermissionChecker.check_permission(
            tool=tool_def,
            agent_id=request.agent_id,
            agent_role=agent_role,
            agent_authority_level=agent_authority_level,
        )

        # 5. Classify risk & evaluate approval requirement
        risk_level, requires_approval = ToolRiskEvaluator.evaluate(
            tool=tool_def,
            action=request.action,
            parameters=sanitized_params,
        )

        # 6. Approval Gate: If approval is mandated, intercept and halt execution
        # (Phase 10 will provide the operator approval review and release mechanism)
        if requires_approval:
            duration_ms = max(1, int((time.perf_counter() - start_time) * 1000))
            return ToolCallResult(
                tool_name=tool_def.name,
                action=request.action,
                status=ToolExecutionStatus.APPROVAL_REQUIRED.value,
                output={},
                risk_level=risk_level.value,
                requires_approval=True,
                duration_ms=duration_ms,
                error_details=(
                    f"Action '{request.action}' on tool '{tool_def.name}' declared risk level '{risk_level.value}' "
                    "and requires human operator approval before execution."
                ),
            )

        # 7. Execute tool adapter
        handler = self.registry.get_handler(tool_def.name)
        output: dict[str, Any] = {}
        status = ToolExecutionStatus.SUCCESS.value
        error_details: str | None = None

        try:
            output = await handler(action=request.action, parameters=sanitized_params)
        except Exception as exc:
            status = ToolExecutionStatus.FAILED.value
            error_details = str(exc)

        duration_ms = max(1, int((time.perf_counter() - start_time) * 1000))

        # 8. Return normalized result packet
        return ToolCallResult(
            tool_name=tool_def.name,
            action=request.action,
            status=status,
            output=output,
            risk_level=risk_level.value,
            requires_approval=False,
            duration_ms=duration_ms,
            error_details=error_details,
        )
