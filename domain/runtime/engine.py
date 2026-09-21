"""Agent Runtime Engine executing bounded specialist agent reasoning loops."""

import asyncio
import time
from typing import Protocol

from domain.runtime.exceptions import (
    ExecutionTimeoutError,
    MaxStepsExceededError,
)
from domain.runtime.schemas import (
    AgentExecutionContext,
    ExecutionResult,
    RuntimeLimits,
)


class ExecutionGateway(Protocol):
    """Protocol for LLM execution gateways decoupling domain runtime from infrastructure."""

    async def execute_agent_task(
        self,
        context: AgentExecutionContext,
        limits: RuntimeLimits,
    ) -> ExecutionResult: ...


class AgentRuntimeEngine:
    """Bounded, reusable runtime for executing any registered specialist agent."""

    def __init__(self, llm_gateway: ExecutionGateway | None = None) -> None:
        if llm_gateway is None:
            from infrastructure.llm.gateway import LLMGateway

            self.llm_gateway: ExecutionGateway = LLMGateway()
        else:
            self.llm_gateway = llm_gateway

    async def run_task(
        self,
        context: AgentExecutionContext,
        limits: RuntimeLimits | None = None,
    ) -> ExecutionResult:
        """Run an assigned agent task through the bounded execution loop.

        Args:
            context: Full execution context (agent definition, task, company, prerequisites).
            limits: Configurable runtime bounds and budgets.

        Returns:
            ExecutionResult with structured deliverable, steps, metrics, and verification notes.

        Raises:
            ExecutionTimeoutError: If execution exceeds max_duration_seconds.
            MaxStepsExceededError: If execution takes more than max_steps.
        """
        active_limits = limits or RuntimeLimits()
        start_time = time.perf_counter()

        try:
            # 1. Execute task with timeout guard
            result = await asyncio.wait_for(
                self.llm_gateway.execute_agent_task(context, active_limits),
                timeout=float(active_limits.max_duration_seconds),
            )
        except TimeoutError as err:
            elapsed_sec = time.perf_counter() - start_time
            raise ExecutionTimeoutError(
                duration_seconds=elapsed_sec,
                limit_seconds=float(active_limits.max_duration_seconds),
            ) from err

        duration_ms = max(1, int((time.perf_counter() - start_time) * 1000))
        result.duration_ms = duration_ms

        # 2. Enforce max_steps guardrail
        if result.step_count > active_limits.max_steps:
            raise MaxStepsExceededError(
                steps_taken=result.step_count,
                max_steps=active_limits.max_steps,
            )

        return result
