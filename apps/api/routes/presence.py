"""FastAPI route handlers for Agent Presence per docs/Phases.md Section 18."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.presence_service import PresenceService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.presence import (
    AgentPresenceItemResponse,
    HeartbeatApiRequest,
    PresenceListResponse,
    PresenceSummaryResponse,
    PresenceUpdateApiRequest,
)
from domain.presence.exceptions import (
    PresenceAccessDeniedError,
    PresenceNotFoundError,
)
from domain.presence.schemas import PresenceUpdateParams
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session

router = APIRouter(prefix="/api/v1/companies/{company_id}", tags=["Agent Presence"])


@router.get("/presence", response_model=PresenceListResponse)
async def get_company_presence(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    stale_threshold_seconds: int = Query(
        default=60, ge=10, le=3600, description="Seconds before an unreported agent is marked stale"
    ),
) -> PresenceListResponse:
    """Retrieve real-time presence states and current activities for all company agents."""
    service = PresenceService(session)
    try:
        presences = await service.get_company_presence(
            user_id=current_user.id,
            company_id=company_id,
            include_stale_eval=True,
            stale_threshold_seconds=stale_threshold_seconds,
        )
        return PresenceListResponse(
            items=[AgentPresenceItemResponse.model_validate(p) for p in presences],
            total=len(presences),
        )
    except PresenceAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/presence/summary", response_model=PresenceSummaryResponse)
async def get_presence_summary(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    stale_threshold_seconds: int = Query(
        default=60, ge=10, le=3600, description="Seconds before an unreported agent is marked stale"
    ),
) -> PresenceSummaryResponse:
    """Retrieve lightweight presence counters for dashboard telemetry."""
    service = PresenceService(session)
    try:
        summary = await service.get_presence_summary(
            user_id=current_user.id,
            company_id=company_id,
            stale_threshold_seconds=stale_threshold_seconds,
        )
        return summary
    except PresenceAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/agents/{agent_id}/presence", response_model=AgentPresenceItemResponse)
async def get_agent_presence(
    company_id: str,
    agent_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AgentPresenceItemResponse:
    """Retrieve detailed real-time presence for a specific agent."""
    service = PresenceService(session)
    try:
        presence = await service.get_agent_presence(
            user_id=current_user.id,
            company_id=company_id,
            agent_id=agent_id,
        )
        return AgentPresenceItemResponse.model_validate(presence)
    except PresenceAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except PresenceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/agents/{agent_id}/presence/heartbeat", response_model=AgentPresenceItemResponse)
async def record_agent_heartbeat(
    company_id: str,
    agent_id: str,
    payload: HeartbeatApiRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AgentPresenceItemResponse:
    """Record an agent heartbeat, updating last seen timestamp and current step."""
    service = PresenceService(session)
    try:
        await service.record_heartbeat(
            company_id=company_id,
            agent_id=agent_id,
            current_step=payload.current_step,
            activity=payload.current_activity,
            details=payload.details,
        )
        await session.commit()
        presence = await service.get_agent_presence(
            user_id=current_user.id,
            company_id=company_id,
            agent_id=agent_id,
        )
        return AgentPresenceItemResponse.model_validate(presence)
    except PresenceAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except PresenceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/agents/{agent_id}/presence", response_model=AgentPresenceItemResponse)
async def update_agent_presence(
    company_id: str,
    agent_id: str,
    payload: PresenceUpdateApiRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AgentPresenceItemResponse:
    """Operator override to update an agent's presence status and activity description."""
    service = PresenceService(session)
    try:
        params = PresenceUpdateParams(
            status=payload.status,
            current_activity=payload.current_activity,
            current_step=payload.current_step,
            details=payload.details,
        )
        presence = await service.update_presence_status(
            user_id=current_user.id,
            company_id=company_id,
            agent_id=agent_id,
            params=params,
        )
        await session.commit()
        return AgentPresenceItemResponse.model_validate(presence)
    except PresenceAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except PresenceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
