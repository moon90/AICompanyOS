"""FastAPI route handlers for Artifacts and Documents adhering to docs/Phases.md Section 22 and docs/Memory.md Section 31."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.artifact_service import ArtifactService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.artifact import (
    ArtifactCreatePayload,
    ArtifactListResponse,
    ArtifactResponse,
    ArtifactUpdatePayload,
    ArtifactVersionCreatePayload,
    ArtifactVersionItem,
)
from domain.agents.exceptions import AgentNotFoundError
from domain.artifacts.exceptions import (
    ArtifactAccessDeniedError,
    ArtifactNotFoundError,
    InvalidArtifactOperationError,
)
from domain.work.exceptions import ProjectNotFoundError, TaskNotFoundError
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session

router = APIRouter(
    prefix="/api/v1/companies/{company_id}/artifacts",
    tags=["Documents & Artifacts"],
)


@router.post(
    "",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_artifact(
    company_id: str,
    payload: ArtifactCreatePayload,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ArtifactResponse:
    """Create a new artifact or document for a company."""
    service = ArtifactService(session)
    try:
        return await service.create_artifact(
            company_id=company_id,
            payload=payload,
            user_id=current_user.id,
        )
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ProjectNotFoundError, TaskNotFoundError, AgentNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidArtifactOperationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "",
    response_model=ArtifactListResponse,
)
async def list_artifacts(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    project_id: str | None = None,
    task_id: str | None = None,
    artifact_type: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> ArtifactListResponse:
    """List artifacts with optional filtering, search query, and pagination."""
    service = ArtifactService(session)
    try:
        return await service.list_artifacts(
            company_id=company_id,
            user_id=current_user.id,
            project_id=project_id,
            task_id=task_id,
            artifact_type=artifact_type,
            search=search,
            page=page,
            page_size=page_size,
        )
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get(
    "/{artifact_id}",
    response_model=ArtifactResponse,
)
async def get_artifact(
    company_id: str,
    artifact_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ArtifactResponse:
    """Fetch a single artifact by ID."""
    service = ArtifactService(session)
    try:
        return await service.get_artifact(
            company_id=company_id,
            artifact_id=artifact_id,
            user_id=current_user.id,
        )
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/{artifact_id}",
    response_model=ArtifactResponse,
)
async def update_artifact(
    company_id: str,
    artifact_id: str,
    payload: ArtifactUpdatePayload,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ArtifactResponse:
    """Update artifact attributes or metadata."""
    service = ArtifactService(session)
    try:
        return await service.update_artifact(
            company_id=company_id,
            artifact_id=artifact_id,
            payload=payload,
            user_id=current_user.id,
        )
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ArtifactNotFoundError, ProjectNotFoundError, TaskNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidArtifactOperationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/{artifact_id}/versions",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_artifact_version(
    company_id: str,
    artifact_id: str,
    payload: ArtifactVersionCreatePayload,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ArtifactResponse:
    """Create a new version for an artifact lineage."""
    service = ArtifactService(session)
    try:
        return await service.create_new_version(
            company_id=company_id,
            artifact_id=artifact_id,
            payload=payload,
            user_id=current_user.id,
        )
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidArtifactOperationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/{artifact_id}/versions",
    response_model=list[ArtifactVersionItem],
)
async def get_artifact_versions(
    company_id: str,
    artifact_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ArtifactVersionItem]:
    """Fetch lineage version history for an artifact."""
    service = ArtifactService(session)
    try:
        return await service.get_version_history(
            company_id=company_id,
            artifact_id=artifact_id,
            user_id=current_user.id,
        )
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/{artifact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_artifact(
    company_id: str,
    artifact_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Delete an artifact."""
    service = ArtifactService(session)
    try:
        await service.delete_artifact(
            company_id=company_id,
            artifact_id=artifact_id,
            user_id=current_user.id,
        )
    except ArtifactAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
