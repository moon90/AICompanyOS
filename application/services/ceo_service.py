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
    DelegationRecord,
    Department,
    Project,
    Task,
    TaskDependency,
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

    async def delegate_plan(
        self,
        user_id: str,
        company_id: str,
        plan_id: str,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> dict[str, Any]:
        """Decompose a proposed CEO plan into an authoritative Project, Parent Task, Child Tasks, DAG dependencies, and DelegationRecords per docs/Phases.md Section 11."""
        await self._verify_membership(user_id, company_id)

        # 1. Load CeoPlan
        plan = await self.get_plan(user_id=user_id, company_id=company_id, plan_id=plan_id)
        if plan.status == "delegated" and plan.project_id:
            raise ValueError(
                f"Plan '{plan_id}' has already been delegated to project '{plan.project_id}'."
            )

        # 2. Resolve CEO agent if available
        ceo_agent = None
        try:
            ceo_agent = await self.get_company_ceo(user_id, company_id)
        except CeoNotFoundError:
            ceo_agent = None

        # 3. Create or resolve Project
        project: Project
        if project_id:
            proj_res = await self.db.execute(
                select(Project).where(Project.id == project_id, Project.company_id == company_id)
            )
            found_proj = proj_res.scalars().first()
            if not found_proj:
                raise ValueError(
                    f"Target project '{project_id}' not found in company '{company_id}'."
                )
            project = found_proj
        else:
            resolved_name = project_name or f"Strategic: {plan.goal[:60]}"
            project = Project(
                id=str(uuid.uuid4()),
                company_id=company_id,
                name=resolved_name,
                description=plan.reasoning_summary,
                objective=plan.requested_outcome or plan.goal,
                status="IN_PROGRESS",
                priority=plan.priority,
                owner_user_id=user_id,
                owner_agent_id=ceo_agent.id if ceo_agent else None,
            )
            self.db.add(project)
            await self.db.flush()

        # 4. Create 1 Parent Task representing the overarching strategic mission
        parent_task = Task(
            id=str(uuid.uuid4()),
            company_id=company_id,
            project_id=project.id,
            parent_task_id=None,
            title=f"Strategic Objective: {plan.goal[:100]}",
            description=plan.reasoning_summary,
            objective=plan.requested_outcome or plan.goal,
            created_by_user_id=user_id,
            created_by_agent_id=ceo_agent.id if ceo_agent else None,
            assigned_to_agent_id=ceo_agent.id if ceo_agent else None,
            department_id=None,
            status="ASSIGNED" if ceo_agent else "CREATED",
            priority=plan.priority,
        )
        self.db.add(parent_task)
        await self.db.flush()

        # 5. Load company departments and active agents for step assignment resolution
        dept_res = await self.db.execute(
            select(Department).where(Department.company_id == company_id)
        )
        dept_map: dict[str, str] = {d.code.lower(): d.id for d in dept_res.scalars().all()}

        agent_res = await self.db.execute(
            select(Agent).where(Agent.company_id == company_id, Agent.status == "active")
        )
        agents = agent_res.scalars().all()
        agents_by_id: dict[str, Agent] = {a.id: a for a in agents}

        # 6. Create Multiple Child Tasks and Delegation Records
        step_task_map: dict[str, Task] = {}
        child_tasks: list[Task] = []
        delegations: list[DelegationRecord] = []

        for step in plan.plan_steps:
            step_id = step.get("step_id", str(uuid.uuid4()))
            step_title = step.get("title", "Untitled Task")
            step_desc = step.get("description", "")
            step_output = step.get("expected_output", "")
            dept_code = (step.get("department_code") or "").lower()
            dept_id = dept_map.get(dept_code)

            # Resolve assigned agent
            assigned_agent: Agent | None = None
            raw_agent_id = step.get("assigned_agent_id")
            if raw_agent_id and raw_agent_id in agents_by_id:
                assigned_agent = agents_by_id[raw_agent_id]
            else:
                # Fallback match by department or role
                role_target = (step.get("assigned_agent_role") or "").lower()
                for ag in agents:
                    if role_target and (
                        role_target in ag.role.lower() or role_target in ag.name.lower()
                    ):
                        assigned_agent = ag
                        break
                if not assigned_agent and dept_id:
                    # Match department lead or first agent in department
                    for ag in agents:
                        if ag.department_id == dept_id:
                            assigned_agent = ag
                            break

            child_task = Task(
                id=str(uuid.uuid4()),
                company_id=company_id,
                project_id=project.id,
                parent_task_id=parent_task.id,
                title=step_title,
                description=step_desc,
                objective=step_output,
                created_by_user_id=user_id,
                created_by_agent_id=ceo_agent.id if ceo_agent else None,
                assigned_to_agent_id=assigned_agent.id if assigned_agent else None,
                department_id=dept_id or (assigned_agent.department_id if assigned_agent else None),
                status="ASSIGNED" if assigned_agent else "READY",
                priority=plan.priority,
            )
            self.db.add(child_task)
            await self.db.flush()

            step_task_map[step_id] = child_task
            child_tasks.append(child_task)

            # Record delegation from CEO/User to assigned agent
            if assigned_agent:
                delegation = DelegationRecord(
                    id=str(uuid.uuid4()),
                    company_id=company_id,
                    task_id=child_task.id,
                    delegated_by_user_id=user_id if ceo_agent is None else None,
                    delegated_by_agent_id=ceo_agent.id if ceo_agent else None,
                    delegated_to_agent_id=assigned_agent.id,
                    scope=step.get("verification_criteria"),
                    reason=f"Delegated from CEO for plan step: {step_title}",
                    depth=1,
                    status="active",
                )
                self.db.add(delegation)
                delegations.append(delegation)

        # 7. Link Task Dependencies from plan DAG
        dependencies: list[TaskDependency] = []
        for step in plan.plan_steps:
            raw_step_id = step.get("step_id")
            if not raw_step_id or not isinstance(raw_step_id, str):
                continue
            current_task = step_task_map.get(raw_step_id)
            if not current_task:
                continue

            for dep_step_id in step.get("depends_on", []):
                if not dep_step_id or not isinstance(dep_step_id, str):
                    continue
                dep_task = step_task_map.get(dep_step_id)
                if dep_task and dep_task.id != current_task.id:
                    dep_link = TaskDependency(
                        id=str(uuid.uuid4()),
                        company_id=company_id,
                        task_id=current_task.id,
                        depends_on_task_id=dep_task.id,
                    )
                    self.db.add(dep_link)
                    dependencies.append(dep_link)

        # 8. Update CeoPlan status and reference
        plan.status = "delegated"
        plan.project_id = project.id

        await self.db.commit()
        await self.db.refresh(plan)

        return {
            "plan_id": plan.id,
            "project_id": project.id,
            "project_name": project.name,
            "parent_task_id": parent_task.id,
            "parent_task_title": parent_task.title,
            "child_tasks_count": len(child_tasks),
            "child_task_ids": [t.id for t in child_tasks],
            "dependencies_count": len(dependencies),
            "delegations_count": len(delegations),
        }
