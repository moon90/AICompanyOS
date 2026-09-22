"""Application service for Tool Gateway execution adhering to docs/Phases.md Section 13 and docs/Architecture.md Sections 30-36."""

import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.runtime.exceptions import AgentInactiveError
from domain.tools.exceptions import (
    ToolAccessDeniedError,
    ToolExecutionNotFoundError,
)
from domain.tools.schemas import ToolCallRequest, ToolDefinition
from domain.work.exceptions import TaskNotFoundError
from domain.work.state_machine import TaskStatus
from infrastructure.database.models import (
    Agent,
    ApprovalRequest,
    CompanyMember,
    ExecutionRecord,
    Task,
    ToolExecutionRecord,
)
from tools.gateway.gateway import ToolGateway
from tools.gateway.validator import ToolValidator


class ToolService:
    """Service managing agent tool invocations, company isolation, and audit persistence."""

    def __init__(
        self,
        db: AsyncSession,
        gateway: ToolGateway | None = None,
    ) -> None:
        self.db = db
        self.gateway = gateway or ToolGateway()

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
            raise ToolAccessDeniedError(
                f"Access denied: User '{user_id}' does not have active membership in company '{company_id}'."
            )
        return membership

    async def list_tools(
        self,
        company_id: str,
        user_id: str,
        role: str | None = None,
    ) -> list[ToolDefinition]:
        """List all available tools in the gateway, optionally filtered by agent role."""
        await self._verify_membership(user_id=user_id, company_id=company_id)
        if role:
            return self.gateway.registry.get_tools_for_role(role)
        return self.gateway.registry.list_tools()

    async def get_tool(
        self,
        company_id: str,
        user_id: str,
        tool_name: str,
    ) -> ToolDefinition:
        """Get a single tool definition by name."""
        await self._verify_membership(user_id=user_id, company_id=company_id)
        return self.gateway.registry.get_tool(tool_name)

    async def execute_tool(
        self,
        company_id: str,
        user_id: str,
        request: ToolCallRequest,
    ) -> ToolExecutionRecord:
        """Execute a tool through the authoritative 8-step security gateway and persist audit record."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        # 1. Validate agent exists and is active in target company
        agent_res = await self.db.execute(
            select(Agent).where(
                Agent.id == request.agent_id,
                Agent.company_id == company_id,
            )
        )
        agent = agent_res.scalars().first()
        if not agent:
            raise ToolAccessDeniedError(
                f"Agent '{request.agent_id}' does not exist in company '{company_id}'."
            )
        if agent.status != "active":
            raise AgentInactiveError(agent.id, agent.name)

        # 2. Validate optional task isolation
        if request.task_id:
            task_res = await self.db.execute(
                select(Task).where(
                    Task.id == request.task_id,
                    Task.company_id == company_id,
                )
            )
            if not task_res.scalars().first():
                raise TaskNotFoundError(
                    f"Task '{request.task_id}' not found in company '{company_id}'."
                )

        # 3. Validate optional execution record isolation
        if request.execution_id:
            exec_res = await self.db.execute(
                select(ExecutionRecord).where(
                    ExecutionRecord.id == request.execution_id,
                    ExecutionRecord.company_id == company_id,
                )
            )
            if not exec_res.scalars().first():
                raise ToolExecutionNotFoundError(
                    f"Execution record '{request.execution_id}' not found in company '{company_id}'."
                )

        # 4. Invoke the 8-step gateway pipeline
        result = await self.gateway.invoke(
            request=request,
            agent_role=agent.role,
            agent_authority_level=agent.authority_level,
        )

        # 5. Persist immutable audit record in PostgreSQL
        sanitized_input = ToolValidator.sanitize_parameters(request.parameters)
        record_id = str(uuid.uuid4())
        record = ToolExecutionRecord(
            id=record_id,
            company_id=company_id,
            agent_id=agent.id,
            task_id=request.task_id,
            execution_id=request.execution_id,
            tool_name=result.tool_name,
            action=result.action,
            risk_level=result.risk_level,
            requires_approval=result.requires_approval,
            status=result.status,
            input_params=sanitized_input,
            output_data=result.output,
            error_details=result.error_details,
            duration_ms=result.duration_ms,
        )
        self.db.add(record)

        # 6. Auto-generate ApprovalRequest if execution was halted for human approval
        if result.status == "APPROVAL_REQUIRED" or result.requires_approval:
            approval_req = ApprovalRequest(
                company_id=company_id,
                task_id=request.task_id,
                agent_id=agent.id,
                execution_id=request.execution_id,
                tool_execution_id=record_id,
                action_type=f"TOOL_{result.tool_name.upper()}_{result.action.upper()}",
                description=(
                    f"Tool invocation '{result.tool_name}.{result.action}' halted pending human approval: "
                    f"{result.error_details or 'High-risk or gated tool execution.'}"
                ),
                payload={"parameters": sanitized_input},
                risk_level=result.risk_level,
                status="PENDING",
            )
            self.db.add(approval_req)

            if request.task_id:
                task_res = await self.db.execute(select(Task).where(Task.id == request.task_id))
                task_obj = task_res.scalars().first()
                if task_obj and task_obj.status not in (
                    TaskStatus.COMPLETED.value,
                    TaskStatus.FAILED.value,
                    TaskStatus.CANCELLED.value,
                ):
                    task_obj.status = TaskStatus.APPROVAL_REQUIRED.value

        await self.db.commit()
        await self.db.refresh(record)

        return record

    async def list_tool_executions(
        self,
        company_id: str,
        user_id: str,
        agent_id: str | None = None,
        task_id: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ToolExecutionRecord], int]:
        """List audit records for tool executions in company with filtering and pagination."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        # Base conditions
        conditions = [ToolExecutionRecord.company_id == company_id]
        if agent_id:
            conditions.append(ToolExecutionRecord.agent_id == agent_id)
        if task_id:
            conditions.append(ToolExecutionRecord.task_id == task_id)
        if tool_name:
            conditions.append(ToolExecutionRecord.tool_name == tool_name)
        if status:
            conditions.append(ToolExecutionRecord.status == status)

        # Count total
        count_stmt = select(func.count(ToolExecutionRecord.id)).where(*conditions)
        total_count = (await self.db.execute(count_stmt)).scalar_one()

        # Fetch records ordered by created_at DESC
        stmt = (
            select(ToolExecutionRecord)
            .where(*conditions)
            .order_by(desc(ToolExecutionRecord.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        records = list(result.scalars().all())

        return records, total_count

    async def get_tool_execution(
        self,
        company_id: str,
        user_id: str,
        execution_id: str,
    ) -> ToolExecutionRecord:
        """Fetch a specific tool execution audit record by ID."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        stmt = select(ToolExecutionRecord).where(
            ToolExecutionRecord.id == execution_id,
            ToolExecutionRecord.company_id == company_id,
        )
        result = await self.db.execute(stmt)
        record = result.scalars().first()
        if not record:
            raise ToolExecutionNotFoundError(execution_id)

        return record
