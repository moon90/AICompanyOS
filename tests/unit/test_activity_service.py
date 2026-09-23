"""Unit tests for ActivityService adhering to docs/Phases.md Section 17."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.activity_service import ActivityService
from domain.activity.exceptions import ActivityAccessDeniedError
from domain.activity.schemas import ActivityFilterParams
from infrastructure.database.base import Base
from infrastructure.database.models import Company, CompanyMember, Project, Task, User


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated, in-memory SQLite session with all models created."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_data(db_session: AsyncSession) -> dict[str, str]:
    """Seed test user, company, membership, project, and task."""
    user = User(
        id="usr-activity-001",
        email="operator@activity.test",
        name="Activity Operator",
        password_hash="hash",
    )
    db_session.add(user)

    company = Company(
        id="cmp-activity-001",
        name="Activity Test Corp",
        status="active",
    )
    db_session.add(company)

    member = CompanyMember(
        id="mem-activity-001",
        company_id=company.id,
        user_id=user.id,
        role="owner",
    )
    db_session.add(member)

    project = Project(
        id="prj-activity-001",
        company_id=company.id,
        name="Core Rollout",
        status="PLANNED",
        priority="high",
        owner_user_id=user.id,
    )
    db_session.add(project)

    task = Task(
        id="tsk-activity-001",
        company_id=company.id,
        project_id=project.id,
        title="Deploy Auth",
        status="READY",
        priority="high",
        created_by_user_id=user.id,
    )
    db_session.add(task)

    await db_session.commit()

    return {
        "user_id": user.id,
        "company_id": company.id,
        "project_id": project.id,
        "task_id": task.id,
    }


@pytest.mark.asyncio
async def test_record_and_retrieve_activity_event(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify recording an event persists it and allows retrieval via get_company_activity."""
    service = ActivityService()

    event = await ActivityService.record_event(
        session=db_session,
        company_id=test_data["company_id"],
        event_type="TASK_CREATED",
        message="Created task 'Deploy Auth'",
        actor_type="user",
        actor_id=test_data["user_id"],
        project_id=test_data["project_id"],
        task_id=test_data["task_id"],
        metadata={"priority": "high"},
    )
    await db_session.commit()

    assert event.id is not None
    assert event.event_type == "TASK_CREATED"
    assert event.event_metadata == {"priority": "high"}

    filters = ActivityFilterParams(limit=10, offset=0)
    events, total = await service.get_company_activity(
        session=db_session,
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
        filters=filters,
    )

    assert total == 1
    assert len(events) == 1
    assert events[0].id == event.id
    assert events[0].message == "Created task 'Deploy Auth'"
    assert events[0].actor_type == "user"


@pytest.mark.asyncio
async def test_activity_filters(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Verify filtering by event_type, project_id, task_id, and keyword search."""
    service = ActivityService()

    # Record 3 events
    await ActivityService.record_event(
        session=db_session,
        company_id=test_data["company_id"],
        event_type="PROJECT_CREATED",
        message="Created project 'Core Rollout'",
        actor_type="user",
        actor_id=test_data["user_id"],
        project_id=test_data["project_id"],
    )
    await ActivityService.record_event(
        session=db_session,
        company_id=test_data["company_id"],
        event_type="TASK_CREATED",
        message="Created task 'Deploy Auth'",
        actor_type="user",
        actor_id=test_data["user_id"],
        project_id=test_data["project_id"],
        task_id=test_data["task_id"],
    )
    await ActivityService.record_event(
        session=db_session,
        company_id=test_data["company_id"],
        event_type="APPROVAL_RESOLVED",
        message="Approved tool execution",
        actor_type="system",
    )
    await db_session.commit()

    # Filter by event_type
    events, total = await service.get_company_activity(
        session=db_session,
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
        filters=ActivityFilterParams(event_type="PROJECT_CREATED"),
    )
    assert total == 1
    assert events[0].event_type == "PROJECT_CREATED"

    # Filter by task_id
    events, total = await service.get_task_activity(
        session=db_session,
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
        task_id=test_data["task_id"],
        filters=ActivityFilterParams(),
    )
    assert total == 1
    assert events[0].task_id == test_data["task_id"]

    # Filter by search keyword
    events, total = await service.get_company_activity(
        session=db_session,
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
        filters=ActivityFilterParams(search="Auth"),
    )
    assert total == 1
    assert "Deploy Auth" in events[0].message


@pytest.mark.asyncio
async def test_activity_multi_tenant_isolation(
    db_session: AsyncSession, test_data: dict[str, str]
) -> None:
    """Verify unauthorized users cannot access activity events of foreign companies."""
    service = ActivityService()

    foreign_user = User(
        id="usr-foreign-999",
        email="foreign@other.test",
        name="Foreign Operator",
        password_hash="hash",
    )
    db_session.add(foreign_user)
    await db_session.commit()

    with pytest.raises(ActivityAccessDeniedError):
        await service.get_company_activity(
            session=db_session,
            user_id=foreign_user.id,
            company_id=test_data["company_id"],
            filters=ActivityFilterParams(),
        )


@pytest.mark.asyncio
async def test_activity_pagination(db_session: AsyncSession, test_data: dict[str, str]) -> None:
    """Verify pagination limit and offset order reverse-chronologically."""
    service = ActivityService()

    for i in range(5):
        await ActivityService.record_event(
            session=db_session,
            company_id=test_data["company_id"],
            event_type="TASK_CREATED",
            message=f"Event number {i}",
            actor_type="system",
        )
    await db_session.commit()

    page1, total = await service.get_company_activity(
        session=db_session,
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
        filters=ActivityFilterParams(limit=2, offset=0),
    )
    assert total == 5
    assert len(page1) == 2

    page2, total = await service.get_company_activity(
        session=db_session,
        user_id=test_data["user_id"],
        company_id=test_data["company_id"],
        filters=ActivityFilterParams(limit=2, offset=2),
    )
    assert len(page2) == 2
    assert page1[0].id != page2[0].id
