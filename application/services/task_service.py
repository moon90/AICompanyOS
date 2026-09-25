"""Application service managing task lifecycles, assignments, dependencies, and state transitions."""

import uuid
from collections import deque
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.work.exceptions import (
    CircularDependencyError,
    InvalidWorkAssignmentError,
    ProjectNotFoundError,
    SelfDependencyError,
    TaskNotFoundError,
    WorkAccessDeniedError,
)
from domain.work.state_machine import TaskPriority, TaskStateMachine, TaskStatus
from infrastructure.database.models import (
    Agent,
    CompanyMember,
    Department,
    Project,
    Task,
    TaskDependency,
)


class TaskService:
    """Service layer managing task entities, dependency graphs, and state machines."""

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

    async def create_task(
        self,
        user_id: str,
        company_id: str,
        title: str,
        description: str | None = None,
        objective: str | None = None,
        project_id: str | None = None,
        parent_task_id: str | None = None,
        assigned_to_agent_id: str | None = None,
        assigned_to_user_id: str | None = None,
        department_id: str | None = None,
        status: str = TaskStatus.CREATED.value,
        priority: str = TaskPriority.MEDIUM.value,
        deadline: datetime | None = None,
        dependency_task_ids: list[str] | None = None,
    ) -> Task:
        """Create a new task within company boundaries."""
        await self._verify_membership(user_id, company_id)

        # Validate project if provided
        if project_id:
            proj_res = await self.db.execute(
                select(Project).where(
                    Project.id == project_id,
                    Project.company_id == company_id,
                )
            )
            if not proj_res.scalars().first():
                raise ProjectNotFoundError(
                    f"Project '{project_id}' not found in company '{company_id}'."
                )

        # Validate parent task if provided
        if parent_task_id:
            parent_res = await self.db.execute(
                select(Task).where(
                    Task.id == parent_task_id,
                    Task.company_id == company_id,
                )
            )
            if not parent_res.scalars().first():
                raise TaskNotFoundError(
                    f"Parent task '{parent_task_id}' not found in company '{company_id}'."
                )

        # Validate assigned agent
        if assigned_to_agent_id:
            agent_res = await self.db.execute(
                select(Agent).where(
                    Agent.id == assigned_to_agent_id,
                    Agent.company_id == company_id,
                )
            )
            agent = agent_res.scalars().first()
            if not agent:
                raise InvalidWorkAssignmentError(
                    f"Agent '{assigned_to_agent_id}' does not belong to company '{company_id}'."
                )
            # Auto-populate department from agent if department not explicitly set
            if not department_id and agent.department_id:
                department_id = agent.department_id

        # Validate assigned user
        if assigned_to_user_id:
            await self._verify_membership(assigned_to_user_id, company_id)

        # Validate department if provided
        if department_id:
            dept_res = await self.db.execute(
                select(Department).where(
                    Department.id == department_id,
                    Department.company_id == company_id,
                )
            )
            if not dept_res.scalars().first():
                raise InvalidWorkAssignmentError(
                    f"Department '{department_id}' does not belong to company '{company_id}'."
                )

        # Auto-advance to ASSIGNED if assigned at creation and status was CREATED
        if (assigned_to_agent_id or assigned_to_user_id) and status == TaskStatus.CREATED.value:
            status = TaskStatus.ASSIGNED.value

        valid_priorities = {p.value for p in TaskPriority}
        if priority not in valid_priorities:
            priority = TaskPriority.MEDIUM.value

        started_at, completed_at = TaskStateMachine.calculate_timestamps(status, None, None)

        task = Task(
            id=str(uuid.uuid4()),
            company_id=company_id,
            project_id=project_id,
            parent_task_id=parent_task_id,
            title=title.strip(),
            description=description.strip() if description else None,
            objective=objective.strip() if objective else None,
            created_by_user_id=user_id,
            assigned_to_agent_id=assigned_to_agent_id,
            assigned_to_user_id=assigned_to_user_id,
            department_id=department_id,
            status=status,
            priority=priority,
            deadline=deadline,
            started_at=started_at,
            completed_at=completed_at,
        )
        self.db.add(task)
        await self.db.flush()

        # Add initial dependencies if provided
        if dependency_task_ids:
            for dep_id in dependency_task_ids:
                if dep_id == task.id:
                    continue
                dep_task_res = await self.db.execute(
                    select(Task).where(Task.id == dep_id, Task.company_id == company_id)
                )
                if dep_task_res.scalars().first():
                    dep = TaskDependency(
                        id=str(uuid.uuid4()),
                        company_id=company_id,
                        task_id=task.id,
                        depends_on_task_id=dep_id,
                    )
                    self.db.add(dep)

        from application.services.activity_service import ActivityService

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            project_id=task.project_id,
            task_id=task.id,
            actor_type="user",
            actor_id=user_id,
            event_type="TASK_CREATED",
            message=f"Created task '{task.title}'",
            metadata={"status": task.status, "priority": task.priority},
        )

        await self.db.commit()
        return await self.get_task(user_id, company_id, task.id)

    async def get_task(
        self,
        user_id: str,
        company_id: str,
        task_id: str,
    ) -> Task:
        """Retrieve task details with loaded associations and dependency links."""
        await self._verify_membership(user_id, company_id)

        result = await self.db.execute(
            select(Task)
            .options(
                selectinload(Task.project),
                selectinload(Task.parent_task),
                selectinload(Task.subtasks),
                selectinload(Task.department),
                selectinload(Task.assigned_agent),
                selectinload(Task.assigned_user),
                selectinload(Task.created_by_user),
                selectinload(Task.created_by_agent),
                selectinload(Task.dependencies).selectinload(TaskDependency.depends_on_task),
                selectinload(Task.dependents).selectinload(TaskDependency.task),
            )
            .where(
                Task.id == task_id,
                Task.company_id == company_id,
            )
        )
        task = result.scalars().first()
        if not task:
            raise TaskNotFoundError(f"Task '{task_id}' not found in company '{company_id}'.")
        return task

    async def list_tasks(
        self,
        user_id: str,
        company_id: str,
        project_id: str | None = None,
        parent_task_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        department_id: str | None = None,
        assigned_to_agent_id: str | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Task], int]:
        """List tasks for a company with multi-faceted filtering."""
        await self._verify_membership(user_id, company_id)

        query = select(Task).where(Task.company_id == company_id)

        if project_id:
            query = query.where(Task.project_id == project_id)
        if parent_task_id:
            query = query.where(Task.parent_task_id == parent_task_id)
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if department_id:
            query = query.where(Task.department_id == department_id)
        if assigned_to_agent_id:
            query = query.where(Task.assigned_to_agent_id == assigned_to_agent_id)
        if search:
            query = query.where(
                Task.title.ilike(f"%{search}%")
                | Task.description.ilike(f"%{search}%")
                | Task.objective.ilike(f"%{search}%")
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await self.db.execute(count_query)).scalar_one()

        paginated_query = (
            query.options(
                selectinload(Task.project),
                selectinload(Task.assigned_agent),
                selectinload(Task.assigned_user),
                selectinload(Task.department),
                selectinload(Task.subtasks),
                selectinload(Task.dependencies).selectinload(TaskDependency.depends_on_task),
            )
            .order_by(Task.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        tasks = list((await self.db.execute(paginated_query)).scalars().all())
        return tasks, total_count

    async def update_task(
        self,
        user_id: str,
        company_id: str,
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        objective: str | None = None,
        project_id: str | None = None,
        department_id: str | None = None,
        priority: str | None = None,
        deadline: datetime | None = None,
    ) -> Task:
        """Update task metadata."""
        await self._verify_membership(user_id, company_id)

        task = await self.get_task(user_id, company_id, task_id)

        if title is not None:
            task.title = title.strip()
        if description is not None:
            task.description = description.strip() if description else None
        if objective is not None:
            task.objective = objective.strip() if objective else None

        if project_id is not None:
            if project_id:
                proj_res = await self.db.execute(
                    select(Project).where(
                        Project.id == project_id, Project.company_id == company_id
                    )
                )
                if not proj_res.scalars().first():
                    raise ProjectNotFoundError(
                        f"Project '{project_id}' not found in company '{company_id}'."
                    )
            task.project_id = project_id or None

        if department_id is not None:
            if department_id:
                dept_res = await self.db.execute(
                    select(Department).where(
                        Department.id == department_id, Department.company_id == company_id
                    )
                )
                if not dept_res.scalars().first():
                    raise InvalidWorkAssignmentError(
                        f"Department '{department_id}' not found in company '{company_id}'."
                    )
            task.department_id = department_id or None

        if priority is not None:
            valid_priorities = {p.value for p in TaskPriority}
            if priority in valid_priorities:
                task.priority = priority

        if deadline is not None:
            task.deadline = deadline

        await self.db.commit()
        return await self.get_task(user_id, company_id, task_id)

    async def update_task_status(
        self,
        user_id: str,
        company_id: str,
        task_id: str,
        new_status: str,
        output: str | None = None,
        error_details: str | None = None,
    ) -> Task:
        """Validate and advance task status through the state machine."""
        await self._verify_membership(user_id, company_id)

        task = await self.get_task(user_id, company_id, task_id)

        TaskStateMachine.validate_transition(task.status, new_status)

        started_at, completed_at = TaskStateMachine.calculate_timestamps(
            new_status, task.started_at, task.completed_at
        )

        old_status = task.status
        task.status = new_status
        task.started_at = started_at
        task.completed_at = completed_at

        if output is not None:
            task.output = output.strip() if output else None
        if error_details is not None:
            task.error_details = error_details.strip() if error_details else None

        from application.services.activity_service import ActivityService

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            project_id=task.project_id,
            task_id=task.id,
            actor_type="user",
            actor_id=user_id,
            event_type="TASK_STATUS_CHANGED",
            message=f"Task '{task.title}' transitioned from {old_status} to {new_status}",
            metadata={"old_status": old_status, "new_status": new_status},
        )

        await self.db.commit()
        return await self.get_task(user_id, company_id, task_id)

    async def assign_task(
        self,
        user_id: str,
        company_id: str,
        task_id: str,
        assigned_to_agent_id: str | None = None,
        assigned_to_user_id: str | None = None,
    ) -> Task:
        """Assign task to an agent or user, advancing status if appropriate."""
        await self._verify_membership(user_id, company_id)

        task = await self.get_task(user_id, company_id, task_id)

        if assigned_to_agent_id:
            agent_res = await self.db.execute(
                select(Agent).where(
                    Agent.id == assigned_to_agent_id,
                    Agent.company_id == company_id,
                )
            )
            agent = agent_res.scalars().first()
            if not agent:
                raise InvalidWorkAssignmentError(
                    f"Agent '{assigned_to_agent_id}' does not belong to company '{company_id}'."
                )
            task.assigned_to_agent_id = assigned_to_agent_id
            if not task.department_id and agent.department_id:
                task.department_id = agent.department_id

        if assigned_to_user_id:
            await self._verify_membership(assigned_to_user_id, company_id)
            task.assigned_to_user_id = assigned_to_user_id

        # If current status is CREATED or PLANNED, automatically advance to ASSIGNED
        if task.status in {
            TaskStatus.CREATED.value,
            TaskStatus.PLANNED.value,
            TaskStatus.READY.value,
        }:
            task.status = TaskStatus.ASSIGNED.value

        from application.services.activity_service import ActivityService

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            project_id=task.project_id,
            task_id=task.id,
            actor_type="user",
            actor_id=user_id,
            event_type="TASK_ASSIGNED",
            message=f"Task '{task.title}' assigned",
            metadata={
                "assigned_to_agent_id": assigned_to_agent_id,
                "assigned_to_user_id": assigned_to_user_id,
                "status": task.status,
            },
        )

        await self.db.commit()
        return await self.get_task(user_id, company_id, task_id)

    async def _check_cycle(self, company_id: str, source_task_id: str, target_task_id: str) -> None:
        """Verify adding dependency (source depends on target) won't create a circular dependency.

        A cycle occurs if source_task_id is already reachable by following dependencies from target_task_id.
        """
        # Fetch all dependencies for the company
        deps_res = await self.db.execute(
            select(TaskDependency.task_id, TaskDependency.depends_on_task_id).where(
                TaskDependency.company_id == company_id
            )
        )
        # Graph where adj[u] = list of tasks that u depends on
        adj: dict[str, list[str]] = {}
        for t_id, dep_id in deps_res.all():
            adj.setdefault(t_id, []).append(dep_id)

        # BFS starting from target_task_id following dependencies
        queue: deque[str] = deque([target_task_id])
        visited: set[str] = {target_task_id}

        while queue:
            curr = queue.popleft()
            if curr == source_task_id:
                raise CircularDependencyError(
                    f"Circular dependency detected: task '{source_task_id}' cannot depend on '{target_task_id}' "
                    f"because '{target_task_id}' already transitively depends on '{source_task_id}'."
                )
            for neighbor in adj.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

    async def add_dependency(
        self,
        user_id: str,
        company_id: str,
        task_id: str,
        depends_on_task_id: str,
    ) -> TaskDependency:
        """Add a prerequisite dependency: task_id depends on depends_on_task_id."""
        await self._verify_membership(user_id, company_id)

        if task_id == depends_on_task_id:
            raise SelfDependencyError(f"Task '{task_id}' cannot depend on itself.")

        # Ensure both tasks exist in the company
        await self.get_task(user_id, company_id, task_id)
        await self.get_task(user_id, company_id, depends_on_task_id)

        # Check existing
        existing = await self.db.execute(
            select(TaskDependency).where(
                TaskDependency.company_id == company_id,
                TaskDependency.task_id == task_id,
                TaskDependency.depends_on_task_id == depends_on_task_id,
            )
        )
        if existing.scalars().first():
            return existing.scalars().first()  # type: ignore[return-value]

        # Check cycle
        await self._check_cycle(company_id, task_id, depends_on_task_id)

        dependency = TaskDependency(
            id=str(uuid.uuid4()),
            company_id=company_id,
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
        )
        self.db.add(dependency)
        await self.db.commit()
        await self.db.refresh(dependency)
        return dependency

    async def remove_dependency(
        self,
        user_id: str,
        company_id: str,
        task_id: str,
        depends_on_task_id: str,
    ) -> None:
        """Remove a dependency prerequisite."""
        await self._verify_membership(user_id, company_id)

        dep_res = await self.db.execute(
            select(TaskDependency).where(
                TaskDependency.company_id == company_id,
                TaskDependency.task_id == task_id,
                TaskDependency.depends_on_task_id == depends_on_task_id,
            )
        )
        dep = dep_res.scalars().first()
        if dep:
            await self.db.delete(dep)
            await self.db.commit()

    async def delete_task(
        self,
        user_id: str,
        company_id: str,
        task_id: str,
    ) -> None:
        """Delete a task and its cascade relationships."""
        await self._verify_membership(user_id, company_id)

        task = await self.get_task(user_id, company_id, task_id)
        await self.db.delete(task)
        await self.db.commit()
