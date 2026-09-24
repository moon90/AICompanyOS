"""Activity service orchestrating human-readable operational company history."""

from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.activity.exceptions import ActivityAccessDeniedError
from domain.activity.schemas import ActivityFilterParams
from infrastructure.database.models import ActivityEvent, CompanyMember


class ActivityService:
    """Service orchestrating human-readable activity history per docs/Phases.md Section 17."""

    async def _verify_company_access(
        self, session: AsyncSession, user_id: str, company_id: str
    ) -> CompanyMember:
        """Verify that the user is an active member of the company."""
        stmt = select(CompanyMember).where(
            CompanyMember.company_id == company_id,
            CompanyMember.user_id == user_id,
        )
        result = await session.execute(stmt)
        member = result.scalar_one_or_none()
        if not member:
            raise ActivityAccessDeniedError(
                f"User '{user_id}' does not have access to company '{company_id}'."
            )
        return member

    @staticmethod
    async def record_event(
        session: AsyncSession,
        company_id: str,
        event_type: str,
        message: str,
        actor_type: str = "system",
        actor_id: str | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ActivityEvent:
        """Record an authoritative operational activity event.

        Can be invoked within any transaction across application services.
        """
        event = ActivityEvent(
            company_id=company_id,
            project_id=project_id,
            task_id=task_id,
            actor_type=actor_type,
            actor_id=actor_id,
            event_type=event_type,
            message=message,
            event_metadata=metadata or {},
        )
        session.add(event)
        await session.flush()

        # Broadcast over real-time operations event stream (Phase 17)
        try:
            from infrastructure.events.dispatcher import EventDispatcher

            dispatcher = EventDispatcher.get_instance()
            await dispatcher.broadcast_event(
                company_id=company_id,
                event_type=event_type,
                message=message,
                actor_type=actor_type,
                actor_id=actor_id,
                project_id=project_id,
                task_id=task_id,
                metadata=metadata or {},
            )
        except Exception:
            # Real-time failure must never compromise authoritative database transaction
            pass

        return event

    async def get_company_activity(
        self,
        session: AsyncSession,
        user_id: str,
        company_id: str,
        filters: ActivityFilterParams,
    ) -> tuple[list[ActivityEvent], int]:
        """Fetch paginated company activity events with filtering."""
        await self._verify_company_access(session, user_id, company_id)

        query = select(ActivityEvent).where(ActivityEvent.company_id == company_id)

        if filters.project_id:
            query = query.where(ActivityEvent.project_id == filters.project_id)
        if filters.task_id:
            query = query.where(ActivityEvent.task_id == filters.task_id)
        if filters.actor_type:
            query = query.where(ActivityEvent.actor_type == filters.actor_type)
        if filters.actor_id:
            query = query.where(ActivityEvent.actor_id == filters.actor_id)
        if filters.event_type:
            query = query.where(ActivityEvent.event_type == filters.event_type)
        if filters.search:
            search_pattern = f"%{filters.search}%"
            query = query.where(ActivityEvent.message.ilike(search_pattern))

        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        query = (
            query.order_by(desc(ActivityEvent.created_at))
            .limit(filters.limit)
            .offset(filters.offset)
        )
        result = await session.execute(query)
        events = list(result.scalars().all())

        return events, total

    async def get_project_activity(
        self,
        session: AsyncSession,
        user_id: str,
        company_id: str,
        project_id: str,
        filters: ActivityFilterParams,
    ) -> tuple[list[ActivityEvent], int]:
        """Fetch activity events scoped to a specific project."""
        scoped_filters = filters.model_copy(update={"project_id": project_id})
        return await self.get_company_activity(session, user_id, company_id, scoped_filters)

    async def get_task_activity(
        self,
        session: AsyncSession,
        user_id: str,
        company_id: str,
        task_id: str,
        filters: ActivityFilterParams,
    ) -> tuple[list[ActivityEvent], int]:
        """Fetch activity events scoped to a specific task."""
        scoped_filters = filters.model_copy(update={"task_id": task_id})
        return await self.get_company_activity(session, user_id, company_id, scoped_filters)

    async def get_agent_activity(
        self,
        session: AsyncSession,
        user_id: str,
        company_id: str,
        agent_id: str,
        filters: ActivityFilterParams,
    ) -> tuple[list[ActivityEvent], int]:
        """Fetch activity events performed by or associated with a specific agent."""
        scoped_filters = filters.model_copy(update={"actor_id": agent_id, "actor_type": "agent"})
        return await self.get_company_activity(session, user_id, company_id, scoped_filters)
