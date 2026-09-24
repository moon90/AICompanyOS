"""Application service for error and bug management adhering to docs/Phases.md Section 19 and docs/Memory.md Section 20."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application.services.activity_service import ActivityService
from domain.errors.exceptions import (
    ErrorAccessDeniedError,
    ErrorNotFoundError,
    MissingEvidenceError,
    MissingResolutionError,
)
from domain.errors.schemas import (
    ErrorAssignPayload,
    ErrorCreatePayload,
    ErrorListResponse,
    ErrorRecordResponse,
    ErrorResolvePayload,
    ErrorSeverity,
    ErrorStatus,
    ErrorSummaryResponse,
    ErrorUpdatePayload,
    ErrorVerifyPayload,
)
from infrastructure.database.models import (
    CompanyMember,
    ErrorRecord,
    Project,
    Task,
)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure datetime is UTC-aware, handling SQLite naive datetime values in tests."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class ErrorService:
    """Authoritative error and bug management orchestrator answering all 8 operational questions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _verify_company_access(self, company_id: str, user_id: str) -> CompanyMember:
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
            raise ErrorAccessDeniedError(
                f"User '{user_id}' does not have access to company '{company_id}'."
            )
        return member

    def _to_response(self, error: ErrorRecord) -> ErrorRecordResponse:
        """Map ORM ErrorRecord to domain response with relationship fallbacks."""
        return ErrorRecordResponse(
            id=error.id,
            company_id=error.company_id,
            project_id=error.project_id,
            project_name=error.project.name if error.project else None,
            task_id=error.task_id,
            task_title=error.task.title if error.task else None,
            title=error.title,
            description=error.description,
            severity=ErrorSeverity(error.severity),
            status=ErrorStatus(error.status),
            detected_by=error.detected_by,
            assigned_to=error.assigned_to,
            investigated_by=error.investigated_by,
            resolved_by=error.resolved_by,
            verified_by=error.verified_by,
            assigned_agent_id=error.assigned_agent_id,
            assigned_agent_name=error.assigned_agent.name if error.assigned_agent else None,
            assigned_user_id=error.assigned_user_id,
            assigned_user_name=error.assigned_user.name if error.assigned_user else None,
            root_cause=error.root_cause,
            resolution=error.resolution,
            evidence=error.evidence or {},
            created_at=_ensure_utc(error.created_at) or datetime.now(UTC),
            resolved_at=_ensure_utc(error.resolved_at),
            verified_at=_ensure_utc(error.verified_at),
        )

    async def _fetch_error_record(self, company_id: str, error_id: str) -> ErrorRecord:
        """Fetch error record with eager loaded relationships."""
        stmt = (
            select(ErrorRecord)
            .where(ErrorRecord.id == error_id, ErrorRecord.company_id == company_id)
            .options(
                selectinload(ErrorRecord.project),
                selectinload(ErrorRecord.task),
                selectinload(ErrorRecord.assigned_agent),
                selectinload(ErrorRecord.assigned_user),
            )
            .execution_options(populate_existing=True)
        )
        result = await self.db.execute(stmt)
        record = result.scalars().first()
        if not record:
            raise ErrorNotFoundError(
                f"Error record '{error_id}' not found in company '{company_id}'."
            )
        return record

    async def create_error(
        self,
        company_id: str,
        payload: ErrorCreatePayload,
        user_id: str | None = None,
    ) -> ErrorRecordResponse:
        """Record an authoritative error or bug."""
        if user_id:
            await self._verify_company_access(company_id=company_id, user_id=user_id)

        # Validate project/task if given
        if payload.project_id:
            proj_res = await self.db.execute(
                select(Project.id).where(
                    Project.id == payload.project_id, Project.company_id == company_id
                )
            )
            if not proj_res.scalars().first():
                payload.project_id = None

        if payload.task_id:
            task_res = await self.db.execute(
                select(Task.id).where(Task.id == payload.task_id, Task.company_id == company_id)
            )
            if not task_res.scalars().first():
                payload.task_id = None

        initial_status = (
            ErrorStatus.ASSIGNED.value
            if (payload.assigned_to or payload.assigned_agent_id or payload.assigned_user_id)
            else ErrorStatus.OPEN.value
        )

        error_id = str(uuid.uuid4())
        record = ErrorRecord(
            id=error_id,
            company_id=company_id,
            project_id=payload.project_id,
            task_id=payload.task_id,
            title=payload.title,
            description=payload.description,
            severity=payload.severity.value,
            status=initial_status,
            detected_by=payload.detected_by,
            assigned_to=payload.assigned_to,
            assigned_agent_id=payload.assigned_agent_id,
            assigned_user_id=payload.assigned_user_id,
            evidence=payload.evidence or {},
        )
        self.db.add(record)
        await self.db.flush()

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            event_type="error.detected",
            message=f"Error detected: '{record.title}' (Severity: {record.severity})",
            actor_type="system" if not user_id else "user",
            actor_id=user_id or payload.detected_by,
            project_id=record.project_id,
            task_id=record.task_id,
            metadata={
                "error_id": record.id,
                "severity": record.severity,
                "detected_by": record.detected_by,
            },
        )
        await self.db.commit()

        # Reload with relationships
        loaded = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        return self._to_response(loaded)

    async def get_errors(
        self,
        company_id: str,
        user_id: str | None = None,
        status: ErrorStatus | None = None,
        severity: ErrorSeverity | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
        assigned_to: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> ErrorListResponse:
        """List and filter errors for a company with counts."""
        if user_id:
            await self._verify_company_access(company_id=company_id, user_id=user_id)

        stmt = select(ErrorRecord).where(ErrorRecord.company_id == company_id)

        if status:
            stmt = stmt.where(ErrorRecord.status == status.value)
        if severity:
            stmt = stmt.where(ErrorRecord.severity == severity.value)
        if project_id:
            stmt = stmt.where(ErrorRecord.project_id == project_id)
        if task_id:
            stmt = stmt.where(ErrorRecord.task_id == task_id)
        if assigned_to:
            stmt = stmt.where(ErrorRecord.assigned_to.ilike(f"%{assigned_to}%"))

        # Eager load relationships
        stmt = (
            stmt.options(
                selectinload(ErrorRecord.project),
                selectinload(ErrorRecord.task),
                selectinload(ErrorRecord.assigned_agent),
                selectinload(ErrorRecord.assigned_user),
            )
            .order_by(desc(ErrorRecord.created_at))
            .offset(offset)
            .limit(limit)
        )

        res = await self.db.execute(stmt)
        records = res.scalars().all()

        # Aggregation counts
        count_stmt = select(
            func.count().label("total"),
            func.count()
            .filter(ErrorRecord.status.in_([ErrorStatus.OPEN.value, ErrorStatus.TRIAGED.value]))
            .label("open_count"),
            func.count()
            .filter(
                ErrorRecord.status.in_(
                    [ErrorStatus.ASSIGNED.value, ErrorStatus.INVESTIGATING.value]
                )
            )
            .label("investigating_count"),
            func.count()
            .filter(ErrorRecord.status == ErrorStatus.RESOLVED.value)
            .label("resolved_count"),
            func.count()
            .filter(
                ErrorRecord.status.in_(
                    [
                        ErrorStatus.VERIFYING.value,
                        ErrorStatus.VERIFIED.value,
                        ErrorStatus.CLOSED.value,
                    ]
                )
            )
            .label("verified_count"),
        ).where(ErrorRecord.company_id == company_id)
        counts_res = await self.db.execute(count_stmt)
        counts_row = counts_res.fetchone()

        total = counts_row.total if counts_row else len(records)
        open_count = counts_row.open_count if counts_row else 0
        investigating_count = counts_row.investigating_count if counts_row else 0
        resolved_count = counts_row.resolved_count if counts_row else 0
        verified_count = counts_row.verified_count if counts_row else 0

        items = [self._to_response(r) for r in records]
        return ErrorListResponse(
            items=items,
            total=total,
            open_count=open_count,
            investigating_count=investigating_count,
            resolved_count=resolved_count,
            verified_count=verified_count,
        )

    async def get_error(
        self,
        company_id: str,
        error_id: str,
        user_id: str | None = None,
    ) -> ErrorRecordResponse:
        """Retrieve a single error record by ID."""
        if user_id:
            await self._verify_company_access(company_id=company_id, user_id=user_id)
        record = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        return self._to_response(record)

    async def update_error(
        self,
        company_id: str,
        error_id: str,
        payload: ErrorUpdatePayload,
        user_id: str | None = None,
    ) -> ErrorRecordResponse:
        """Update fields of an error record."""
        if user_id:
            await self._verify_company_access(company_id=company_id, user_id=user_id)

        record = await self._fetch_error_record(company_id=company_id, error_id=error_id)

        if payload.title is not None:
            record.title = payload.title
        if payload.description is not None:
            record.description = payload.description
        if payload.severity is not None:
            record.severity = payload.severity.value
        if payload.status is not None:
            record.status = payload.status.value
        if payload.assigned_to is not None:
            record.assigned_to = payload.assigned_to
        if payload.assigned_agent_id is not None:
            record.assigned_agent_id = payload.assigned_agent_id
        if payload.assigned_user_id is not None:
            record.assigned_user_id = payload.assigned_user_id
        if payload.investigated_by is not None:
            record.investigated_by = payload.investigated_by
        if payload.resolved_by is not None:
            record.resolved_by = payload.resolved_by
        if payload.verified_by is not None:
            record.verified_by = payload.verified_by
        if payload.root_cause is not None:
            record.root_cause = payload.root_cause
        if payload.resolution is not None:
            record.resolution = payload.resolution
        if payload.evidence is not None:
            merged_evidence = dict(record.evidence or {})
            merged_evidence.update(payload.evidence)
            record.evidence = merged_evidence

        await self.db.commit()
        loaded = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        return self._to_response(loaded)

    async def assign_error(
        self,
        company_id: str,
        error_id: str,
        payload: ErrorAssignPayload,
        user_id: str | None = None,
    ) -> ErrorRecordResponse:
        """Assign an error to an agent or user."""
        if user_id:
            await self._verify_company_access(company_id=company_id, user_id=user_id)

        record = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        record.assigned_to = payload.assigned_to
        if payload.assigned_agent_id:
            record.assigned_agent_id = payload.assigned_agent_id
        if payload.assigned_user_id:
            record.assigned_user_id = payload.assigned_user_id

        if record.status in [ErrorStatus.OPEN.value, ErrorStatus.TRIAGED.value]:
            record.status = ErrorStatus.ASSIGNED.value

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            event_type="error.assigned",
            message=f"Error '{record.title}' assigned to {payload.assigned_to}",
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            project_id=record.project_id,
            task_id=record.task_id,
            metadata={"error_id": record.id, "assigned_to": payload.assigned_to},
        )
        await self.db.commit()
        loaded = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        return self._to_response(loaded)

    async def start_investigation(
        self,
        company_id: str,
        error_id: str,
        investigated_by: str,
        user_id: str | None = None,
    ) -> ErrorRecordResponse:
        """Mark an error as under active investigation."""
        if user_id:
            await self._verify_company_access(company_id=company_id, user_id=user_id)

        record = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        record.investigated_by = investigated_by
        record.status = ErrorStatus.INVESTIGATING.value

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            event_type="error.investigating",
            message=f"Error '{record.title}' is being investigated by {investigated_by}",
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            project_id=record.project_id,
            task_id=record.task_id,
            metadata={"error_id": record.id, "investigated_by": investigated_by},
        )
        await self.db.commit()
        loaded = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        return self._to_response(loaded)

    async def resolve_error(
        self,
        company_id: str,
        error_id: str,
        payload: ErrorResolvePayload,
        user_id: str | None = None,
    ) -> ErrorRecordResponse:
        """Mark an error as resolved with root cause and resolution description."""
        if user_id:
            await self._verify_company_access(company_id=company_id, user_id=user_id)

        if not payload.resolution or not payload.resolution.strip():
            raise MissingResolutionError("Resolution description is required to resolve an error.")

        record = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        record.resolved_by = payload.resolved_by
        record.resolution = payload.resolution.strip()
        if payload.root_cause:
            record.root_cause = payload.root_cause.strip()

        record.status = ErrorStatus.RESOLVED.value
        record.resolved_at = datetime.now(UTC)

        if payload.evidence:
            merged = dict(record.evidence or {})
            merged.update(payload.evidence)
            record.evidence = merged

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            event_type="error.resolved",
            message=f"Error '{record.title}' resolved by {payload.resolved_by}",
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            project_id=record.project_id,
            task_id=record.task_id,
            metadata={"error_id": record.id, "resolved_by": payload.resolved_by},
        )
        await self.db.commit()
        loaded = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        return self._to_response(loaded)

    async def verify_error(
        self,
        company_id: str,
        error_id: str,
        payload: ErrorVerifyPayload,
        user_id: str | None = None,
    ) -> ErrorRecordResponse:
        """Verify an error resolution with proof/evidence per docs/Phases.md Section 19."""
        if user_id:
            await self._verify_company_access(company_id=company_id, user_id=user_id)

        if not payload.evidence or len(payload.evidence) == 0:
            raise MissingEvidenceError(
                "Evidence of verification (tests, logs, outputs) is required to verify resolution."
            )

        record = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        record.verified_by = payload.verified_by
        record.verified_at = datetime.now(UTC)

        merged = dict(record.evidence or {})
        merged.update(payload.evidence)
        record.evidence = merged

        if payload.close_immediately:
            record.status = ErrorStatus.CLOSED.value
        else:
            record.status = ErrorStatus.VERIFIED.value

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            event_type="error.verified",
            message=f"Error '{record.title}' verified by {payload.verified_by}",
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            project_id=record.project_id,
            task_id=record.task_id,
            metadata={"error_id": record.id, "verified_by": payload.verified_by},
        )
        await self.db.commit()
        loaded = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        return self._to_response(loaded)

    async def reopen_error(
        self,
        company_id: str,
        error_id: str,
        reason: str,
        actor: str = "operator",
        user_id: str | None = None,
    ) -> ErrorRecordResponse:
        """Reopen a previously resolved or verified error if the bug persists."""
        if user_id:
            await self._verify_company_access(company_id=company_id, user_id=user_id)

        record = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        record.status = ErrorStatus.REOPENED.value
        record.resolved_at = None
        record.verified_at = None

        merged = dict(record.evidence or {})
        merged["reopened_reason"] = reason
        merged["reopened_by"] = actor
        record.evidence = merged

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            event_type="error.reopened",
            message=f"Error '{record.title}' reopened by {actor}: {reason}",
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            project_id=record.project_id,
            task_id=record.task_id,
            metadata={"error_id": record.id, "reason": reason},
        )
        await self.db.commit()
        loaded = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        return self._to_response(loaded)

    async def close_error(
        self,
        company_id: str,
        error_id: str,
        actor: str = "operator",
        user_id: str | None = None,
    ) -> ErrorRecordResponse:
        """Formally close an error after completed verification."""
        if user_id:
            await self._verify_company_access(company_id=company_id, user_id=user_id)

        record = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        record.status = ErrorStatus.CLOSED.value

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            event_type="error.closed",
            message=f"Error '{record.title}' closed by {actor}",
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            project_id=record.project_id,
            task_id=record.task_id,
            metadata={"error_id": record.id, "closed_by": actor},
        )
        await self.db.commit()
        loaded = await self._fetch_error_record(company_id=company_id, error_id=error_id)
        return self._to_response(loaded)

    async def get_error_summary(
        self,
        company_id: str,
        user_id: str | None = None,
    ) -> ErrorSummaryResponse:
        """Aggregate error status and severity metrics for executive dashboards."""
        if user_id:
            await self._verify_company_access(company_id=company_id, user_id=user_id)

        stmt = select(
            func.count().label("total"),
            func.count().filter(ErrorRecord.status == ErrorStatus.OPEN.value).label("open"),
            func.count().filter(ErrorRecord.status == ErrorStatus.TRIAGED.value).label("triaged"),
            func.count().filter(ErrorRecord.status == ErrorStatus.ASSIGNED.value).label("assigned"),
            func.count()
            .filter(ErrorRecord.status == ErrorStatus.INVESTIGATING.value)
            .label("investigating"),
            func.count().filter(ErrorRecord.status == ErrorStatus.BLOCKED.value).label("blocked"),
            func.count().filter(ErrorRecord.status == ErrorStatus.RESOLVED.value).label("resolved"),
            func.count()
            .filter(ErrorRecord.status == ErrorStatus.VERIFYING.value)
            .label("verifying"),
            func.count().filter(ErrorRecord.status == ErrorStatus.VERIFIED.value).label("verified"),
            func.count().filter(ErrorRecord.status == ErrorStatus.REOPENED.value).label("reopened"),
            func.count().filter(ErrorRecord.status == ErrorStatus.CLOSED.value).label("closed"),
            func.count()
            .filter(ErrorRecord.severity == ErrorSeverity.CRITICAL.value)
            .label("critical"),
            func.count().filter(ErrorRecord.severity == ErrorSeverity.HIGH.value).label("high"),
            func.count().filter(ErrorRecord.severity == ErrorSeverity.MEDIUM.value).label("medium"),
            func.count().filter(ErrorRecord.severity == ErrorSeverity.LOW.value).label("low"),
        ).where(ErrorRecord.company_id == company_id)
        res = await self.db.execute(stmt)
        row = res.fetchone()

        if not row:
            return ErrorSummaryResponse()

        return ErrorSummaryResponse(
            total_errors=row.total or 0,
            open_count=row.open or 0,
            triaged_count=row.triaged or 0,
            assigned_count=row.assigned or 0,
            investigating_count=row.investigating or 0,
            blocked_count=row.blocked or 0,
            resolved_count=row.resolved or 0,
            verifying_count=row.verifying or 0,
            verified_count=row.verified or 0,
            reopened_count=row.reopened or 0,
            closed_count=row.closed or 0,
            critical_count=row.critical or 0,
            high_count=row.high or 0,
            medium_count=row.medium or 0,
            low_count=row.low or 0,
        )
