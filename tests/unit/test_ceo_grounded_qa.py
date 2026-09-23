"""Unit tests for Grounded CEO Q&A strictly adhering to docs/Phases.md § 15.

Acceptance Criterion:
'The CEO can answer questions using current persistent company state without inventing information.'
"""

from datetime import UTC, datetime

from domain.memory.context_retriever import answer_ceo_inquiry_grounded
from domain.memory.schemas import CompanyContextPacket


def build_sample_packet() -> CompanyContextPacket:
    """Build an authoritative sample company packet."""
    return CompanyContextPacket(
        company={
            "id": "comp-777",
            "name": "Aether Dynamics",
            "mission": "Deliver real-time conversational AI operating systems",
            "description": "Deep enterprise automation platform",
        },
        departments=[
            {"id": "dept-eng", "name": "Engineering"},
            {"id": "dept-ops", "name": "Operations"},
        ],
        agents=[
            {"id": "agent-ceo", "name": "Chief Executive", "role": "CEO", "system_status": "IDLE"},
            {
                "id": "agent-lead",
                "name": "Code Lead",
                "role": "Software Architect",
                "system_status": "IDLE",
            },
        ],
        projects=[
            {
                "id": "proj-apollo",
                "name": "Project Apollo",
                "status": "ACTIVE",
                "priority": "critical",
                "objective": "Launch core agent orchestration engine",
            },
            {
                "id": "proj-zeus",
                "name": "Project Zeus",
                "status": "PLANNED",
                "priority": "low",
                "objective": "Build quantum telemetry dashboard",
            },
        ],
        tasks_summary={
            "total": 3,
            "by_status": {"READY": 1, "IN_PROGRESS": 2},
            "recent_active_tasks": [
                {
                    "id": "task-101",
                    "title": "Implement Tool Gateway",
                    "status": "IN_PROGRESS",
                    "priority": "high",
                },
                {
                    "id": "task-102",
                    "title": "Setup PostgreSQL Memory",
                    "status": "IN_PROGRESS",
                    "priority": "critical",
                },
            ],
        },
        recent_approvals=[
            {
                "id": "appr-01",
                "action_type": "DEPLOY_PRODUCTION",
                "status": "PENDING",
                "risk_level": "HIGH",
                "description": "Deploy Gateway to production cluster",
            }
        ],
        decisions=[
            {
                "id": "dec-01",
                "title": "Immutable Decision Chaining",
                "decision": "All decisions use non-destructive supersedence.",
                "rationale": "Ensures complete compliance and provenance.",
                "status": "ACTIVE",
                "superseded_by_decision_id": None,
            },
            {
                "id": "dec-00",
                "title": "Original State Architecture",
                "decision": "Store state in text files.",
                "rationale": "Simplicity.",
                "status": "SUPERSEDED",
                "superseded_by_decision_id": "dec-01",
            },
        ],
        generated_at=datetime.now(UTC),
    )


def test_ceo_inquiry_company_mission() -> None:
    """Verify CEO accurately quotes company mission and identity from memory."""
    packet = build_sample_packet()
    res = answer_ceo_inquiry_grounded("What is our company mission?", packet)

    assert "Aether Dynamics" in res.answer
    assert "Deliver real-time conversational AI operating systems" in res.answer
    assert any(c.source_type == "COMPANY" for c in res.citations)


def test_ceo_inquiry_active_projects() -> None:
    """Verify CEO answers about projects using persistent records and citations."""
    packet = build_sample_packet()
    res = answer_ceo_inquiry_grounded("What active projects are we currently working on?", packet)

    assert "Project Apollo" in res.answer
    assert "Launch core agent orchestration engine" in res.answer
    assert any(c.source_type == "PROJECT" and c.source_id == "proj-apollo" for c in res.citations)


def test_ceo_inquiry_agents_roster() -> None:
    """Verify CEO answers team inquiries using the registered agents state."""
    packet = build_sample_packet()
    res = answer_ceo_inquiry_grounded("Who is on our agent team?", packet)

    assert "Chief Executive" in res.answer
    assert "Code Lead" in res.answer
    assert any(c.source_type == "AGENT" for c in res.citations)


def test_ceo_inquiry_decisions_and_supersedence() -> None:
    """Verify CEO accurately reports decisions and supersedence history."""
    packet = build_sample_packet()

    # Query all decisions
    res_dec = answer_ceo_inquiry_grounded("What decisions have been made?", packet)
    assert "Immutable Decision Chaining" in res_dec.answer
    assert any(c.source_type == "DECISION" for c in res_dec.citations)

    # Query specifically superseded decisions
    res_sup = answer_ceo_inquiry_grounded("Which decisions were superseded?", packet)
    assert "Original State Architecture" in res_sup.answer
    assert "superseded by `dec-01`" in res_sup.answer


def test_ceo_inquiry_tasks_and_approvals() -> None:
    """Verify CEO answers about task pipeline and pending human approvals."""
    packet = build_sample_packet()

    res_tasks = answer_ceo_inquiry_grounded("What is the status of our task pipeline?", packet)
    assert "Implement Tool Gateway" in res_tasks.answer
    assert any(c.source_type == "TASK" for c in res_tasks.citations)

    res_appr = answer_ceo_inquiry_grounded(
        "Do we have any pending approvals or oversight requests?", packet
    )
    assert "DEPLOY_PRODUCTION" in res_appr.answer
    assert any(c.source_type == "APPROVAL" for c in res_appr.citations)


def test_ceo_inquiry_zero_hallucination_on_unknown_topic() -> None:
    """Verify CEO strictly refuses to invent answers when information is not in memory."""
    packet = build_sample_packet()
    res = answer_ceo_inquiry_grounded(
        "What is our policy on interstellar warp drive travel?", packet
    )

    # CEO must not invent facts
    assert "no operational records or decisions match the inquiry" in res.answer
    assert "without inventing information" in res.answer
    assert len(res.citations) == 0
