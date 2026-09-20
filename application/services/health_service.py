"""Application service for system health checks."""

from datetime import UTC, datetime

from apps.api.schemas.health import HealthResponse
from infrastructure.config import Settings, get_settings


class HealthService:
    """Service providing application health status."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def get_health_status(self) -> HealthResponse:
        """Return deterministic system health information."""
        return HealthResponse(
            status="ok",
            version=self.settings.app_version,
            timestamp=datetime.now(UTC),
            environment=self.settings.app_env,
        )
