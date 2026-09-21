"""Abstract base class for LLM Providers in the LLM Gateway."""

from abc import ABC, abstractmethod
from typing import Any

from domain.runtime.schemas import AgentExecutionContext, ExecutionResult, RuntimeLimits
from orchestration.planner.schemas import GoalIntake, PlanResult


class BaseLLMProvider(ABC):
    """Abstract interface for LLM planning and agent execution providers."""

    @abstractmethod
    async def generate_plan(
        self,
        goal: GoalIntake,
        context: dict[str, Any],
    ) -> PlanResult:
        """Generate a structured plan from a user goal and authoritative company context.

        Args:
            goal: User goal intake with objective and constraints.
            context: Authoritative company context snapshot (company, departments, agents).

        Returns:
            PlanResult containing steps, delegation proposals, approvals, risks, and assumptions.
        """
        pass

    @abstractmethod
    async def execute_task(
        self,
        context: AgentExecutionContext,
        limits: RuntimeLimits,
    ) -> ExecutionResult:
        """Execute a specialist agent task within given context and runtime limits.

        Args:
            context: Authoritative agent execution context packet.
            limits: Execution safety limits and budgets.

        Returns:
            ExecutionResult containing structured deliverable, steps, metrics, and verification notes.
        """
        pass
