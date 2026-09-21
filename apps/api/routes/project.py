"""FastAPI route handlers for Project management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.project_service import ProjectService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.work import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectTaskStats,
    ProjectUpdateRequest,
)
from domain.work.exceptions import (
    InvalidWorkAssignmentError,
    ProjectNotFoundError,
    WorkAccessDeniedError,
)
from infrastructure.database.models import Project, User
from infrastructure.database.session import get_db_session

router = APIRouter(prefix="/api/v1/companies/{company_id}/projects", tags=["Projects"])


def get_project_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProjectService:
    """Dependency provider for ProjectService."""
    return ProjectService(db=session)


def _to_project_response(project: Project, stats: dict[str, int] | None = None) -> ProjectResponse:
    """Helper to convert project model and optional stats into ProjectResponse."""
    return ProjectResponse(
        id=project.id,
        company_id=project.company_id,
        name=project.name,
        description=project.description,
        objective=project.objective,
        status=project.status,
        priority=project.priority,
        owner_user_id=project.owner_user_id,
        owner_agent_id=project.owner_agent_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        completed_at=project.completed_at,
        stats=ProjectTaskStats(**stats) if stats else None,
    )


@router.get("", response_model=ProjectListResponse, status_code=status.HTTP_200_OK)
async def list_projects(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProjectService, Depends(get_project_service)],
    project_status: Annotated[str | None, Query(alias="status")] = None,
    priority: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProjectListResponse:
    """List projects belonging to the company with status and priority filtering."""
    try:
        items, total = await service.list_projects(
            user_id=current_user.id,
            company_id=company_id,
            status=project_status,
            priority=priority,
            search=search,
            limit=limit,
            offset=offset,
        )
        return ProjectListResponse(
            items=[_to_project_response(p, stats) for p, stats in items],
            total=total,
        )
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    company_id: str,
    payload: ProjectCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    """Create a new project in the specified company."""
    try:
        project = await service.create_project(
            user_id=current_user.id,
            company_id=company_id,
            name=payload.name,
            description=payload.description,
            objective=payload.objective,
            status=payload.status,
            priority=payload.priority,
            owner_user_id=payload.owner_user_id,
            owner_agent_id=payload.owner_agent_id,
        )
        _, stats = await service.get_project(
            user_id=current_user.id,
            company_id=company_id,
            project_id=project.id,
        )
        return _to_project_response(project, stats)
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except InvalidWorkAssignmentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
async def get_project(
    company_id: str,
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    """Retrieve detailed project information with task rollups."""
    try:
        project, stats = await service.get_project(
            user_id=current_user.id,
            company_id=company_id,
            project_id=project_id,
        )
        return _to_project_response(project, stats)
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
async def update_project(
    company_id: str,
    project_id: str,
    payload: ProjectUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    """Update project metadata or status."""
    try:
        project = await service.update_project(
            user_id=current_user.id,
            company_id=company_id,
            project_id=project_id,
            name=payload.name,
            description=payload.description,
            objective=payload.objective,
            status=payload.status,
            priority=payload.priority,
            owner_user_id=payload.owner_user_id,
            owner_agent_id=payload.owner_agent_id,
        )
        _, stats = await service.get_project(
            user_id=current_user.id,
            company_id=company_id,
            project_id=project.id,
        )
        return _to_project_response(project, stats)
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except InvalidWorkAssignmentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    company_id: str,
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> None:
    """Delete a project and cascade delete associated records."""
    try:
        await service.delete_project(
            user_id=current_user.id,
            company_id=company_id,
            project_id=project_id,
        )
    except WorkAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
