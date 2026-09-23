"""Application service for agent presence adhering to docs/Phases.md Section 18 and docs/Memory.md Section 20."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.presence.exceptions import (
    PresenceAccessDeniedError,
    PresenceNotFoundError,
)
from domain.presence.schemas import (
    AgentPresenceResponse,
    PresenceStatus,
    PresenceSummaryResponse,
    PresenceUpdateParams,
)
from infrastructure.database.models import (
    Agent,
    AgentPresence,
    CompanyMember,
)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure datetime is UTC-aware, handling SQLite naive datetime values in tests."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class PresenceService:
    """Service managing authoritative real-time agent presence and heartbeat tracking."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _verify_membership(self, user_id: str, company_id: str) -> CompanyMember:
        """Verify user is an active member of the target company."""
        result = await self.db.execute(
            select(CompanyMember).where(
                CompanyMember.company_id == company_id,
                CompanyMember.user_id == user_id,
                CompanyMember.status == "active",
            )
        )
        member = result.scalars().first()
        if not member:
            raise PresenceAccessDeniedError(
                f"User '{user_id}' does not have access to company '{company_id}'."
            )
        return member

    async def sync_all_agent_presences(self, company_id: str) -> None:
        """Ensure every agent registered in the company has an authoritative AgentPresence record."""
        # Query all agents in the company
        agents_res = await self.db.execute(select(Agent).where(Agent.company_id == company_id))
        agents = agents_res.scalars().all()

        # Query existing presence records
        presence_res = await self.db.execute(
            select(AgentPresence.agent_id).where(AgentPresence.company_id == company_id)
        )
        existing_agent_ids = set(presence_res.scalars().all())

        now = datetime.now(UTC)
        for agent in agents:
            if agent.id not in existing_agent_ids:
                initial_status = (
                    PresenceStatus.IDLE if agent.status == "active" else PresenceStatus.OFFLINE
                )
                new_presence = AgentPresence(
                    id=str(uuid.uuid4()),
                    agent_id=agent.id,
                    company_id=company_id,
                    status=initial_status.value,
                    current_activity=None,
                    current_step=None,
                    last_heartbeat_at=now,
                    started_at=None,
                    updated_at=now,
                    details={},
                )
                self.db.add(new_presence)
        await self.db.flush()

    async def evaluate_stale_presence(
        self,
        company_id: str,
        stale_threshold_seconds: int = 60,
    ) -> int:
        """Detect and transition stale working agents whose heartbeats have expired per docs/Memory.md Section 20.

        Rule: Presence must be stale-aware. If an agent stops reporting, the system must not assume it is still working.
        """
        now = datetime.now(UTC)
        threshold_time = now - timedelta(seconds=stale_threshold_seconds)

        # Find agents marked WORKING whose last_heartbeat_at is older than threshold
        stale_query = select(AgentPresence).where(
            AgentPresence.company_id == company_id,
            AgentPresence.status == PresenceStatus.WORKING.value,
            AgentPresence.last_heartbeat_at < threshold_time,
        )
        res = await self.db.execute(stale_query)
        stale_records = res.scalars().all()

        for rec in stale_records:
            # Revert to IDLE operational state
            rec.status = PresenceStatus.IDLE.value
            rec.current_activity = "Heartbeat lapsed (auto-reset to IDLE)"
            rec.current_step = None
            rec.started_at = None
            rec.updated_at = now

        if stale_records:
            await self.db.flush()

        return len(stale_records)

    async def get_company_presence(
        self,
        user_id: str,
        company_id: str,
        include_stale_eval: bool = True,
        stale_threshold_seconds: int = 60,
    ) -> list[AgentPresenceResponse]:
        """Retrieve authoritative operational presence for all agents in the company."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        # Sync any missing presences
        await self.sync_all_agent_presences(company_id=company_id)

        # Stale awareness check
        if include_stale_eval:
            await self.evaluate_stale_presence(
                company_id=company_id,
                stale_threshold_seconds=stale_threshold_seconds,
            )

        # Query presences with relationships
        query = (
            select(AgentPresence)
            .where(AgentPresence.company_id == company_id)
            .options(
                selectinload(AgentPresence.agent).selectinload(Agent.department),
                selectinload(AgentPresence.current_task),
                selectinload(AgentPresence.current_project),
            )
        )
        res = await self.db.execute(query)
        presences = res.scalars().all()

        now = datetime.now(UTC)
        threshold_time = now - timedelta(seconds=stale_threshold_seconds)

        response_list: list[AgentPresenceResponse] = []
        for p in presences:
            agent = p.agent
            agent_name = agent.name if agent else "Unknown Agent"
            agent_role = agent.role if agent else "Specialist"
            dept_id = agent.department_id if agent else None
            dept_name = agent.department.name if agent and agent.department else None

            task_title = p.current_task.title if p.current_task else None
            project_name = p.current_project.name if p.current_project else None

            # Calculate working duration in seconds if started_at is populated
            duration = 0
            started_aware = _ensure_utc(p.started_at)
            if started_aware and p.status == PresenceStatus.WORKING.value:
                duration = max(0, int((now - started_aware).total_seconds()))

            last_hb_aware = _ensure_utc(p.last_heartbeat_at)
            is_stale = (
                p.status == PresenceStatus.WORKING.value
                and last_hb_aware is not None
                and last_hb_aware < threshold_time
            )

            # Cast status string to PresenceStatus enum safely
            try:
                status_enum = PresenceStatus(p.status)
            except ValueError:
                status_enum = PresenceStatus.IDLE

            response_list.append(
                AgentPresenceResponse(
                    id=p.id,
                    agent_id=p.agent_id,
                    agent_name=agent_name,
                    agent_role=agent_role,
                    department_id=dept_id,
                    department_name=dept_name,
                    company_id=p.company_id,
                    status=status_enum,
                    current_task_id=p.current_task_id,
                    current_task_title=task_title,
                    current_project_id=p.current_project_id,
                    current_project_name=project_name,
                    current_activity=p.current_activity,
                    current_step=p.current_step,
                    last_heartbeat_at=p.last_heartbeat_at,
                    started_at=p.started_at,
                    updated_at=p.updated_at,
                    duration_seconds=duration,
                    is_stale=is_stale,
                    details=p.details or {},
                )
            )

        # Sort order: WORKING -> WAITING -> BLOCKED -> ERROR -> ONLINE -> IDLE -> OFFLINE
        status_priority: dict[PresenceStatus, int] = {
            PresenceStatus.WORKING: 0,
            PresenceStatus.WAITING: 1,
            PresenceStatus.BLOCKED: 2,
            PresenceStatus.ERROR: 3,
            PresenceStatus.ONLINE: 4,
            PresenceStatus.IDLE: 5,
            PresenceStatus.OFFLINE: 6,
        }
        response_list.sort(key=lambda r: (status_priority.get(r.status, 99), r.agent_name))

        return response_list

    async def get_presence_summary(
        self,
        user_id: str,
        company_id: str,
        stale_threshold_seconds: int = 60,
    ) -> PresenceSummaryResponse:
        """Calculate real-time presence rollup summary for executive dashboard."""
        await self._verify_membership(user_id=user_id, company_id=company_id)
        await self.sync_all_agent_presences(company_id=company_id)
        await self.evaluate_stale_presence(
            company_id=company_id,
            stale_threshold_seconds=stale_threshold_seconds,
        )

        query = (
            select(AgentPresence.status, func.count(AgentPresence.id))
            .where(AgentPresence.company_id == company_id)
            .group_by(AgentPresence.status)
        )
        res = await self.db.execute(query)
        counts: dict[str, int] = {str(row[0]): int(row[1]) for row in res.all()}

        summary = PresenceSummaryResponse(
            total_agents=sum(counts.values()),
            working_count=counts.get(PresenceStatus.WORKING.value, 0),
            idle_count=counts.get(PresenceStatus.IDLE.value, 0),
            waiting_count=counts.get(PresenceStatus.WAITING.value, 0),
            blocked_count=counts.get(PresenceStatus.BLOCKED.value, 0),
            error_count=counts.get(PresenceStatus.ERROR.value, 0),
            offline_count=counts.get(PresenceStatus.OFFLINE.value, 0),
        )
        return summary

    async def get_agent_presence(
        self,
        user_id: str,
        company_id: str,
        agent_id: str,
    ) -> AgentPresenceResponse:
        """Get real-time presence for a specific agent."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        query = (
            select(AgentPresence)
            .where(
                AgentPresence.company_id == company_id,
                AgentPresence.agent_id == agent_id,
            )
            .options(
                selectinload(AgentPresence.agent).selectinload(Agent.department),
                selectinload(AgentPresence.current_task),
                selectinload(AgentPresence.current_project),
            )
        )
        res = await self.db.execute(query)
        presence = res.scalars().first()

        if not presence:
            # Check if agent exists in this company
            agent_res = await self.db.execute(
                select(Agent).where(Agent.id == agent_id, Agent.company_id == company_id)
            )
            agent = agent_res.scalars().first()
            if not agent:
                raise PresenceNotFoundError(
                    f"Agent '{agent_id}' not found in company '{company_id}'."
                )

            # Create default presence on-the-fly
            now = datetime.now(UTC)
            initial_status = (
                PresenceStatus.IDLE if agent.status == "active" else PresenceStatus.OFFLINE
            )
            presence = AgentPresence(
                id=str(uuid.uuid4()),
                agent_id=agent.id,
                company_id=company_id,
                status=initial_status.value,
                current_activity=None,
                current_step=None,
                last_heartbeat_at=now,
                started_at=None,
                updated_at=now,
                details={},
            )
            self.db.add(presence)
            await self.db.flush()
            # Re-fetch with relationships
            presence = (await self.db.execute(query)).scalars().first()

        assert presence is not None
        now = datetime.now(UTC)
        duration = 0
        started_aware = _ensure_utc(presence.started_at)
        if started_aware and presence.status == PresenceStatus.WORKING.value:
            duration = max(0, int((now - started_aware).total_seconds()))

        agent = presence.agent
        try:
            status_enum = PresenceStatus(presence.status)
        except ValueError:
            status_enum = PresenceStatus.IDLE

        return AgentPresenceResponse(
            id=presence.id,
            agent_id=presence.agent_id,
            agent_name=agent.name if agent else "Unknown Agent",
            agent_role=agent.role if agent else "Specialist",
            department_id=agent.department_id if agent else None,
            department_name=agent.department.name if agent and agent.department else None,
            company_id=presence.company_id,
            status=status_enum,
            current_task_id=presence.current_task_id,
            current_task_title=presence.current_task.title if presence.current_task else None,
            current_project_id=presence.current_project_id,
            current_project_name=presence.current_project.name
            if presence.current_project
            else None,
            current_activity=presence.current_activity,
            current_step=presence.current_step,
            last_heartbeat_at=presence.last_heartbeat_at,
            started_at=presence.started_at,
            updated_at=presence.updated_at,
            duration_seconds=duration,
            is_stale=False,
            details=presence.details or {},
        )

    async def record_heartbeat(
        self,
        company_id: str,
        agent_id: str,
        current_step: str | None = None,
        activity: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AgentPresence:
        """Update last heartbeat timestamp and optional current step."""
        res = await self.db.execute(
            select(AgentPresence).where(
                AgentPresence.company_id == company_id,
                AgentPresence.agent_id == agent_id,
            )
        )
        presence = res.scalars().first()
        now = datetime.now(UTC)

        if not presence:
            presence = AgentPresence(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                company_id=company_id,
                status=PresenceStatus.IDLE.value,
                last_heartbeat_at=now,
                updated_at=now,
                details={},
            )
            self.db.add(presence)

        presence.last_heartbeat_at = now
        presence.updated_at = now
        if current_step is not None:
            presence.current_step = current_step
        if activity is not None:
            presence.current_activity = activity
        if details:
            presence.details = {**(presence.details or {}), **details}

        await self.db.flush()
        return presence

    async def set_working(
        self,
        company_id: str,
        agent_id: str,
        task_id: str | None = None,
        project_id: str | None = None,
        activity: str | None = None,
        current_step: str | None = None,
    ) -> AgentPresence:
        """Transition agent presence to WORKING state adhering to docs/UI.md Section 75."""
        res = await self.db.execute(
            select(AgentPresence).where(
                AgentPresence.company_id == company_id,
                AgentPresence.agent_id == agent_id,
            )
        )
        presence = res.scalars().first()
        now = datetime.now(UTC)

        if not presence:
            presence = AgentPresence(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                company_id=company_id,
                status=PresenceStatus.WORKING.value,
                current_task_id=task_id,
                current_project_id=project_id,
                current_activity=activity,
                current_step=current_step,
                started_at=now,
                last_heartbeat_at=now,
                updated_at=now,
                details={},
            )
            self.db.add(presence)
        else:
            presence.status = PresenceStatus.WORKING.value
            presence.current_task_id = task_id
            presence.current_project_id = project_id
            presence.current_activity = activity
            presence.current_step = current_step
            presence.started_at = now
            presence.last_heartbeat_at = now
            presence.updated_at = now

        await self.db.flush()
        return presence

    async def set_idle(
        self,
        company_id: str,
        agent_id: str,
    ) -> AgentPresence:
        """Transition agent presence to IDLE state upon task completion or release."""
        res = await self.db.execute(
            select(AgentPresence).where(
                AgentPresence.company_id == company_id,
                AgentPresence.agent_id == agent_id,
            )
        )
        presence = res.scalars().first()
        now = datetime.now(UTC)

        if not presence:
            presence = AgentPresence(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                company_id=company_id,
                status=PresenceStatus.IDLE.value,
                last_heartbeat_at=now,
                updated_at=now,
                details={},
            )
            self.db.add(presence)
        else:
            presence.status = PresenceStatus.IDLE.value
            presence.current_task_id = None
            presence.current_project_id = None
            presence.current_activity = None
            presence.current_step = None
            presence.started_at = None
            presence.last_heartbeat_at = now
            presence.updated_at = now

        await self.db.flush()
        return presence

    async def set_waiting(
        self,
        company_id: str,
        agent_id: str,
        task_id: str | None = None,
        reason: str | None = None,
    ) -> AgentPresence:
        """Transition agent presence to WAITING state (e.g., human approval required)."""
        res = await self.db.execute(
            select(AgentPresence).where(
                AgentPresence.company_id == company_id,
                AgentPresence.agent_id == agent_id,
            )
        )
        presence = res.scalars().first()
        now = datetime.now(UTC)

        if not presence:
            presence = AgentPresence(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                company_id=company_id,
                status=PresenceStatus.WAITING.value,
                current_task_id=task_id,
                current_activity=reason or "Awaiting approval / dependencies",
                last_heartbeat_at=now,
                updated_at=now,
                details={},
            )
            self.db.add(presence)
        else:
            presence.status = PresenceStatus.WAITING.value
            presence.current_task_id = task_id or presence.current_task_id
            presence.current_activity = reason or "Awaiting approval / dependencies"
            presence.last_heartbeat_at = now
            presence.updated_at = now

        await self.db.flush()
        return presence

    async def set_error(
        self,
        company_id: str,
        agent_id: str,
        task_id: str | None = None,
        error_details: str | None = None,
    ) -> AgentPresence:
        """Transition agent presence to ERROR state upon execution failure."""
        res = await self.db.execute(
            select(AgentPresence).where(
                AgentPresence.company_id == company_id,
                AgentPresence.agent_id == agent_id,
            )
        )
        presence = res.scalars().first()
        now = datetime.now(UTC)

        if not presence:
            presence = AgentPresence(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                company_id=company_id,
                status=PresenceStatus.ERROR.value,
                current_task_id=task_id,
                current_activity=error_details or "Execution failure",
                last_heartbeat_at=now,
                updated_at=now,
                details={},
            )
            self.db.add(presence)
        else:
            presence.status = PresenceStatus.ERROR.value
            presence.current_task_id = task_id or presence.current_task_id
            presence.current_activity = error_details or "Execution failure"
            presence.last_heartbeat_at = now
            presence.updated_at = now

        await self.db.flush()
        return presence

    async def update_presence_status(
        self,
        user_id: str,
        company_id: str,
        agent_id: str,
        params: PresenceUpdateParams,
    ) -> AgentPresenceResponse:
        """Allow an authorized operator to manually override an agent's presence status."""
        await self._verify_membership(user_id=user_id, company_id=company_id)

        res = await self.db.execute(
            select(AgentPresence).where(
                AgentPresence.company_id == company_id,
                AgentPresence.agent_id == agent_id,
            )
        )
        presence = res.scalars().first()
        now = datetime.now(UTC)

        if not presence:
            presence = AgentPresence(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                company_id=company_id,
                status=params.status.value,
                current_activity=params.current_activity,
                current_step=params.current_step,
                last_heartbeat_at=now,
                started_at=now if params.status == PresenceStatus.WORKING else None,
                updated_at=now,
                details=params.details,
            )
            self.db.add(presence)
        else:
            presence.status = params.status.value
            if params.current_activity is not None:
                presence.current_activity = params.current_activity
            if params.current_step is not None:
                presence.current_step = params.current_step
            if params.details:
                presence.details = {**(presence.details or {}), **params.details}
            if params.status == PresenceStatus.WORKING and not presence.started_at:
                presence.started_at = now
            elif params.status != PresenceStatus.WORKING:
                presence.started_at = None
            presence.last_heartbeat_at = now
            presence.updated_at = now

        await self.db.flush()
        return await self.get_agent_presence(
            user_id=user_id, company_id=company_id, agent_id=agent_id
        )
