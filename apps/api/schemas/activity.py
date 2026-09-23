"""Pydantic schemas for Activity History API per docs/Phases.md Section 17."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ActivityEventItemResponse(BaseModel):
    """Pydantic schema representing a single activity event."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    project_id: str | None = None
    task_id: str | None = None
    actor_type: str
    actor_id: str | None = None
    event_type: str
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def extract_from_orm(cls, data: Any) -> Any:
        """Map event_metadata attribute from SQLAlchemy ORM models."""
        if hasattr(data, "event_metadata"):
            return {
                "id": getattr(data, "id", None),
                "company_id": getattr(data, "company_id", None),
                "project_id": getattr(data, "project_id", None),
                "task_id": getattr(data, "task_id", None),
                "actor_type": getattr(data, "actor_type", "system"),
                "actor_id": getattr(data, "actor_id", None),
                "event_type": getattr(data, "event_type", ""),
                "message": getattr(data, "message", ""),
                "metadata": getattr(data, "event_metadata", {}) or {},
                "created_at": getattr(data, "created_at", None),
            }
        return data


class ActivityListResponse(BaseModel):
    """Paginated list of activity events."""

    items: list[ActivityEventItemResponse]
    total: int
    limit: int
    offset: int
