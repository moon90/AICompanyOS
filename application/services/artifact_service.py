"""Application service for artifacts and documents adhering to docs/Phases.md Section 22 and docs/Memory.md Section 31."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.activity_service import ActivityService
from domain.agents.exceptions import AgentNotFoundError
from domain.artifacts.exceptions import (
    ArtifactAccessDeniedError,
    ArtifactNotFoundError,
)
from domain.artifacts.schemas import (
    ArtifactCreatePayload,
    ArtifactListResponse,
    ArtifactResponse,
    ArtifactUpdatePayload,
    ArtifactVersionCreatePayload,
    ArtifactVersionItem,
)
from domain.work.exceptions import ProjectNotFoundError, TaskNotFoundError
from infrastructure.database.models import (
    Agent,
    Artifact,
    CompanyMember,
    Project,
    Task,
    User,
)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure datetime is UTC-aware, handling SQLite naive datetime values in tests."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class ArtifactService:
    """Authoritative artifacts and documents manager adhering to docs/Phases.md Section 22.

    Tracks reports, summaries, code, text, markdown, and structured outputs
    produced by agents and operators with full version lineage.
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
            raise ArtifactAccessDeniedError(
                f"User {user_id} does not have access to company {company_id}"
            )
        return member

    def _to_response(self, artifact: Artifact) -> ArtifactResponse:
        """Convert ORM model to ArtifactResponse schema."""
        created_at = _ensure_utc(artifact.created_at) or datetime.now(UTC)
        updated_at = _ensure_utc(artifact.updated_at) or datetime.now(UTC)
        return ArtifactResponse(
            id=artifact.id,
            company_id=artifact.company_id,
            project_id=artifact.project_id,
            task_id=artifact.task_id,
            created_by_agent_id=artifact.created_by_agent_id,
            created_by_user_id=artifact.created_by_user_id,
            creator_name=artifact.creator_name,
            name=artifact.name,
            artifact_type=artifact.artifact_type,
            version=artifact.version,
            parent_artifact_id=artifact.parent_artifact_id,
            location=artifact.location,
            content=artifact.content,
            file_size_bytes=artifact.file_size_bytes,
            change_summary=artifact.change_summary,
            metadata=dict(artifact.artifact_metadata or {}),
            created_at=created_at,
            updated_at=updated_at,
        )

    async def create_artifact(
        self,
        company_id: str,
        payload: ArtifactCreatePayload,
        user_id: str | None = None,
    ) -> ArtifactResponse:
        """Create a new root (v1) artifact or document."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        # Validate project if provided
        if payload.project_id:
            proj_res = await self.db.execute(
                select(Project).where(
                    Project.id == payload.project_id,
                    Project.company_id == company_id,
                )
            )
            if not proj_res.scalar_one_or_none():
                raise ProjectNotFoundError(
                    f"Project {payload.project_id} not found in company {company_id}"
                )

        # Validate task if provided
        if payload.task_id:
            task_res = await self.db.execute(
                select(Task).where(
                    Task.id == payload.task_id,
                    Task.company_id == company_id,
                )
            )
            if not task_res.scalar_one_or_none():
                raise TaskNotFoundError(f"Task {payload.task_id} not found in company {company_id}")

        # Resolve creator attribution
        creator_name = payload.creator_name
        if not creator_name:
            if payload.created_by_agent_id:
                agent_res = await self.db.execute(
                    select(Agent).where(
                        Agent.id == payload.created_by_agent_id,
                        Agent.company_id == company_id,
                    )
                )
                agent = agent_res.scalar_one_or_none()
                if not agent:
                    raise AgentNotFoundError(
                        f"Agent {payload.created_by_agent_id} not found in company {company_id}"
                    )
                creator_name = agent.name
            elif user_id or payload.created_by_user_id:
                uid = payload.created_by_user_id or user_id
                u_res = await self.db.execute(select(User).where(User.id == uid))
                u = u_res.scalar_one_or_none()
                creator_name = u.name if u else "User"
            else:
                creator_name = "Operator"

        # Compute file size if not explicitly provided
        file_size = payload.file_size_bytes
        if file_size is None or file_size == 0:
            file_size = len(payload.content.encode("utf-8")) if payload.content else 0

        artifact = Artifact(
            id=str(uuid.uuid4()),
            company_id=company_id,
            project_id=payload.project_id,
            task_id=payload.task_id,
            created_by_agent_id=payload.created_by_agent_id,
            created_by_user_id=payload.created_by_user_id or user_id,
            creator_name=creator_name,
            name=payload.name.strip(),
            artifact_type=str(payload.artifact_type),
            version=1,
            parent_artifact_id=None,
            location=payload.location,
            content=payload.content,
            file_size_bytes=file_size,
            change_summary=payload.change_summary or "Initial version",
            artifact_metadata=payload.metadata,
        )
        self.db.add(artifact)
        await self.db.flush()

        # Emit Activity Event
        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            project_id=payload.project_id,
            task_id=payload.task_id,
            actor_type="agent" if payload.created_by_agent_id else "user",
            actor_id=payload.created_by_agent_id or user_id or payload.created_by_user_id,
            event_type="artifact.created",
            message=f"Artifact '{artifact.name}' (v1, {artifact.artifact_type}) created by {artifact.creator_name}",
            metadata={
                "artifact_id": artifact.id,
                "artifact_name": artifact.name,
                "artifact_type": artifact.artifact_type,
                "version": 1,
                "file_size_bytes": artifact.file_size_bytes,
            },
        )
        await self.db.commit()
        await self.db.refresh(artifact)

        return self._to_response(artifact)

    async def get_artifact(
        self,
        company_id: str,
        artifact_id: str,
        user_id: str | None = None,
    ) -> ArtifactResponse:
        """Fetch a specific artifact ensuring multi-tenant isolation."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        res = await self.db.execute(
            select(Artifact).where(
                Artifact.id == artifact_id,
                Artifact.company_id == company_id,
            )
        )
        artifact = res.scalar_one_or_none()
        if not artifact:
            raise ArtifactNotFoundError(f"Artifact {artifact_id} not found in company {company_id}")

        return self._to_response(artifact)

    async def list_artifacts(
        self,
        company_id: str,
        user_id: str | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
        artifact_type: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> ArtifactListResponse:
        """List artifacts with optional filtering, search, and pagination."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        filters = [Artifact.company_id == company_id]
        if project_id:
            filters.append(Artifact.project_id == project_id)
        if task_id:
            filters.append(Artifact.task_id == task_id)
        if artifact_type:
            filters.append(func.upper(Artifact.artifact_type) == artifact_type.strip().upper())
        if search:
            s = f"%{search.strip()}%"
            filters.append(
                or_(
                    Artifact.name.ilike(s),
                    Artifact.creator_name.ilike(s),
                    Artifact.location.ilike(s),
                    Artifact.change_summary.ilike(s),
                )
            )

        count_stmt = select(func.count()).select_from(Artifact).where(*filters)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        stmt = (
            select(Artifact)
            .where(*filters)
            .order_by(desc(Artifact.created_at))
            .offset(offset)
            .limit(page_size)
        )
        res = await self.db.execute(stmt)
        artifacts = res.scalars().all()

        items = [self._to_response(a) for a in artifacts]
        return ArtifactListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_artifact(
        self,
        company_id: str,
        artifact_id: str,
        payload: ArtifactUpdatePayload,
        user_id: str | None = None,
    ) -> ArtifactResponse:
        """Update an artifact's attributes."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        res = await self.db.execute(
            select(Artifact).where(
                Artifact.id == artifact_id,
                Artifact.company_id == company_id,
            )
        )
        artifact = res.scalar_one_or_none()
        if not artifact:
            raise ArtifactNotFoundError(f"Artifact {artifact_id} not found in company {company_id}")

        if payload.project_id is not None:
            if payload.project_id != "":
                proj_res = await self.db.execute(
                    select(Project).where(
                        Project.id == payload.project_id,
                        Project.company_id == company_id,
                    )
                )
                if not proj_res.scalar_one_or_none():
                    raise ProjectNotFoundError(
                        f"Project {payload.project_id} not found in company {company_id}"
                    )
                artifact.project_id = payload.project_id
            else:
                artifact.project_id = None

        if payload.task_id is not None:
            if payload.task_id != "":
                task_res = await self.db.execute(
                    select(Task).where(
                        Task.id == payload.task_id,
                        Task.company_id == company_id,
                    )
                )
                if not task_res.scalar_one_or_none():
                    raise TaskNotFoundError(
                        f"Task {payload.task_id} not found in company {company_id}"
                    )
                artifact.task_id = payload.task_id
            else:
                artifact.task_id = None

        if payload.name is not None:
            artifact.name = payload.name.strip()
        if payload.artifact_type is not None:
            artifact.artifact_type = str(payload.artifact_type)
        if payload.location is not None:
            artifact.location = payload.location
        if payload.change_summary is not None:
            artifact.change_summary = payload.change_summary
        if payload.content is not None:
            artifact.content = payload.content
            if payload.file_size_bytes is None:
                artifact.file_size_bytes = len(payload.content.encode("utf-8"))
        if payload.file_size_bytes is not None:
            artifact.file_size_bytes = payload.file_size_bytes
        if payload.metadata is not None:
            merged = dict(artifact.artifact_metadata or {})
            merged.update(payload.metadata)
            artifact.artifact_metadata = merged

        await self.db.flush()

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            project_id=artifact.project_id,
            task_id=artifact.task_id,
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            event_type="artifact.updated",
            message=f"Artifact '{artifact.name}' (v{artifact.version}) updated",
            metadata={
                "artifact_id": artifact.id,
                "version": artifact.version,
            },
        )
        await self.db.commit()
        await self.db.refresh(artifact)

        return self._to_response(artifact)

    async def create_new_version(
        self,
        company_id: str,
        artifact_id: str,
        payload: ArtifactVersionCreatePayload,
        user_id: str | None = None,
    ) -> ArtifactResponse:
        """Create an incremented version linked to the lineage root."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        res = await self.db.execute(
            select(Artifact).where(
                Artifact.id == artifact_id,
                Artifact.company_id == company_id,
            )
        )
        target = res.scalar_one_or_none()
        if not target:
            raise ArtifactNotFoundError(f"Artifact {artifact_id} not found in company {company_id}")

        # Lineage root is either target's parent or target itself
        root_id = target.parent_artifact_id or target.id

        # Calculate next version number
        ver_stmt = select(func.max(Artifact.version)).where(
            Artifact.company_id == company_id,
            or_(Artifact.id == root_id, Artifact.parent_artifact_id == root_id),
        )
        max_ver = (await self.db.execute(ver_stmt)).scalar() or target.version
        next_ver = max_ver + 1

        # Resolve creator attribution
        creator_name = payload.creator_name
        if not creator_name:
            if payload.created_by_agent_id:
                agent_res = await self.db.execute(
                    select(Agent).where(
                        Agent.id == payload.created_by_agent_id,
                        Agent.company_id == company_id,
                    )
                )
                agent = agent_res.scalar_one_or_none()
                creator_name = agent.name if agent else "Agent"
            elif user_id or payload.created_by_user_id:
                uid = payload.created_by_user_id or user_id
                u_res = await self.db.execute(select(User).where(User.id == uid))
                u = u_res.scalar_one_or_none()
                creator_name = u.name if u else "User"
            else:
                creator_name = target.creator_name

        content = payload.content if payload.content is not None else target.content
        location = payload.location or target.location
        file_size = payload.file_size_bytes
        if file_size is None:
            file_size = len(content.encode("utf-8")) if content else target.file_size_bytes

        merged_metadata = dict(target.artifact_metadata or {})
        merged_metadata.update(payload.metadata)

        new_version_artifact = Artifact(
            id=str(uuid.uuid4()),
            company_id=company_id,
            project_id=target.project_id,
            task_id=target.task_id,
            created_by_agent_id=payload.created_by_agent_id or target.created_by_agent_id,
            created_by_user_id=payload.created_by_user_id or user_id or target.created_by_user_id,
            creator_name=creator_name,
            name=target.name,
            artifact_type=target.artifact_type,
            version=next_ver,
            parent_artifact_id=root_id,
            location=location,
            content=content,
            file_size_bytes=file_size,
            change_summary=payload.change_summary,
            artifact_metadata=merged_metadata,
        )
        self.db.add(new_version_artifact)
        await self.db.flush()

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            project_id=target.project_id,
            task_id=target.task_id,
            actor_type="agent" if payload.created_by_agent_id else "user",
            actor_id=payload.created_by_agent_id or user_id or payload.created_by_user_id,
            event_type="artifact.versioned",
            message=f"New version v{next_ver} created for artifact '{target.name}' by {creator_name}: {payload.change_summary}",
            metadata={
                "artifact_id": new_version_artifact.id,
                "parent_artifact_id": root_id,
                "version": next_ver,
                "change_summary": payload.change_summary,
            },
        )
        await self.db.commit()
        await self.db.refresh(new_version_artifact)

        return self._to_response(new_version_artifact)

    async def get_version_history(
        self,
        company_id: str,
        artifact_id: str,
        user_id: str | None = None,
    ) -> list[ArtifactVersionItem]:
        """Fetch all versions belonging to the target artifact's lineage."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        res = await self.db.execute(
            select(Artifact).where(
                Artifact.id == artifact_id,
                Artifact.company_id == company_id,
            )
        )
        target = res.scalar_one_or_none()
        if not target:
            raise ArtifactNotFoundError(f"Artifact {artifact_id} not found in company {company_id}")

        root_id = target.parent_artifact_id or target.id

        stmt = (
            select(Artifact)
            .where(
                Artifact.company_id == company_id,
                or_(Artifact.id == root_id, Artifact.parent_artifact_id == root_id),
            )
            .order_by(Artifact.version.asc())
        )
        rows = (await self.db.execute(stmt)).scalars().all()

        return [
            ArtifactVersionItem(
                id=item.id,
                version=item.version,
                creator_name=item.creator_name,
                change_summary=item.change_summary,
                file_size_bytes=item.file_size_bytes,
                created_at=_ensure_utc(item.created_at) or datetime.now(UTC),
                parent_artifact_id=item.parent_artifact_id,
            )
            for item in rows
        ]

    async def delete_artifact(
        self,
        company_id: str,
        artifact_id: str,
        user_id: str | None = None,
    ) -> bool:
        """Delete an artifact record."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        res = await self.db.execute(
            select(Artifact).where(
                Artifact.id == artifact_id,
                Artifact.company_id == company_id,
            )
        )
        artifact = res.scalar_one_or_none()
        if not artifact:
            raise ArtifactNotFoundError(f"Artifact {artifact_id} not found in company {company_id}")

        name = artifact.name
        version = artifact.version
        proj_id = artifact.project_id
        t_id = artifact.task_id

        await self.db.delete(artifact)
        await self.db.flush()

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            project_id=proj_id,
            task_id=t_id,
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            event_type="artifact.deleted",
            message=f"Artifact '{name}' (v{version}) deleted",
            metadata={
                "artifact_id": artifact_id,
                "name": name,
                "version": version,
            },
        )
        await self.db.commit()
        return True
