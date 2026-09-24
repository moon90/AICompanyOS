"""Application service for engineering file tracking adhering to docs/Phases.md Section 20 and docs/Memory.md Section 61."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application.services.activity_service import ActivityService
from domain.engineering.exceptions import (
    EngineeringAccessDeniedError,
    InvalidEngineeringOperationError,
)
from domain.engineering.schemas import (
    CompanyFileHistoryItem,
    EngineeringContextResponse,
    EngineeringContextUpsertPayload,
    EngineeringTaskViewResponse,
    FileChangeBulkCreatePayload,
    FileChangeResponse,
    VerificationState,
)
from domain.work.exceptions import TaskNotFoundError
from infrastructure.database.models import (
    CompanyMember,
    Task,
    TaskEngineeringContext,
    TaskFileChange,
)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure datetime is UTC-aware, handling SQLite naive datetime values in tests."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class EngineeringService:
    """Authoritative engineering file tracking orchestrator.

    Connects engineering tasks to code artifacts, branches, commits, PRs, and verification states.
    Does NOT replace Git; stores operational context and task attribution.
    """

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
        member = result.scalar_one_or_none()
        if not member:
            raise EngineeringAccessDeniedError(
                f"User {user_id} does not have access to company {company_id}"
            )
        return member

    async def _get_task(self, company_id: str, task_id: str) -> Task:
        """Retrieve task ensuring it belongs to the given company."""
        result = await self.db.execute(
            select(Task)
            .options(selectinload(Task.assigned_agent))
            .where(
                Task.id == task_id,
                Task.company_id == company_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found in company {company_id}")
        return task

    async def get_task_engineering_view(
        self,
        company_id: str,
        task_id: str,
        user_id: str | None = None,
    ) -> EngineeringTaskViewResponse:
        """Fetch unified engineering view for a task: context and all tracked file changes."""
        if user_id:
            await self._verify_company_access(company_id, user_id)
        await self._get_task(company_id, task_id)

        # Context query
        ctx_result = await self.db.execute(
            select(TaskEngineeringContext).where(
                TaskEngineeringContext.company_id == company_id,
                TaskEngineeringContext.task_id == task_id,
            )
        )
        context_record = ctx_result.scalar_one_or_none()

        # File changes query
        changes_result = await self.db.execute(
            select(TaskFileChange)
            .where(
                TaskFileChange.company_id == company_id,
                TaskFileChange.task_id == task_id,
            )
            .order_by(desc(TaskFileChange.last_modified_at))
        )
        file_change_records = list(changes_result.scalars().all())

        context_resp = None
        if context_record:
            context_resp = EngineeringContextResponse(
                id=context_record.id,
                company_id=context_record.company_id,
                task_id=context_record.task_id,
                repository=context_record.repository,
                branch=context_record.branch,
                pull_request_number=context_record.pull_request_number,
                pull_request_url=context_record.pull_request_url,
                pull_request_title=context_record.pull_request_title,
                commit_count=context_record.commit_count,
                test_status=context_record.test_status,
                test_output_summary=context_record.test_output_summary,
                verification_state=context_record.verification_state,
                verification_notes=context_record.verification_notes,
                created_at=_ensure_utc(context_record.created_at) or datetime.now(UTC),
                updated_at=_ensure_utc(context_record.updated_at) or datetime.now(UTC),
            )

        file_change_resps = [
            FileChangeResponse(
                id=c.id,
                company_id=c.company_id,
                task_id=c.task_id,
                file_path=c.file_path,
                repository=c.repository,
                branch=c.branch,
                agent_id=c.agent_id,
                agent_name=c.agent_name,
                change_type=c.change_type,
                commit_hash=c.commit_hash,
                commit_message=c.commit_message,
                additions=c.additions,
                deletions=c.deletions,
                change_summary=c.change_summary,
                last_modified_at=_ensure_utc(c.last_modified_at) or datetime.now(UTC),
                created_at=_ensure_utc(c.created_at) or datetime.now(UTC),
            )
            for c in file_change_records
        ]

        total_additions = sum(c.additions for c in file_change_records)
        total_deletions = sum(c.deletions for c in file_change_records)

        return EngineeringTaskViewResponse(
            task_id=task_id,
            company_id=company_id,
            context=context_resp,
            file_changes=file_change_resps,
            total_files_changed=len(file_change_resps),
            total_additions=total_additions,
            total_deletions=total_deletions,
        )

    async def upsert_engineering_context(
        self,
        company_id: str,
        task_id: str,
        payload: EngineeringContextUpsertPayload,
        user_id: str | None = None,
    ) -> EngineeringContextResponse:
        """Create or update engineering context for a task."""
        if user_id:
            await self._verify_company_access(company_id, user_id)
        task = await self._get_task(company_id, task_id)

        result = await self.db.execute(
            select(TaskEngineeringContext).where(
                TaskEngineeringContext.company_id == company_id,
                TaskEngineeringContext.task_id == task_id,
            )
        )
        context = result.scalar_one_or_none()

        old_verification = context.verification_state if context else None

        if context is None:
            is_new = True
            context = TaskEngineeringContext(
                id=str(uuid.uuid4()),
                company_id=company_id,
                task_id=task_id,
                repository=payload.repository or "main",
                branch=payload.branch or "main",
                pull_request_number=payload.pull_request_number,
                pull_request_url=payload.pull_request_url,
                pull_request_title=payload.pull_request_title,
                commit_count=payload.commit_count if payload.commit_count is not None else 0,
                test_status=payload.test_status.value if payload.test_status else "PENDING",
                test_output_summary=payload.test_output_summary,
                verification_state=(
                    payload.verification_state.value if payload.verification_state else "PENDING"
                ),
                verification_notes=payload.verification_notes,
            )
            self.db.add(context)
        else:
            is_new = False
            if payload.repository is not None:
                context.repository = payload.repository
            if payload.branch is not None:
                context.branch = payload.branch
            if payload.pull_request_number is not None:
                context.pull_request_number = payload.pull_request_number
            if payload.pull_request_url is not None:
                context.pull_request_url = payload.pull_request_url
            if payload.pull_request_title is not None:
                context.pull_request_title = payload.pull_request_title
            if payload.commit_count is not None:
                context.commit_count = payload.commit_count
            if payload.test_status is not None:
                context.test_status = payload.test_status.value
            if payload.test_output_summary is not None:
                context.test_output_summary = payload.test_output_summary
            if payload.verification_state is not None:
                context.verification_state = payload.verification_state.value
            if payload.verification_notes is not None:
                context.verification_notes = payload.verification_notes

        await self.db.flush()

        # Emit Activity Event
        event_type = "engineering.context_created" if is_new else "engineering.context_updated"
        msg = (
            f"Engineering context initialized for task '{task.title}' on branch '{context.branch}'"
            if is_new
            else f"Engineering context updated for task '{task.title}' ({context.branch}, PR: {context.pull_request_number or 'None'})"
        )
        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            project_id=task.project_id,
            task_id=task_id,
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            event_type=event_type,
            message=msg,
            metadata={
                "branch": context.branch,
                "repository": context.repository,
                "verification_state": context.verification_state,
                "test_status": context.test_status,
                "pull_request_number": context.pull_request_number,
            },
        )

        if context.verification_state != old_verification:
            if context.verification_state == VerificationState.VERIFIED.value:
                await ActivityService.record_event(
                    session=self.db,
                    company_id=company_id,
                    project_id=task.project_id,
                    task_id=task_id,
                    actor_type="user" if user_id else "system",
                    actor_id=user_id,
                    event_type="engineering.verified",
                    message=f"Engineering verification passed for task '{task.title}'",
                    metadata={"verification_notes": context.verification_notes},
                )
            elif context.verification_state == VerificationState.REJECTED.value:
                await ActivityService.record_event(
                    session=self.db,
                    company_id=company_id,
                    project_id=task.project_id,
                    task_id=task_id,
                    actor_type="user" if user_id else "system",
                    actor_id=user_id,
                    event_type="engineering.verification_rejected",
                    message=f"Engineering verification rejected for task '{task.title}'",
                    metadata={"verification_notes": context.verification_notes},
                )

        # Re-fetch context to avoid lazy-loading expired attributes without greenlet
        re_result = await self.db.execute(
            select(TaskEngineeringContext).where(
                TaskEngineeringContext.company_id == company_id,
                TaskEngineeringContext.task_id == task_id,
            )
        )
        context = re_result.scalar_one()

        return EngineeringContextResponse(
            id=context.id,
            company_id=context.company_id,
            task_id=context.task_id,
            repository=context.repository,
            branch=context.branch,
            pull_request_number=context.pull_request_number,
            pull_request_url=context.pull_request_url,
            pull_request_title=context.pull_request_title,
            commit_count=context.commit_count,
            test_status=context.test_status,
            test_output_summary=context.test_output_summary,
            verification_state=context.verification_state,
            verification_notes=context.verification_notes,
            created_at=_ensure_utc(context.created_at) or datetime.now(UTC),
            updated_at=_ensure_utc(context.updated_at) or datetime.now(UTC),
        )

    async def record_file_changes(
        self,
        company_id: str,
        task_id: str,
        payload: FileChangeBulkCreatePayload,
        user_id: str | None = None,
    ) -> list[FileChangeResponse]:
        """Record batch file changes attributed to an engineering task."""
        if user_id:
            await self._verify_company_access(company_id, user_id)
        task = await self._get_task(company_id, task_id)

        if not payload.changes:
            raise InvalidEngineeringOperationError("No file changes provided")

        new_entities: list[TaskFileChange] = []
        default_agent_name = task.assigned_agent.name if task.assigned_agent else "System Engineer"

        for change in payload.changes:
            entity = TaskFileChange(
                id=str(uuid.uuid4()),
                company_id=company_id,
                task_id=task_id,
                file_path=change.file_path,
                repository=change.repository,
                branch=change.branch,
                agent_id=change.agent_id or task.assigned_to_agent_id,
                agent_name=change.agent_name or default_agent_name,
                change_type=change.change_type.value,
                commit_hash=change.commit_hash,
                commit_message=change.commit_message,
                additions=change.additions,
                deletions=change.deletions,
                change_summary=change.change_summary,
                last_modified_at=datetime.now(UTC),
            )
            self.db.add(entity)
            new_entities.append(entity)

        # Ensure engineering context exists / sync commit count if given
        ctx_result = await self.db.execute(
            select(TaskEngineeringContext).where(
                TaskEngineeringContext.company_id == company_id,
                TaskEngineeringContext.task_id == task_id,
            )
        )
        context = ctx_result.scalar_one_or_none()
        primary_branch = payload.changes[0].branch
        primary_repo = payload.changes[0].repository

        if not context:
            context = TaskEngineeringContext(
                id=str(uuid.uuid4()),
                company_id=company_id,
                task_id=task_id,
                repository=primary_repo,
                branch=primary_branch,
                commit_count=1 if payload.changes[0].commit_hash else 0,
            )
            self.db.add(context)
        else:
            if context.branch == "main" and primary_branch != "main":
                context.branch = primary_branch
            if payload.changes[0].commit_hash:
                context.commit_count += 1

        await self.db.flush()

        # Emit Activity Event
        file_paths = [c.file_path for c in payload.changes[:5]]
        if len(payload.changes) > 5:
            file_paths.append(f"... +{len(payload.changes) - 5} more")

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            project_id=task.project_id,
            task_id=task_id,
            actor_type="user" if user_id else "agent",
            actor_id=user_id or task.assigned_to_agent_id,
            event_type="engineering.file_changes_recorded",
            message=f"Recorded {len(payload.changes)} file change(s) for task '{task.title}' on branch '{primary_branch}'",
            metadata={
                "files_count": len(payload.changes),
                "branch": primary_branch,
                "repository": primary_repo,
                "sample_files": file_paths,
            },
        )

        # Re-fetch entities to avoid lazy-loading expired attributes without greenlet
        re_files = await self.db.execute(
            select(TaskFileChange)
            .where(
                TaskFileChange.company_id == company_id,
                TaskFileChange.id.in_([e.id for e in new_entities]),
            )
            .order_by(desc(TaskFileChange.last_modified_at))
        )
        saved_entities = list(re_files.scalars().all())
        entity_map = {e.id: e for e in saved_entities}
        ordered_entities = [entity_map[e.id] for e in new_entities if e.id in entity_map]

        return [
            FileChangeResponse(
                id=e.id,
                company_id=e.company_id,
                task_id=e.task_id,
                file_path=e.file_path,
                repository=e.repository,
                branch=e.branch,
                agent_id=e.agent_id,
                agent_name=e.agent_name,
                change_type=e.change_type,
                commit_hash=e.commit_hash,
                commit_message=e.commit_message,
                additions=e.additions,
                deletions=e.deletions,
                change_summary=e.change_summary,
                last_modified_at=_ensure_utc(e.last_modified_at) or datetime.now(UTC),
                created_at=_ensure_utc(e.created_at) or datetime.now(UTC),
            )
            for e in ordered_entities
        ]

    async def get_company_file_history(
        self,
        company_id: str,
        user_id: str | None = None,
        branch: str | None = None,
        limit: int = 50,
    ) -> list[CompanyFileHistoryItem]:
        """Aggregate company-wide file touches across tasks and branches."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        query = select(TaskFileChange).where(TaskFileChange.company_id == company_id)
        if branch:
            query = query.where(TaskFileChange.branch == branch)
        query = query.order_by(desc(TaskFileChange.last_modified_at))

        result = await self.db.execute(query)
        all_changes = list(result.scalars().all())

        # Group by file_path and repository
        grouped: dict[str, list[TaskFileChange]] = {}
        for c in all_changes:
            key = f"{c.repository}:{c.file_path}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(c)

        items: list[CompanyFileHistoryItem] = []
        for _key, changes in grouped.items():
            first = changes[0]  # newest change
            branches = list({c.branch for c in changes})
            items.append(
                CompanyFileHistoryItem(
                    file_path=first.file_path,
                    repository=first.repository,
                    branches=branches,
                    change_count=len(changes),
                    last_modified_at=_ensure_utc(first.last_modified_at) or datetime.now(UTC),
                    last_commit_hash=first.commit_hash,
                    last_agent_id=first.agent_id,
                    last_agent_name=first.agent_name,
                )
            )

        items.sort(key=lambda x: x.last_modified_at, reverse=True)
        return items[:limit]
