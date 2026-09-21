"""Schemas for company, department, and organization endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class CompanyCreateRequest(BaseModel):
    """Request schema for creating a new company."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Legal or operational company name"
    )
    description: str | None = Field(
        None, max_length=2048, description="Brief description of the business"
    )
    mission: str | None = Field(None, max_length=2048, description="Company mission statement")
    industry: str | None = Field(None, max_length=128, description="Primary industry sector")


class CompanyUpdateRequest(BaseModel):
    """Request schema for updating company profile."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2048)
    mission: str | None = Field(None, max_length=2048)
    industry: str | None = Field(None, max_length=128)
    status: str | None = Field(None, pattern=r"^(active|pending|archived)$")


class CompanyResponse(BaseModel):
    """Response schema for company information."""

    id: str
    name: str
    description: str | None = None
    mission: str | None = None
    industry: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    user_role: str | None = Field(None, description="Active role of caller within this company")


class DepartmentCreateRequest(BaseModel):
    """Request schema for creating a department."""

    name: str = Field(..., min_length=1, max_length=128, description="Department name (e.g. CTO)")
    code: str = Field(
        ..., min_length=1, max_length=32, description="Short code identifier (e.g. cto)"
    )
    description: str | None = Field(None, max_length=2048)
    lead_role: str | None = Field(None, max_length=128, description="Organizational lead title")


class DepartmentUpdateRequest(BaseModel):
    """Request schema for updating department properties."""

    name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = Field(None, max_length=2048)
    lead_role: str | None = Field(None, max_length=128)
    status: str | None = Field(None, pattern=r"^(active|planned|inactive)$")


class DepartmentResponse(BaseModel):
    """Response schema for department entities."""

    id: str
    company_id: str
    name: str
    code: str
    description: str | None = None
    lead_role: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class CompanyMemberResponse(BaseModel):
    """Response schema for company members."""

    id: str
    company_id: str
    user_id: str
    user_name: str
    user_email: str
    role: str
    status: str
    created_at: datetime
