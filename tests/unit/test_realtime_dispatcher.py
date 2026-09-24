"""Unit tests for EventDispatcher and RealtimeService adhering to docs/Phases.md Section 21."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.realtime_service import RealtimeService
from domain.realtime.exceptions import RealtimeAccessDeniedError
from domain.realtime.schemas import (
    RealtimeEmitRequest,
    RealtimeEventPayload,
    RealtimeEventType,
)
from infrastructure.database.base import Base
from infrastructure.database.models import Company, CompanyMember, User
from infrastructure.events.dispatcher import EventDispatcher


@pytest.fixture(autouse=True)
def reset_dispatcher() -> None:
    """Ensure a clean singleton dispatcher instance for each test."""
    EventDispatcher.reset_instance()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create in-memory SQLite async database session for unit testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_event_dispatcher_register_and_broadcast() -> None:
    """Verify that multiple subscribers receive broadcast events."""
    dispatcher = EventDispatcher()
    company_id = "comp-1"

    queue1 = await dispatcher.register_subscriber(company_id)
    queue2 = await dispatcher.register_subscriber(company_id)

    event = RealtimeEventPayload(
        company_id=company_id,
        event_type=RealtimeEventType.TASK_ASSIGNED.value,
        message="Task 'Implement Auth' assigned to Agent Coder",
        actor_type="agent",
        actor_id="agent-1",
        task_id="task-101",
    )

    dispatched = await dispatcher.broadcast(company_id, event)
    assert dispatched == 2

    recv1 = await queue1.get()
    recv2 = await queue2.get()

    assert recv1.id == event.id
    assert recv1.message == event.message
    assert recv2.id == event.id
    assert recv2.task_id == "task-101"

    # Unregister queue1
    await dispatcher.unregister_subscriber(company_id, queue1)
    status = await dispatcher.get_status(company_id)
    assert status.active_subscribers == 1
    assert status.events_dispatched == 1


@pytest.mark.asyncio
async def test_event_dispatcher_company_isolation() -> None:
    """Verify that real-time events strictly adhere to multi-tenant boundaries."""
    dispatcher = EventDispatcher()
    comp_a = "company-alpha"
    comp_b = "company-beta"

    queue_a = await dispatcher.register_subscriber(comp_a)
    queue_b = await dispatcher.register_subscriber(comp_b)

    event_a = RealtimeEventPayload(
        company_id=comp_a,
        event_type=RealtimeEventType.CEO_PLANNING.value,
        message="CEO generated new roadmap proposal",
    )

    await dispatcher.broadcast(comp_a, event_a)

    # Queue A should have the event
    recv_a = await queue_a.get()
    assert recv_a.message == "CEO generated new roadmap proposal"

    # Queue B should remain empty
    assert queue_b.empty()


@pytest.mark.asyncio
async def test_event_dispatcher_queue_overflow_drop_oldest() -> None:
    """Verify that slow consumers do not leak memory or deadlock dispatcher."""
    dispatcher = EventDispatcher(queue_maxsize=2)
    company_id = "comp-overflow"

    queue = await dispatcher.register_subscriber(company_id)

    # Broadcast 3 events with maxsize 2
    for i in range(3):
        ev = RealtimeEventPayload(
            company_id=company_id,
            event_type=RealtimeEventType.TOOL_CALLED.value,
            message=f"Event {i}",
        )
        await dispatcher.broadcast(company_id, ev)

    # Queue should contain only 2 newest events (Event 1 and Event 2)
    assert queue.qsize() == 2
    item1 = await queue.get()
    assert item1.message == "Event 1"
    item2 = await queue.get()
    assert item2.message == "Event 2"


@pytest.mark.asyncio
async def test_realtime_service_access_denied(db_session: AsyncSession) -> None:
    """Verify non-members are rejected from accessing company real-time streams."""
    user = User(
        name="External User",
        email="external@example.com",
        password_hash="hashed",
    )
    db_session.add(user)
    await db_session.flush()

    service = RealtimeService()
    with pytest.raises(RealtimeAccessDeniedError):
        await service.verify_company_access(
            session=db_session,
            user_id=user.id,
            company_id="non-existent-or-unauthorized-comp",
        )


@pytest.mark.asyncio
async def test_realtime_service_emit_event_success(
    db_session: AsyncSession,
) -> None:
    """Verify authenticated operators can emit operational events."""
    user = User(
        name="Operator Alpha",
        email="operator@ice.io",
        password_hash="hashed",
    )
    company = Company(
        name="IceSoft Corp",
        mission="Build autonomous agent company OS",
        industry="Technology",
    )
    db_session.add_all([user, company])
    await db_session.flush()

    member = CompanyMember(
        company_id=company.id,
        user_id=user.id,
        role="owner",
    )
    db_session.add(member)
    await db_session.flush()

    dispatcher = EventDispatcher.get_instance()
    queue = await dispatcher.register_subscriber(company.id)

    service = RealtimeService(dispatcher)
    req = RealtimeEmitRequest(
        event_type=RealtimeEventType.TEST_PULSE.value,
        message="Manual test pulse from operator",
        actor_type="user",
        actor_id=user.id,
    )

    emitted = await service.emit_event(
        session=db_session,
        user_id=user.id,
        company_id=company.id,
        payload=req,
    )

    assert emitted.company_id == company.id
    assert emitted.event_type == "test.pulse"
    assert emitted.actor_name == "Operator Alpha"

    # Verify queue received the emitted event
    received = await queue.get()
    assert received.id == emitted.id
    assert received.message == "Manual test pulse from operator"
