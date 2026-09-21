"""Abstract base class for LLM Providers in the LLM Gateway."""

from abc import ABC, abstractmethod
from typing import Any

from orchestration.planner.schemas import GoalIntake, PlanResult


class BaseLLMProvider(ABC):
    """Abstract interface for LLM planning providers."""

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
