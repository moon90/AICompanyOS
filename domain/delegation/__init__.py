"""Delegation domain package exporting exceptions and rules."""

from domain.delegation.exceptions import (
    CircularDelegationError,
    DelegationAccessDeniedError,
    DelegationError,
    DelegationNotFoundError,
    InvalidDelegationHierarchyError,
    MaxDelegationDepthExceededError,
)
from domain.delegation.rules import DelegationRuleEngine

__all__ = [
    "CircularDelegationError",
    "DelegationAccessDeniedError",
    "DelegationError",
    "DelegationNotFoundError",
    "DelegationRuleEngine",
    "InvalidDelegationHierarchyError",
    "MaxDelegationDepthExceededError",
]
