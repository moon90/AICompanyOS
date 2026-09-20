"""Unit tests for HealthService."""

from application.services.health_service import HealthService
from infrastructure.config import Settings


def test_health_service_returns_ok_status() -> None:
    """Verify health service returns deterministic ok status and version."""
    settings = Settings(
        app_name="AI Company OS Test",
        app_version="0.1.0-test",
        app_env="test",
    )
    service = HealthService(settings=settings)
    response = service.get_health_status()

    assert response.status == "ok"
    assert response.version == "0.1.0-test"
    assert response.environment == "test"
    assert response.timestamp is not None
