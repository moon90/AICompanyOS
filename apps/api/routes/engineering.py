"""FastAPI route handlers for Engineering File Tracking adhering to docs/Phases.md Section 20 and docs/Memory.md Section 61."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.engineering_service import EngineeringService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.engineering import (
    CompanyFileHistoryItem,
    EngineeringContextResponse,
    EngineeringContextUpsertPayload,
    EngineeringTaskViewResponse,
    FileChangeBulkCreatePayload,
    FileChangeResponse,
)
from domain.engineering.exceptions import (
    EngineeringAccessDeniedError,
    InvalidEngineeringOperationError,
)
from domain.work.exceptions import TaskNotFoundError
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session

router = APIRouter(
    prefix="/api/v1/companies/{company_id}/engineering",
    tags=["Engineering File Tracking"],
)


@router.get("/tasks/{task_id}", response_model=EngineeringTaskViewResponse)
async def get_task_engineering_view(
    company_id: str,
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> EngineeringTaskViewResponse:
    """Retrieve full engineering context and file changes for a specific task."""
    service = EngineeringService(session)
    try:
        return await service.get_task_engineering_view(
            company_id=company_id,
            task_id=task_id,
            user_id=current_user.id,
        )
    except EngineeringAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/tasks/{task_id}/context", response_model=EngineeringContextResponse)
async def upsert_task_engineering_context(
    company_id: str,
    task_id: str,
    payload: EngineeringContextUpsertPayload,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> EngineeringContextResponse:
    """Initialize or update the engineering context (branch, PR, tests, verification) for a task."""
    service = EngineeringService(session)
    try:
        return await service.upsert_engineering_context(
            company_id=company_id,
            task_id=task_id,
            payload=payload,
            user_id=current_user.id,
        )
    except EngineeringAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/tasks/{task_id}/files",
    response_model=list[FileChangeResponse],
    status_code=status.HTTP_201_CREATED,
)
async def record_task_file_changes(
    company_id: str,
    task_id: str,
    payload: FileChangeBulkCreatePayload,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[FileChangeResponse]:
    """Record code file changes (diffs, additions, deletions, commits) linked to a task."""
    service = EngineeringService(session)
    try:
        return await service.record_file_changes(
            company_id=company_id,
            task_id=task_id,
            payload=payload,
            user_id=current_user.id,
        )
    except EngineeringAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidEngineeringOperationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/files", response_model=list[CompanyFileHistoryItem])
async def get_company_file_history(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    branch: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[CompanyFileHistoryItem]:
    """Retrieve company-wide file touch history aggregated across tasks and branches."""
    service = EngineeringService(session)
    try:
        return await service.get_company_file_history(
            company_id=company_id,
            user_id=current_user.id,
            branch=branch,
            limit=limit,
        )
    except EngineeringAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
