"""DAG validation engine for CEO plan task graphs."""

from collections import defaultdict

from domain.ceo.exceptions import InvalidPlanGraphError, PlanDepthExceededError
from orchestration.planner.schemas import PlanStep

MAX_PLAN_STEPS = 20
MAX_DEPENDENCY_DEPTH = 5


def validate_plan_dag(
    steps: list[PlanStep],
    allowed_agent_ids: set[str] | None = None,
    max_steps: int = MAX_PLAN_STEPS,
    max_depth: int = MAX_DEPENDENCY_DEPTH,
) -> None:
    """Validate a list of plan steps as a valid, bounded Directed Acyclic Graph (DAG).

    Raises:
        InvalidPlanGraphError: If step IDs are duplicated, dependencies are invalid,
            self-dependencies exist, or cycles are detected.
        PlanDepthExceededError: If step count or dependency depth exceeds safety bounds.
    """
    if not steps:
        raise InvalidPlanGraphError("A plan must contain at least one step.")

    if len(steps) > max_steps:
        raise PlanDepthExceededError(
            f"Plan step count ({len(steps)}) exceeds maximum allowable limit of {max_steps} steps."
        )

    # 1. Check for unique step identifiers
    step_ids: set[str] = set()
    for step in steps:
        if not step.step_id or not step.step_id.strip():
            raise InvalidPlanGraphError("Every plan step must have a non-empty step_id.")
        if step.step_id in step_ids:
            raise InvalidPlanGraphError(f"Duplicate step_id detected: '{step.step_id}'.")
        step_ids.add(step.step_id)

    # 2. Check for assigned agent validity (if provided)
    if allowed_agent_ids is not None:
        for step in steps:
            if step.assigned_agent_id and step.assigned_agent_id not in allowed_agent_ids:
                raise InvalidPlanGraphError(
                    f"Step '{step.step_id}' references agent_id '{step.assigned_agent_id}' "
                    "which does not exist in the company's active registry."
                )

    # 3. Check for dependency existence and self-dependencies
    adjacency: dict[str, list[str]] = defaultdict(list)
    in_degree: dict[str, int] = dict.fromkeys(step_ids, 0)

    for step in steps:
        for dep in step.depends_on:
            if dep == step.step_id:
                raise InvalidPlanGraphError(
                    f"Step '{step.step_id}' cannot depend on itself (self-dependency detected)."
                )
            if dep not in step_ids:
                raise InvalidPlanGraphError(
                    f"Step '{step.step_id}' references non-existent dependency step_id '{dep}'."
                )
            # Edge dep -> step (dep must complete before step can begin)
            adjacency[dep].append(step.step_id)
            in_degree[step.step_id] += 1

    # 4. Cycle detection using Kahn's algorithm (Topological Sort)
    queue: list[str] = [sid for sid, deg in in_degree.items() if deg == 0]
    visited_count = 0

    while queue:
        current = queue.pop(0)
        visited_count += 1
        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited_count != len(step_ids):
        # Remaining nodes with in_degree > 0 indicate a cycle
        cycled_nodes = [sid for sid, deg in in_degree.items() if deg > 0]
        raise InvalidPlanGraphError(
            f"Cyclic dependency detected among steps: {', '.join(cycled_nodes)}. Task graphs must be strictly acyclic."
        )

    # 5. Calculate maximum dependency depth
    # Depth of a node = 1 + max(depth of all prerequisites)
    # Roots have depth 1
    depths: dict[str, int] = {}

    def get_depth(node_id: str) -> int:
        if node_id in depths:
            return depths[node_id]
        # Find all prerequisites for node_id
        step_obj = next(s for s in steps if s.step_id == node_id)
        if not step_obj.depends_on:
            depths[node_id] = 1
        else:
            prereq_depths = [get_depth(d) for d in step_obj.depends_on]
            depths[node_id] = 1 + max(prereq_depths)
        return depths[node_id]

    max_found_depth = 0
    for sid in step_ids:
        d = get_depth(sid)
        if d > max_found_depth:
            max_found_depth = d

    if max_found_depth > max_depth:
        raise PlanDepthExceededError(
            f"Plan dependency depth ({max_found_depth}) exceeds maximum allowable depth of {max_depth} levels."
        )
