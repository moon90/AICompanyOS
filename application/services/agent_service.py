"""Application service for Agent Registry management and organizational hierarchy."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.agents.exceptions import (
    AgentAccessDeniedError,
    AgentNotFoundError,
    DuplicateAgentVersionError,
    InvalidAgentDataError,
    InvalidAgentDepartmentError,
    InvalidAgentHierarchyError,
)
from infrastructure.database.models import (
    Agent,
    AgentDefinition,
    CompanyMember,
    Department,
)

_UNSET: Any = object()


class AgentService:
    """Service handling Agent Registry, definitions, and organizational reporting relationships."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _verify_membership(
        self,
        company_id: str,
        user_id: str,
        require_manage: bool = False,
    ) -> CompanyMember:
        """Verify user membership in company and check authorization."""
        stmt = select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        member = result.scalar_one_or_none()
        if not member:
            raise AgentAccessDeniedError(
                "User does not have access to this company's agent registry."
            )

        if require_manage and member.role not in ("owner", "admin"):
            raise AgentAccessDeniedError(
                "Insufficient permissions to manage agents in this company."
            )

        return member

    async def _validate_department(self, company_id: str, department_id: str | None) -> None:
        """Validate that department exists and belongs to the company."""
        if not department_id:
            return

        stmt = select(Department).where(Department.id == department_id)
        result = await self.session.execute(stmt)
        dept = result.scalar_one_or_none()
        if not dept or dept.company_id != company_id:
            raise InvalidAgentDepartmentError(
                "Department does not exist or belongs to another company."
            )

    async def _validate_manager(
        self,
        company_id: str,
        agent_id: str | None,
        manager_id: str | None,
    ) -> None:
        """Validate manager belongs to company, is not self, and avoids circular hierarchy cycles."""
        if not manager_id:
            return

        if agent_id is not None and manager_id == agent_id:
            raise InvalidAgentHierarchyError("An agent cannot report to itself.")

        manager_stmt = select(Agent).where(Agent.id == manager_id)
        manager_res = await self.session.execute(manager_stmt)
        manager = manager_res.scalar_one_or_none()

        if not manager or manager.company_id != company_id:
            raise InvalidAgentHierarchyError(
                "Reporting manager does not exist or belongs to another company."
            )

        # Cycle detection: traverse ancestors of proposed manager to verify agent_id is not among them
        if agent_id is not None:
            curr_id: str | None = manager_id
            visited: set[str] = {agent_id}
            while curr_id is not None:
                if curr_id in visited:
                    raise InvalidAgentHierarchyError(
                        "Circular reporting relationship detected in agent hierarchy."
                    )
                visited.add(curr_id)
                curr_agent = await self.session.get(Agent, curr_id)
                curr_id = curr_agent.reports_to if curr_agent else None

    async def get_company_agents(
        self,
        company_id: str,
        user_id: str,
        department_id: str | None = None,
        status: str | None = None,
    ) -> list[Agent]:
        """List agents belonging to a company with their current definitions."""
        await self._verify_membership(company_id, user_id)

        stmt = (
            select(Agent)
            .options(
                selectinload(Agent.department),
                selectinload(Agent.manager),
                selectinload(Agent.definitions),
            )
            .where(Agent.company_id == company_id)
            .order_by(Agent.name)
        )

        if department_id:
            stmt = stmt.where(Agent.department_id == department_id)
        if status:
            stmt = stmt.where(Agent.status == status)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_agent(self, company_id: str, agent_id: str, user_id: str) -> Agent:
        """Retrieve single agent with department, manager, subordinates, and definitions."""
        await self._verify_membership(company_id, user_id)

        stmt = (
            select(Agent)
            .options(
                selectinload(Agent.department),
                selectinload(Agent.manager),
                selectinload(Agent.subordinates),
                selectinload(Agent.definitions),
            )
            .where(Agent.company_id == company_id, Agent.id == agent_id)
        )
        result = await self.session.execute(stmt)
        agent = result.scalar_one_or_none()
        if not agent:
            raise AgentNotFoundError(f"Agent with id {agent_id} not found.")

        return agent

    async def create_agent(
        self,
        company_id: str,
        user_id: str,
        name: str,
        role: str,
        type: str = "specialist",
        department_id: str | None = None,
        reports_to: str | None = None,
        mission: str | None = None,
        authority_level: str = "specialist",
        system_prompt: str | None = None,
        model: str = "gemini-1.5-pro",
        capabilities: list[str] | None = None,
        tools: list[str] | None = None,
        configuration: dict[str, Any] | None = None,
    ) -> Agent:
        """Register a new agent with an initial versioned definition (v1.0)."""
        await self._verify_membership(company_id, user_id, require_manage=True)

        name_clean = name.strip()
        role_clean = role.strip()
        if not name_clean:
            raise InvalidAgentDataError("Agent name cannot be empty.")
        if not role_clean:
            raise InvalidAgentDataError("Agent role cannot be empty.")

        await self._validate_department(company_id, department_id)
        await self._validate_manager(company_id, None, reports_to)

        agent = Agent(
            id=str(uuid.uuid4()),
            company_id=company_id,
            department_id=department_id,
            name=name_clean,
            role=role_clean,
            type=type,
            reports_to=reports_to,
            mission=mission.strip() if mission else None,
            status="active",
            authority_level=authority_level,
        )
        self.session.add(agent)
        await self.session.flush()

        # Create initial AgentDefinition v1.0 per Rule 129
        initial_def = AgentDefinition(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            version="1.0",
            system_prompt=system_prompt,
            model=model,
            capabilities=capabilities or [],
            tools=tools or [],
            configuration=configuration or {},
            is_current=True,
        )
        self.session.add(initial_def)
        await self.session.commit()

        return await self.get_agent(company_id, agent.id, user_id)

    async def update_agent(
        self,
        company_id: str,
        agent_id: str,
        user_id: str,
        name: str | None = None,
        role: str | None = None,
        type: str | None = None,
        department_id: Any = _UNSET,
        reports_to: Any = _UNSET,
        mission: str | None = None,
        status: str | None = None,
        authority_level: str | None = None,
    ) -> Agent:
        """Update agent metadata and reporting relationships."""
        await self._verify_membership(company_id, user_id, require_manage=True)
        agent = await self.get_agent(company_id, agent_id, user_id)

        if name is not None:
            name_clean = name.strip()
            if not name_clean:
                raise InvalidAgentDataError("Agent name cannot be empty.")
            agent.name = name_clean

        if role is not None:
            role_clean = role.strip()
            if not role_clean:
                raise InvalidAgentDataError("Agent role cannot be empty.")
            agent.role = role_clean

        if type is not None:
            agent.type = type

        if department_id is not _UNSET:
            await self._validate_department(company_id, department_id)
            agent.department_id = department_id

        if reports_to is not _UNSET:
            await self._validate_manager(company_id, agent.id, reports_to)
            agent.reports_to = reports_to

        if mission is not None:
            agent.mission = mission.strip() if mission else None

        if status is not None:
            if status not in ("active", "inactive", "archived"):
                raise InvalidAgentDataError("Status must be 'active', 'inactive', or 'archived'.")
            agent.status = status

        if authority_level is not None:
            agent.authority_level = authority_level

        await self.session.commit()
        return await self.get_agent(company_id, agent.id, user_id)

    async def create_agent_definition(
        self,
        company_id: str,
        agent_id: str,
        user_id: str,
        version: str,
        system_prompt: str | None = None,
        model: str = "gemini-1.5-pro",
        capabilities: list[str] | None = None,
        tools: list[str] | None = None,
        configuration: dict[str, Any] | None = None,
    ) -> AgentDefinition:
        """Create a new versioned definition for an agent, preserving definition history."""
        await self._verify_membership(company_id, user_id, require_manage=True)
        agent = await self.get_agent(company_id, agent_id, user_id)

        version_clean = version.strip()
        if not version_clean:
            raise InvalidAgentDataError("Version cannot be empty.")

        # Check for duplicate version on this agent
        stmt = select(AgentDefinition).where(
            AgentDefinition.agent_id == agent.id,
            AgentDefinition.version == version_clean,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            raise DuplicateAgentVersionError(
                f"Version {version_clean} already exists for this agent."
            )

        # Demote existing definitions to is_current = False
        update_stmt = select(AgentDefinition).where(AgentDefinition.agent_id == agent.id)
        current_defs = (await self.session.execute(update_stmt)).scalars().all()
        for d in current_defs:
            d.is_current = False

        new_def = AgentDefinition(
            id=str(uuid.uuid4()),
            agent_id=agent.id,
            version=version_clean,
            system_prompt=system_prompt,
            model=model,
            capabilities=capabilities or [],
            tools=tools or [],
            configuration=configuration or {},
            is_current=True,
        )
        self.session.add(new_def)
        await self.session.commit()
        await self.session.refresh(new_def)
        return new_def

    async def get_agent_definitions(
        self,
        company_id: str,
        agent_id: str,
        user_id: str,
    ) -> list[AgentDefinition]:
        """List all versioned definitions for an agent."""
        await self._verify_membership(company_id, user_id)
        agent = await self.get_agent(company_id, agent_id, user_id)

        stmt = (
            select(AgentDefinition)
            .where(AgentDefinition.agent_id == agent.id)
            .order_by(AgentDefinition.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def provision_default_agents(
        self,
        company_id: str,
        user_id: str,
    ) -> list[Agent]:
        """Provision the foundational 11 initial company agents per docs/Phases.md Section 8."""
        await self._verify_membership(company_id, user_id, require_manage=True)

        # Check if agents already exist
        existing = await self.get_company_agents(company_id, user_id)
        if existing:
            return existing

        dept_stmt = select(Department).where(Department.company_id == company_id)
        dept_res = await self.session.execute(dept_stmt)
        departments = {d.code.upper(): d.id for d in dept_res.scalars().all()}

        cto_id = departments.get("CTO")
        cmo_id = departments.get("CMO")
        sales_id = departments.get("SALES")

        # 1. CEO (Top of hierarchy, reports_to=None)
        ceo = Agent(
            id=str(uuid.uuid4()),
            company_id=company_id,
            department_id=None,
            name="CEO",
            role="Chief Executive Officer",
            type="executive",
            reports_to=None,
            mission="Lead overall company vision, strategic priorities, and autonomous executive coordination.",
            status="active",
            authority_level="executive",
        )
        self.session.add(ceo)
        await self.session.flush()

        # 2. Executive Assistant
        ea = Agent(
            id=str(uuid.uuid4()),
            company_id=company_id,
            department_id=None,
            name="Executive Assistant",
            role="Executive Assistant",
            type="specialist",
            reports_to=ceo.id,
            mission="Support executive schedule, meeting synthesis, and cross-department briefings.",
            status="active",
            authority_level="specialist",
        )
        self.session.add(ea)

        # 3. CTO (Reports to CEO)
        cto = Agent(
            id=str(uuid.uuid4()),
            company_id=company_id,
            department_id=cto_id,
            name="CTO",
            role="Chief Technology Officer",
            type="department_head",
            reports_to=ceo.id,
            mission="Direct software architecture, technical governance, and engineering execution.",
            status="active",
            authority_level="department",
        )
        self.session.add(cto)
        await self.session.flush()

        # 4. CTO Subordinates: Software Architect, Full Stack Engineer
        arch = Agent(
            id=str(uuid.uuid4()),
            company_id=company_id,
            department_id=cto_id,
            name="Software Architect",
            role="Software Architect",
            type="specialist",
            reports_to=cto.id,
            mission="Design scalable system components, database schemas, and API protocols.",
            status="active",
            authority_level="specialist",
        )
        fse = Agent(
            id=str(uuid.uuid4()),
            company_id=company_id,
            department_id=cto_id,
            name="Full Stack Engineer",
            role="Full Stack Engineer",
            type="specialist",
            reports_to=cto.id,
            mission="Implement backend microservices, web user interfaces, and integration tests.",
            status="active",
            authority_level="specialist",
        )
        self.session.add_all([arch, fse])

        # 5. CMO (Reports to CEO)
        cmo = Agent(
            id=str(uuid.uuid4()),
            company_id=company_id,
            department_id=cmo_id,
            name="CMO",
            role="Chief Marketing Officer",
            type="department_head",
            reports_to=ceo.id,
            mission="Lead brand awareness, customer acquisition campaigns, and market positioning.",
            status="active",
            authority_level="department",
        )
        self.session.add(cmo)
        await self.session.flush()

        # 6. CMO Subordinates: Marketing Strategist, Copywriter
        strat = Agent(
            id=str(uuid.uuid4()),
            company_id=company_id,
            department_id=cmo_id,
            name="Marketing Strategist",
            role="Marketing Strategist",
            type="specialist",
            reports_to=cmo.id,
            mission="Formulate targeted go-to-market strategies and competitive intelligence reports.",
            status="active",
            authority_level="specialist",
        )
        copy = Agent(
            id=str(uuid.uuid4()),
            company_id=company_id,
            department_id=cmo_id,
            name="Copywriter",
            role="Content & Copy Specialist",
            type="specialist",
            reports_to=cmo.id,
            mission="Draft compelling marketing copy, documentation, and external announcements.",
            status="active",
            authority_level="specialist",
        )
        self.session.add_all([strat, copy])

        # 7. Sales Director (Reports to CEO)
        sales_dir = Agent(
            id=str(uuid.uuid4()),
            company_id=company_id,
            department_id=sales_id,
            name="Sales Director",
            role="Head of Sales",
            type="department_head",
            reports_to=ceo.id,
            mission="Drive enterprise revenue growth, client acquisition, and pipeline management.",
            status="active",
            authority_level="department",
        )
        self.session.add(sales_dir)
        await self.session.flush()

        # 8. Sales Director Subordinates: Lead Researcher, Sales Analyst
        lead_res = Agent(
            id=str(uuid.uuid4()),
            company_id=company_id,
            department_id=sales_id,
            name="Lead Researcher",
            role="Market & Lead Researcher",
            type="specialist",
            reports_to=sales_dir.id,
            mission="Discover qualified enterprise prospects and profile account decision-makers.",
            status="active",
            authority_level="specialist",
        )
        sales_ana = Agent(
            id=str(uuid.uuid4()),
            company_id=company_id,
            department_id=sales_id,
            name="Sales Analyst",
            role="Sales Operations Analyst",
            type="specialist",
            reports_to=sales_dir.id,
            mission="Analyze pipeline conversion velocity, revenue forecasts, and deal performance.",
            status="active",
            authority_level="specialist",
        )
        self.session.add_all([lead_res, sales_ana])
        await self.session.flush()

        all_agents = [ceo, ea, cto, arch, fse, cmo, strat, copy, sales_dir, lead_res, sales_ana]

        # Add initial AgentDefinition (v1.0) for each agent
        for ag in all_agents:
            ag_def = AgentDefinition(
                id=str(uuid.uuid4()),
                agent_id=ag.id,
                version="1.0",
                system_prompt=f"You are the {ag.role} of the company. Mission: {ag.mission}",
                model="gemini-1.5-pro",
                capabilities=["domain_planning", "structured_reasoning"],
                tools=["web_search", "document_reader"],
                configuration={"temperature": 0.2},
                is_current=True,
            )
            self.session.add(ag_def)

        await self.session.commit()
        return await self.get_company_agents(company_id, user_id)
