"""System foundation and infrastructure telemetry route handlers."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.system_service import SystemService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.system import SystemStatusResponse
from infrastructure.config import get_settings
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session

router = APIRouter(prefix="/api/v1/system", tags=["system"])


def get_system_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    request: Request,
) -> SystemService:
    """Dependency provider for SystemService."""
    settings = getattr(request.app.state, "settings", None) or get_settings()
    return SystemService(session=session, settings=settings)


@router.get(
    "/status",
    response_model=SystemStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="System and Infrastructure Status",
    description="Returns live system infrastructure readiness and verified PostgreSQL connection status.",
)
async def get_system_status(
    _current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[SystemService, Depends(get_system_service)],
) -> SystemStatusResponse:
    """Return live system telemetry for authenticated operators."""
    return await service.get_system_status()
