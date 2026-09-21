"""Deterministic planning provider for offline execution, testing, and CI/CD."""

import uuid
from typing import Any

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
