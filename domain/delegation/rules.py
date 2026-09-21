"""Delegation rule engine enforcing hierarchy, cycle protection, and depth limits per docs/Rules.md §§ 58, 60, 61."""

from domain.delegation.exceptions import (
    CircularDelegationError,
    DelegationError,
    InvalidDelegationHierarchyError,
    MaxDelegationDepthExceededError,
)
from infrastructure.database.models import Agent, DelegationRecord


class DelegationRuleEngine:
    """Deterministic validation engine for organizational agent delegation."""

    DEFAULT_MAX_DELEGATION_DEPTH: int = 3

    @classmethod
    def validate_delegation(
        cls,
        target_agent: Agent,
        source_agent: Agent | None = None,
        existing_history: list[DelegationRecord] | None = None,
        max_depth: int = DEFAULT_MAX_DELEGATION_DEPTH,
    ) -> int:
        """Validate an agent delegation request and compute the resulting delegation depth.

        Returns:
            int: The calculated depth level for the new delegation record.

        Raises:
            DelegationError: If source and target agents belong to different companies.
            InvalidDelegationHierarchyError: If the delegation hierarchy is violated.
            CircularDelegationError: If the target agent already participated in the delegation chain.
            MaxDelegationDepthExceededError: If the delegation chain exceeds max_depth.
        """
        # 1. Target agent must be active
        if target_agent.status != "active":
            raise DelegationError(
                f"Cannot delegate to inactive agent '{target_agent.name}' ({target_agent.id})."
            )

        # 2. If delegated by human operator (source_agent is None)
        if source_agent is None:
            # Human operator directly assigning work starts at depth 1
            return 1

        # 3. Tenant matching
        if source_agent.company_id != target_agent.company_id:
            raise DelegationError(
                f"Cross-company delegation denied: Delegator company '{source_agent.company_id}' "
                f"does not match target company '{target_agent.company_id}'."
            )

        # 4. Self-delegation prohibition
        if source_agent.id == target_agent.id:
            raise CircularDelegationError(
                f"Self-delegation prohibited: Agent '{source_agent.name}' cannot delegate to itself."
            )

        # 5. Circular delegation detection across history
        history = existing_history or []
        prior_delegators: set[str] = {
            r.delegated_by_agent_id for r in history if r.delegated_by_agent_id is not None
        }
        prior_delegators.add(source_agent.id)

        if target_agent.id in prior_delegators:
            raise CircularDelegationError(
                f"Circular delegation rejected: Target agent '{target_agent.name}' ({target_agent.id}) "
                f"is already an ancestor in the delegation chain for this task."
            )

        # 6. Organizational hierarchy rules per docs/Rules.md §§ 60 & 61
        cls._validate_hierarchy_rules(source_agent, target_agent)

        # 7. Calculate and enforce delegation depth per docs/Rules.md § 58
        if history:
            current_max_depth = max(r.depth for r in history)
            next_depth = current_max_depth + 1
        else:
            # First delegation in the task chain
            if cls._is_executive(source_agent):
                next_depth = 1
            elif cls._is_department_lead(source_agent):
                next_depth = 2
            else:
                next_depth = 3

        if next_depth > max_depth:
            raise MaxDelegationDepthExceededError(
                f"Maximum delegation depth of {max_depth} exceeded. Next depth would be {next_depth}."
            )

        return next_depth

    @classmethod
    def _validate_hierarchy_rules(cls, source: Agent, target: Agent) -> None:
        """Enforce strict organizational delegation hierarchy."""
        source_is_exec = cls._is_executive(source)
        target_is_exec = cls._is_executive(target)

        # Rule 1: No agent can delegate upwards to an executive (CEO)
        if target_is_exec and not source_is_exec:
            raise InvalidDelegationHierarchyError(
                f"Upward delegation rejected: Agent '{source.name}' cannot delegate to Executive '{target.name}'."
            )

        # Rule 2: Executive (CEO) can delegate to Department Heads or direct reports
        if source_is_exec:
            # CEO can delegate to department leads or specialists
            return

        # Rule 3: Department Heads can delegate to specialists within their own department or direct reports
        if cls._is_department_lead(source):
            # Same department check
            if (
                source.department_id
                and target.department_id
                and source.department_id == target.department_id
            ):
                return

            # Direct report check
            if target.reports_to == source.id:
                return

            raise InvalidDelegationHierarchyError(
                f"Cross-department delegation rejected: Department lead '{source.name}' cannot delegate to "
                f"agent '{target.name}' outside their department hierarchy without executive coordination."
            )

        # Rule 4: Specialists generally cannot delegate work
        # Unless target explicitly reports to this specialist
        if target.reports_to == source.id:
            return

        raise InvalidDelegationHierarchyError(
            f"Unauthorized delegation: Specialist agent '{source.name}' is not authorized to delegate tasks."
        )

    @classmethod
    def _is_executive(cls, agent: Agent) -> bool:
        """Check if an agent holds executive authority."""
        return (
            agent.type == "executive"
            or agent.authority_level == "executive"
            or agent.role.lower() in ("ceo", "chief executive officer")
            or agent.name.lower() == "ceo"
        )

    @classmethod
    def _is_department_lead(cls, agent: Agent) -> bool:
        """Check if an agent is a department head/lead."""
        return (
            agent.type in ("department_lead", "lead")
            or agent.authority_level in ("department_lead", "lead")
            or any(
                keyword in agent.role.lower()
                for keyword in ("chief", "head of", "director", "lead", "cmo", "cto")
            )
        )
