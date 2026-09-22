"""Domain package for Approval & Oversight System."""

from domain.approvals.exceptions import (
    AgentCannotApproveError,
    ApprovalAccessDeniedError,
    ApprovalAlreadyProcessedError,
    ApprovalError,
    ApprovalNotFoundError,
    InvalidApprovalTransitionError,
)
from domain.approvals.policy_engine import ApprovalPolicyEngine
from domain.approvals.schemas import (
    ApprovalActionType,
    ApprovalDecision,
    ApprovalDecisionInput,
    ApprovalFilter,
    ApprovalRequestCreate,
    ApprovalRiskLevel,
    ApprovalStatus,
)
from domain.approvals.state_machine import ApprovalStateMachine

__all__ = [
    "AgentCannotApproveError",
    "ApprovalAccessDeniedError",
    "ApprovalActionType",
    "ApprovalAlreadyProcessedError",
    "ApprovalDecision",
    "ApprovalDecisionInput",
    "ApprovalError",
    "ApprovalFilter",
    "ApprovalNotFoundError",
    "ApprovalPolicyEngine",
    "ApprovalRequestCreate",
    "ApprovalRiskLevel",
    "ApprovalStateMachine",
    "ApprovalStatus",
    "InvalidApprovalTransitionError",
]
