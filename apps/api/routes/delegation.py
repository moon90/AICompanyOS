"""API route handlers for agent task delegation adhering to docs/Phases.md Section 11."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.delegation_service import DelegationService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.delegation import (
    DelegationListResponse,
    DelegationRecordResponse,
    TaskDelegateRequest,
)
from domain.delegation.exceptions import (
    CircularDelegationError,
    DelegationAccessDeniedError,
    DelegationError,
    DelegationNotFoundError,
    InvalidDelegationHierarchyError,
    MaxDelegationDepthExceededError,
)
from domain.work.exceptions import TaskNotFoundError
from infrastructure.database.models import DelegationRecord, User
from infrastructure.database.session import get_db_session

router = APIRouter(prefix="/api/v1/companies/{company_id}", tags=["delegation"])


def get_delegation_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DelegationService:
    """Dependency provider for DelegationService."""
    return DelegationService(db=session)


def _to_response(record: DelegationRecord) -> DelegationRecordResponse:
    """Convert a DelegationRecord model into a DelegationRecordResponse."""
    target_name = None
    target_role = None
    if "delegated_to_agent" in record.__dict__ and record.delegated_to_agent:
        target_name = record.delegated_to_agent.name
        target_role = record.delegated_to_agent.role

    by_agent_name = None
    if "delegated_by_agent" in record.__dict__ and record.delegated_by_agent:
        by_agent_name = record.delegated_by_agent.name

    by_user_name = None
    if "delegated_by_user" in record.__dict__ and record.delegated_by_user:
        by_user_name = record.delegated_by_user.name

    return DelegationRecordResponse(
        id=record.id,
        company_id=record.company_id,
        task_id=record.task_id,
        delegated_by_user_id=record.delegated_by_user_id,
        delegated_by_agent_id=record.delegated_by_agent_id,
        delegated_to_agent_id=record.delegated_to_agent_id,
        scope=record.scope,
        reason=record.reason,
        depth=record.depth,
        status=record.status,
        created_at=record.created_at,
        delegated_to_agent_name=target_name,
        delegated_to_agent_role=target_role,
        delegated_by_agent_name=by_agent_name,
        delegated_by_user_name=by_user_name,
    )


@router.post(
    "/tasks/{task_id}/delegate",
    response_model=DelegationRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Delegate Task",
    description="Delegate a task to an agent with hierarchy validation, cycle rejection, and audit tracking.",
)
async def delegate_task(
    company_id: str,
    task_id: str,
    request: TaskDelegateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[DelegationService, Depends(get_delegation_service)],
) -> DelegationRecordResponse:
    """Delegate an existing task to an authorized agent."""
    try:
        record = await service.delegate_task(
            company_id=company_id,
            task_id=task_id,
            user_id=current_user.id,
            target_agent_id=request.target_agent_id,
            reason=request.reason,
            scope=request.scope,
            delegator_agent_id=request.delegator_agent_id,
        )
        return _to_response(record)
    except DelegationAccessDeniedError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err.message) from err
    except (TaskNotFoundError, DelegationNotFoundError) as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err.message) from err
    except (
        CircularDelegationError,
        MaxDelegationDepthExceededError,
        InvalidDelegationHierarchyError,
        DelegationError,
    ) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err.message) from err
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err)
        ) from err


@router.get(
    "/tasks/{task_id}/delegations",
    response_model=list[DelegationRecordResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Task Delegation Lineage",
    description="Retrieve the chronological delegation history and lineage for a specific task.",
)
async def get_task_delegations(
    company_id: str,
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[DelegationService, Depends(get_delegation_service)],
) -> list[DelegationRecordResponse]:
    """Retrieve all delegation records for a task."""
    try:
        records = await service.get_task_delegations(
            company_id=company_id,
            user_id=current_user.id,
            task_id=task_id,
        )
        return [_to_response(r) for r in records]
    except DelegationAccessDeniedError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err.message) from err
    except TaskNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err.message) from err


@router.get(
    "/delegations",
    response_model=DelegationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Company Delegations",
    description="List all delegation audit records across the company workspace.",
)
async def list_company_delegations(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[DelegationService, Depends(get_delegation_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DelegationListResponse:
    """Retrieve paginated company delegation history."""
    try:
        records, total = await service.list_company_delegations(
            company_id=company_id,
            user_id=current_user.id,
            limit=limit,
            offset=offset,
        )
        return DelegationListResponse(
            items=[_to_response(r) for r in records],
            total=total,
        )
    except DelegationAccessDeniedError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err.message) from err
