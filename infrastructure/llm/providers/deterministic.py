"""Deterministic planning provider for offline execution, testing, and CI/CD."""

import uuid
from typing import Any

from domain.runtime.schemas import (
    AgentExecutionContext,
    Deliverable,
    ExecutionResult,
    ExecutionStep,
    RuntimeLimits,
)
from infrastructure.llm.providers.base import BaseLLMProvider
from orchestration.planner.schemas import (
    ApprovalRequirement,
    DelegationProposal,
    GoalIntake,
    PlanResult,
    PlanStep,
)


class DeterministicPlannerProvider(BaseLLMProvider):
    """Deterministic planning provider that maps company context to a structured plan."""

    async def generate_plan(
        self,
        goal: GoalIntake,
        context: dict[str, Any],
    ) -> PlanResult:
        agents: list[dict[str, Any]] = context.get("agents", [])
        company_name = context.get("company", {}).get("name", "Company")

        # Map available agents by role and department
        agents_by_role: dict[str, dict[str, Any]] = {}
        for ag in agents:
            r = ag.get("role", "").lower().strip()
            n = ag.get("name", "").lower().strip()
            agents_by_role[r] = ag
            if "chief executive officer" in r or n == "ceo":
                agents_by_role["ceo"] = ag
            if "chief marketing officer" in r or n == "cmo":
                agents_by_role["cmo"] = ag
            if "chief technology officer" in r or n == "cto":
                agents_by_role["cto"] = ag
            if "sales director" in r or "sales" in r:
                agents_by_role["sales_director"] = ag
            if "software architect" in r:
                agents_by_role["software_architect"] = ag
            if "lead researcher" in r or "researcher" in r:
                agents_by_role["lead_researcher"] = ag

        # Resolve primary stakeholders
        ceo_agent = agents_by_role.get("ceo")
        cmo_agent = agents_by_role.get("cmo")
        cto_agent = agents_by_role.get("cto")
        sales_agent = agents_by_role.get("sales_director") or agents_by_role.get("sales")
        architect_agent = agents_by_role.get("software_architect")
        researcher_agent = agents_by_role.get("lead_researcher")

        ceo_id = ceo_agent["id"] if ceo_agent else None
        objective = goal.objective.strip()

        # Step 1: Initial Discovery & Market / Problem Analysis
        step_1_agent = researcher_agent or cmo_agent or ceo_agent or (agents[0] if agents else None)
        step_1_id = "step_1"
        step_1 = PlanStep(
            step_id=step_1_id,
            title="Discovery & Requirements Analysis",
            description=f"Analyze strategic requirements, market factors, and user constraints for objective: '{objective}'.",
            assigned_agent_id=step_1_agent["id"] if step_1_agent else None,
            assigned_agent_role=step_1_agent["role"] if step_1_agent else "analyst",
            department_code=step_1_agent.get("department_code") if step_1_agent else None,
            depends_on=[],
            required_capabilities=["research", "analysis"],
            expected_output="Comprehensive requirements brief and discovery report.",
            verification_criteria="Deliverable covers market sizing, user personas, and regulatory constraints.",
        )

        # Step 2: Technical & Architectural Assessment
        step_2_agent = architect_agent or cto_agent or ceo_agent or (agents[0] if agents else None)
        step_2_id = "step_2"
        step_2 = PlanStep(
            step_id=step_2_id,
            title="Technical & Architectural Feasibility",
            description="Evaluate architectural feasibility, infrastructure dependencies, and system integration points.",
            assigned_agent_id=step_2_agent["id"] if step_2_agent else None,
            assigned_agent_role=step_2_agent["role"] if step_2_agent else "architect",
            department_code=step_2_agent.get("department_code") if step_2_agent else None,
            depends_on=[step_1_id],
            required_capabilities=["system_architecture", "technical_review"],
            expected_output="Technical feasibility assessment and component architecture spec.",
            verification_criteria="Architecture spec defines data flows, security controls, and scaling limits.",
        )

        # Step 3: Go-to-Market & Commercial Strategy
        step_3_agent = sales_agent or cmo_agent or ceo_agent or (agents[0] if agents else None)
        step_3_id = "step_3"
        step_3 = PlanStep(
            step_id=step_3_id,
            title="Go-To-Market & Commercial Strategy",
            description="Formulate commercial positioning, channel distribution, and customer acquisition model.",
            assigned_agent_id=step_3_agent["id"] if step_3_agent else None,
            assigned_agent_role=step_3_agent["role"] if step_3_agent else "sales",
            department_code=step_3_agent.get("department_code") if step_3_agent else None,
            depends_on=[step_1_id],
            required_capabilities=["commercial_strategy", "outreach"],
            expected_output="GTM strategy document with distribution milestones.",
            verification_criteria="Strategy includes unit economics, pricing proposals, and target metrics.",
        )

        # Step 4: Executive Review & Final Recommendation
        step_4_agent = ceo_agent or (agents[0] if agents else None)
        step_4_id = "step_4"
        step_4 = PlanStep(
            step_id=step_4_id,
            title="Executive Review & Governance Recommendation",
            description="Synthesize research and technical findings into an executive recommendation for leadership approval.",
            assigned_agent_id=step_4_agent["id"] if step_4_agent else None,
            assigned_agent_role=step_4_agent["role"] if step_4_agent else "ceo",
            department_code=step_4_agent.get("department_code") if step_4_agent else None,
            depends_on=[step_2_id, step_3_id],
            required_capabilities=["executive_orchestration", "risk_evaluation"],
            expected_output="Executive synthesis package with risk score and decision matrix.",
            verification_criteria="Synthesis reconciles technical and commercial streams for owner sign-off.",
        )

        steps = [step_1, step_2, step_3, step_4]

        # Generate Delegation Proposals from steps
        delegations: list[DelegationProposal] = []
        for step in steps:
            if step.assigned_agent_id and step.assigned_agent_id != ceo_id:
                delegations.append(
                    DelegationProposal(
                        proposal_id=f"prop_{uuid.uuid4().hex[:8]}",
                        source_agent_id=ceo_id,
                        target_agent_id=step.assigned_agent_id,
                        target_role=step.assigned_agent_role,
                        objective=step.title,
                        scope=step.description,
                        expected_output=step.expected_output,
                        required_capabilities=step.required_capabilities,
                        constraints=goal.constraints,
                        authority_level_required=2 if step.step_id != "step_4" else 4,
                    )
                )

        # Generate Approval Requirements
        approvals = [
            ApprovalRequirement(
                step_id=step_4_id,
                action_description="Authorization to transition from proposed plan to Phase 6 task execution.",
                risk_level="high" if goal.priority in ("high", "critical") else "medium",
                reason_for_approval="Governance policy dictates that human executive review is required before task dispatch.",
            )
        ]

        risks = [
            {
                "risk": "Cross-functional dependency delay between discovery and technical architecture.",
                "mitigation": "Parallelize discovery and architecture exploration where requirements overlap.",
                "severity": "medium",
            },
            {
                "risk": "Regulatory or regional compliance divergence.",
                "mitigation": "Include compliance gate in Step 1 requirements discovery.",
                "severity": "high"
                if "germany" in objective.lower() or "europe" in objective.lower()
                else "low",
            },
        ]

        assumptions = [
            f"Active organization state for {company_name} remains authoritative throughout plan lifecycle.",
            "Specialist agents are registered and available to receive delegated scopes once Phase 6 activates.",
            "All actions remain in PROPOSAL state until explicit human governance authorization.",
        ]

        reasoning = (
            f"Decomposed goal '{objective}' into a 4-stage sequential/parallel execution DAG. "
            f"Stage 1 establishes the discovery baseline. Stages 2 and 3 evaluate technical architecture "
            f"and commercial strategy concurrently. Stage 4 converges all streams into an executive decision package."
        )

        return PlanResult(
            goal=objective,
            reasoning_summary=reasoning,
            steps=steps,
            delegation_proposals=delegations,
            approval_requirements=approvals,
            risks=risks,
            assumptions=assumptions,
        )

    async def execute_task(
        self,
        context: AgentExecutionContext,
        limits: RuntimeLimits,
    ) -> ExecutionResult:
        """Execute a specialist agent task deterministically with rich role-specific output."""
        role = (context.agent_role or "").lower()
        title = context.task_title
        objective = context.task_objective or "Fulfill specified task requirements"
        desc = context.task_description or ""

        # Construct role-specific deliverables
        deliverable_content: str
        deliverable_format: str = "markdown"

        if "backend" in role:
            deliverable_format = "python"
            deliverable_content = (
                f"# Implementation for: {title}\n"
                f'"""Objective: {objective}\n'
                f"Generated by: {context.agent_name} ({context.agent_role})\n"
                f'"""\n\n'
                f"import logging\n"
                f"from typing import Any\n\n"
                f"logger = logging.getLogger(__name__)\n\n"
                f"class TaskHandler:\n"
                f'    """Executable handler addressing {title}."""\n\n'
                f"    def __init__(self, config: dict[str, Any] | None = None) -> None:\n"
                f"        self.config = config or {{}}\n\n"
                f"    async def execute(self) -> dict[str, Any]:\n"
                f'        logger.info("Executing {title} under {context.company_name}")\n'
                f"        return {{\n"
                f'            "status": "success",\n'
                f'            "task": "{title}",\n'
                f'            "objective": "{objective}",\n'
                f'            "details": "{desc[:100]}",\n'
                f"        }}\n"
            )
        elif "frontend" in role:
            deliverable_format = "typescript"
            deliverable_content = (
                f"// UI Component for: {title}\n"
                f"// Objective: {objective}\n"
                f"// Assigned: {context.agent_name}\n\n"
                f'import React from "react";\n\n'
                f"export function TaskView() {{\n"
                f"  return (\n"
                f'    <div className="p-4 bg-zinc-900 border border-zinc-800 rounded-xl">\n'
                f'      <h2 className="text-lg font-bold text-zinc-100">{title}</h2>\n'
                f'      <p className="text-sm text-zinc-400 mt-1">{objective}</p>\n'
                f"    </div>\n"
                f"  );\n"
                f"}}\n"
            )
        elif "qa" in role:
            deliverable_content = (
                f"# Verification Test Plan: {title}\n\n"
                f"**Target Objective**: {objective}\n"
                f"**Quality Assurance Lead**: {context.agent_name}\n\n"
                f"## 1. Test Matrix\n"
                f"- [x] **Unit Verification**: Validate core input contracts and edge boundary cases.\n"
                f"- [x] **Integration Verification**: Verify multi-tenant isolation and database foreign keys.\n"
                f"- [x] **Safety Verification**: Verify zero unhandled exceptions and adherence to SLA.\n\n"
                f"## 2. Assertion Results\n"
                f"- All unit assertions: **PASSED** (100% test scenario coverage)\n"
                f"- Regression risk: **NONE DETECTED**\n"
            )
        elif "devops" in role or "infra" in role:
            deliverable_format = "yaml"
            deliverable_content = (
                f"# Infrastructure & Deployment Specification\n"
                f"# Task: {title}\n"
                f"# Operator: {context.agent_name}\n"
                f"version: '3.8'\n"
                f"services:\n"
                f"  task-runner:\n"
                f"    image: runtime-executor:latest\n"
                f"    environment:\n"
                f"      - TASK_ID={context.task_id}\n"
                f"      - COMPANY={context.company_name}\n"
                f"    restart: unless-stopped\n"
            )
        elif "architect" in role or "cto" in role:
            deliverable_content = (
                f"# Technical Architecture Specification: {title}\n\n"
                f"**Objective**: {objective}\n"
                f"**Executive Author**: {context.agent_name} ({context.agent_role})\n"
                f"**Company**: {context.company_name}\n\n"
                f"## 1. System Overview\n"
                f"Architectural design and component topology to fulfill the stated objective.\n\n"
                f"## 2. Key Decisions & Trade-offs\n"
                f"- **Data Integrity**: Enforce strict relational schemas with cascading constraints.\n"
                f"- **Scalability**: Decouple domain services from delivery mechanisms.\n"
                f"- **Security**: Multi-tenant isolation verified server-side on every request.\n\n"
                f"## 3. Implementation Blueprint\n"
                f"1. Database models & schema migration\n"
                f"2. Domain boundary & state transition enforcement\n"
                f"3. Application service orchestration\n"
                f"4. REST API contract & client integration\n"
            )
        elif "marketing" in role or "cmo" in role or "content" in role:
            deliverable_content = (
                f"# Strategic Marketing & Growth Deliverable: {title}\n\n"
                f"**Target Objective**: {objective}\n"
                f"**Prepared By**: {context.agent_name}\n\n"
                f"## 1. Executive Positioning\n"
                f"Key value proposition and competitive differentiation for {context.company_name}.\n\n"
                f"## 2. Campaign Strategy & Channels\n"
                f"- **Primary Channel**: Direct outbound to enterprise AI operators.\n"
                f"- **Content Pillar**: Authoritative technical benchmarks and case studies.\n"
                f"- **Conversion Metric**: Qualified evaluation pipeline growth.\n"
            )
        elif "sales" in role:
            deliverable_content = (
                f"# Commercial Enablement Playbook: {title}\n\n"
                f"**Objective**: {objective}\n"
                f"**Sales Lead**: {context.agent_name}\n\n"
                f"## 1. ICP Definition & Criteria\n"
                f"Targeting companies requiring verifiable multi-agent governance and deterministic state management.\n\n"
                f"## 2. Discovery Framework\n"
                f"1. What is the current failure rate of unconstrained agent loops?\n"
                f"2. How are task dependencies and delegation audits tracked?\n"
            )
        elif "finance" in role:
            deliverable_content = (
                f"# Financial Model & Feasibility Assessment: {title}\n\n"
                f"**Objective**: {objective}\n"
                f"**Analyst**: {context.agent_name}\n\n"
                f"## 1. Unit Economics\n"
                f"- Token cost per task execution: ~$0.0025\n"
                f"- Gross margin on managed autonomous services: >82%\n"
                f"- Payback period: < 3.2 months\n"
            )
        else:
            deliverable_content = (
                f"# Operational Deliverable: {title}\n\n"
                f"**Objective**: {objective}\n"
                f"**Author**: {context.agent_name} ({context.agent_role})\n\n"
                f"## Executive Summary\n"
                f"Comprehensive work product fulfilling the directives of task {title}. "
                f"All requirements have been addressed and verified against company standards.\n"
            )

        steps = [
            ExecutionStep(
                step_number=1,
                thought=f"Reviewing task objective '{objective}' and {context.company_name} context.",
                action_type="ANALYZE",
                observation="Context and requirements loaded successfully. Dependencies verified.",
            ),
            ExecutionStep(
                step_number=2,
                thought=f"Formulating domain-specific solution according to role {context.agent_role}.",
                action_type="DRAFT",
                observation="Structure drafted and aligned with quality and security boundaries.",
            ),
            ExecutionStep(
                step_number=3,
                thought="Generating full deliverable and technical work product.",
                action_type="IMPLEMENT",
                observation="Deliverable produced without errors.",
            ),
            ExecutionStep(
                step_number=4,
                thought="Evaluating deliverable against initial objective and requirements.",
                action_type="VERIFY",
                observation="Deliverable meets all verifiable criteria. Ready for verification.",
            ),
        ]

        # Respect max_steps limit if configured smaller
        if limits.max_steps < len(steps):
            steps = steps[: limits.max_steps]

        tokens_estimate = min(1200 + len(title) * 8, limits.max_tokens)
        cost_estimate = round(tokens_estimate * 0.000002, 6)

        deliverable = Deliverable(
            title=title,
            format=deliverable_format,
            content=deliverable_content,
            summary=f"Successfully fulfilled objective '{objective}' with structured {deliverable_format} deliverable.",
        )

        return ExecutionResult(
            status="SUCCESS",
            summary=f"Task '{title}' executed by {context.agent_name} ({context.agent_role}). Deliverable ready for verification.",
            deliverable=deliverable,
            steps=steps,
            self_assessment_score=0.96,
            verification_notes="Deliverable complete and verified against task objective. Awaiting operator sign-off.",
            step_count=len(steps),
            tokens_used=tokens_estimate,
            estimated_cost=cost_estimate,
        )
