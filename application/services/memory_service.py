"""Application service for Company Memory, Decisions, and Operational State.

Adheres strictly to docs/Phases.md Section 15, docs/Memory.md Sections 33-34, and docs/Architecture.md.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.memory.context_retriever import (
    answer_ceo_inquiry_grounded,
    synthesize_task_context,
)
from domain.memory.exceptions import (
    DecisionAlreadySupersededError,
    DecisionNotFoundError,
    MemoryAccessDeniedError,
)
from domain.memory.schemas import (
    CeoInquiryRequest,
    CeoInquiryResponse,
    CompanyContextPacket,
    CompanyDecisionCreate,
    CompanyDecisionFilter,
    DecisionStatus,
)
from domain.work.exceptions import ProjectNotFoundError, TaskNotFoundError
from infrastructure.database.models import (
    Agent,
    ApprovalRequest,
    Company,
    CompanyDecision,
    CompanyMember,
    Department,
    Project,
    Task,
)


class MemoryService:
    """Service orchestrating authoritative company memory, decisions, and grounded retrieval."""

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
            raise MemoryAccessDeniedError(
                f"Access denied: User '{user_id}' does not have active membership in company '{company_id}'."
            )
        return membership

    async def record_decision(
        self,
        company_id: str,
        user_id: str,
        data: CompanyDecisionCreate,
    ) -> CompanyDecision:
        """Record an authoritative new company decision adhering to docs/Memory.md § 33."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        # Verify project linkage if provided
        if data.project_id:
            proj_res = await self.db.execute(
                select(Project).where(
                    Project.id == data.project_id,
                    Project.company_id == company_id,
                )
            )
            if not proj_res.scalars().first():
                raise ProjectNotFoundError(
                    f"Project '{data.project_id}' not found in company '{company_id}'."
                )

        # Verify task linkage if provided
        if data.task_id:
            task_res = await self.db.execute(
                select(Task).where(
                    Task.id == data.task_id,
                    Task.company_id == company_id,
                )
            )
            if not task_res.scalars().first():
                raise TaskNotFoundError(
                    f"Task '{data.task_id}' not found in company '{company_id}'."
                )

        decision = CompanyDecision(
            id=str(uuid.uuid4()),
            company_id=company_id,
            project_id=data.project_id,
            task_id=data.task_id,
            title=data.title,
            decision=data.decision,
            rationale=data.rationale,
            evidence=data.evidence,
            status=DecisionStatus.ACTIVE.value,
            decided_by_user_id=user_id,
            decided_by_agent_id=data.decided_by_agent_id,
        )
        self.db.add(decision)
        await self.db.flush()

        from application.services.activity_service import ActivityService

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            project_id=data.project_id,
            task_id=data.task_id,
            actor_type="user" if user_id else ("agent" if data.decided_by_agent_id else "system"),
            actor_id=user_id or data.decided_by_agent_id,
            event_type="DECISION_RECORDED",
            message=f"Recorded decision: '{decision.title}'",
            metadata={"decision": decision.decision, "status": decision.status},
        )

        await self.db.commit()
        await self.db.refresh(decision)
        return decision

    async def supersede_decision(
        self,
        company_id: str,
        user_id: str,
        old_decision_id: str,
        data: CompanyDecisionCreate,
    ) -> CompanyDecision:
        """Supersede an existing decision with an immutable audit trail.

        The existing decision is marked SUPERSEDED and points to the new decision ID.
        """
        await self._verify_membership(user_id=user_id, company_id=company_id)

        old_res = await self.db.execute(
            select(CompanyDecision).where(
                CompanyDecision.id == old_decision_id,
                CompanyDecision.company_id == company_id,
            )
        )
        old_decision = old_res.scalars().first()
        if not old_decision:
            raise DecisionNotFoundError(
                f"Decision '{old_decision_id}' not found in company '{company_id}'."
            )

        if old_decision.status != DecisionStatus.ACTIVE.value:
            raise DecisionAlreadySupersededError(
                f"Decision '{old_decision_id}' is already {old_decision.status} and cannot be superseded."
            )

        new_decision_id = str(uuid.uuid4())
        new_decision = CompanyDecision(
            id=new_decision_id,
            company_id=company_id,
            project_id=data.project_id or old_decision.project_id,
            task_id=data.task_id or old_decision.task_id,
            title=data.title,
            decision=data.decision,
            rationale=data.rationale,
            evidence=data.evidence,
            status=DecisionStatus.ACTIVE.value,
            decided_by_user_id=user_id,
            decided_by_agent_id=data.decided_by_agent_id,
        )

        self.db.add(new_decision)
        await self.db.flush()

        old_decision.status = DecisionStatus.SUPERSEDED.value
        old_decision.superseded_by_decision_id = new_decision.id

        from application.services.activity_service import ActivityService

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            project_id=new_decision.project_id,
            task_id=new_decision.task_id,
            actor_type="user" if user_id else ("agent" if data.decided_by_agent_id else "system"),
            actor_id=user_id or data.decided_by_agent_id,
            event_type="DECISION_SUPERSEDED",
            message=f"Superseded decision '{old_decision.title}' with '{new_decision.title}'",
            metadata={
                "superseded_decision_id": old_decision.id,
                "new_decision_id": new_decision.id,
            },
        )

        await self.db.commit()
        await self.db.refresh(new_decision)
        return new_decision

    async def get_decision(
        self,
        company_id: str,
        user_id: str,
        decision_id: str,
    ) -> CompanyDecision:
        """Fetch a specific decision by ID within company tenancy."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        res = await self.db.execute(
            select(CompanyDecision).where(
                CompanyDecision.id == decision_id,
                CompanyDecision.company_id == company_id,
            )
        )
        decision = res.scalars().first()
        if not decision:
            raise DecisionNotFoundError(
                f"Decision '{decision_id}' not found in company '{company_id}'."
            )
        return decision

    async def list_decisions(
        self,
        company_id: str,
        user_id: str,
        filter_params: CompanyDecisionFilter | None = None,
    ) -> list[CompanyDecision]:
        """List company decisions with optional filtering."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        conditions = [CompanyDecision.company_id == company_id]
        if filter_params:
            if filter_params.status:
                conditions.append(CompanyDecision.status == filter_params.status.value)
            if filter_params.project_id:
                conditions.append(CompanyDecision.project_id == filter_params.project_id)
            if filter_params.task_id:
                conditions.append(CompanyDecision.task_id == filter_params.task_id)

        stmt = select(CompanyDecision).where(*conditions).order_by(desc(CompanyDecision.created_at))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_company_state(
        self,
        company_id: str,
        user_id: str,
    ) -> CompanyContextPacket:
        """Synthesize live authoritative operational state across all company entities."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        # 1. Company
        comp_res = await self.db.execute(select(Company).where(Company.id == company_id))
        comp = comp_res.scalars().first()
        if not comp:
            raise MemoryAccessDeniedError(f"Company '{company_id}' not found.")

        comp_data = {
            "id": comp.id,
            "name": comp.name,
            "mission": comp.mission,
            "description": comp.description,
            "created_at": comp.created_at.isoformat() if comp.created_at else None,
        }

        # 2. Departments
        dept_res = await self.db.execute(
            select(Department).where(Department.company_id == company_id)
        )
        departments = [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in dept_res.scalars().all()
        ]

        # 3. Agents
        agent_res = await self.db.execute(select(Agent).where(Agent.company_id == company_id))
        agents = [
            {
                "id": a.id,
                "name": a.name,
                "role": a.role,
                "department_id": a.department_id,
                "status": a.status,
                "authority_level": a.authority_level,
            }
            for a in agent_res.scalars().all()
        ]

        # 4. Projects
        proj_res = await self.db.execute(
            select(Project)
            .where(Project.company_id == company_id)
            .order_by(desc(Project.created_at))
        )
        projects = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "objective": p.objective,
                "status": p.status,
                "priority": p.priority,
            }
            for p in proj_res.scalars().all()
        ]

        # 5. Task Pipeline Summary
        total_tasks = (
            await self.db.execute(select(func.count(Task.id)).where(Task.company_id == company_id))
        ).scalar_one()

        status_counts_res = await self.db.execute(
            select(Task.status, func.count(Task.id))
            .where(Task.company_id == company_id)
            .group_by(Task.status)
        )
        by_status: dict[str, int] = {str(row[0]): int(row[1]) for row in status_counts_res.all()}

        recent_tasks_res = await self.db.execute(
            select(Task)
            .where(Task.company_id == company_id)
            .order_by(desc(Task.created_at))
            .limit(5)
        )
        recent_tasks = [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
            }
            for t in recent_tasks_res.scalars().all()
        ]

        tasks_summary = {
            "total": total_tasks,
            "by_status": by_status,
            "recent_active_tasks": recent_tasks,
        }

        # 6. Recent Approvals
        appr_res = await self.db.execute(
            select(ApprovalRequest)
            .where(ApprovalRequest.company_id == company_id)
            .order_by(desc(ApprovalRequest.created_at))
            .limit(10)
        )
        recent_approvals = [
            {
                "id": ap.id,
                "action_type": ap.action_type,
                "risk_level": ap.risk_level,
                "status": ap.status,
                "description": ap.description,
            }
            for ap in appr_res.scalars().all()
        ]

        # 7. Decisions
        dec_res = await self.db.execute(
            select(CompanyDecision)
            .where(CompanyDecision.company_id == company_id)
            .order_by(desc(CompanyDecision.created_at))
        )
        decisions = [
            {
                "id": dec.id,
                "title": dec.title,
                "decision": dec.decision,
                "rationale": dec.rationale,
                "status": dec.status,
                "superseded_by_decision_id": dec.superseded_by_decision_id,
                "created_at": dec.created_at.isoformat() if dec.created_at else None,
            }
            for dec in dec_res.scalars().all()
        ]

        return CompanyContextPacket(
            company=comp_data,
            departments=departments,
            agents=agents,
            projects=projects,
            tasks_summary=tasks_summary,
            recent_approvals=recent_approvals,
            decisions=decisions,
            generated_at=datetime.now(UTC),
        )

    async def get_context_for_task(
        self,
        company_id: str,
        user_id: str,
        task_id: str,
    ) -> dict[str, Any]:
        """Fetch task-scoped context bundle with relevant decisions and execution history."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        task_res = await self.db.execute(
            select(Task)
            .options(
                selectinload(Task.project),
                selectinload(Task.company),
                selectinload(Task.execution_records),
            )
            .where(
                Task.id == task_id,
                Task.company_id == company_id,
            )
        )
        task = task_res.scalars().first()
        if not task:
            raise TaskNotFoundError(f"Task '{task_id}' not found in company '{company_id}'.")

        # Fetch active decisions for this task or project or company
        dec_conditions = [
            CompanyDecision.company_id == company_id,
            CompanyDecision.status == DecisionStatus.ACTIVE.value,
        ]
        dec_res = await self.db.execute(
            select(CompanyDecision)
            .where(*dec_conditions)
            .order_by(desc(CompanyDecision.created_at))
            .limit(10)
        )
        decisions = [
            {
                "id": d.id,
                "title": d.title,
                "decision": d.decision,
                "rationale": d.rationale,
            }
            for d in dec_res.scalars().all()
        ]

        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
        }
        project_data = (
            {
                "id": task.project.id,
                "name": task.project.name,
                "status": task.project.status,
            }
            if task.project
            else None
        )
        comp_data = {
            "id": task.company.id,
            "name": task.company.name,
        }
        execution_history = [
            {
                "id": rec.id,
                "status": rec.status,
                "agent_id": rec.agent_id,
                "created_at": rec.created_at.isoformat() if rec.created_at else None,
            }
            for rec in (task.execution_records or [])
        ]

        prompt_str = synthesize_task_context(
            task=task_data,
            project=project_data,
            company=comp_data,
            decisions=decisions,
            execution_history=execution_history,
        )

        return {
            "task": task_data,
            "project": project_data,
            "company": comp_data,
            "decisions": decisions,
            "execution_history": execution_history,
            "synthesized_prompt": prompt_str,
        }

    async def ceo_inquire(
        self,
        company_id: str,
        user_id: str,
        inquiry: CeoInquiryRequest,
    ) -> CeoInquiryResponse:
        """Answer an inquiry strictly grounded in company state without hallucinating."""
        packet = await self.get_company_state(company_id=company_id, user_id=user_id)
        return answer_ceo_inquiry_grounded(question=inquiry.question, packet=packet)
