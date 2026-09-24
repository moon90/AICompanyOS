"""FastAPI route handlers for Real-Time Operations adhering to docs/Phases.md Section 21."""

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.realtime_service import RealtimeService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.realtime import (
    RealtimeEmitRequest,
    RealtimeEventPayload,
    RealtimeStatusResponse,
)
from domain.realtime.exceptions import RealtimeAccessDeniedError
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session
from infrastructure.events.dispatcher import EventDispatcher

router = APIRouter(
    prefix="/api/v1/companies/{company_id}/realtime",
    tags=["Real-Time Operations"],
)


@router.get("/events")
async def stream_company_events(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StreamingResponse:
    """Stream real-time company events via Server-Sent Events (SSE)."""
    service = RealtimeService()
    try:
        await service.verify_company_access(session, current_user.id, company_id)
    except RealtimeAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    dispatcher = EventDispatcher.get_instance()

    async def sse_event_generator() -> AsyncGenerator[str, None]:
        queue = await dispatcher.register_subscriber(company_id)
        try:
            # Yield initial connection confirmation frame
            connected_data = json.dumps(
                {
                    "status": "connected",
                    "company_id": company_id,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
            yield f"event: system.connected\ndata: {connected_data}\n\n"

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"id: {event.id}\nevent: {event.event_type}\ndata: {event.to_sse_data()}\n\n"
                except TimeoutError:
                    # Keep-alive comment ping every 15s to keep proxy/browser connections open
                    yield ": ping\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await dispatcher.unregister_subscriber(company_id, queue)

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/emit",
    response_model=RealtimeEventPayload,
    status_code=status.HTTP_201_CREATED,
)
async def emit_company_event(
    company_id: str,
    payload: RealtimeEmitRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RealtimeEventPayload:
    """Emit a test pulse or operator operational event to the real-time stream."""
    service = RealtimeService()
    try:
        return await service.emit_event(
            session=session,
            user_id=current_user.id,
            company_id=company_id,
            payload=payload,
        )
    except RealtimeAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/status", response_model=RealtimeStatusResponse)
async def get_realtime_status(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RealtimeStatusResponse:
    """Retrieve real-time channel telemetry and active subscriber metrics."""
    service = RealtimeService()
    try:
        return await service.get_channel_status(
            session=session,
            user_id=current_user.id,
            company_id=company_id,
        )
    except RealtimeAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
