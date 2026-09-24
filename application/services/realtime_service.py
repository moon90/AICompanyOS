"""Application service orchestrating real-time operations per docs/Phases.md Section 21."""

from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.realtime.exceptions import RealtimeAccessDeniedError
from domain.realtime.schemas import (
    RealtimeEmitRequest,
    RealtimeEventPayload,
    RealtimeStatusResponse,
)
from infrastructure.database.models import CompanyMember, User
from infrastructure.events.dispatcher import EventDispatcher


class RealtimeService:
    """Service layer managing real-time operations, event dispatching, and SSE streams."""

    def __init__(self, dispatcher: EventDispatcher | None = None) -> None:
        self.dispatcher = dispatcher or EventDispatcher.get_instance()

    async def verify_company_access(
        self, session: AsyncSession, user_id: str, company_id: str
    ) -> CompanyMember:
        """Verify that the authenticated operator has access to the target company."""
        stmt = select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user_id,
        )
        result = await session.execute(stmt)
        member = result.scalar_one_or_none()
        if not member:
            raise RealtimeAccessDeniedError(
                f"User '{user_id}' does not have access to real-time events for company '{company_id}'."
            )
        return member

    async def emit_event(
        self,
        session: AsyncSession,
        user_id: str,
        company_id: str,
        payload: RealtimeEmitRequest,
    ) -> RealtimeEventPayload:
        """Emit an operational event into the company's real-time event stream."""
        await self.verify_company_access(session, user_id, company_id)

        # Lookup actor name if actor is user
        actor_name = payload.actor_name
        if not actor_name and payload.actor_type == "user":
            user_stmt = select(User).where(User.id == user_id)
            user_res = await session.execute(user_stmt)
            user_obj = user_res.scalar_one_or_none()
            if user_obj:
                actor_name = user_obj.name

        event = await self.dispatcher.broadcast_event(
            company_id=company_id,
            event_type=payload.event_type,
            message=payload.message,
            actor_type=payload.actor_type,
            actor_id=payload.actor_id or user_id,
            actor_name=actor_name,
            project_id=payload.project_id,
            task_id=payload.task_id,
            metadata=payload.metadata,
        )
        return event

    async def get_channel_status(
        self, session: AsyncSession, user_id: str, company_id: str
    ) -> RealtimeStatusResponse:
        """Retrieve real-time channel telemetry and active subscriber metrics."""
        await self.verify_company_access(session, user_id, company_id)
        return await self.dispatcher.get_status(company_id)

    def stream_company_events(self, company_id: str) -> AsyncGenerator[RealtimeEventPayload, None]:
        """Stream real-time events as an asynchronous generator for SSE delivery."""
        return self.dispatcher.stream_events(company_id)
