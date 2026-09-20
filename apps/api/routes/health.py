"""Health check route handlers."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from application.services.health_service import HealthService
from apps.api.schemas.health import HealthResponse
from infrastructure.config import get_settings

router = APIRouter(tags=["health"])


def get_health_service(request: Request) -> HealthService:
    """Dependency provider for HealthService resolving settings from application state."""
    settings = getattr(request.app.state, "settings", None) or get_settings()
    return HealthService(settings=settings)


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health Check",
    description="Deterministic health check endpoint indicating API operational status.",
)
def get_health(
    service: Annotated[HealthService, Depends(get_health_service)],
) -> HealthResponse:
    """Return application health status."""
    return service.get_health_status()
