"""Unit tests for ApprovalPolicyEngine adhering to docs/Rules.md §§ 40-50."""

import pytest

from domain.approvals.exceptions import AgentCannotApproveError
from domain.approvals.policy_engine import ApprovalPolicyEngine
from domain.approvals.schemas import ApprovalActionType, ApprovalRiskLevel


def test_consequential_actions_require_approval() -> None:
    """Verify all consequential actions defined in docs/Rules.md § 40 require approval."""
    consequential_types = [
        ApprovalActionType.SEND_EMAIL.value,
        ApprovalActionType.PUBLISH_CONTENT.value,
        ApprovalActionType.SPEND_MONEY.value,
        ApprovalActionType.DELETE_DATA.value,
        ApprovalActionType.DEPLOY_PRODUCTION.value,
        ApprovalActionType.MODIFY_CONFIGURATION.value,
        ApprovalActionType.EXTERNAL_COMMUNICATION.value,
        ApprovalActionType.DATABASE_MIGRATION.value,
        ApprovalActionType.HIGH_RISK_ACTION.value,
    ]
    for action in consequential_types:
        req, reason = ApprovalPolicyEngine.requires_approval(action_type=action)
        assert req is True, f"Action {action} should mandate approval"
        assert "consequential" in reason.lower() or "requires human approval" in reason.lower()


def test_tool_explicit_flag_mandates_approval() -> None:
    """Verify explicit requires_approval flag on tool triggers gate regardless of action."""
    req, reason = ApprovalPolicyEngine.requires_approval(
        action_type="custom_tool_action",
        risk_level=ApprovalRiskLevel.LOW.value,
        tool_requires_approval=True,
    )
    assert req is True
    assert "explicitly mandates human approval" in reason


def test_high_and_critical_risk_require_approval() -> None:
    """Verify HIGH and CRITICAL risk actions automatically require approval."""
    for risk in [ApprovalRiskLevel.HIGH.value, ApprovalRiskLevel.CRITICAL.value]:
        req, reason = ApprovalPolicyEngine.requires_approval(
            action_type="arbitrary_action",
            risk_level=risk,
        )
        assert req is True
        assert f"risk level '{risk}'" in reason


def test_financial_spend_threshold_triggers_approval() -> None:
    """Verify actions incurring financial spend exceeding threshold mandate approval."""
    req, reason = ApprovalPolicyEngine.requires_approval(
        action_type="purchase_domain",
        risk_level=ApprovalRiskLevel.LOW.value,
        payload={"amount": 45.0},
        spend_threshold=0.0,
    )
    assert req is True
    assert "financial expenditure of 45.00" in reason


def test_low_risk_action_without_gates_passes() -> None:
    """Verify standard low-risk action does not require approval."""
    req, reason = ApprovalPolicyEngine.requires_approval(
        action_type="READ_LOCAL_DOCUMENT",
        risk_level=ApprovalRiskLevel.LOW.value,
        payload={"query": "test"},
        tool_requires_approval=False,
    )
    assert req is False
    assert "does not mandate human approval" in reason


def test_agent_cannot_approve_enforcement() -> None:
    """Verify docs/Rules.md § 42: Agents cannot approve actions."""
    with pytest.raises(AgentCannotApproveError) as exc_info:
        ApprovalPolicyEngine.validate_approver_is_human(is_agent=True)
    assert "Agents cannot approve or reject actions" in str(exc_info.value)

    # Human approver succeeds without exception
    ApprovalPolicyEngine.validate_approver_is_human(is_agent=False)
