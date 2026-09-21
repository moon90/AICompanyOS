"""API route handlers for company, department, and organization management."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.company_service import CompanyService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.company import (
    CompanyCreateRequest,
    CompanyMemberResponse,
    CompanyResponse,
    CompanyUpdateRequest,
    DepartmentCreateRequest,
    DepartmentResponse,
    DepartmentUpdateRequest,
)
from domain.company.exceptions import (
    CompanyAccessDeniedError,
    CompanyNotFoundError,
    DepartmentAlreadyExistsError,
    DepartmentNotFoundError,
    InvalidCompanyDataError,
)
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


def get_company_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CompanyService:
    """Dependency provider for CompanyService."""
    return CompanyService(session=session)


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Company",
    description="Create a new company, establish caller as owner, and seed initial departments.",
)
async def create_company(
    request: CompanyCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyResponse:
    """Create a new company entity."""
    try:
        company, member = await service.create_company(
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            mission=request.mission,
            industry=request.industry,
        )
        return CompanyResponse(
            id=company.id,
            name=company.name,
            description=company.description,
            mission=company.mission,
            industry=company.industry,
            status=company.status,
            created_at=company.created_at,
            updated_at=company.updated_at,
            user_role=member.role,
        )
    except InvalidCompanyDataError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err.message,
        ) from err


@router.get(
    "",
    response_model=list[CompanyResponse],
    status_code=status.HTTP_200_OK,
    summary="List User Companies",
    description="List all active companies that the authenticated user belongs to.",
)
async def list_companies(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> list[CompanyResponse]:
    """Retrieve companies for the authenticated user."""
    records = await service.get_user_companies(user_id=current_user.id)
    return [
        CompanyResponse(
            id=company.id,
            name=company.name,
            description=company.description,
            mission=company.mission,
            industry=company.industry,
            status=company.status,
            created_at=company.created_at,
            updated_at=company.updated_at,
            user_role=member.role,
        )
        for company, member in records
    ]


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Company",
    description="Retrieve company details after validating caller membership.",
)
async def get_company(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyResponse:
    """Get company by ID."""
    try:
        company, member = await service.get_company(user_id=current_user.id, company_id=company_id)
        return CompanyResponse(
            id=company.id,
            name=company.name,
            description=company.description,
            mission=company.mission,
            industry=company.industry,
            status=company.status,
            created_at=company.created_at,
            updated_at=company.updated_at,
            user_role=member.role,
        )
    except CompanyNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=err.message,
        ) from err
    except CompanyAccessDeniedError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=err.message,
        ) from err


@router.patch(
    "/{company_id}",
    response_model=CompanyResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Company",
    description="Update company settings. Requires owner or administrator role.",
)
async def update_company(
    company_id: str,
    request: CompanyUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyResponse:
    """Update company details."""
    try:
        company = await service.update_company(
            user_id=current_user.id,
            company_id=company_id,
            name=request.name,
            description=request.description,
            mission=request.mission,
            industry=request.industry,
            status=request.status,
        )
        _, member = await service.get_company(user_id=current_user.id, company_id=company_id)
        return CompanyResponse(
            id=company.id,
            name=company.name,
            description=company.description,
            mission=company.mission,
            industry=company.industry,
            status=company.status,
            created_at=company.created_at,
            updated_at=company.updated_at,
            user_role=member.role,
        )
    except CompanyNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=err.message,
        ) from err
    except CompanyAccessDeniedError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=err.message,
        ) from err
    except InvalidCompanyDataError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err.message,
        ) from err


@router.get(
    "/{company_id}/departments",
    response_model=list[DepartmentResponse],
    status_code=status.HTTP_200_OK,
    summary="List Departments",
    description="List all organizational departments for a company.",
)
async def list_departments(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> list[DepartmentResponse]:
    """Retrieve departments for a company."""
    try:
        departments = await service.get_departments(user_id=current_user.id, company_id=company_id)
        return [
            DepartmentResponse(
                id=d.id,
                company_id=d.company_id,
                name=d.name,
                code=d.code,
                description=d.description,
                lead_role=d.lead_role,
                status=d.status,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in departments
        ]
    except CompanyNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=err.message,
        ) from err
    except CompanyAccessDeniedError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=err.message,
        ) from err


@router.post(
    "/{company_id}/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Department",
    description="Create a department within a company. Requires administrative role.",
)
async def create_department(
    company_id: str,
    request: DepartmentCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> DepartmentResponse:
    """Create a new department in a company."""
    try:
        dept = await service.create_department(
            user_id=current_user.id,
            company_id=company_id,
            name=request.name,
            code=request.code,
            description=request.description,
            lead_role=request.lead_role,
        )
        return DepartmentResponse(
            id=dept.id,
            company_id=dept.company_id,
            name=dept.name,
            code=dept.code,
            description=dept.description,
            lead_role=dept.lead_role,
            status=dept.status,
            created_at=dept.created_at,
            updated_at=dept.updated_at,
        )
    except CompanyNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=err.message,
        ) from err
    except CompanyAccessDeniedError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=err.message,
        ) from err
    except DepartmentAlreadyExistsError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=err.message,
        ) from err
    except InvalidCompanyDataError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err.message,
        ) from err


@router.patch(
    "/{company_id}/departments/{department_id}",
    response_model=DepartmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Department",
    description="Update department properties. Requires administrative role.",
)
async def update_department(
    company_id: str,
    department_id: str,
    request: DepartmentUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> DepartmentResponse:
    """Update department configuration."""
    try:
        dept = await service.update_department(
            user_id=current_user.id,
            company_id=company_id,
            department_id=department_id,
            name=request.name,
            description=request.description,
            lead_role=request.lead_role,
            status=request.status,
        )
        return DepartmentResponse(
            id=dept.id,
            company_id=dept.company_id,
            name=dept.name,
            code=dept.code,
            description=dept.description,
            lead_role=dept.lead_role,
            status=dept.status,
            created_at=dept.created_at,
            updated_at=dept.updated_at,
        )
    except CompanyNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=err.message,
        ) from err
    except CompanyAccessDeniedError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=err.message,
        ) from err
    except DepartmentNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=err.message,
        ) from err
    except InvalidCompanyDataError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err.message,
        ) from err


@router.get(
    "/{company_id}/members",
    response_model=list[CompanyMemberResponse],
    status_code=status.HTTP_200_OK,
    summary="List Company Members",
    description="List members of a company.",
)
async def list_company_members(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> list[CompanyMemberResponse]:
    """Retrieve members for a company."""
    try:
        members = await service.get_company_members(user_id=current_user.id, company_id=company_id)
        return [
            CompanyMemberResponse(
                id=m.id,
                company_id=m.company_id,
                user_id=u.id,
                user_name=u.name,
                user_email=u.email,
                role=m.role,
                status=m.status,
                created_at=m.created_at,
            )
            for m, u in members
        ]
    except CompanyNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=err.message,
        ) from err
    except CompanyAccessDeniedError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=err.message,
        ) from err
