"""Application service for agent task execution adhering to docs/Phases.md Section 12."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application.services.presence_service import PresenceService
from domain.runtime.engine import AgentRuntimeEngine
from domain.runtime.exceptions import (
    AgentInactiveError,
    ExecutionAccessDeniedError,
    ExecutionError,
    ExecutionTimeoutError,
    InvalidTaskStateForExecutionError,
    UnassignedTaskError,
)
from domain.runtime.schemas import (
    AgentExecutionContext,
    ExecutionResult,
    RuntimeLimits,
)
from domain.work.exceptions import TaskNotFoundError
from domain.work.state_machine import TaskStateMachine, TaskStatus
from infrastructure.database.models import (
    Agent,
    Company,
    CompanyMember,
    ExecutionRecord,
    Task,
    TaskDependency,
)


class ExecutionService:
    """Service managing specialist agent execution runs and lifecycle transitions."""

    def __init__(
        self,
        db: AsyncSession,
        runtime_engine: AgentRuntimeEngine | None = None,
    ) -> None:
        self.db = db
        self.runtime_engine = runtime_engine or AgentRuntimeEngine()

    async def _verify_membership(self, user_id: str, company_id: str) -> CompanyMember:
        """Verify that user has active membership in the target company."""
        result = await self.db.execute(
            select(CompanyMember).where(
                CompanyMember.company_id == company_id,
                CompanyMember.user_id == user_id,
                CompanyMember.status == "active",
            )
        )
        membership = result.scalars().first()
        if not membership:
            raise ExecutionAccessDeniedError(
                f"Access denied: User '{user_id}' does not have active membership in company '{company_id}'."
            )
        return membership

    async def execute_task(
        self,
        company_id: str,
        task_id: str,
        user_id: str,
        limits: RuntimeLimits | None = None,
    ) -> ExecutionRecord:
        """Execute a task using its assigned specialist agent.

        Follows Phase 8 lifecycle:
        1. Validates company isolation and user membership.
        2. Validates task executable status (ASSIGNED, READY, PLANNED, FAILED).
        3. Validates assigned agent exists and is active.
        4. Advances task status to IN_PROGRESS.
        5. Persists initial ExecutionRecord (RUNNING).
        6. Runs AgentRuntimeEngine with bounds (max_steps, timeout, max_tokens).
        7. On success: Advances task to VERIFYING (Phase 8 Golden Rule: agent claiming
           'Task completed' does not make it COMPLETED; moves to VERIFYING).
        8. On failure: Advances task to FAILED with error_details.
        """
        await self._verify_membership(user_id=user_id, company_id=company_id)

        # 1. Fetch task with eager loading
        task_res = await self.db.execute(
            select(Task)
            .where(
                Task.id == task_id,
                Task.company_id == company_id,
            )
            .options(
                selectinload(Task.dependencies).selectinload(TaskDependency.depends_on_task),
                selectinload(Task.department),
            )
        )
        task = task_res.scalars().first()
        if not task:
            raise TaskNotFoundError(f"Task '{task_id}' not found in company '{company_id}'.")

        # 2. Validate assigned agent
        if not task.assigned_to_agent_id:
            raise UnassignedTaskError(task_id)

        # 3. Validate executable status
        executable_statuses = {
            TaskStatus.ASSIGNED.value,
            TaskStatus.READY.value,
            TaskStatus.PLANNED.value,
            TaskStatus.FAILED.value,
        }
        if task.status not in executable_statuses:
            raise InvalidTaskStateForExecutionError(task_id, task.status)

        # 4. Fetch agent and current definition
        agent_res = await self.db.execute(
            select(Agent)
            .where(
                Agent.id == task.assigned_to_agent_id,
                Agent.company_id == company_id,
            )
            .options(
                selectinload(Agent.definitions),
                selectinload(Agent.department),
            )
        )
        agent = agent_res.scalars().first()
        if not agent:
            raise UnassignedTaskError(f"Assigned agent '{task.assigned_to_agent_id}' not found.")

        if agent.status != "active":
            raise AgentInactiveError(agent.id, agent.name)

        # Current active definition
        current_def = next((d for d in agent.definitions if d.is_current), None)
        if not current_def and agent.definitions:
            current_def = agent.definitions[0]

        # 5. Fetch company details
        company_res = await self.db.execute(select(Company).where(Company.id == company_id))
        company = company_res.scalars().one()

        # 6. Gather prerequisite deliverables
        prereq_outputs: list[dict[str, Any]] = []
        for dep in task.dependencies:
            if dep.depends_on_task:
                prereq_outputs.append(
                    {
                        "task_id": dep.depends_on_task.id,
                        "title": dep.depends_on_task.title,
                        "status": dep.depends_on_task.status,
                        "output": dep.depends_on_task.output,
                    }
                )

        # 7. Advance task status to IN_PROGRESS
        TaskStateMachine.validate_transition(task.status, TaskStatus.IN_PROGRESS.value)
        task.status = TaskStatus.IN_PROGRESS.value
        task.started_at = datetime.now(UTC)

        # Update agent presence to WORKING per Phase 14
        presence_svc = PresenceService(self.db)
        await presence_svc.set_working(
            company_id=company_id,
            agent_id=agent.id,
            task_id=task.id,
            project_id=task.project_id,
            activity=f"Executing: {task.title}",
            current_step="Initializing agent runtime",
        )

        # 8. Create ExecutionRecord in RUNNING state
        execution_record = ExecutionRecord(
            company_id=company_id,
            task_id=task_id,
            agent_id=agent.id,
            executed_by_user_id=user_id,
            status="RUNNING",
            step_count=0,
            duration_ms=0,
            tokens_used=0,
            estimated_cost=0.0,
            steps_json=[],
        )
        self.db.add(execution_record)
        await self.db.flush()

        # 9. Assemble context packet
        context = AgentExecutionContext(
            company_id=company_id,
            company_name=company.name,
            company_mission=company.mission,
            company_industry=company.industry,
            department_name=task.department.name if task.department else None,
            department_code=task.department.code if task.department else None,
            task_id=task.id,
            task_title=task.title,
            task_objective=task.objective,
            task_description=task.description,
            task_priority=task.priority,
            prerequisite_outputs=prereq_outputs,
            agent_id=agent.id,
            agent_name=agent.name,
            agent_role=agent.role,
            agent_authority_level=agent.authority_level,
            system_prompt=current_def.system_prompt if current_def else None,
            model=current_def.model if current_def else "gemini-1.5-pro",
            capabilities=current_def.capabilities if current_def else [],
            tools=current_def.tools if current_def else [],
            configuration=current_def.configuration if current_def else {},
        )

        active_limits = limits or RuntimeLimits()

        # 10. Run bounded execution
        result: ExecutionResult | None = None
        try:
            result = await self.runtime_engine.run_task(context, active_limits)

            # Verification Guard: advance to VERIFYING, not COMPLETED
            TaskStateMachine.validate_transition(task.status, TaskStatus.VERIFYING.value)
            task.status = TaskStatus.VERIFYING.value
            task.output = result.deliverable.content
            task.error_details = None

            execution_record.status = "SUCCESS"
            execution_record.step_count = result.step_count
            execution_record.duration_ms = result.duration_ms
            execution_record.tokens_used = result.tokens_used
            execution_record.estimated_cost = result.estimated_cost
            execution_record.result_summary = result.summary
            execution_record.deliverable = result.deliverable.content
            execution_record.steps_json = [s.model_dump(mode="json") for s in result.steps]
            execution_record.completed_at = datetime.now(UTC)

            # Revert agent presence to IDLE upon successful execution
            await presence_svc.set_idle(
                company_id=company_id,
                agent_id=agent.id,
            )

        except Exception as exc:
            TaskStateMachine.validate_transition(task.status, TaskStatus.FAILED.value)
            task.status = TaskStatus.FAILED.value
            task.error_details = str(exc)

            execution_record.status = (
                "TIMED_OUT" if isinstance(exc, ExecutionTimeoutError) else "FAILED"
            )
            execution_record.error_details = str(exc)
            execution_record.completed_at = datetime.now(UTC)

            # Revert agent presence to ERROR upon failure
            await presence_svc.set_error(
                company_id=company_id,
                agent_id=agent.id,
                task_id=task.id,
                error_details=str(exc),
            )
            await self.db.commit()
            raise

        await self.db.commit()
        await self.db.refresh(execution_record)
        return execution_record

    async def list_task_executions(
        self,
        company_id: str,
        task_id: str,
        user_id: str,
    ) -> list[ExecutionRecord]:
        """List all execution records for a task in chronological order."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        res = await self.db.execute(
            select(ExecutionRecord)
            .where(
                ExecutionRecord.company_id == company_id,
                ExecutionRecord.task_id == task_id,
            )
            .options(
                selectinload(ExecutionRecord.agent),
                selectinload(ExecutionRecord.executed_by_user),
            )
            .order_by(desc(ExecutionRecord.created_at))
        )
        return list(res.scalars().all())

    async def get_execution(
        self,
        company_id: str,
        execution_id: str,
        user_id: str,
    ) -> ExecutionRecord:
        """Get a single execution record by ID with full details."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        res = await self.db.execute(
            select(ExecutionRecord)
            .where(
                ExecutionRecord.id == execution_id,
                ExecutionRecord.company_id == company_id,
            )
            .options(
                selectinload(ExecutionRecord.agent),
                selectinload(ExecutionRecord.executed_by_user),
                selectinload(ExecutionRecord.task),
            )
        )
        record = res.scalars().first()
        if not record:
            raise ExecutionError(f"Execution record '{execution_id}' not found.")
        return record
