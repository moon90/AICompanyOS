"""Application service managing CEO orchestration, context assembly, and plan generation."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.ceo.exceptions import (
    CeoAccessDeniedError,
    CeoNotFoundError,
    InvalidGoalError,
    PlanNotFoundError,
)
from infrastructure.database.models import (
    Agent,
    CeoPlan,
    Company,
    CompanyMember,
    Department,
)
from infrastructure.llm.gateway import LLMGateway
from orchestration.planner.schemas import GoalIntake


class CeoService:
    """Service layer orchestrating CEO planning, context assembly, and delegation proposals."""

    def __init__(self, db: AsyncSession, llm_gateway: LLMGateway | None = None) -> None:
        self.db = db
        self.llm_gateway = llm_gateway or LLMGateway()

    async def _verify_membership(self, user_id: str, company_id: str) -> CompanyMember:
        """Verify that user has active membership in the target company."""
        result = await self.db.execute(
            select(CompanyMember).where(
                CompanyMember.company_id == company_id,
                CompanyMember.user_id == user_id,
            )
        )
        membership = result.scalars().first()
        if not membership:
            raise CeoAccessDeniedError(
                f"Access denied: User '{user_id}' does not have active membership in company '{company_id}'."
            )
        return membership

    async def get_company_ceo(self, user_id: str, company_id: str) -> Agent:
        """Resolve the authoritative registered CEO agent for the company."""
        await self._verify_membership(user_id, company_id)

        result = await self.db.execute(
            select(Agent)
            .options(selectinload(Agent.definitions))
            .where(
                Agent.company_id == company_id,
                Agent.status == "active",
            )
        )
        agents = result.scalars().all()
        ceo_agent = next(
            (
                a
                for a in agents
                if a.role.lower() in ("ceo", "chief executive officer") or a.name.lower() == "ceo"
            ),
            None,
        )
        if not ceo_agent:
            raise CeoNotFoundError(
                f"No active CEO agent is registered for company '{company_id}'. "
                "Please provision default agents or register a CEO agent in the Agent Registry."
            )
        return ceo_agent

    async def get_ceo_context(self, user_id: str, company_id: str) -> dict[str, Any]:
        """Assemble authoritative company context from PostgreSQL for CEO reasoning."""
        await self._verify_membership(user_id, company_id)

        # 1. Company Profile
        comp_res = await self.db.execute(select(Company).where(Company.id == company_id))
        company = comp_res.scalars().first()
        if not company:
            raise CeoAccessDeniedError(f"Company '{company_id}' not found.")

        # 2. Departments
        dept_res = await self.db.execute(
            select(Department).where(
                Department.company_id == company_id, Department.status == "active"
            )
        )
        departments = dept_res.scalars().all()

        # 3. Registered Agents with active definitions
        agent_res = await self.db.execute(
            select(Agent)
            .options(
                selectinload(Agent.definitions),
                selectinload(Agent.department),
            )
            .where(Agent.company_id == company_id, Agent.status == "active")
        )
        agents = agent_res.scalars().all()

        # 4. Resolve CEO if present
        ceo_agent = next(
            (
                a
                for a in agents
                if a.role.lower() in ("ceo", "chief executive officer") or a.name.lower() == "ceo"
            ),
            None,
        )

        agents_data = []
        for ag in agents:
            current_def = next((d for d in ag.definitions if d.is_current), None)
            agents_data.append(
                {
                    "id": ag.id,
                    "name": ag.name,
                    "role": ag.role,
                    "type": ag.type,
                    "authority_level": ag.authority_level,
                    "reports_to": ag.reports_to,
                    "department_id": ag.department_id,
                    "department_code": ag.department.code if ag.department else None,
                    "department_name": ag.department.name if ag.department else None,
                    "mission": ag.mission,
                    "model": current_def.model if current_def else "gemini-2.0-flash",
                    "version": current_def.version if current_def else "1.0",
                    "capabilities": current_def.capabilities if current_def else [],
                    "tools": current_def.tools if current_def else [],
                }
            )

        departments_data = [
            {
                "id": d.id,
                "name": d.name,
                "code": d.code,
                "lead_role": d.lead_role,
            }
            for d in departments
        ]

        return {
            "company": {
                "id": company.id,
                "name": company.name,
                "description": company.description,
                "mission": company.mission,
                "industry": company.industry,
                "status": company.status,
            },
            "ceo_agent": (
                {
                    "id": ceo_agent.id,
                    "name": ceo_agent.name,
                    "role": ceo_agent.role,
                    "authority_level": ceo_agent.authority_level,
                    "status": ceo_agent.status,
                }
                if ceo_agent
                else None
            ),
            "departments": departments_data,
            "agents": agents_data,
            "agent_count": len(agents_data),
            "department_count": len(departments_data),
        }

    async def generate_plan(
        self,
        user_id: str,
        company_id: str,
        goal: GoalIntake,
    ) -> CeoPlan:
        """Intake user goal, assemble context, generate plan DAG, and persist proposal."""
        await self._verify_membership(user_id, company_id)

        if not goal.objective or not goal.objective.strip():
            raise InvalidGoalError("Goal objective must not be empty.")

        # 1. Resolve CEO identity
        ceo_agent = await self.get_company_ceo(user_id, company_id)

        # 2. Assemble authoritative company context
        context = await self.get_ceo_context(user_id, company_id)

        # 3. Collect active agent IDs for reference validation
        allowed_agent_ids = {a["id"] for a in context["agents"]}

        # 4. Generate and validate plan DAG through LLMGateway
        plan_result = await self.llm_gateway.generate_plan(
            goal=goal,
            context=context,
            allowed_agent_ids=allowed_agent_ids,
        )

        # 5. Persist CeoPlan record as a PROPOSAL
        new_plan = CeoPlan(
            id=str(uuid.uuid4()),
            company_id=company_id,
            user_id=user_id,
            ceo_agent_id=ceo_agent.id,
            goal=goal.objective.strip(),
            requested_outcome=goal.requested_outcome.strip() if goal.requested_outcome else None,
            priority=goal.priority,
            status="proposed",
            reasoning_summary=plan_result.reasoning_summary,
            context_snapshot={
                "company_name": context["company"]["name"],
                "department_count": context["department_count"],
                "agent_count": context["agent_count"],
            },
            plan_steps=[s.model_dump() for s in plan_result.steps],
            delegation_proposals=[d.model_dump() for d in plan_result.delegation_proposals],
            approval_requirements=[a.model_dump() for a in plan_result.approval_requirements],
            risks=plan_result.risks,
            assumptions=plan_result.assumptions,
        )

        self.db.add(new_plan)
        await self.db.commit()
        await self.db.refresh(new_plan)

        return new_plan

    async def list_plans(
        self,
        user_id: str,
        company_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CeoPlan]:
        """List generated CEO plans for the company."""
        await self._verify_membership(user_id, company_id)

        result = await self.db.execute(
            select(CeoPlan)
            .where(CeoPlan.company_id == company_id)
            .order_by(CeoPlan.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_plan(
        self,
        user_id: str,
        company_id: str,
        plan_id: str,
    ) -> CeoPlan:
        """Retrieve a specific CEO plan by ID."""
        await self._verify_membership(user_id, company_id)

        result = await self.db.execute(
            select(CeoPlan).where(
                CeoPlan.id == plan_id,
                CeoPlan.company_id == company_id,
            )
        )
        plan = result.scalars().first()
        if not plan:
            raise PlanNotFoundError(f"Plan '{plan_id}' not found in company '{company_id}'.")
        return plan
