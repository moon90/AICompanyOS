"""LLM Gateway abstraction decoupling the application layer from model providers."""

from typing import Any

from domain.runtime.schemas import AgentExecutionContext, ExecutionResult, RuntimeLimits
from infrastructure.llm.providers.base import BaseLLMProvider
from infrastructure.llm.providers.deterministic import DeterministicPlannerProvider
from orchestration.planner.dag_validator import validate_plan_dag
from orchestration.planner.schemas import GoalIntake, PlanResult


class LLMGateway:
    """Provider-agnostic gateway for AI agent reasoning and planning."""

    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        self.provider: BaseLLMProvider = provider or DeterministicPlannerProvider()

    async def generate_plan(
        self,
        goal: GoalIntake,
        context: dict[str, Any],
        allowed_agent_ids: set[str] | None = None,
    ) -> PlanResult:
        """Generate and validate a structured plan using the active provider.

        Args:
            goal: Structured goal intake.
            context: Company context snapshot.
            allowed_agent_ids: Active company agent IDs for reference validation.

        Returns:
            Validated PlanResult adhering strictly to DAG constraints.
        """
        # 1. Generate plan using provider
        raw_plan = await self.provider.generate_plan(goal, context)

        # 2. Strict DAG and safety validation
        validate_plan_dag(
            steps=raw_plan.steps,
            allowed_agent_ids=allowed_agent_ids,
        )

        return raw_plan

    async def execute_agent_task(
        self,
        context: AgentExecutionContext,
        limits: RuntimeLimits,
    ) -> ExecutionResult:
        """Execute a specialist agent task using the active provider.

        Args:
            context: Full agent execution context.
            limits: Runtime limits and constraints.

        Returns:
            ExecutionResult with structured deliverable, steps, metrics, and verification notes.
        """
        return await self.provider.execute_task(context, limits)
