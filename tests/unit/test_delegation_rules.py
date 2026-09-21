"""Unit tests for delegation rule engine adhering to docs/Rules.md §§ 58, 60, 61."""

import uuid

import pytest

from domain.delegation.exceptions import (
    CircularDelegationError,
    DelegationError,
    InvalidDelegationHierarchyError,
    MaxDelegationDepthExceededError,
)
from domain.delegation.rules import DelegationRuleEngine
from infrastructure.database.models import Agent, DelegationRecord


@pytest.fixture
def company_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def cto_dept_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def cmo_dept_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def ceo_agent(company_id: str) -> Agent:
    return Agent(
        id=str(uuid.uuid4()),
        company_id=company_id,
        name="CEO",
        role="Chief Executive Officer",
        type="executive",
        status="active",
        authority_level="executive",
    )


@pytest.fixture
def cto_agent(company_id: str, cto_dept_id: str, ceo_agent: Agent) -> Agent:
    return Agent(
        id=str(uuid.uuid4()),
        company_id=company_id,
        department_id=cto_dept_id,
        name="CTO",
        role="Chief Technology Officer",
        type="department_lead",
        status="active",
        authority_level="department_lead",
        reports_to=ceo_agent.id,
    )


@pytest.fixture
def cmo_agent(company_id: str, cmo_dept_id: str, ceo_agent: Agent) -> Agent:
    return Agent(
        id=str(uuid.uuid4()),
        company_id=company_id,
        department_id=cmo_dept_id,
        name="CMO",
        role="Chief Marketing Officer",
        type="department_lead",
        status="active",
        authority_level="department_lead",
        reports_to=ceo_agent.id,
    )


@pytest.fixture
def architect_agent(company_id: str, cto_dept_id: str, cto_agent: Agent) -> Agent:
    return Agent(
        id=str(uuid.uuid4()),
        company_id=company_id,
        department_id=cto_dept_id,
        name="Software Architect",
        role="Principal Systems Architect",
        type="specialist",
        status="active",
        authority_level="specialist",
        reports_to=cto_agent.id,
    )


@pytest.fixture
def marketer_agent(company_id: str, cmo_dept_id: str, cmo_agent: Agent) -> Agent:
    return Agent(
        id=str(uuid.uuid4()),
        company_id=company_id,
        department_id=cmo_dept_id,
        name="Growth Marketer",
        role="Marketing Strategist",
        type="specialist",
        status="active",
        authority_level="specialist",
        reports_to=cmo_agent.id,
    )


def test_human_user_direct_delegation(cto_agent: Agent) -> None:
    """Human operator directly assigning a task starts at depth 1."""
    depth = DelegationRuleEngine.validate_delegation(
        target_agent=cto_agent,
        source_agent=None,
        existing_history=None,
    )
    assert depth == 1


def test_ceo_delegation_to_department_lead(ceo_agent: Agent, cto_agent: Agent) -> None:
    """CEO can delegate to department heads."""
    depth = DelegationRuleEngine.validate_delegation(
        target_agent=cto_agent,
        source_agent=ceo_agent,
        existing_history=None,
    )
    assert depth == 1


def test_department_lead_delegation_to_specialist(cto_agent: Agent, architect_agent: Agent) -> None:
    """Department heads can delegate to specialists within their department."""
    depth = DelegationRuleEngine.validate_delegation(
        target_agent=architect_agent,
        source_agent=cto_agent,
        existing_history=None,
    )
    assert depth == 2


def test_cross_department_delegation_rejected(cto_agent: Agent, marketer_agent: Agent) -> None:
    """Department heads cannot delegate across departments without executive coordination."""
    with pytest.raises(
        InvalidDelegationHierarchyError, match="Cross-department delegation rejected"
    ):
        DelegationRuleEngine.validate_delegation(
            target_agent=marketer_agent,
            source_agent=cto_agent,
            existing_history=None,
        )


def test_upward_delegation_rejected(cto_agent: Agent, ceo_agent: Agent) -> None:
    """Subordinates cannot delegate upwards to the CEO."""
    with pytest.raises(InvalidDelegationHierarchyError, match="Upward delegation rejected"):
        DelegationRuleEngine.validate_delegation(
            target_agent=ceo_agent,
            source_agent=cto_agent,
            existing_history=None,
        )


def test_specialist_delegation_rejected(architect_agent: Agent, cto_agent: Agent) -> None:
    """Specialists cannot delegate tasks."""
    with pytest.raises(InvalidDelegationHierarchyError, match="Unauthorized delegation"):
        DelegationRuleEngine.validate_delegation(
            target_agent=cto_agent,
            source_agent=architect_agent,
            existing_history=None,
        )


def test_self_delegation_prohibited(ceo_agent: Agent) -> None:
    """Agents cannot delegate to themselves."""
    with pytest.raises(CircularDelegationError, match="Self-delegation prohibited"):
        DelegationRuleEngine.validate_delegation(
            target_agent=ceo_agent,
            source_agent=ceo_agent,
            existing_history=None,
        )


def test_circular_delegation_detected(
    ceo_agent: Agent, cto_agent: Agent, architect_agent: Agent, company_id: str
) -> None:
    """Circular delegation (A -> B -> A) is rejected."""
    task_id = str(uuid.uuid4())
    # CEO delegated to CTO
    record1 = DelegationRecord(
        id=str(uuid.uuid4()),
        company_id=company_id,
        task_id=task_id,
        delegated_by_agent_id=ceo_agent.id,
        delegated_to_agent_id=cto_agent.id,
        depth=1,
        reason="Initial delegation",
        status="active",
    )

    # Now if someone attempts to delegate back to CEO:
    with pytest.raises(CircularDelegationError, match="Circular delegation rejected"):
        DelegationRuleEngine.validate_delegation(
            target_agent=ceo_agent,
            source_agent=cto_agent,
            existing_history=[record1],
        )


def test_max_delegation_depth_exceeded(
    cto_agent: Agent, architect_agent: Agent, company_id: str
) -> None:
    """Delegation depth exceeding MAX_DELEGATION_DEPTH is rejected."""
    task_id = str(uuid.uuid4())
    # Create history at depth 3
    r1 = DelegationRecord(
        id=str(uuid.uuid4()),
        company_id=company_id,
        task_id=task_id,
        delegated_by_agent_id=str(uuid.uuid4()),
        delegated_to_agent_id=str(uuid.uuid4()),
        depth=1,
        reason="D1",
        status="active",
    )
    r2 = DelegationRecord(
        id=str(uuid.uuid4()),
        company_id=company_id,
        task_id=task_id,
        delegated_by_agent_id=str(uuid.uuid4()),
        delegated_to_agent_id=cto_agent.id,
        depth=3,
        reason="D3",
        status="active",
    )

    with pytest.raises(MaxDelegationDepthExceededError, match="Maximum delegation depth"):
        DelegationRuleEngine.validate_delegation(
            target_agent=architect_agent,
            source_agent=cto_agent,
            existing_history=[r1, r2],
            max_depth=3,
        )


def test_inactive_target_agent_rejected(ceo_agent: Agent, cto_agent: Agent) -> None:
    """Cannot delegate to an inactive agent."""
    cto_agent.status = "inactive"
    with pytest.raises(DelegationError, match="inactive agent"):
        DelegationRuleEngine.validate_delegation(
            target_agent=cto_agent,
            source_agent=ceo_agent,
            existing_history=None,
        )
