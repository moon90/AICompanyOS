"""FastAPI route handlers for Company Activity History per docs/Phases.md Section 17."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.activity_service import ActivityService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.activity import ActivityEventItemResponse, ActivityListResponse
from domain.activity.exceptions import ActivityAccessDeniedError
from domain.activity.schemas import ActivityFilterParams
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session

router = APIRouter(prefix="/api/v1/companies/{company_id}", tags=["Company Activity"])
service = ActivityService()


@router.get("/activity", response_model=ActivityListResponse)
async def get_company_activity(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    project_id: str | None = Query(default=None, description="Filter by project ID"),
    task_id: str | None = Query(default=None, description="Filter by task ID"),
    actor_type: str | None = Query(
        default=None, description="Filter by actor type (user/agent/system)"
    ),
    actor_id: str | None = Query(default=None, description="Filter by actor ID"),
    event_type: str | None = Query(default=None, description="Filter by event type"),
    search: str | None = Query(default=None, description="Keyword search in event message"),
    limit: int = Query(default=50, ge=1, le=100, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
) -> ActivityListResponse:
    """Retrieve reverse-chronological operational activity events for the company."""
    filters = ActivityFilterParams(
        project_id=project_id,
        task_id=task_id,
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=event_type,
        search=search,
        limit=limit,
        offset=offset,
    )
    try:
        events, total = await service.get_company_activity(
            session=session,
            user_id=current_user.id,
            company_id=company_id,
            filters=filters,
        )
        return ActivityListResponse(
            items=[ActivityEventItemResponse.model_validate(e) for e in events],
            total=total,
            limit=limit,
            offset=offset,
        )
    except ActivityAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/projects/{project_id}/activity", response_model=ActivityListResponse)
async def get_project_activity(
    company_id: str,
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    event_type: str | None = Query(default=None, description="Filter by event type"),
    search: str | None = Query(default=None, description="Keyword search in event message"),
    limit: int = Query(default=50, ge=1, le=100, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
) -> ActivityListResponse:
    """Retrieve operational activity events scoped to a specific project."""
    filters = ActivityFilterParams(
        event_type=event_type,
        search=search,
        limit=limit,
        offset=offset,
    )
    try:
        events, total = await service.get_project_activity(
            session=session,
            user_id=current_user.id,
            company_id=company_id,
            project_id=project_id,
            filters=filters,
        )
        return ActivityListResponse(
            items=[ActivityEventItemResponse.model_validate(e) for e in events],
            total=total,
            limit=limit,
            offset=offset,
        )
    except ActivityAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/tasks/{task_id}/activity", response_model=ActivityListResponse)
async def get_task_activity(
    company_id: str,
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    event_type: str | None = Query(default=None, description="Filter by event type"),
    search: str | None = Query(default=None, description="Keyword search in event message"),
    limit: int = Query(default=50, ge=1, le=100, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
) -> ActivityListResponse:
    """Retrieve operational activity events scoped to a specific task."""
    filters = ActivityFilterParams(
        event_type=event_type,
        search=search,
        limit=limit,
        offset=offset,
    )
    try:
        events, total = await service.get_task_activity(
            session=session,
            user_id=current_user.id,
            company_id=company_id,
            task_id=task_id,
            filters=filters,
        )
        return ActivityListResponse(
            items=[ActivityEventItemResponse.model_validate(e) for e in events],
            total=total,
            limit=limit,
            offset=offset,
        )
    except ActivityAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/agents/{agent_id}/activity", response_model=ActivityListResponse)
async def get_agent_activity(
    company_id: str,
    agent_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    event_type: str | None = Query(default=None, description="Filter by event type"),
    search: str | None = Query(default=None, description="Keyword search in event message"),
    limit: int = Query(default=50, ge=1, le=100, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
) -> ActivityListResponse:
    """Retrieve operational activity events scoped to a specific agent."""
    filters = ActivityFilterParams(
        event_type=event_type,
        search=search,
        limit=limit,
        offset=offset,
    )
    try:
        events, total = await service.get_agent_activity(
            session=session,
            user_id=current_user.id,
            company_id=company_id,
            agent_id=agent_id,
            filters=filters,
        )
        return ActivityListResponse(
            items=[ActivityEventItemResponse.model_validate(e) for e in events],
            total=total,
            limit=limit,
            offset=offset,
        )
    except ActivityAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
