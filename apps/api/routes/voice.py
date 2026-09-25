"""FastAPI route handlers for Voice Interface adhering to docs/Phases.md Section 25 and docs/Memory.md Section 60."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.voice_service import VoiceService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.voice import (
    VoiceCommandPayload,
    VoiceCommandResponse,
    VoiceSessionCreatePayload,
    VoiceSessionListResponse,
    VoiceSessionResponse,
    VoiceSynthesizeRequest,
    VoiceSynthesizeResponse,
    VoiceTelemetryResponse,
)
from domain.voice.exceptions import (
    InvalidVoiceCommandError,
    VoiceAccessDeniedError,
    VoiceError,
    VoiceSessionNotFoundError,
)
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session

router = APIRouter(
    prefix="/api/v1/companies/{company_id}/voice",
    tags=["Voice Interface"],
)


@router.post(
    "/sessions",
    response_model=VoiceSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_voice_session(
    company_id: str,
    payload: VoiceSessionCreatePayload | None = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> VoiceSessionResponse:
    """Initialize a conversational voice session for speech interaction and state tracking."""
    service = VoiceService(session)
    try:
        return await service.create_session(
            company_id=company_id,
            user_id=current_user.id,
            payload=payload,
        )
    except VoiceAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VoiceSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VoiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/sessions",
    response_model=VoiceSessionListResponse,
)
async def list_voice_sessions(
    company_id: str,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> VoiceSessionListResponse:
    """List historical conversational voice sessions for the user."""
    service = VoiceService(session)
    try:
        return await service.list_sessions(
            company_id=company_id,
            user_id=current_user.id,
            limit=limit,
        )
    except VoiceAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VoiceSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VoiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/sessions/{session_id}",
    response_model=VoiceSessionResponse,
)
async def get_voice_session(
    company_id: str,
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> VoiceSessionResponse:
    """Retrieve details and interaction timeline of a specific voice session."""
    service = VoiceService(session)
    try:
        return await service.get_session(
            company_id=company_id,
            user_id=current_user.id,
            session_id=session_id,
        )
    except VoiceAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VoiceSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VoiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.post(
    "/command",
    response_model=VoiceCommandResponse,
)
async def execute_voice_command(
    company_id: str,
    payload: VoiceCommandPayload,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> VoiceCommandResponse:
    """Process a natural language spoken command, route to company system, and return speech response."""
    service = VoiceService(session)
    try:
        return await service.process_command(
            company_id=company_id,
            user_id=current_user.id,
            payload=payload,
        )
    except VoiceAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VoiceSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidVoiceCommandError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except VoiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.post(
    "/synthesize",
    response_model=VoiceSynthesizeResponse,
)
async def synthesize_voice_speech(
    company_id: str,
    payload: VoiceSynthesizeRequest,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> VoiceSynthesizeResponse:
    """Synthesize textual response into audio synthesis metadata and phonetic structure."""
    service = VoiceService(session)
    try:
        return await service.synthesize_speech(
            company_id=company_id,
            user_id=current_user.id,
            request=payload,
        )
    except VoiceAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VoiceSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VoiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get(
    "/telemetry",
    response_model=VoiceTelemetryResponse,
)
async def get_voice_telemetry(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,  # type: ignore[assignment]
) -> VoiceTelemetryResponse:
    """Retrieve voice interface telemetry, intent distributions, and latency metrics."""
    service = VoiceService(session)
    try:
        return await service.get_telemetry(
            company_id=company_id,
            user_id=current_user.id,
        )
    except VoiceAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except VoiceSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except VoiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
