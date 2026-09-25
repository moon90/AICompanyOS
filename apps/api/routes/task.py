"""FastAPI route handlers for Task management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.task_service import TaskService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.work import (
    TaskAssignRequest,
    TaskCreateRequest,
    TaskDependencyCreateRequest,
    TaskDependencyResponse,
    TaskListResponse,
    TaskResponse,
    TaskStatusUpdateRequest,
    TaskUpdateRequest,
)
from domain.work.exceptions import (
    CircularDependencyError,
    InvalidStatusTransitionError,
    InvalidWorkAssignmentError,
    ProjectNotFoundError,
    SelfDependencyError,
    TaskNotFoundError,
    WorkAccessDeniedError,
)
from infrastructure.database.models import Task, User
from infrastructure.database.session import get_db_session

router = APIRouter(prefix="/api/v1/companies/{company_id}/tasks", tags=["Tasks"])


def get_task_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> TaskService:
    """Dependency provider for TaskService."""
    return TaskService(db=session)


def _to_task_response(task: Task) -> TaskResponse:
    """Helper to convert task model into TaskResponse with enriched presentation attributes."""
    from sqlalchemy import inspect

    insp = inspect(task)
    unloaded = insp.unloaded if insp is not None else set()

    dependencies: list[TaskDependencyResponse] = []
    if "dependencies" not in unloaded and task.dependencies:
        for d in task.dependencies:
            d_insp = inspect(d)
            d_unloaded = d_insp.unloaded if d_insp is not None else set()
            dep_task = d.depends_on_task if "depends_on_task" not in d_unloaded else None
            dependencies.append(
                TaskDependencyResponse(
                    id=d.id,
                    task_id=d.task_id,
                    depends_on_task_id=d.depends_on_task_id,
                    depends_on_task_title=dep_task.title if dep_task else None,
                    depends_on_task_status=dep_task.status if dep_task else None,
                    created_at=d.created_at,
                )
            )

    project_name = task.project.name if "project" not in unloaded and task.project else None
    assigned_agent_name = (
        task.assigned_agent.name if "assigned_agent" not in unloaded and task.assigned_agent else None
    )
    assigned_agent_role = (
        task.assigned_agent.role if "assigned_agent" not in unloaded and task.assigned_agent else None
    )
    department_name = (
        task.department.name if "department" not in unloaded and task.department else None
    )
    subtasks_count = len(task.subtasks) if "subtasks" not in unloaded and task.subtasks else 0

    return TaskResponse(
        id=task.id,
        company_id=task.company_id,
        project_id=task.project_id,
        parent_task_id=task.parent_task_id,
        title=task.title,
        description=task.description,
        objective=task.objective,
        created_by_user_id=task.created_by_user_id,
        assigned_to_agent_id=task.assigned_to_agent_id,
        assigned_to_user_id=task.assigned_to_user_id,
        department_id=task.department_id,
        status=task.status,
        priority=task.priority,
        deadline=task.deadline,
        output=task.output,
        error_details=task.error_details,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        project_name=project_name,
        assigned_agent_name=assigned_agent_name,
        assigned_agent_role=assigned_agent_role,
        department_name=department_name,
        dependencies=dependencies,
        subtasks_count=subtasks_count,
    )


@router.get("", response_model=TaskListResponse, status_code=status.HTTP_200_OK)
async def list_tasks(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
    project_id: Annotated[str | None, Query()] = None,
    parent_task_id: Annotated[str | None, Query()] = None,
    task_status: Annotated[str | None, Query(alias="status")] = None,
    priority: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
    assigned_to_agent_id: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TaskListResponse:
    """List tasks with comprehensive filtering and search."""
    try:
        tasks, total = await service.list_tasks(
            user_id=current_user.id,
            company_id=company_id,
            project_id=project_id,
            parent_task_id=parent_task_id,
            status=task_status,
            priority=priority,
            department_id=department_id,
            assigned_to_agent_id=assigned_to_agent_id,
            search=search,
            limit=limit,
            offset=offset,
        )
        return TaskListResponse(
            items=[_to_task_response(t) for t in tasks],
            total=total,
        )
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    company_id: str,
    payload: TaskCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskResponse:
    """Create a new task within company boundaries."""
    try:
        task = await service.create_task(
            user_id=current_user.id,
            company_id=company_id,
            title=payload.title,
            description=payload.description,
            objective=payload.objective,
            project_id=payload.project_id,
            parent_task_id=payload.parent_task_id,
            assigned_to_agent_id=payload.assigned_to_agent_id,
            assigned_to_user_id=payload.assigned_to_user_id,
            department_id=payload.department_id,
            status=payload.status,
            priority=payload.priority,
            deadline=payload.deadline,
            dependency_task_ids=payload.dependency_task_ids,
        )
        return _to_task_response(task)
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except (ProjectNotFoundError, TaskNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (InvalidWorkAssignmentError, InvalidStatusTransitionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def get_task(
    company_id: str,
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskResponse:
    """Retrieve detailed task information with dependencies and subtasks."""
    try:
        task = await service.get_task(
            user_id=current_user.id,
            company_id=company_id,
            task_id=task_id,
        )
        return _to_task_response(task)
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def update_task(
    company_id: str,
    task_id: str,
    payload: TaskUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskResponse:
    """Update task title, description, objective, or priority."""
    try:
        task = await service.update_task(
            user_id=current_user.id,
            company_id=company_id,
            task_id=task_id,
            title=payload.title,
            description=payload.description,
            objective=payload.objective,
            project_id=payload.project_id,
            department_id=payload.department_id,
            priority=payload.priority,
            deadline=payload.deadline,
        )
        return _to_task_response(task)
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except (TaskNotFoundError, ProjectNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except InvalidWorkAssignmentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.patch("/{task_id}/status", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def update_task_status(
    company_id: str,
    task_id: str,
    payload: TaskStatusUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskResponse:
    """Advance or update task status according to state machine rules."""
    try:
        task = await service.update_task_status(
            user_id=current_user.id,
            company_id=company_id,
            task_id=task_id,
            new_status=payload.status,
            output=payload.output,
            error_details=payload.error_details,
        )
        return _to_task_response(task)
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/{task_id}/assign", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def assign_task(
    company_id: str,
    task_id: str,
    payload: TaskAssignRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskResponse:
    """Assign task to an agent or user."""
    try:
        task = await service.assign_task(
            user_id=current_user.id,
            company_id=company_id,
            task_id=task_id,
            assigned_to_agent_id=payload.assigned_to_agent_id,
            assigned_to_user_id=payload.assigned_to_user_id,
        )
        return _to_task_response(task)
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except InvalidWorkAssignmentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/{task_id}/dependencies",
    response_model=TaskDependencyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_task_dependency(
    company_id: str,
    task_id: str,
    payload: TaskDependencyCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskDependencyResponse:
    """Add a prerequisite dependency link between two tasks."""
    try:
        dep = await service.add_dependency(
            user_id=current_user.id,
            company_id=company_id,
            task_id=task_id,
            depends_on_task_id=payload.depends_on_task_id,
        )
        # Fetch target task title/status for response
        target_task = await service.get_task(
            current_user.id, company_id, payload.depends_on_task_id
        )
        return TaskDependencyResponse(
            id=dep.id,
            task_id=dep.task_id,
            depends_on_task_id=dep.depends_on_task_id,
            depends_on_task_title=target_task.title,
            depends_on_task_status=target_task.status,
            created_at=dep.created_at,
        )
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (CircularDependencyError, SelfDependencyError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete(
    "/{task_id}/dependencies/{depends_on_task_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_task_dependency(
    company_id: str,
    task_id: str,
    depends_on_task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> None:
    """Remove a prerequisite dependency link."""
    try:
        await service.remove_dependency(
            user_id=current_user.id,
            company_id=company_id,
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
        )
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    company_id: str,
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> None:
    """Delete a task and its associated dependencies and subtasks."""
    try:
        await service.delete_task(
            user_id=current_user.id,
            company_id=company_id,
            task_id=task_id,
        )
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
