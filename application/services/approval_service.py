"""Application service for Human Approval & Oversight System adhering to docs/Phases.md Section 14 and docs/Architecture.md Sections 40-45."""

from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.approvals.exceptions import (
    ApprovalAccessDeniedError,
    ApprovalNotFoundError,
)
from domain.approvals.policy_engine import ApprovalPolicyEngine
from domain.approvals.schemas import (
    ApprovalDecisionInput,
    ApprovalFilter,
    ApprovalRequestCreate,
    ApprovalStatus,
)
from domain.approvals.state_machine import ApprovalStateMachine
from domain.work.exceptions import TaskNotFoundError
from domain.work.state_machine import TaskStatus
from infrastructure.database.models import (
    ApprovalRequest,
    CompanyMember,
    Task,
    ToolExecutionRecord,
)
from tools.gateway.gateway import ToolGateway


class ApprovalService:
    """Service orchestrating human review workflows, consequential action gating, and execution resumption."""

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
            raise ApprovalAccessDeniedError(
                f"Access denied: User '{user_id}' does not have active membership in company '{company_id}'."
            )
        return membership

    async def create_approval(
        self,
        company_id: str,
        creator_id: str,
        request_data: ApprovalRequestCreate,
        is_agent: bool = False,
    ) -> ApprovalRequest:
        """Create a new human approval request for a consequential action."""
        if not is_agent:
            await self._verify_membership(user_id=creator_id, company_id=company_id)

        # 1. Evaluate or confirm risk classification
        risk_level = request_data.risk_level or ApprovalPolicyEngine.classify_risk(
            request_data.action_type
        )

        # 2. Check task relationship if task_id provided
        if request_data.task_id:
            task_res = await self.db.execute(
                select(Task).where(
                    Task.id == request_data.task_id,
                    Task.company_id == company_id,
                )
            )
            task_obj = task_res.scalars().first()
            if not task_obj:
                raise TaskNotFoundError(
                    f"Task '{request_data.task_id}' not found in company '{company_id}'."
                )

            # Move task to APPROVAL_REQUIRED if currently in progress or ready
            if task_obj.status not in (
                TaskStatus.COMPLETED.value,
                TaskStatus.FAILED.value,
                TaskStatus.CANCELLED.value,
            ):
                task_obj.status = TaskStatus.APPROVAL_REQUIRED.value

        # 3. Create persistent approval record
        approval = ApprovalRequest(
            company_id=company_id,
            task_id=request_data.task_id,
            agent_id=request_data.agent_id,
            execution_id=request_data.execution_id,
            tool_execution_id=request_data.tool_execution_id,
            action_type=request_data.action_type,
            description=request_data.description,
            payload=request_data.payload,
            risk_level=risk_level,
            status=ApprovalStatus.PENDING.value,
        )
        self.db.add(approval)
        await self.db.commit()
        await self.db.refresh(approval)

        return approval

    async def list_approvals(
        self,
        company_id: str,
        user_id: str,
        filter_params: ApprovalFilter,
    ) -> tuple[list[ApprovalRequest], int]:
        """List approval requests in company with filtering and pagination."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        conditions = [ApprovalRequest.company_id == company_id]
        if filter_params.status:
            conditions.append(ApprovalRequest.status == filter_params.status.value)
        if filter_params.risk_level:
            conditions.append(ApprovalRequest.risk_level == filter_params.risk_level.value)
        if filter_params.action_type:
            conditions.append(ApprovalRequest.action_type == filter_params.action_type)
        if filter_params.agent_id:
            conditions.append(ApprovalRequest.agent_id == filter_params.agent_id)

        # Count total
        count_stmt = select(func.count(ApprovalRequest.id)).where(*conditions)
        total_count = (await self.db.execute(count_stmt)).scalar_one()

        # Query records with relations eagerly loaded
        stmt = (
            select(ApprovalRequest)
            .where(*conditions)
            .options(
                selectinload(ApprovalRequest.task),
                selectinload(ApprovalRequest.agent),
                selectinload(ApprovalRequest.reviewed_by_user),
                selectinload(ApprovalRequest.tool_execution),
            )
            .order_by(desc(ApprovalRequest.created_at))
            .offset(filter_params.offset)
            .limit(filter_params.limit)
        )
        result = await self.db.execute(stmt)
        records = list(result.scalars().all())

        return records, total_count

    async def get_approval(
        self,
        company_id: str,
        user_id: str,
        approval_id: str,
    ) -> ApprovalRequest:
        """Fetch a specific approval request by ID with relations."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        stmt = (
            select(ApprovalRequest)
            .where(
                ApprovalRequest.id == approval_id,
                ApprovalRequest.company_id == company_id,
            )
            .options(
                selectinload(ApprovalRequest.task),
                selectinload(ApprovalRequest.agent),
                selectinload(ApprovalRequest.reviewed_by_user),
                selectinload(ApprovalRequest.tool_execution),
            )
        )
        result = await self.db.execute(stmt)
        record = result.scalars().first()
        if not record:
            raise ApprovalNotFoundError(
                f"Approval request '{approval_id}' not found in company '{company_id}'."
            )

        return record

    async def approve_request(
        self,
        company_id: str,
        user_id: str,
        approval_id: str,
        decision_input: ApprovalDecisionInput,
        is_agent: bool = False,
    ) -> ApprovalRequest:
        """Approve a pending request, executing any gated tool operations and resuming blocked tasks."""
        # 1. Enforce that only humans can approve (docs/Rules.md § 42)
        ApprovalPolicyEngine.validate_approver_is_human(is_agent=is_agent)
        await self._verify_membership(user_id=user_id, company_id=company_id)

        # 2. Fetch approval request
        approval = await self.get_approval(
            company_id=company_id,
            user_id=user_id,
            approval_id=approval_id,
        )

        # 3. Validate state transition
        ApprovalStateMachine.validate_transition(
            current_status=approval.status,
            new_status=ApprovalStatus.APPROVED.value,
        )

        # 4. Mark approved
        approval.status = ApprovalStatus.APPROVED.value
        approval.reviewed_by_user_id = user_id
        approval.reviewed_at = datetime.now(UTC)
        approval.decision_reason = decision_input.decision_reason

        # 5. If gated tool execution is attached, execute the underlying adapter
        if approval.tool_execution_id:
            tool_res = await self.db.execute(
                select(ToolExecutionRecord).where(
                    ToolExecutionRecord.id == approval.tool_execution_id
                )
            )
            tool_record = tool_res.scalars().first()
            if tool_record:
                status, output, duration_ms, error_details = await self.gateway.execute_approved(
                    tool_name=tool_record.tool_name,
                    action=tool_record.action,
                    parameters=tool_record.input_params,
                )
                tool_record.status = status
                tool_record.output_data = output
                tool_record.duration_ms += duration_ms
                tool_record.error_details = error_details

        # 6. If task is attached and was waiting for approval, resume it to IN_PROGRESS
        if approval.task_id:
            task_res = await self.db.execute(select(Task).where(Task.id == approval.task_id))
            task_obj = task_res.scalars().first()
            if task_obj and task_obj.status == TaskStatus.APPROVAL_REQUIRED.value:
                task_obj.status = TaskStatus.IN_PROGRESS.value

        await self.db.commit()
        await self.db.refresh(approval)
        return approval

    async def reject_request(
        self,
        company_id: str,
        user_id: str,
        approval_id: str,
        decision_input: ApprovalDecisionInput,
        is_agent: bool = False,
    ) -> ApprovalRequest:
        """Reject a pending request, permanently blocking any gated action."""
        # 1. Enforce that only humans can reject (docs/Rules.md § 42)
        ApprovalPolicyEngine.validate_approver_is_human(is_agent=is_agent)
        await self._verify_membership(user_id=user_id, company_id=company_id)

        # 2. Fetch approval request
        approval = await self.get_approval(
            company_id=company_id,
            user_id=user_id,
            approval_id=approval_id,
        )

        # 3. Validate state transition
        ApprovalStateMachine.validate_transition(
            current_status=approval.status,
            new_status=ApprovalStatus.REJECTED.value,
        )

        # 4. Mark rejected
        approval.status = ApprovalStatus.REJECTED.value
        approval.reviewed_by_user_id = user_id
        approval.reviewed_at = datetime.now(UTC)
        approval.decision_reason = decision_input.decision_reason

        # 5. If gated tool execution is attached, permanently block execution record
        if approval.tool_execution_id:
            tool_res = await self.db.execute(
                select(ToolExecutionRecord).where(
                    ToolExecutionRecord.id == approval.tool_execution_id
                )
            )
            tool_record = tool_res.scalars().first()
            if tool_record:
                tool_record.status = "BLOCKED"
                tool_record.error_details = f"Action rejected by human operator: {decision_input.decision_reason or 'No reason provided'}"

        # 6. If task is attached, mark as BLOCKED
        if approval.task_id:
            task_res = await self.db.execute(select(Task).where(Task.id == approval.task_id))
            task_obj = task_res.scalars().first()
            if task_obj and task_obj.status == TaskStatus.APPROVAL_REQUIRED.value:
                task_obj.status = TaskStatus.BLOCKED.value

        await self.db.commit()
        await self.db.refresh(approval)
        return approval
