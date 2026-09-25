"""FastAPI route handlers for Verification & AI Evaluation adhering to docs/Phases.md Section 26, docs/Architecture.md Section 71, and docs/Rules.md Section 17."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.verification_service import VerificationService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.verification import (
    BenchmarkDefinitionResponse,
    BenchmarkRunRequest,
    BenchmarkRunResponse,
    TaskVerificationRequest,
    VerificationRunListResponse,
    VerificationRunResponse,
    VerificationTelemetryResponse,
)
from domain.verification.exceptions import (
    InvalidVerificationCriteriaError,
    VerificationAccessDeniedError,
    VerificationError,
    VerificationNotFoundError,
)
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session

router = APIRouter(
    prefix="/api/v1/companies/{company_id}/verification",
    tags=["Verification & AI Evaluation"],
)


@router.post(
    "/verify/task/{task_id}",
    response_model=VerificationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def verify_task(
    company_id: str,
    task_id: str,
    payload: TaskVerificationRequest | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> VerificationRunResponse:
    """Execute the 5-stage verification pipeline against a task result."""
    service = VerificationService(session)
    try:
        return await service.verify_task(
            company_id=company_id,
            user_id=current_user.id,
            task_id=task_id,
            request=payload,
        )
    except VerificationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VerificationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidVerificationCriteriaError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except VerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.post(
    "/verify/artifact/{artifact_id}",
    response_model=VerificationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def verify_artifact(
    company_id: str,
    artifact_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> VerificationRunResponse:
    """Verify an artifact schema, content completeness, and evidence citations."""
    service = VerificationService(session)
    try:
        return await service.verify_artifact(
            company_id=company_id,
            user_id=current_user.id,
            artifact_id=artifact_id,
        )
    except VerificationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VerificationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.post(
    "/benchmarks/run",
    response_model=BenchmarkRunResponse,
)
async def run_benchmark(
    company_id: str,
    payload: BenchmarkRunRequest,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> BenchmarkRunResponse:
    """Execute a representative evaluation benchmark suite."""
    service = VerificationService(session)
    try:
        return await service.run_benchmark(
            company_id=company_id,
            user_id=current_user.id,
            request=payload,
        )
    except VerificationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VerificationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/benchmarks",
    response_model=list[BenchmarkDefinitionResponse],
)
async def list_benchmarks(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> list[BenchmarkDefinitionResponse]:
    """List all representative evaluation benchmark suites for the company."""
    service = VerificationService(session)
    try:
        return await service.list_benchmarks(
            company_id=company_id,
            user_id=current_user.id,
        )
    except VerificationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VerificationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/runs",
    response_model=VerificationRunListResponse,
)
async def list_verification_runs(
    company_id: str,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    target_type: Annotated[str | None, Query()] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> VerificationRunListResponse:
    """List historical verification runs and evaluation logs."""
    service = VerificationService(session)
    try:
        return await service.list_runs(
            company_id=company_id,
            user_id=current_user.id,
            limit=limit,
            target_type=target_type,
        )
    except VerificationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VerificationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/runs/{run_id}",
    response_model=VerificationRunResponse,
)
async def get_verification_run(
    company_id: str,
    run_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> VerificationRunResponse:
    """Retrieve details and criteria scorecards of a specific verification run."""
    service = VerificationService(session)
    try:
        return await service.get_run(
            company_id=company_id,
            user_id=current_user.id,
            run_id=run_id,
        )
    except VerificationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VerificationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/telemetry",
    response_model=VerificationTelemetryResponse,
)
async def get_verification_telemetry(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> VerificationTelemetryResponse:
    """Retrieve company-wide verification passes, failure rates, and criterion averages."""
    service = VerificationService(session)
    try:
        return await service.get_telemetry(
            company_id=company_id,
            user_id=current_user.id,
        )
    except VerificationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VerificationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
