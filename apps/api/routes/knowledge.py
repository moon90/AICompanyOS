"""FastAPI route handlers for Company Knowledge adhering to docs/Phases.md Section 23 and docs/Memory.md Sections 31-39."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.knowledge_service import KnowledgeService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.knowledge import (
    KnowledgeCreatePayload,
    KnowledgeListResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    KnowledgeResponse,
    KnowledgeUpdatePayload,
    SelectiveContextRequest,
    SelectiveContextResponse,
)
from domain.artifacts.exceptions import ArtifactNotFoundError
from domain.knowledge.exceptions import (
    InvalidKnowledgeOperationError,
    KnowledgeAccessDeniedError,
    KnowledgeNotFoundError,
)
from domain.memory.exceptions import DecisionNotFoundError
from domain.work.exceptions import ProjectNotFoundError, TaskNotFoundError
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session

router = APIRouter(
    prefix="/api/v1/companies/{company_id}/knowledge",
    tags=["Company Knowledge"],
)


@router.post(
    "",
    response_model=KnowledgeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_item(
    company_id: str,
    payload: KnowledgeCreatePayload,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> KnowledgeResponse:
    """Create a new persistent company knowledge item."""
    service = KnowledgeService(session)
    try:
        return await service.create_knowledge_item(
            company_id=company_id,
            payload=payload,
            user_id=current_user.id,
        )
    except KnowledgeAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (
        ProjectNotFoundError,
        TaskNotFoundError,
        DecisionNotFoundError,
        ArtifactNotFoundError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidKnowledgeOperationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "",
    response_model=KnowledgeListResponse,
)
async def list_knowledge_items(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    category: str | None = None,
    project_id: str | None = None,
    decision_id: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> KnowledgeListResponse:
    """List paginated company knowledge items with optional filtering and search."""
    service = KnowledgeService(session)
    try:
        return await service.list_knowledge_items(
            company_id=company_id,
            user_id=current_user.id,
            category=category,
            project_id=project_id,
            decision_id=decision_id,
            search=search,
            page=page,
            page_size=page_size,
        )
    except KnowledgeAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post(
    "/query",
    response_model=KnowledgeQueryResponse,
)
async def query_knowledge(
    company_id: str,
    payload: KnowledgeQueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> KnowledgeQueryResponse:
    """Ask canonical company questions with grounded citations and precedents."""
    service = KnowledgeService(session)
    try:
        return await service.query_knowledge(
            company_id=company_id,
            user_id=current_user.id,
            request=payload,
        )
    except KnowledgeAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post(
    "/context",
    response_model=SelectiveContextResponse,
)
async def get_selective_context(
    company_id: str,
    payload: SelectiveContextRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SelectiveContextResponse:
    """Retrieve selective bounded company context for agent execution without loading full DB."""
    service = KnowledgeService(session)
    try:
        return await service.get_selective_context(
            company_id=company_id,
            user_id=current_user.id,
            request=payload,
        )
    except KnowledgeAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get(
    "/{item_id}",
    response_model=KnowledgeResponse,
)
async def get_knowledge_item(
    company_id: str,
    item_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> KnowledgeResponse:
    """Get a single company knowledge record by ID."""
    service = KnowledgeService(session)
    try:
        return await service.get_knowledge_item(
            company_id=company_id,
            item_id=item_id,
            user_id=current_user.id,
        )
    except KnowledgeAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except KnowledgeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put(
    "/{item_id}",
    response_model=KnowledgeResponse,
)
async def update_knowledge_item(
    company_id: str,
    item_id: str,
    payload: KnowledgeUpdatePayload,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> KnowledgeResponse:
    """Update an existing company knowledge record."""
    service = KnowledgeService(session)
    try:
        return await service.update_knowledge_item(
            company_id=company_id,
            item_id=item_id,
            payload=payload,
            user_id=current_user.id,
        )
    except KnowledgeAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (
        KnowledgeNotFoundError,
        ProjectNotFoundError,
        TaskNotFoundError,
        DecisionNotFoundError,
        ArtifactNotFoundError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidKnowledgeOperationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_knowledge_item(
    company_id: str,
    item_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Delete a company knowledge record."""
    service = KnowledgeService(session)
    try:
        await service.delete_knowledge_item(
            company_id=company_id,
            item_id=item_id,
            user_id=current_user.id,
        )
    except KnowledgeAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except KnowledgeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
