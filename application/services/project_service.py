"""Application service managing project lifecycles, progress tracking, and company isolation."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.work.exceptions import (
    InvalidWorkAssignmentError,
    ProjectNotFoundError,
    WorkAccessDeniedError,
)
from domain.work.state_machine import ProjectPriority, ProjectStatus, TaskStateMachine, TaskStatus
from infrastructure.database.models import (
    Agent,
    CompanyMember,
    Project,
    Task,
    TaskDependency,
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
        await self.db.flush()

        from application.services.activity_service import ActivityService

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            project_id=project.id,
            actor_type="user",
            actor_id=user_id,
            event_type="PROJECT_CREATED",
            message=f"Created project '{project.name}'",
            metadata={"project_name": project.name, "priority": project.priority},
        )

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

        status_changed = False
        old_status = project.status
        if status is not None:
            valid_statuses = {s.value for s in ProjectStatus}
            if status in valid_statuses:
                if status != old_status:
                    status_changed = True
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

        if status_changed:
            from application.services.activity_service import ActivityService

            await ActivityService.record_event(
                session=self.db,
                company_id=company_id,
                project_id=project.id,
                actor_type="user",
                actor_id=user_id,
                event_type="PROJECT_STATUS_CHANGED",
                message=f"Project '{project.name}' status transitioned from {old_status} to {project.status}",
                metadata={"old_status": old_status, "new_status": project.status},
            )

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

    async def get_project_board(
        self,
        user_id: str,
        company_id: str,
        project_id: str,
    ) -> dict[str, Any]:
        """Fetch project details, tasks, columns, and allowed transitions for the Kanban board."""
        await self._verify_membership(user_id, company_id)

        # 1. Fetch Project with owner details
        proj_query = (
            select(Project)
            .where(
                Project.id == project_id,
                Project.company_id == company_id,
            )
            .options(
                selectinload(Project.owner_agent),
                selectinload(Project.owner_user),
            )
        )
        proj_res = await self.db.execute(proj_query)
        project = proj_res.scalars().first()
        if not project:
            raise ProjectNotFoundError(
                f"Project '{project_id}' not found in company '{company_id}'."
            )

        # 2. Fetch Tasks belonging to this project
        task_query = (
            select(Task)
            .where(
                Task.project_id == project_id,
                Task.company_id == company_id,
            )
            .options(
                selectinload(Task.assigned_agent),
                selectinload(Task.assigned_user),
                selectinload(Task.department),
                selectinload(Task.project),
                selectinload(Task.subtasks),
                selectinload(Task.dependencies).selectinload(TaskDependency.depends_on_task),
            )
            .order_by(Task.priority.desc(), Task.created_at.asc())
        )
        task_res = await self.db.execute(task_query)
        tasks = list(task_res.scalars().all())

        # 3. Canonical Kanban Columns configuration (docs/Phases.md Section 16)
        column_configs = [
            {
                "id": "READY",
                "title": "Ready",
                "statuses": [
                    TaskStatus.CREATED.value,
                    TaskStatus.PLANNED.value,
                    TaskStatus.READY.value,
                ],
                "color": "blue",
            },
            {
                "id": "IN_PROGRESS",
                "title": "In Progress",
                "statuses": [
                    TaskStatus.ASSIGNED.value,
                    TaskStatus.IN_PROGRESS.value,
                ],
                "color": "amber",
            },
            {
                "id": "WAITING",
                "title": "Waiting & Approvals",
                "statuses": [
                    TaskStatus.WAITING.value,
                    TaskStatus.APPROVAL_REQUIRED.value,
                ],
                "color": "yellow",
            },
            {
                "id": "BLOCKED",
                "title": "Blocked",
                "statuses": [TaskStatus.BLOCKED.value],
                "color": "red",
            },
            {
                "id": "VERIFYING",
                "title": "Verifying",
                "statuses": [TaskStatus.VERIFYING.value],
                "color": "indigo",
            },
            {
                "id": "COMPLETED",
                "title": "Completed",
                "statuses": [TaskStatus.COMPLETED.value],
                "color": "emerald",
            },
            {
                "id": "ARCHIVED",
                "title": "Failed / Cancelled",
                "statuses": [
                    TaskStatus.FAILED.value,
                    TaskStatus.CANCELLED.value,
                ],
                "color": "zinc",
            },
        ]

        # Calculate counts per column
        status_counts: dict[str, int] = {}
        for t in tasks:
            status_counts[t.status] = status_counts.get(t.status, 0) + 1

        columns = []
        for col in column_configs:
            count = sum(status_counts.get(s, 0) for s in col["statuses"])
            columns.append(
                {
                    "id": col["id"],
                    "title": col["title"],
                    "statuses": col["statuses"],
                    "color": col["color"],
                    "task_count": count,
                }
            )

        # 4. Rollup Statistics
        total_tasks = len(tasks)
        completed_tasks = status_counts.get(TaskStatus.COMPLETED.value, 0)
        in_progress_tasks = status_counts.get(TaskStatus.ASSIGNED.value, 0) + status_counts.get(
            TaskStatus.IN_PROGRESS.value, 0
        )
        waiting_tasks = status_counts.get(TaskStatus.WAITING.value, 0) + status_counts.get(
            TaskStatus.APPROVAL_REQUIRED.value, 0
        )
        blocked_tasks = status_counts.get(TaskStatus.BLOCKED.value, 0)
        completion_rate = (
            round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0
        )

        summary = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "waiting_tasks": waiting_tasks,
            "blocked_tasks": blocked_tasks,
            "completion_rate": completion_rate,
        }

        # 5. Allowed Transitions Map (TaskStateMachine)
        allowed_transitions = {
            status: sorted(targets)
            for status, targets in TaskStateMachine.ALLOWED_TRANSITIONS.items()
        }

        return {
            "project": project,
            "columns": columns,
            "tasks": tasks,
            "allowed_transitions": allowed_transitions,
            "summary": summary,
        }
