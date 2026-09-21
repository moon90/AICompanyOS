"""Application service for agent task delegation adhering to docs/Phases.md Section 11 and docs/Rules.md §§ 58, 60, 61."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.delegation.exceptions import (
    DelegationAccessDeniedError,
    DelegationNotFoundError,
)
from domain.delegation.rules import DelegationRuleEngine
from domain.work.exceptions import TaskNotFoundError
from infrastructure.database.models import (
    Agent,
    CompanyMember,
    DelegationRecord,
    Task,
)


class DelegationService:
    """Service orchestrating task delegation, organizational hierarchy enforcement, and audit records."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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
            raise DelegationAccessDeniedError(
                f"Access denied: User '{user_id}' does not have active membership in company '{company_id}'."
            )
        return membership

    async def delegate_task(
        self,
        company_id: str,
        task_id: str,
        user_id: str,
        target_agent_id: str,
        reason: str,
        scope: str | None = None,
        delegator_agent_id: str | None = None,
    ) -> DelegationRecord:
        """Delegate a task to an agent with hierarchy validation, cycle prevention, and audit tracking."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        clean_reason = reason.strip()
        if not clean_reason:
            raise ValueError("Delegation reason cannot be empty.")

        # 1. Load target task
        task_res = await self.db.execute(
            select(Task).where(Task.id == task_id, Task.company_id == company_id)
        )
        task = task_res.scalars().first()
        if not task:
            raise TaskNotFoundError(f"Task '{task_id}' not found in company '{company_id}'.")

        # 2. Load target agent
        target_res = await self.db.execute(
            select(Agent).where(Agent.id == target_agent_id, Agent.company_id == company_id)
        )
        target_agent = target_res.scalars().first()
        if not target_agent:
            raise DelegationNotFoundError(
                f"Target agent '{target_agent_id}' not found in company '{company_id}'."
            )

        # 3. Load delegator agent if specified
        source_agent: Agent | None = None
        if delegator_agent_id:
            source_res = await self.db.execute(
                select(Agent).where(Agent.id == delegator_agent_id, Agent.company_id == company_id)
            )
            source_agent = source_res.scalars().first()
            if not source_agent:
                raise DelegationNotFoundError(
                    f"Delegator agent '{delegator_agent_id}' not found in company '{company_id}'."
                )

        # 4. Load existing delegation history on this task
        history_res = await self.db.execute(
            select(DelegationRecord)
            .where(
                DelegationRecord.task_id == task_id,
                DelegationRecord.company_id == company_id,
            )
            .order_by(DelegationRecord.created_at.asc())
        )
        existing_history = list(history_res.scalars().all())

        # 5. Validate through DelegationRuleEngine
        depth = DelegationRuleEngine.validate_delegation(
            target_agent=target_agent,
            source_agent=source_agent,
            existing_history=existing_history,
        )

        # 6. Create DelegationRecord
        delegation_record = DelegationRecord(
            id=str(uuid.uuid4()),
            company_id=company_id,
            task_id=task_id,
            delegated_by_user_id=user_id if source_agent is None else None,
            delegated_by_agent_id=source_agent.id if source_agent else None,
            delegated_to_agent_id=target_agent.id,
            scope=scope.strip() if scope else None,
            reason=clean_reason,
            depth=depth,
            status="active",
        )
        delegation_record.delegated_to_agent = target_agent
        if source_agent:
            delegation_record.delegated_by_agent = source_agent

        self.db.add(delegation_record)

        # 7. Update Task assignment & advance status if in initial states
        task.assigned_to_agent_id = target_agent.id
        task.department_id = target_agent.department_id
        if task.status in ("CREATED", "PLANNED", "READY"):
            task.status = "ASSIGNED"

        await self.db.flush()
        return delegation_record

    async def get_task_delegations(
        self,
        company_id: str,
        user_id: str,
        task_id: str,
    ) -> list[DelegationRecord]:
        """Retrieve chronological delegation history for a task."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        # Verify task exists
        task_res = await self.db.execute(
            select(Task).where(Task.id == task_id, Task.company_id == company_id)
        )
        if not task_res.scalars().first():
            raise TaskNotFoundError(f"Task '{task_id}' not found in company '{company_id}'.")

        stmt = (
            select(DelegationRecord)
            .options(
                selectinload(DelegationRecord.delegated_to_agent),
                selectinload(DelegationRecord.delegated_by_agent),
                selectinload(DelegationRecord.delegated_by_user),
            )
            .where(
                DelegationRecord.task_id == task_id,
                DelegationRecord.company_id == company_id,
            )
            .order_by(DelegationRecord.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_company_delegations(
        self,
        company_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DelegationRecord], int]:
        """List all company delegation records with pagination."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        count_stmt = select(func.count(DelegationRecord.id)).where(
            DelegationRecord.company_id == company_id
        )
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar_one()

        stmt = (
            select(DelegationRecord)
            .options(
                selectinload(DelegationRecord.task),
                selectinload(DelegationRecord.delegated_to_agent),
                selectinload(DelegationRecord.delegated_by_agent),
                selectinload(DelegationRecord.delegated_by_user),
            )
            .where(DelegationRecord.company_id == company_id)
            .order_by(DelegationRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
