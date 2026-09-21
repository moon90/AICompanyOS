"""System and infrastructure status schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class SystemStatusResponse(BaseModel):
    """System status and infrastructure readiness response."""

    status: str = Field(..., description="Overall system operational status (e.g. 'operational')")
    database: str = Field(..., description="Database connection status (e.g. 'connected')")
    auth_authority: str = Field(
        ..., description="Authoritative session management source (e.g. 'postgresql_sessions')"
    )
    environment: str = Field(..., description="Application execution environment")
    version: str = Field(..., description="Application semantic version")
    current_phase: str = Field(..., description="Current roadmap phase name and identifier")
    timestamp: datetime = Field(..., description="UTC timestamp of the status check")
