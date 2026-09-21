"""Tool risk evaluation and approval enforcement adhering to docs/Rules.md Section 36."""

from typing import Any

from domain.tools.schemas import ToolDefinition, ToolRiskLevel


class ToolRiskEvaluator:
    """Evaluates the risk tier of a tool invocation and determines approval requirements."""

    # Default action risk overrides
    CRITICAL_ACTIONS = {"delete_repo", "drop_table", "deploy_production", "transfer_funds"}
    HIGH_RISK_ACTIONS = {
        "create_pr",
        "write_file",
        "send_email",
        "publish_content",
        "modify_config",
    }
    MEDIUM_RISK_ACTIONS = {"search_issues", "query_database", "inspect_repo"}

    @classmethod
    def evaluate(
        cls,
        tool: ToolDefinition,
        action: str,
        parameters: dict[str, Any],
    ) -> tuple[ToolRiskLevel, bool]:
        """Classify invocation risk and determine if operator approval is required.

        Returns:
            Tuple of (ToolRiskLevel, requires_approval: bool)
        """
        clean_action = action.strip().lower()

        # Start with tool's declared default risk
        risk = tool.risk_level
        requires_approval = tool.requires_approval

        if clean_action in cls.CRITICAL_ACTIONS:
            risk = ToolRiskLevel.CRITICAL
            requires_approval = True
        elif clean_action in cls.HIGH_RISK_ACTIONS:
            risk = ToolRiskLevel.HIGH
            requires_approval = True
        elif clean_action in cls.MEDIUM_RISK_ACTIONS and risk == ToolRiskLevel.LOW:
            risk = ToolRiskLevel.MEDIUM

        # Explicit parameter checks: e.g. actions operating on main/production branches
        branch = str(parameters.get("branch", "")).lower()
        if branch in ("main", "master", "prod", "production") and clean_action not in (
            "read",
            "inspect",
            "search",
        ):
            risk = ToolRiskLevel.HIGH
            requires_approval = True

        # Any HIGH or CRITICAL action automatically requires human approval per docs/Rules.md § 37
        if risk in (ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL):
            requires_approval = True

        return risk, requires_approval
