"""Policy engine enforcing human oversight and approval rules adhering to docs/Rules.md Sections 40-50."""

from typing import Any

from domain.approvals.exceptions import AgentCannotApproveError
from domain.approvals.schemas import (
    ApprovalActionType,
    ApprovalRiskLevel,
)


class ApprovalPolicyEngine:
    """Authoritative policy engine for evaluating consequential actions and gate requirements."""

    # Consequential actions that ALWAYS require human approval per docs/Rules.md Section 40
    CONSEQUENTIAL_ACTIONS: set[str] = {
        ApprovalActionType.SEND_EMAIL.value,
        ApprovalActionType.PUBLISH_CONTENT.value,
        ApprovalActionType.SPEND_MONEY.value,
        ApprovalActionType.DELETE_DATA.value,
        ApprovalActionType.DEPLOY_PRODUCTION.value,
        ApprovalActionType.MODIFY_CONFIGURATION.value,
        ApprovalActionType.EXTERNAL_COMMUNICATION.value,
        ApprovalActionType.DATABASE_MIGRATION.value,
        ApprovalActionType.HIGH_RISK_ACTION.value,
    }

    # High-risk tiers that automatically mandate human approval
    MANDATORY_APPROVAL_RISK_LEVELS: set[str] = {
        ApprovalRiskLevel.HIGH.value,
        ApprovalRiskLevel.CRITICAL.value,
    }

    # Action-to-risk mapping defaults
    ACTION_DEFAULT_RISK: dict[str, ApprovalRiskLevel] = {
        ApprovalActionType.SEND_EMAIL.value: ApprovalRiskLevel.MEDIUM,
        ApprovalActionType.PUBLISH_CONTENT.value: ApprovalRiskLevel.HIGH,
        ApprovalActionType.SPEND_MONEY.value: ApprovalRiskLevel.HIGH,
        ApprovalActionType.DELETE_DATA.value: ApprovalRiskLevel.CRITICAL,
        ApprovalActionType.DEPLOY_PRODUCTION.value: ApprovalRiskLevel.CRITICAL,
        ApprovalActionType.MODIFY_CONFIGURATION.value: ApprovalRiskLevel.HIGH,
        ApprovalActionType.EXTERNAL_COMMUNICATION.value: ApprovalRiskLevel.MEDIUM,
        ApprovalActionType.DATABASE_MIGRATION.value: ApprovalRiskLevel.CRITICAL,
        ApprovalActionType.HIGH_RISK_ACTION.value: ApprovalRiskLevel.HIGH,
        ApprovalActionType.TOOL_EXECUTION.value: ApprovalRiskLevel.LOW,
    }

    @classmethod
    def classify_risk(cls, action_type: str, explicit_risk: str | None = None) -> str:
        """Classify risk level for an action or tool execution."""
        if explicit_risk:
            try:
                return ApprovalRiskLevel(explicit_risk.upper()).value
            except ValueError:
                pass

        default_level = cls.ACTION_DEFAULT_RISK.get(action_type, ApprovalRiskLevel.MEDIUM)
        return default_level.value

    @classmethod
    def requires_approval(
        cls,
        action_type: str,
        risk_level: str = ApprovalRiskLevel.LOW.value,
        payload: dict[str, Any] | None = None,
        tool_requires_approval: bool = False,
        spend_threshold: float = 0.0,
    ) -> tuple[bool, str]:
        """Determine whether an action requires human approval.

        Returns a tuple of (requires_approval: bool, reason: str).
        """
        # 1. Tool-level explicit flag
        if tool_requires_approval:
            return True, f"Tool action '{action_type}' explicitly mandates human approval."

        # 2. Consequential action policy
        normalized_action = action_type.upper()
        if normalized_action in cls.CONSEQUENTIAL_ACTIONS:
            return (
                True,
                f"Action '{action_type}' is classified as consequential and requires human approval.",
            )

        # 3. High or critical risk tier
        normalized_risk = risk_level.upper()
        if normalized_risk in cls.MANDATORY_APPROVAL_RISK_LEVELS:
            return (
                True,
                f"Action '{action_type}' has risk level '{risk_level}', requiring human oversight.",
            )

        # 4. Financial / spending checks
        if payload:
            amount = payload.get("amount") or payload.get("cost") or payload.get("budget")
            if amount is not None:
                try:
                    num_amount = float(amount)
                    if num_amount > spend_threshold:
                        return (
                            True,
                            f"Action '{action_type}' incurs financial expenditure of {num_amount:.2f}, "
                            f"exceeding the approval threshold of {spend_threshold:.2f}.",
                        )
                except (ValueError, TypeError):
                    pass

        return False, "Action does not mandate human approval."

    @classmethod
    def validate_approver_is_human(cls, is_agent: bool) -> None:
        """Enforce docs/Rules.md Section 42: Agents cannot approve actions for themselves or other agents."""
        if is_agent:
            raise AgentCannotApproveError(
                "Agents cannot approve or reject actions. Only human operators with active company membership may review approval requests."
            )
