"""Domain exceptions for Agent Runtime adhering to docs/Phases.md Section 12."""


class ExecutionError(Exception):
    """Base exception for agent execution errors."""

    def __init__(self, message: str = "Agent execution failed.") -> None:
        super().__init__(message)
        self.message = message


class ExecutionTimeoutError(ExecutionError):
    """Raised when agent execution exceeds the configured duration limit."""

    def __init__(self, duration_seconds: float, limit_seconds: float) -> None:
        super().__init__(
            f"Agent execution timed out after {duration_seconds:.1f}s (limit: {limit_seconds}s)."
        )
        self.duration_seconds = duration_seconds
        self.limit_seconds = limit_seconds


class MaxStepsExceededError(ExecutionError):
    """Raised when agent reasoning loop exceeds the step limit."""

    def __init__(self, steps_taken: int, max_steps: int) -> None:
        super().__init__(
            f"Agent execution exceeded maximum allowed steps: {steps_taken} > {max_steps}."
        )
        self.steps_taken = steps_taken
        self.max_steps = max_steps


class AgentInactiveError(ExecutionError):
    """Raised when trying to execute an agent marked inactive in the registry."""

    def __init__(self, agent_id: str, agent_name: str) -> None:
        super().__init__(f"Agent '{agent_name}' ({agent_id}) is inactive and cannot execute tasks.")
        self.agent_id = agent_id
        self.agent_name = agent_name


class UnassignedTaskError(ExecutionError):
    """Raised when trying to execute a task with no assigned agent."""

    def __init__(self, task_id: str) -> None:
        super().__init__(f"Task {task_id} has no assigned specialist agent.")
        self.task_id = task_id


class InvalidTaskStateForExecutionError(ExecutionError):
    """Raised when trying to execute a task in an incompatible state."""

    def __init__(self, task_id: str, status: str) -> None:
        super().__init__(
            f"Task {task_id} is in status '{status}' and cannot be executed. "
            "Executable statuses: ASSIGNED, READY, PLANNED, FAILED."
        )
        self.task_id = task_id
        self.status = status


class ExecutionAccessDeniedError(ExecutionError):
    """Raised when attempting to execute tasks outside authorized company tenant."""

    def __init__(self, message: str = "Access denied to task or agent for company.") -> None:
        super().__init__(message)
