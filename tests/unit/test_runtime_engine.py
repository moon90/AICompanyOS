"""Unit tests for the Agent Runtime Engine adhering to docs/Phases.md Section 12."""

import pytest

from domain.runtime.engine import AgentRuntimeEngine
from domain.runtime.exceptions import (
    ExecutionTimeoutError,
    MaxStepsExceededError,
)
from domain.runtime.schemas import (
    AgentExecutionContext,
    ExecutionResult,
    RuntimeLimits,
)
from infrastructure.llm.gateway import LLMGateway
from infrastructure.llm.providers.deterministic import DeterministicPlannerProvider


@pytest.fixture
def sample_context() -> AgentExecutionContext:
    """Fixture providing a realistic agent execution context."""
    return AgentExecutionContext(
        company_id="comp-123",
        company_name="Nexus AI Technologies",
        company_mission="Build autonomous verifiable software systems",
        company_industry="Enterprise AI",
        department_name="Technology & Engineering",
        department_code="CTO",
        task_id="task-456",
        task_title="Implement database connection pooling middleware",
        task_objective="Provide robust connection pooling with retry backoff",
        task_description="Configure async connection pool with max 20 connections and health probe.",
        task_priority="high",
        agent_id="agent-789",
        agent_name="Senior Backend Specialist",
        agent_role="backend_specialist",
        agent_authority_level=1,
        system_prompt="You are an expert Python backend engineer.",
        model="gemini-1.5-pro",
        capabilities=["python", "fastapi", "sqlalchemy"],
        tools=["code_generator", "linter"],
    )


@pytest.mark.asyncio
async def test_runtime_engine_successful_execution(sample_context: AgentExecutionContext) -> None:
    """Verify that runtime engine produces valid structured deliverable and steps within limits."""
    engine = AgentRuntimeEngine()
    limits = RuntimeLimits(max_steps=5, max_duration_seconds=10, max_tokens=8000)

    result = await engine.run_task(sample_context, limits)

    assert isinstance(result, ExecutionResult)
    assert result.status == "SUCCESS"
    assert result.step_count <= limits.max_steps
    assert result.tokens_used <= limits.max_tokens
    assert result.deliverable is not None
    assert result.deliverable.format == "python"
    assert "class TaskHandler" in result.deliverable.content
    assert len(result.steps) > 0
    assert result.self_assessment_score >= 0.90
    assert "verified" in result.verification_notes.lower()


@pytest.mark.asyncio
async def test_runtime_engine_role_deliverables(sample_context: AgentExecutionContext) -> None:
    """Verify role-specific deliverable generation for different specialists."""
    engine = AgentRuntimeEngine()
    limits = RuntimeLimits(max_steps=5, max_duration_seconds=10)

    # 1. Frontend specialist
    sample_context.agent_role = "frontend_specialist"
    frontend_res = await engine.run_task(sample_context, limits)
    assert frontend_res.deliverable.format == "typescript"
    assert "export function TaskView" in frontend_res.deliverable.content

    # 2. QA specialist
    sample_context.agent_role = "qa_specialist"
    qa_res = await engine.run_task(sample_context, limits)
    assert "Test Plan" in qa_res.deliverable.content

    # 3. DevOps specialist
    sample_context.agent_role = "devops_specialist"
    devops_res = await engine.run_task(sample_context, limits)
    assert devops_res.deliverable.format == "yaml"
    assert "services:" in devops_res.deliverable.content

    # 4. Lead Architect
    sample_context.agent_role = "lead_architect"
    arch_res = await engine.run_task(sample_context, limits)
    assert "Architecture Specification" in arch_res.deliverable.content


@pytest.mark.asyncio
async def test_runtime_engine_max_steps_exceeded(sample_context: AgentExecutionContext) -> None:
    """Verify that exceeding max_steps raises MaxStepsExceededError."""

    # Create mock provider returning more steps than allowed
    class RunawayProvider(DeterministicPlannerProvider):
        async def execute_task(
            self, context: AgentExecutionContext, limits: RuntimeLimits
        ) -> ExecutionResult:
            res = await super().execute_task(context, limits)
            res.step_count = 10  # exceeds limit of 3
            return res

    gateway = LLMGateway(provider=RunawayProvider())
    engine = AgentRuntimeEngine(llm_gateway=gateway)

    with pytest.raises(MaxStepsExceededError) as exc_info:
        await engine.run_task(sample_context, RuntimeLimits(max_steps=3))

    assert "exceeded maximum allowed steps" in str(exc_info.value)


@pytest.mark.asyncio
async def test_runtime_engine_timeout_enforcement(sample_context: AgentExecutionContext) -> None:
    """Verify that execution exceeding max_duration_seconds raises ExecutionTimeoutError."""
    import asyncio

    class SlowProvider(DeterministicPlannerProvider):
        async def execute_task(
            self, context: AgentExecutionContext, limits: RuntimeLimits
        ) -> ExecutionResult:
            await asyncio.sleep(1.2)  # longer than 1.0s limit
            return await super().execute_task(context, limits)

    gateway = LLMGateway(provider=SlowProvider())
    engine = AgentRuntimeEngine(llm_gateway=gateway)

    with pytest.raises(ExecutionTimeoutError) as exc_info:
        await engine.run_task(sample_context, RuntimeLimits(max_duration_seconds=1))

    assert "timed out" in str(exc_info.value)
