"""Integration tests for GET /health endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import create_application
from infrastructure.config import Settings


@pytest.mark.asyncio
async def test_get_health_endpoint_success() -> None:
    """Verify GET /health returns 200 OK with expected structure."""
    settings = Settings(
        app_name="AI Company OS Test",
        app_version="0.1.0-test",
        app_env="test",
    )
    app = create_application(settings=settings)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0-test"
    assert data["environment"] == "test"
    assert "timestamp" in data
