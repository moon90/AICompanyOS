"""Unit tests for Grounded Context Retrieval and Operational State Memory."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.memory_service import MemoryService
from domain.memory.context_retriever import (
    build_grounded_company_prompt,
    synthesize_task_context,
)
from domain.memory.schemas import CompanyContextPacket, CompanyDecisionCreate
from infrastructure.database.base import Base
from infrastructure.database.models import (
    Agent,
    ApprovalRequest,
    Company,
    CompanyMember,
    Department,
    Project,
    Task,
    User,
)


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an in-memory SQLite async database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def seeded_company_environment(async_session: AsyncSession) -> dict[str, str]:
    """Seed comprehensive company environment across departments, agents, projects, tasks, approvals."""
    user = User(
        id=str(uuid.uuid4()),
        name="Founder",
        email="founder@innovate.co",
        password_hash="hash",
        status="active",
    )
    company = Company(
        id=str(uuid.uuid4()),
        name="Hyperion Dynamics",
        mission="Autonomous logistics orchestration",
        description="Next-gen AI operations platform",
    )
    member = CompanyMember(
        id=str(uuid.uuid4()),
        company_id=company.id,
        user_id=user.id,
        role="owner",
        status="active",
    )
    department = Department(
        id=str(uuid.uuid4()),
        company_id=company.id,
        name="Core Infrastructure",
        code="INFRA",
        description="Scalable cloud architectures",
    )
    agent = Agent(
        id=str(uuid.uuid4()),
        company_id=company.id,
        department_id=department.id,
        name="Architect Agent",
        role="System Architect",
        status="active",
        authority_level="specialist",
    )
    project = Project(
        id=str(uuid.uuid4()),
        company_id=company.id,
        name="Project Hyperdrive",
        description="Ultra-fast event routing",
        objective="Process 1M events per second",
        status="ACTIVE",
        priority="high",
    )
    task1 = Task(
        id=str(uuid.uuid4()),
        company_id=company.id,
        project_id=project.id,
        title="Setup Kafka Partitioning",
        description="Configure 32 partitions per topic",
        status="IN_PROGRESS",
        priority="high",
    )
    task2 = Task(
        id=str(uuid.uuid4()),
        company_id=company.id,
        project_id=project.id,
        title="Benchmark Ingestion Speed",
        description="Verify 1M req/s throughput",
        status="READY",
        priority="medium",
    )
    approval = ApprovalRequest(
        id=str(uuid.uuid4()),
        company_id=company.id,
        task_id=task1.id,
        agent_id=agent.id,
        action_type="DEPLOY_PRODUCTION",
        description="Deploy Kafka broker cluster",
        payload={"nodes": 5},
        risk_level="HIGH",
        status="PENDING",
    )

    async_session.add_all(
        [user, company, member, department, agent, project, task1, task2, approval]
    )
    await async_session.commit()

    return {
        "user_id": user.id,
        "company_id": company.id,
        "department_id": department.id,
        "agent_id": agent.id,
        "project_id": project.id,
        "task1_id": task1.id,
    }


def test_build_grounded_company_prompt_structure() -> None:
    """Verify context formatting produces correct sections and details."""
    packet = CompanyContextPacket(
        company={"id": "comp-1", "name": "OmniCorp", "mission": "Automate everything"},
        departments=[{"id": "dept-1", "name": "AI Lab"}],
        agents=[
            {"id": "agent-1", "name": "Synthetica", "role": "Researcher", "system_status": "IDLE"}
        ],
        projects=[
            {
                "id": "proj-1",
                "name": "Project Alpha",
                "status": "ACTIVE",
                "priority": "high",
                "objective": "AGI",
            }
        ],
        tasks_summary={"total": 5, "by_status": {"READY": 2, "IN_PROGRESS": 3}},
        recent_approvals=[],
        decisions=[
            {
                "id": "dec-1",
                "title": "Use Rust",
                "decision": "Rewriting in Rust",
                "status": "ACTIVE",
            }
        ],
        generated_at=datetime.now(UTC),
    )

    prompt = build_grounded_company_prompt(packet)
    assert "# Authoritative Company State: OmniCorp" in prompt
    assert "## Departments" in prompt
    assert "AI Lab" in prompt
    assert "Synthetica | Role: Researcher" in prompt
    assert "Project Alpha | Status: ACTIVE" in prompt
    assert "Total Tasks: 5" in prompt
    assert "Use Rust: Rewriting in Rust" in prompt


def test_synthesize_task_context_structure() -> None:
    """Verify task context synthesis correctly embeds task, project, and decisions."""
    prompt = synthesize_task_context(
        task={
            "id": "t-1",
            "title": "Build Cache",
            "status": "IN_PROGRESS",
            "priority": "high",
            "description": "Redis cluster",
        },
        project={"id": "p-1", "name": "Cloud Infra", "status": "ACTIVE"},
        company={"id": "c-1", "name": "Apex Corp"},
        decisions=[
            {
                "title": "Zero Eviction Policy",
                "decision": "Never evict keys",
                "rationale": "Data safety",
            }
        ],
        execution_history=[{"id": "exec-1", "status": "FAILED", "agent_id": "agent-7"}],
    )

    assert "# Task Context: Build Cache" in prompt
    assert "Project: Cloud Infra" in prompt
    assert "Redis cluster" in prompt
    assert "Zero Eviction Policy: Never evict keys" in prompt
    assert "Execution exec-1: Status FAILED" in prompt


@pytest.mark.asyncio
async def test_get_company_state_aggregates_operational_memory(
    async_session: AsyncSession,
    seeded_company_environment: dict[str, str],
) -> None:
    """Verify MemoryService.get_company_state queries all relevant tables and returns a populated packet."""
    service = MemoryService(db=async_session)

    # Record a decision first
    await service.record_decision(
        company_id=seeded_company_environment["company_id"],
        user_id=seeded_company_environment["user_id"],
        data=CompanyDecisionCreate(
            title="Deploy on AWS EKS",
            decision="All container workloads deployed on managed Kubernetes.",
            rationale="Automated autoscaling and security isolation.",
        ),
    )

    packet = await service.get_company_state(
        company_id=seeded_company_environment["company_id"],
        user_id=seeded_company_environment["user_id"],
    )

    assert packet.company["name"] == "Hyperion Dynamics"
    assert len(packet.departments) == 1
    assert packet.departments[0]["name"] == "Core Infrastructure"
    assert len(packet.agents) == 1
    assert packet.agents[0]["name"] == "Architect Agent"
    assert len(packet.projects) == 1
    assert packet.projects[0]["name"] == "Project Hyperdrive"
    assert packet.tasks_summary["total"] == 2
    assert len(packet.recent_approvals) == 1
    assert packet.recent_approvals[0]["action_type"] == "DEPLOY_PRODUCTION"
    assert len(packet.decisions) == 1
    assert packet.decisions[0]["title"] == "Deploy on AWS EKS"


@pytest.mark.asyncio
async def test_get_context_for_task(
    async_session: AsyncSession,
    seeded_company_environment: dict[str, str],
) -> None:
    """Verify MemoryService.get_context_for_task returns scoped task bundle and synthesized prompt."""
    service = MemoryService(db=async_session)

    ctx = await service.get_context_for_task(
        company_id=seeded_company_environment["company_id"],
        user_id=seeded_company_environment["user_id"],
        task_id=seeded_company_environment["task1_id"],
    )

    assert ctx["task"]["title"] == "Setup Kafka Partitioning"
    assert ctx["project"]["name"] == "Project Hyperdrive"
    assert ctx["company"]["name"] == "Hyperion Dynamics"
    assert "Setup Kafka Partitioning" in ctx["synthesized_prompt"]
