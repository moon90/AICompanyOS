"""Permission checks for tool access adhering to docs/Rules.md Section 37 and docs/Architecture.md Section 30."""

from domain.tools.exceptions import ToolPermissionDeniedError
from domain.tools.schemas import ToolDefinition


class ToolPermissionChecker:
    """Verifies that an agent role is authorized to invoke a requested tool."""

    @classmethod
    def check_permission(
        cls,
        tool: ToolDefinition,
        agent_id: str,
        agent_role: str,
        agent_authority_level: str | int = "specialist",
    ) -> None:
        """Enforce role-based access control for tool execution.

        Args:
            tool: The target ToolDefinition.
            agent_id: The ID of the invoking agent.
            agent_role: The role name of the agent.
            agent_authority_level: The hierarchical authority of the agent.

        Raises:
            ToolPermissionDeniedError: If the agent is not allowed to use the tool.
        """
        allowed = tool.allowed_roles

        # Wildcard allows all registered company agents
        if "*" in allowed:
            return

        clean_role = agent_role.strip().lower()

        # Check exact or partial role match (e.g. "backend_specialist" matches "backend")
        is_allowed = any(r.lower() == clean_role or r.lower() in clean_role for r in allowed)

        # C-level executives and department leads typically inherit access to inspection tools
        if not is_allowed:
            auth_str = str(agent_authority_level).lower()
            if auth_str in ("c_level", "department_lead", "executive", "3", "4"):
                is_allowed = True

        if not is_allowed:
            raise ToolPermissionDeniedError(
                agent_id=agent_id,
                agent_role=agent_role,
                tool_name=tool.name,
            )
