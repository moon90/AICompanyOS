"""Application service managing project lifecycles, progress tracking, and company isolation."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.work.exceptions import (
    InvalidWorkAssignmentError,
    ProjectNotFoundError,
    WorkAccessDeniedError,
)
from domain.work.state_machine import ProjectPriority, ProjectStatus
from infrastructure.database.models import (
    Agent,
    CompanyMember,
    Project,
    Task,
)


class ProjectService:
    """Service layer managing project portfolios, task rollups, and multi-tenant boundary checks."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _verify_membership(self, user_id: str, company_id: str) -> CompanyMember:
        """Verify that user has active membership in the target company."""
        result = await self.db.execute(
            select(CompanyMember).where(
                CompanyMember.company_id == company_id,
                CompanyMember.user_id == user_id,
            )
        )
        membership = result.scalars().first()
        if not membership:
            raise WorkAccessDeniedError(
                f"Access denied: User '{user_id}' does not have active membership in company '{company_id}'."
            )
        return membership

    async def create_project(
        self,
        user_id: str,
        company_id: str,
        name: str,
        description: str | None = None,
        objective: str | None = None,
        status: str = ProjectStatus.PLANNED.value,
        priority: str = ProjectPriority.MEDIUM.value,
        owner_user_id: str | None = None,
        owner_agent_id: str | None = None,
    ) -> Project:
        """Create a new project scoped to the target company."""
        await self._verify_membership(user_id, company_id)

        # Validate status & priority
        valid_statuses = {s.value for s in ProjectStatus}
        if status not in valid_statuses:
            status = ProjectStatus.PLANNED.value

        valid_priorities = {p.value for p in ProjectPriority}
        if priority not in valid_priorities:
            priority = ProjectPriority.MEDIUM.value

        # If owner agent specified, ensure it belongs to the company
        if owner_agent_id:
            agent_res = await self.db.execute(
                select(Agent).where(
                    Agent.id == owner_agent_id,
                    Agent.company_id == company_id,
                )
            )
            if not agent_res.scalars().first():
                raise InvalidWorkAssignmentError(
                    f"Agent '{owner_agent_id}' does not belong to company '{company_id}'."
                )

        # If owner user specified, ensure membership
        if owner_user_id:
            await self._verify_membership(owner_user_id, company_id)
        elif not owner_agent_id:
            # Default owner to the creator user
            owner_user_id = user_id

        project = Project(
            id=str(uuid.uuid4()),
            company_id=company_id,
            name=name.strip(),
            description=description.strip() if description else None,
            objective=objective.strip() if objective else None,
            status=status,
            priority=priority,
            owner_user_id=owner_user_id,
            owner_agent_id=owner_agent_id,
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def _compute_task_stats(self, project_id: str) -> dict[str, int]:
        """Compute task statistics for a given project."""
        result = await self.db.execute(
            select(Task.status, func.count(Task.id))
            .where(Task.project_id == project_id)
            .group_by(Task.status)
        )
        counts_by_status: dict[str, int] = {str(row[0]): int(row[1]) for row in result.all()}
        total = sum(counts_by_status.values())
        completed = counts_by_status.get("COMPLETED", 0)
        blocked = counts_by_status.get("BLOCKED", 0)
        in_progress = counts_by_status.get("IN_PROGRESS", 0)
        planned = (
            counts_by_status.get("PLANNED", 0)
            + counts_by_status.get("READY", 0)
            + counts_by_status.get("ASSIGNED", 0)
        )

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "blocked_tasks": blocked,
            "in_progress_tasks": in_progress,
            "planned_tasks": planned,
        }

    async def get_project(
        self,
        user_id: str,
        company_id: str,
        project_id: str,
    ) -> tuple[Project, dict[str, int]]:
        """Retrieve a single project along with task summary statistics."""
        await self._verify_membership(user_id, company_id)

        result = await self.db.execute(
            select(Project)
            .options(
                selectinload(Project.owner_user),
                selectinload(Project.owner_agent),
            )
            .where(
                Project.id == project_id,
                Project.company_id == company_id,
            )
        )
        project = result.scalars().first()
        if not project:
            raise ProjectNotFoundError(
                f"Project '{project_id}' not found in company '{company_id}'."
            )

        stats = await self._compute_task_stats(project_id)
        return project, stats

    async def list_projects(
        self,
        user_id: str,
        company_id: str,
        status: str | None = None,
        priority: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[tuple[Project, dict[str, int]]], int]:
        """List company projects with filtering and task count rollups."""
        await self._verify_membership(user_id, company_id)

        query = select(Project).where(Project.company_id == company_id)

        if status:
            query = query.where(Project.status == status)
        if priority:
            query = query.where(Project.priority == priority)
        if search:
            query = query.where(
                Project.name.ilike(f"%{search}%") | Project.description.ilike(f"%{search}%")
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await self.db.execute(count_query)).scalar_one()

        # Fetch projects
        paginated_query = (
            query.options(
                selectinload(Project.owner_user),
                selectinload(Project.owner_agent),
            )
            .order_by(Project.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        projects = list((await self.db.execute(paginated_query)).scalars().all())

        # Compute stats for each project
        items: list[tuple[Project, dict[str, int]]] = []
        for proj in projects:
            stats = await self._compute_task_stats(proj.id)
            items.append((proj, stats))

        return items, total_count

    async def update_project(
        self,
        user_id: str,
        company_id: str,
        project_id: str,
        name: str | None = None,
        description: str | None = None,
        objective: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        owner_user_id: str | None = None,
        owner_agent_id: str | None = None,
    ) -> Project:
        """Update an existing project."""
        await self._verify_membership(user_id, company_id)

        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.company_id == company_id,
            )
        )
        project = result.scalars().first()
        if not project:
            raise ProjectNotFoundError(
                f"Project '{project_id}' not found in company '{company_id}'."
            )

        if name is not None:
            project.name = name.strip()
        if description is not None:
            project.description = description.strip() if description else None
        if objective is not None:
            project.objective = objective.strip() if objective else None

        if status is not None:
            valid_statuses = {s.value for s in ProjectStatus}
            if status in valid_statuses:
                project.status = status
                if status == ProjectStatus.COMPLETED.value and project.completed_at is None:
                    project.completed_at = datetime.now(UTC)
                elif status != ProjectStatus.COMPLETED.value and project.completed_at is not None:
                    project.completed_at = None

        if priority is not None:
            valid_priorities = {p.value for p in ProjectPriority}
            if priority in valid_priorities:
                project.priority = priority

        if owner_agent_id is not None:
            agent_res = await self.db.execute(
                select(Agent).where(
                    Agent.id == owner_agent_id,
                    Agent.company_id == company_id,
                )
            )
            if not agent_res.scalars().first():
                raise InvalidWorkAssignmentError(
                    f"Agent '{owner_agent_id}' does not belong to company '{company_id}'."
                )
            project.owner_agent_id = owner_agent_id

        if owner_user_id is not None:
            await self._verify_membership(owner_user_id, company_id)
            project.owner_user_id = owner_user_id

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete_project(
        self,
        user_id: str,
        company_id: str,
        project_id: str,
    ) -> None:
        """Delete a project and its associated cascade records."""
        await self._verify_membership(user_id, company_id)

        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.company_id == company_id,
            )
        )
        project = result.scalars().first()
        if not project:
            raise ProjectNotFoundError(
                f"Project '{project_id}' not found in company '{company_id}'."
            )

        await self.db.delete(project)
        await self.db.commit()
