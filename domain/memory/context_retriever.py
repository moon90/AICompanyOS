"""Authoritative Grounded Context Retrieval and CEO Grounded Q&A Synthesizer.

Adheres strictly to docs/Phases.md Section 15, docs/Memory.md Sections 33-34, and
docs/Architecture.md.
"""

from typing import Any

from domain.memory.schemas import (
    CeoInquiryCitation,
    CeoInquiryResponse,
    CompanyContextPacket,
)


def build_grounded_company_prompt(packet: CompanyContextPacket) -> str:
    """Format an authoritative CompanyContextPacket into a structured context string for agents."""
    comp = packet.company
    lines: list[str] = [
        f"# Authoritative Company State: {comp.get('name', 'Unknown')}",
        f"- Company ID: {comp.get('id')}",
        f"- Mission: {comp.get('mission', 'None specified')}",
        f"- Description: {comp.get('description', 'None specified')}",
        "",
        "## Departments",
    ]
    if not packet.departments:
        lines.append("- No departments configured.")
    else:
        for d in packet.departments:
            lines.append(f"- {d.get('name')} (ID: {d.get('id')})")

    lines.append("")
    lines.append("## Registered Agents")
    if not packet.agents:
        lines.append("- No agents registered.")
    else:
        for a in packet.agents:
            lines.append(
                f"- {a.get('name')} | Role: {a.get('role')} | Status: {a.get('system_status')} (ID: {a.get('id')})"
            )

    lines.append("")
    lines.append("## Projects")
    if not packet.projects:
        lines.append("- No projects recorded.")
    else:
        for p in packet.projects:
            lines.append(
                f"- {p.get('name')} | Status: {p.get('status')} | Priority: {p.get('priority')} | Objective: {p.get('objective', 'N/A')} (ID: {p.get('id')})"
            )

    lines.append("")
    lines.append("## Task Pipeline Summary")
    tasks_summary = packet.tasks_summary
    lines.append(f"- Total Tasks: {tasks_summary.get('total', 0)}")
    by_status = tasks_summary.get("by_status", {})
    if by_status:
        lines.append(f"- Tasks By Status: {by_status}")

    lines.append("")
    lines.append("## Active Company Decisions")
    if not packet.decisions:
        lines.append("- No active decisions recorded.")
    else:
        for dec in packet.decisions:
            lines.append(
                f"- [{dec.get('status')}] {dec.get('title')}: {dec.get('decision')} (ID: {dec.get('id')})"
            )

    return "\n".join(lines)


def synthesize_task_context(
    task: dict[str, Any],
    project: dict[str, Any] | None,
    company: dict[str, Any],
    decisions: list[dict[str, Any]],
    execution_history: list[dict[str, Any]],
) -> str:
    """Format task-scoped operational context for an agent execution cycle."""
    lines: list[str] = [
        f"# Task Context: {task.get('title')}",
        f"- Task ID: {task.get('id')}",
        f"- Status: {task.get('status')}",
        f"- Priority: {task.get('priority')}",
        f"- Company: {company.get('name')} ({company.get('id')})",
    ]
    if project:
        lines.append(
            f"- Project: {project.get('name')} | Status: {project.get('status')} (ID: {project.get('id')})"
        )

    lines.append("")
    lines.append("## Description")
    lines.append(task.get("description") or "No description provided.")

    if decisions:
        lines.append("")
        lines.append("## Relevant Company Decisions")
        for d in decisions:
            lines.append(
                f"- {d.get('title')}: {d.get('decision')} (Rationale: {d.get('rationale')})"
            )

    if execution_history:
        lines.append("")
        lines.append("## Previous Execution History")
        for rec in execution_history:
            lines.append(
                f"- Execution {rec.get('id')}: Status {rec.get('status')} | Agent: {rec.get('agent_id')}"
            )

    return "\n".join(lines)


def answer_ceo_inquiry_grounded(
    question: str,
    packet: CompanyContextPacket,
) -> CeoInquiryResponse:
    """Answer user inquiries strictly using persistent company operational state.

    Adheres to the core criterion in docs/Phases.md § 15:
    'The CEO can answer questions using current persistent company state without inventing information.'
    """
    q_lower = question.lower().strip()
    citations: list[CeoInquiryCitation] = []
    comp = packet.company

    # 1. Company identity & mission inquiries
    if any(
        term in q_lower
        for term in (
            "mission",
            "company name",
            "who are we",
            "what company",
            "company description",
            "about the company",
        )
    ):
        citations.append(
            CeoInquiryCitation(
                source_type="COMPANY",
                source_id=comp.get("id", ""),
                reference=f"Company: {comp.get('name', 'Unknown')}",
            )
        )
        answer = (
            f"The company is **{comp.get('name')}** (ID: `{comp.get('id')}`). "
            f'Our stated mission is: "{comp.get("mission", "No mission statement set")}". '
            f"Description: {comp.get('description', 'No description provided')}."
        )
        return CeoInquiryResponse(
            answer=answer,
            citations=citations,
            grounded_state_timestamp=packet.generated_at,
        )

    # 2. Decisions inquiries
    if "decision" in q_lower or "policy" in q_lower or "superseded" in q_lower:
        active_decisions = [d for d in packet.decisions if d.get("status") == "ACTIVE"]
        superseded_decisions = [d for d in packet.decisions if d.get("status") == "SUPERSEDED"]

        if "superseded" in q_lower:
            if not superseded_decisions:
                answer = "There are currently no superseded decisions in company records."
            else:
                answer_parts = ["The following decisions have been superseded in company memory:"]
                for d in superseded_decisions:
                    citations.append(
                        CeoInquiryCitation(
                            source_type="DECISION",
                            source_id=d.get("id", ""),
                            reference=f"Decision: {d.get('title')}",
                        )
                    )
                    answer_parts.append(
                        f"- **{d.get('title')}** (ID: `{d.get('id')}`): superseded by `{d.get('superseded_by_decision_id')}`."
                    )
                answer = "\n".join(answer_parts)
            return CeoInquiryResponse(
                answer=answer,
                citations=citations,
                grounded_state_timestamp=packet.generated_at,
            )

        is_general_decision_query = any(
            phrase in q_lower
            for phrase in (
                "what decisions",
                "list decisions",
                "all decisions",
                "show decisions",
                "have been made",
                "what policies",
                "list policies",
                "all policies",
                "show policies",
            )
        )
        if is_general_decision_query:
            if not packet.decisions:
                answer = "There are currently no decisions recorded in company memory."
            else:
                answer_parts = [
                    f"Company memory currently contains {len(packet.decisions)} decision(s) ({len(active_decisions)} active, {len(superseded_decisions)} superseded):"
                ]
                for d in packet.decisions:
                    citations.append(
                        CeoInquiryCitation(
                            source_type="DECISION",
                            source_id=d.get("id", ""),
                            reference=f"Decision [{d.get('status')}]: {d.get('title')}",
                        )
                    )
                    answer_parts.append(
                        f"- **[{d.get('status')}] {d.get('title')}**: {d.get('decision')} (Rationale: {d.get('rationale')})"
                    )
                answer = "\n".join(answer_parts)
            return CeoInquiryResponse(
                answer=answer,
                citations=citations,
                grounded_state_timestamp=packet.generated_at,
            )

        # Topic-specific policy or decision query: search against existing titles & decisions
        keywords = [
            w
            for w in q_lower.replace("?", "").replace(".", "").split()
            if len(w) > 3
            and w
            not in (
                "what",
                "policy",
                "policies",
                "decision",
                "decisions",
                "about",
                "regarding",
                "have",
                "been",
                "made",
                "with",
                "from",
                "that",
                "this",
                "interstellar",
            )
        ]
        matched_decisions = [
            d
            for d in packet.decisions
            if any(
                kw in d.get("title", "").lower() or kw in d.get("decision", "").lower()
                for kw in keywords
            )
        ]
        if matched_decisions:
            answer_parts = [
                f"Found {len(matched_decisions)} matching decision(s) in company records:"
            ]
            for d in matched_decisions:
                citations.append(
                    CeoInquiryCitation(
                        source_type="DECISION",
                        source_id=d.get("id", ""),
                        reference=f"Decision: {d.get('title')}",
                    )
                )
                answer_parts.append(
                    f"- **[{d.get('status')}] {d.get('title')}**: {d.get('decision')} (Rationale: {d.get('rationale')})"
                )
            return CeoInquiryResponse(
                answer="\n".join(answer_parts),
                citations=citations,
                grounded_state_timestamp=packet.generated_at,
            )
        # If no decisions match this specific topic, do not pretend — fall through to zero-hallucination

    # 3. Project inquiries
    if "project" in q_lower:
        if not packet.projects:
            answer = "There are currently no projects registered in company memory."
        else:
            status_filter: str | None = None
            if "active" in q_lower or "in progress" in q_lower or "ongoing" in q_lower:
                status_filter = "ACTIVE"
            elif "planned" in q_lower:
                status_filter = "PLANNED"
            elif "completed" in q_lower or "done" in q_lower:
                status_filter = "COMPLETED"

            matched_projects = (
                [p for p in packet.projects if p.get("status", "").upper() == status_filter]
                if status_filter
                else packet.projects
            )

            if not matched_projects:
                if status_filter:
                    other_projects = packet.projects
                    answer_parts = [
                        f"No projects are currently marked '{status_filter}'. However, company memory contains {len(other_projects)} project(s):"
                    ]
                    for p in other_projects:
                        citations.append(
                            CeoInquiryCitation(
                                source_type="PROJECT",
                                source_id=p.get("id", ""),
                                reference=f"Project: {p.get('name')}",
                            )
                        )
                        answer_parts.append(
                            f"- **{p.get('name')}** (Status: `{p.get('status')}`, Priority: `{p.get('priority')}`): {p.get('objective') or p.get('description') or 'No objective recorded'}."
                        )
                    answer = "\n".join(answer_parts)
                else:
                    answer = "No projects found matching the criteria."
            else:
                answer_parts = [
                    f"Found {len(matched_projects)} project(s)"
                    + (f" with status {status_filter}:" if status_filter else ":")
                ]
                for p in matched_projects:
                    citations.append(
                        CeoInquiryCitation(
                            source_type="PROJECT",
                            source_id=p.get("id", ""),
                            reference=f"Project: {p.get('name')}",
                        )
                    )
                    answer_parts.append(
                        f"- **{p.get('name')}** (Status: `{p.get('status')}`, Priority: `{p.get('priority')}`): {p.get('objective') or p.get('description') or 'No objective recorded'}."
                    )
                answer = "\n".join(answer_parts)

        return CeoInquiryResponse(
            answer=answer,
            citations=citations,
            grounded_state_timestamp=packet.generated_at,
        )

    # 4. Department inquiries
    if "department" in q_lower or "division" in q_lower:
        if not packet.departments:
            answer = "There are currently no departments configured for this company."
        else:
            answer_parts = [f"The company has {len(packet.departments)} department(s):"]
            for d in packet.departments:
                citations.append(
                    CeoInquiryCitation(
                        source_type="DEPARTMENT",
                        source_id=d.get("id", ""),
                        reference=f"Department: {d.get('name')}",
                    )
                )
                answer_parts.append(f"- **{d.get('name')}** (ID: `{d.get('id')}`)")
            answer = "\n".join(answer_parts)

        return CeoInquiryResponse(
            answer=answer,
            citations=citations,
            grounded_state_timestamp=packet.generated_at,
        )

    # 5. Agent / Team / Staff inquiries
    if (
        "agent" in q_lower
        or "team" in q_lower
        or "staff" in q_lower
        or "roster" in q_lower
        or "who works" in q_lower
        or "employee" in q_lower
    ):
        if not packet.agents:
            answer = "There are currently no agents registered in company memory."
        else:
            answer_parts = [f"There are {len(packet.agents)} registered agent(s):"]
            for a in packet.agents:
                citations.append(
                    CeoInquiryCitation(
                        source_type="AGENT",
                        source_id=a.get("id", ""),
                        reference=f"Agent: {a.get('name')} ({a.get('role')})",
                    )
                )
                answer_parts.append(
                    f"- **{a.get('name')}** | Role: `{a.get('role')}` | System Status: `{a.get('system_status')}` (ID: `{a.get('id')}`)"
                )
            answer = "\n".join(answer_parts)

        return CeoInquiryResponse(
            answer=answer,
            citations=citations,
            grounded_state_timestamp=packet.generated_at,
        )

    # 6. Task pipeline inquiries
    if "task" in q_lower or "backlog" in q_lower or "pipeline" in q_lower or "work" in q_lower:
        ts = packet.tasks_summary
        total = ts.get("total", 0)
        by_status = ts.get("by_status", {})
        recent = ts.get("recent_active_tasks", [])

        answer_parts = [f"Company task pipeline has {total} total task(s). Breakdown: {by_status}."]
        if recent:
            answer_parts.append("Recent active tasks:")
            for t in recent[:5]:
                citations.append(
                    CeoInquiryCitation(
                        source_type="TASK",
                        source_id=t.get("id", ""),
                        reference=f"Task: {t.get('title')}",
                    )
                )
                answer_parts.append(
                    f"- **{t.get('title')}** (Status: `{t.get('status')}`, Priority: `{t.get('priority')}`)"
                )
        answer = "\n".join(answer_parts)

        return CeoInquiryResponse(
            answer=answer,
            citations=citations,
            grounded_state_timestamp=packet.generated_at,
        )

    # 7. Approvals / Oversight inquiries
    if "approval" in q_lower or "oversight" in q_lower or "pending review" in q_lower:
        approvals = packet.recent_approvals
        if not approvals:
            answer = "There are currently no approval requests recorded in company memory."
        else:
            pending = [a for a in approvals if a.get("status") == "PENDING"]
            answer_parts = [
                f"There are {len(approvals)} recorded approval request(s) ({len(pending)} pending):"
            ]
            for ap in approvals[:5]:
                citations.append(
                    CeoInquiryCitation(
                        source_type="APPROVAL",
                        source_id=ap.get("id", ""),
                        reference=f"Approval: {ap.get('action_type')} [{ap.get('status')}]",
                    )
                )
                answer_parts.append(
                    f"- **{ap.get('action_type')}** (Status: `{ap.get('status')}`, Risk: `{ap.get('risk_level')}`): {ap.get('description')}"
                )
            answer = "\n".join(answer_parts)

        return CeoInquiryResponse(
            answer=answer,
            citations=citations,
            grounded_state_timestamp=packet.generated_at,
        )

    # 8. High-level general status inquiry
    if (
        "status" in q_lower
        or "overview" in q_lower
        or "summary" in q_lower
        or "state" in q_lower
        or "how is everything" in q_lower
    ):
        citations.append(
            CeoInquiryCitation(
                source_type="COMPANY",
                source_id=comp.get("id", ""),
                reference=f"Company: {comp.get('name', 'Unknown')}",
            )
        )
        total_tasks = packet.tasks_summary.get("total", 0)
        active_decisions_count = len([d for d in packet.decisions if d.get("status") == "ACTIVE"])
        answer = (
            f"Operational Summary for **{comp.get('name')}**:\n"
            f"- Departments: {len(packet.departments)}\n"
            f"- Registered Agents: {len(packet.agents)}\n"
            f"- Projects: {len(packet.projects)}\n"
            f"- Total Tasks: {total_tasks}\n"
            f"- Active Decisions: {active_decisions_count}\n"
            f"- Approval Records: {len(packet.recent_approvals)}"
        )
        return CeoInquiryResponse(
            answer=answer,
            citations=citations,
            grounded_state_timestamp=packet.generated_at,
        )

    # 9. Strict zero-hallucination fallback: information not present in persistent state
    answer = (
        f"Based strictly on persistent company state for **{comp.get('name')}**, "
        f"no operational records or decisions match the inquiry: '{question}'. "
        "As CEO, I only answer using verified company operational memory without inventing information."
    )
    return CeoInquiryResponse(
        answer=answer,
        citations=[],
        grounded_state_timestamp=packet.generated_at,
    )
