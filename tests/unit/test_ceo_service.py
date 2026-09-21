"""Unit tests for CeoService orchestration, context assembly, and plan generation."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.agent_service import AgentService
from application.services.ceo_service import CeoService
from application.services.company_service import CompanyService
from domain.ceo.exceptions import (
    CeoAccessDeniedError,
    CeoNotFoundError,
    InvalidGoalError,
    PlanNotFoundError,
)
from infrastructure.database.base import Base
from infrastructure.database.models import User
from orchestration.planner.schemas import GoalIntake


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create in-memory SQLite database session for testing CeoService."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_ceo_resolution_and_missing_ceo(db_session: AsyncSession) -> None:
    """Verify CeoNotFoundError when CEO is not yet registered, and successful resolution once provisioned."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    ceo_service = CeoService(db_session)

    user = User(name="Founder", email="founder@apex.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Apex Innovations")

    # 1. Without CEO registered, resolution must fail
    with pytest.raises(CeoNotFoundError, match="No active CEO agent is registered"):
        await ceo_service.get_company_ceo(user_id=user.id, company_id=company.id)

    # 2. Provision default organization (includes CEO)
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)

    # 3. Resolution must now succeed
    ceo = await ceo_service.get_company_ceo(user_id=user.id, company_id=company.id)
    assert ceo is not None
    assert ceo.role == "Chief Executive Officer"
    assert ceo.name == "CEO"
    assert ceo.authority_level == "executive"


@pytest.mark.asyncio
async def test_ceo_context_assembly(db_session: AsyncSession) -> None:
    """Verify company context assembly produces comprehensive, authoritative state."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    ceo_service = CeoService(db_session)

    user = User(name="CEO User", email="ceo@orbit.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(
        user_id=user.id,
        name="Orbit Dynamics",
        mission="Autonomous Aerospace Intelligence",
        industry="Aerospace",
    )
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)

    context = await ceo_service.get_ceo_context(user_id=user.id, company_id=company.id)

    assert context["company"]["name"] == "Orbit Dynamics"
    assert context["company"]["mission"] == "Autonomous Aerospace Intelligence"
    assert context["company"]["industry"] == "Aerospace"
    assert context["department_count"] >= 5
    assert context["agent_count"] == 11
    assert context["ceo_agent"] is not None
    assert context["ceo_agent"]["role"] == "Chief Executive Officer"


@pytest.mark.asyncio
async def test_generate_plan_success_and_retrieval(db_session: AsyncSession) -> None:
    """Verify end-to-end plan generation, DAG construction, and persistence as a proposal."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    ceo_service = CeoService(db_session)

    user = User(name="Operator", email="op@company.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Vanguard AI")
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)

    goal = GoalIntake(
        objective="Research whether we should expand our product to Germany.",
        requested_outcome="Executive feasibility report with market and technical recommendations.",
        constraints=["Do not spend money", "Complete research within 2 weeks"],
        priority="high",
        requirements=["Include competitor analysis", "Review GDPR regulatory compliance"],
    )

    plan = await ceo_service.generate_plan(user_id=user.id, company_id=company.id, goal=goal)

    assert plan.id is not None
    assert plan.company_id == company.id
    assert plan.user_id == user.id
    assert plan.status == "proposed"  # Strict proposal boundary!
    assert plan.priority == "high"
    assert len(plan.plan_steps) == 4
    assert len(plan.delegation_proposals) >= 1
    assert len(plan.approval_requirements) >= 1

    # Verify DAG steps structure
    step_ids = [s["step_id"] for s in plan.plan_steps]
    assert "step_1" in step_ids
    assert "step_4" in step_ids
    # step_4 depends on step_2 and step_3
    step_4 = next(s for s in plan.plan_steps if s["step_id"] == "step_4")
    assert "step_2" in step_4["depends_on"]
    assert "step_3" in step_4["depends_on"]

    # Verify retrieval
    fetched = await ceo_service.get_plan(user_id=user.id, company_id=company.id, plan_id=plan.id)
    assert fetched.id == plan.id
    assert fetched.goal == goal.objective

    # Verify listing
    plans = await ceo_service.list_plans(user_id=user.id, company_id=company.id)
    assert len(plans) == 1
    assert plans[0].id == plan.id


@pytest.mark.asyncio
async def test_goal_validation_failures(db_session: AsyncSession) -> None:
    """Verify empty or invalid goal objectives raise InvalidGoalError."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    ceo_service = CeoService(db_session)

    user = User(name="User", email="user@test.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Test Co")
    await agent_service.provision_default_agents(company_id=company.id, user_id=user.id)

    with pytest.raises(InvalidGoalError, match="must not be empty"):
        await ceo_service.generate_plan(
            user_id=user.id,
            company_id=company.id,
            goal=GoalIntake(objective="   "),
        )


@pytest.mark.asyncio
async def test_cross_company_isolation(db_session: AsyncSession) -> None:
    """Verify users cannot access another company's CEO context or plans."""
    company_service = CompanyService(db_session)
    agent_service = AgentService(db_session)
    ceo_service = CeoService(db_session)

    # Company 1
    user_1 = User(name="Owner 1", email="owner1@co.os", password_hash="hash")
    db_session.add(user_1)
    # Company 2
    user_2 = User(name="Owner 2", email="owner2@co.os", password_hash="hash")
    db_session.add(user_2)
    await db_session.flush()

    comp_1, _ = await company_service.create_company(user_id=user_1.id, name="Company One")
    comp_2, _ = await company_service.create_company(user_id=user_2.id, name="Company Two")

    await agent_service.provision_default_agents(company_id=comp_1.id, user_id=user_1.id)

    # User 2 attempts to query Company 1's CEO context
    with pytest.raises(CeoAccessDeniedError, match="does not have active membership"):
        await ceo_service.get_ceo_context(user_id=user_2.id, company_id=comp_1.id)

    # User 2 attempts to generate a plan in Company 1
    with pytest.raises(CeoAccessDeniedError, match="does not have active membership"):
        await ceo_service.generate_plan(
            user_id=user_2.id,
            company_id=comp_1.id,
            goal=GoalIntake(objective="Intrude into company 1"),
        )


@pytest.mark.asyncio
async def test_plan_not_found(db_session: AsyncSession) -> None:
    """Verify requesting a non-existent plan raises PlanNotFoundError."""
    company_service = CompanyService(db_session)
    ceo_service = CeoService(db_session)

    user = User(name="Owner", email="owner@co.os", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    company, _ = await company_service.create_company(user_id=user.id, name="Company")

    with pytest.raises(PlanNotFoundError, match="not found in company"):
        await ceo_service.get_plan(user_id=user.id, company_id=company.id, plan_id="fake-id")
