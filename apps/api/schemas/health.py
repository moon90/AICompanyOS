"""Health check schemas for the API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Deterministic health check response schema."""

    model_config = ConfigDict(frozen=True)

    status: str = Field(..., description="Application operational status")
    version: str = Field(..., description="Application semantic version")
    timestamp: datetime = Field(..., description="UTC timestamp of the health check")
    environment: str = Field(..., description="Current running environment")
