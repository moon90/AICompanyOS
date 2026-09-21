"""Authentication request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    """Registration request payload adhering to docs/Phases.md Section 5."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=255, description="Full name")
    email: str = Field(..., min_length=3, max_length=255, description="User email address")
    password: str = Field(..., min_length=8, description="Account password")
    confirm_password: str = Field(..., min_length=8, description="Password confirmation")


class LoginRequest(BaseModel):
    """Login request payload adhering to docs/Phases.md Section 5."""

    model_config = ConfigDict(frozen=True)

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Account password")


class UserResponse(BaseModel):
    """Public user profile response schema."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    status: str = Field(..., description="Account status")
    created_at: datetime = Field(..., description="Registration timestamp")
    last_login_at: datetime | None = Field(None, description="Last successful login timestamp")


class AuthResponse(BaseModel):
    """Authentication success response payload."""

    model_config = ConfigDict(frozen=True)

    user: UserResponse = Field(..., description="Authenticated user profile")
    token: str = Field(..., description="Session token")
    token_type: str = Field("bearer", description="Token scheme")


class MessageResponse(BaseModel):
    """Generic status response message."""

    model_config = ConfigDict(frozen=True)

    message: str = Field(..., description="Status message")
