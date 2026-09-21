"""Unit tests for the CEO Plan DAG validator and safety limits."""

import pytest

from domain.ceo.exceptions import InvalidPlanGraphError, PlanDepthExceededError
from orchestration.planner.dag_validator import validate_plan_dag
from orchestration.planner.schemas import PlanStep


def _make_step(
    step_id: str, depends_on: list[str] | None = None, agent_id: str | None = None
) -> PlanStep:
    return PlanStep(
        step_id=step_id,
        title=f"Step {step_id}",
        description=f"Description for {step_id}",
        assigned_agent_id=agent_id,
        assigned_agent_role="specialist",
        depends_on=depends_on or [],
        expected_output="Deliverable",
        verification_criteria="Criteria met",
    )


def test_valid_dag_passes_validation() -> None:
    steps = [
        _make_step("step_1", depends_on=[]),
        _make_step("step_2", depends_on=["step_1"]),
        _make_step("step_3", depends_on=["step_1"]),
        _make_step("step_4", depends_on=["step_2", "step_3"]),
    ]
    validate_plan_dag(steps)


def test_empty_steps_fails_validation() -> None:
    with pytest.raises(InvalidPlanGraphError, match="must contain at least one step"):
        validate_plan_dag([])


def test_duplicate_step_id_fails_validation() -> None:
    steps = [
        _make_step("step_1"),
        _make_step("step_1"),
    ]
    with pytest.raises(InvalidPlanGraphError, match="Duplicate step_id detected"):
        validate_plan_dag(steps)


def test_self_dependency_fails_validation() -> None:
    steps = [
        _make_step("step_1", depends_on=["step_1"]),
    ]
    with pytest.raises(InvalidPlanGraphError, match="cannot depend on itself"):
        validate_plan_dag(steps)


def test_missing_dependency_fails_validation() -> None:
    steps = [
        _make_step("step_1", depends_on=["step_nonexistent"]),
    ]
    with pytest.raises(InvalidPlanGraphError, match="references non-existent dependency"):
        validate_plan_dag(steps)


def test_two_node_cycle_fails_validation() -> None:
    steps = [
        _make_step("step_1", depends_on=["step_2"]),
        _make_step("step_2", depends_on=["step_1"]),
    ]
    with pytest.raises(InvalidPlanGraphError, match="Cyclic dependency detected"):
        validate_plan_dag(steps)


def test_multi_node_cycle_fails_validation() -> None:
    steps = [
        _make_step("step_1", depends_on=["step_3"]),
        _make_step("step_2", depends_on=["step_1"]),
        _make_step("step_3", depends_on=["step_2"]),
    ]
    with pytest.raises(InvalidPlanGraphError, match="Cyclic dependency detected"):
        validate_plan_dag(steps)


def test_foreign_agent_id_fails_validation() -> None:
    allowed_agents = {"agent_alpha", "agent_beta"}
    steps = [
        _make_step("step_1", agent_id="agent_gamma"),
    ]
    with pytest.raises(
        InvalidPlanGraphError, match="does not exist in the company's active registry"
    ):
        validate_plan_dag(steps, allowed_agent_ids=allowed_agents)


def test_max_steps_exceeded_fails_validation() -> None:
    steps = [_make_step(f"step_{i}") for i in range(25)]
    with pytest.raises(PlanDepthExceededError, match="exceeds maximum allowable limit of 20"):
        validate_plan_dag(steps, max_steps=20)


def test_max_depth_exceeded_fails_validation() -> None:
    # 6 levels of depth: s1 -> s2 -> s3 -> s4 -> s5 -> s6
    steps = [
        _make_step("step_1"),
        _make_step("step_2", depends_on=["step_1"]),
        _make_step("step_3", depends_on=["step_2"]),
        _make_step("step_4", depends_on=["step_3"]),
        _make_step("step_5", depends_on=["step_4"]),
        _make_step("step_6", depends_on=["step_5"]),
    ]
    with pytest.raises(PlanDepthExceededError, match="exceeds maximum allowable depth of 5"):
        validate_plan_dag(steps, max_depth=5)
