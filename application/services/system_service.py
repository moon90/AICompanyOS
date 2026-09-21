"""Application service for system status and infrastructure telemetry."""

from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.schemas.system import SystemStatusResponse
from infrastructure.config import Settings, get_settings


class SystemService:
    """Service providing live infrastructure and system foundation status."""

    CURRENT_PHASE = "Phase 7 — Task Assignment & Delegation"

    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

    async def get_system_status(self) -> SystemStatusResponse:
        """Check live database connectivity and return system status."""
        try:
            await self.session.execute(text("SELECT 1"))
            db_status = "connected"
            system_status = "operational"
        except Exception:
            db_status = "disconnected"
            system_status = "degraded"

        return SystemStatusResponse(
            status=system_status,
            database=db_status,
            auth_authority="postgresql_sessions",
            environment=self.settings.app_env,
            version=self.settings.app_version,
            current_phase=self.CURRENT_PHASE,
            timestamp=datetime.now(UTC),
        )
