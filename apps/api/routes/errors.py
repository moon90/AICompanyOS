"""FastAPI route handlers for Error & Bug Management per docs/Phases.md Section 19."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.error_service import ErrorService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.error import (
    ErrorAssignPayload,
    ErrorCreatePayload,
    ErrorListResponse,
    ErrorRecordResponse,
    ErrorReopenApiRequest,
    ErrorResolvePayload,
    ErrorSeverity,
    ErrorStatus,
    ErrorSummaryResponse,
    ErrorUpdatePayload,
    ErrorVerifyPayload,
)
from domain.errors.exceptions import (
    ErrorAccessDeniedError,
    ErrorNotFoundError,
    InvalidErrorTransitionError,
    MissingEvidenceError,
    MissingResolutionError,
)
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session

router = APIRouter(prefix="/api/v1/companies/{company_id}/errors", tags=["Errors & Bugs"])


@router.post("", response_model=ErrorRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_error(
    company_id: str,
    payload: ErrorCreatePayload,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ErrorRecordResponse:
    """Record a new error or bug in the authoritative error log."""
    service = ErrorService(session)
    try:
        return await service.create_error(
            company_id=company_id,
            payload=payload,
            user_id=current_user.id,
        )
    except ErrorAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("", response_model=ErrorListResponse)
async def list_errors(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: Annotated[ErrorStatus | None, Query(alias="status")] = None,
    severity: Annotated[ErrorSeverity | None, Query()] = None,
    project_id: Annotated[str | None, Query()] = None,
    task_id: Annotated[str | None, Query()] = None,
    assigned_to: Annotated[str | None, Query()] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ErrorListResponse:
    """List and filter errors for a company with operational counts."""
    service = ErrorService(session)
    try:
        return await service.get_errors(
            company_id=company_id,
            user_id=current_user.id,
            status=status_filter,
            severity=severity,
            project_id=project_id,
            task_id=task_id,
            assigned_to=assigned_to,
            offset=offset,
            limit=limit,
        )
    except ErrorAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/summary", response_model=ErrorSummaryResponse)
async def get_error_summary(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ErrorSummaryResponse:
    """Get aggregated metrics and counts for errors in a company."""
    service = ErrorService(session)
    try:
        return await service.get_error_summary(
            company_id=company_id,
            user_id=current_user.id,
        )
    except ErrorAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/{error_id}", response_model=ErrorRecordResponse)
async def get_error(
    company_id: str,
    error_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ErrorRecordResponse:
    """Retrieve details of a single error record."""
    service = ErrorService(session)
    try:
        return await service.get_error(
            company_id=company_id,
            error_id=error_id,
            user_id=current_user.id,
        )
    except ErrorAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ErrorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{error_id}", response_model=ErrorRecordResponse)
async def update_error(
    company_id: str,
    error_id: str,
    payload: ErrorUpdatePayload,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ErrorRecordResponse:
    """Update fields of an error record."""
    service = ErrorService(session)
    try:
        return await service.update_error(
            company_id=company_id,
            error_id=error_id,
            payload=payload,
            user_id=current_user.id,
        )
    except ErrorAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ErrorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{error_id}/assign", response_model=ErrorRecordResponse)
async def assign_error(
    company_id: str,
    error_id: str,
    payload: ErrorAssignPayload,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ErrorRecordResponse:
    """Assign an error to an agent or user."""
    service = ErrorService(session)
    try:
        return await service.assign_error(
            company_id=company_id,
            error_id=error_id,
            payload=payload,
            user_id=current_user.id,
        )
    except ErrorAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ErrorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{error_id}/investigate", response_model=ErrorRecordResponse)
async def start_investigation(
    company_id: str,
    error_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    investigated_by: Annotated[str | None, Query()] = None,
) -> ErrorRecordResponse:
    """Mark an error as under active investigation."""
    service = ErrorService(session)
    investigator = investigated_by or current_user.name or f"user:{current_user.id}"
    try:
        return await service.start_investigation(
            company_id=company_id,
            error_id=error_id,
            investigated_by=investigator,
            user_id=current_user.id,
        )
    except ErrorAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ErrorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{error_id}/resolve", response_model=ErrorRecordResponse)
async def resolve_error(
    company_id: str,
    error_id: str,
    payload: ErrorResolvePayload,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ErrorRecordResponse:
    """Mark an error as resolved with root cause and resolution description."""
    service = ErrorService(session)
    try:
        return await service.resolve_error(
            company_id=company_id,
            error_id=error_id,
            payload=payload,
            user_id=current_user.id,
        )
    except ErrorAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ErrorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MissingResolutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{error_id}/verify", response_model=ErrorRecordResponse)
async def verify_error(
    company_id: str,
    error_id: str,
    payload: ErrorVerifyPayload,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ErrorRecordResponse:
    """Verify an error resolution with proof and test evidence."""
    service = ErrorService(session)
    try:
        return await service.verify_error(
            company_id=company_id,
            error_id=error_id,
            payload=payload,
            user_id=current_user.id,
        )
    except ErrorAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ErrorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (MissingEvidenceError, InvalidErrorTransitionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{error_id}/reopen", response_model=ErrorRecordResponse)
async def reopen_error(
    company_id: str,
    error_id: str,
    payload: ErrorReopenApiRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ErrorRecordResponse:
    """Reopen a previously resolved error if bug persists."""
    service = ErrorService(session)
    actor = current_user.name or f"user:{current_user.id}"
    try:
        return await service.reopen_error(
            company_id=company_id,
            error_id=error_id,
            reason=payload.reason,
            actor=actor,
            user_id=current_user.id,
        )
    except ErrorAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ErrorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{error_id}/close", response_model=ErrorRecordResponse)
async def close_error(
    company_id: str,
    error_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ErrorRecordResponse:
    """Formally close an error after completed verification."""
    service = ErrorService(session)
    actor = current_user.name or f"user:{current_user.id}"
    try:
        return await service.close_error(
            company_id=company_id,
            error_id=error_id,
            actor=actor,
            user_id=current_user.id,
        )
    except ErrorAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ErrorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
