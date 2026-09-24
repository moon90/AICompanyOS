"""Unit tests for SystemService."""

from unittest.mock import AsyncMock

import pytest

from application.services.system_service import SystemService
from infrastructure.config import Settings


@pytest.mark.asyncio
async def test_system_service_success() -> None:
    """Verify system service returns operational status when database succeeds."""
    mock_session = AsyncMock()
    mock_session.execute.return_value = None

    settings = Settings(
        app_name="AI Company OS Test",
        app_version="0.1.0-test",
        app_env="test",
    )
    service = SystemService(session=mock_session, settings=settings)
    status = await service.get_system_status()

    assert status.status == "operational"
    assert status.database == "connected"
    assert status.auth_authority == "postgresql_sessions"
    assert status.current_phase == "Phase 19 — Advanced Company Knowledge"
    assert status.environment == "test"
    assert status.version == "0.1.0-test"


@pytest.mark.asyncio
async def test_system_service_database_failure() -> None:
    """Verify system service handles database errors gracefully and reports degraded status."""
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("DB unreachable")

    settings = Settings(
        app_name="AI Company OS Test",
        app_version="0.1.0-test",
        app_env="test",
    )
    service = SystemService(session=mock_session, settings=settings)
    status = await service.get_system_status()

    assert status.status == "degraded"
    assert status.database == "disconnected"
