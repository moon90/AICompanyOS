"""FastAPI route handlers for Semantic / Vector Memory adhering to docs/Phases.md Section 24 and docs/Memory.md Section 40."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.semantic_service import SemanticService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.semantic import (
    BatchIndexRequest,
    BatchIndexResponse,
    SemanticContextBuildRequest,
    SemanticContextBuildResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    VectorMemoryStatsResponse,
)
from domain.semantic.exceptions import (
    EmbeddingDimensionMismatchError,
    InvalidSemanticOperationError,
    SemanticAccessDeniedError,
    SemanticMemoryError,
    SemanticMemoryNotFoundError,
)
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session

router = APIRouter(
    prefix="/api/v1/companies/{company_id}/semantic",
    tags=["Semantic Memory"],
)


@router.post(
    "/search",
    response_model=SemanticSearchResponse,
)
async def search_semantic_memory(
    company_id: str,
    payload: SemanticSearchRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SemanticSearchResponse:
    """Perform semantic vector retrieval across company knowledge, decisions, artifacts, and tasks."""
    service = SemanticService(session)
    try:
        return await service.search_semantic(
            company_id=company_id,
            user_id=current_user.id,
            request=payload,
        )
    except SemanticAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidSemanticOperationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SemanticMemoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.post(
    "/context",
    response_model=SemanticContextBuildResponse,
)
async def build_semantic_context(
    company_id: str,
    payload: SemanticContextBuildRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SemanticContextBuildResponse:
    """Synthesize selective, bounded vector context for an agent based on semantic search."""
    service = SemanticService(session)
    try:
        return await service.build_semantic_context(
            company_id=company_id,
            user_id=current_user.id,
            request=payload,
        )
    except SemanticAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidSemanticOperationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SemanticMemoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.post(
    "/index",
    response_model=BatchIndexResponse,
)
async def batch_index_memory(
    company_id: str,
    payload: BatchIndexRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> BatchIndexResponse:
    """Index or re-index structured company entities into dense vector embeddings."""
    service = SemanticService(session)
    try:
        return await service.index_company_knowledge(
            company_id=company_id,
            user_id=current_user.id,
            request=payload,
        )
    except SemanticAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (EmbeddingDimensionMismatchError, InvalidSemanticOperationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SemanticMemoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/stats",
    response_model=VectorMemoryStatsResponse,
)
async def get_vector_memory_stats(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> VectorMemoryStatsResponse:
    """Retrieve vector memory storage, index telemetry, and chunk distribution."""
    service = SemanticService(session)
    try:
        return await service.get_vector_stats(
            company_id=company_id,
            user_id=current_user.id,
        )
    except SemanticAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except SemanticMemoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SemanticMemoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
