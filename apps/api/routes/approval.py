"""FastAPI route handlers for Human Approval & Oversight System adhering to docs/Phases.md Section 14 and docs/Architecture.md Sections 40-45."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.approval_service import ApprovalService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalListResponse,
    ApprovalRequestResponse,
)
from domain.approvals.exceptions import (
    AgentCannotApproveError,
    ApprovalAccessDeniedError,
    ApprovalAlreadyProcessedError,
    ApprovalNotFoundError,
    InvalidApprovalTransitionError,
)
from domain.approvals.schemas import (
    ApprovalDecisionInput,
    ApprovalFilter,
    ApprovalRiskLevel,
    ApprovalStatus,
)
from infrastructure.database.models import ApprovalRequest, User
from infrastructure.database.session import get_db_session

router = APIRouter(
    prefix="/api/v1/companies/{company_id}/approvals", tags=["Approvals & Oversight"]
)


def _format_approval_response(approval: ApprovalRequest) -> ApprovalRequestResponse:
    """Format an ApprovalRequest ORM entity into ApprovalRequestResponse with enriched relations."""
    agent_name = approval.agent.name if approval.agent else None
    task_title = approval.task.title if approval.task else None
    reviewer_name = approval.reviewed_by_user.name if approval.reviewed_by_user else None
    tool_name = approval.tool_execution.tool_name if approval.tool_execution else None

    return ApprovalRequestResponse(
        id=approval.id,
        company_id=approval.company_id,
        task_id=approval.task_id,
        agent_id=approval.agent_id,
        execution_id=approval.execution_id,
        tool_execution_id=approval.tool_execution_id,
        action_type=approval.action_type,
        description=approval.description,
        payload=approval.payload or {},
        risk_level=approval.risk_level,
        status=approval.status,
        reviewed_by_user_id=approval.reviewed_by_user_id,
        reviewed_at=approval.reviewed_at,
        decision_reason=approval.decision_reason,
        created_at=approval.created_at,
        updated_at=approval.updated_at,
        agent_name=agent_name,
        task_title=task_title,
        reviewer_name=reviewer_name,
        tool_name=tool_name,
    )


@router.get(
    "",
    response_model=ApprovalListResponse,
    status_code=status.HTTP_200_OK,
    summary="List approval requests for a company",
)
async def list_approvals(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: Annotated[
        ApprovalStatus | None,
        Query(alias="status", description="Filter by approval status"),
    ] = None,
    risk_level: Annotated[
        ApprovalRiskLevel | None,
        Query(description="Filter by risk level"),
    ] = None,
    action_type: Annotated[
        str | None,
        Query(description="Filter by action type"),
    ] = None,
    agent_id: Annotated[
        str | None,
        Query(description="Filter by calling agent ID"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Items per page"),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0, description="Pagination offset"),
    ] = 0,
) -> ApprovalListResponse:
    """Retrieve all approval requests in the company matching the specified filters."""
    service = ApprovalService(db=db)
    filter_params = ApprovalFilter(
        status=status_filter,
        risk_level=risk_level,
        action_type=action_type,
        agent_id=agent_id,
        limit=limit,
        offset=offset,
    )

    try:
        records, total = await service.list_approvals(
            company_id=company_id,
            user_id=current_user.id,
            filter_params=filter_params,
        )
        return ApprovalListResponse(
            items=[_format_approval_response(r) for r in records],
            total=total,
        )
    except ApprovalAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get(
    "/{approval_id}",
    response_model=ApprovalRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single approval request details",
)
async def get_approval(
    company_id: str,
    approval_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApprovalRequestResponse:
    """Retrieve detailed approval request record by ID."""
    service = ApprovalService(db=db)
    try:
        approval = await service.get_approval(
            company_id=company_id,
            user_id=current_user.id,
            approval_id=approval_id,
        )
        return _format_approval_response(approval)
    except ApprovalAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{approval_id}/approve",
    response_model=ApprovalRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve pending request and execute gated action",
)
async def approve_request(
    company_id: str,
    approval_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    body: ApprovalDecisionRequest | None = None,
) -> ApprovalRequestResponse:
    """Authorize a consequential action or tool invocation. Executes gated actions immediately."""
    service = ApprovalService(db=db)
    decision = ApprovalDecisionInput(decision_reason=body.decision_reason if body else None)

    try:
        approval = await service.approve_request(
            company_id=company_id,
            user_id=current_user.id,
            approval_id=approval_id,
            decision_input=decision,
            is_agent=False,
        )
        return _format_approval_response(approval)
    except ApprovalAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ApprovalAlreadyProcessedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AgentCannotApproveError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidApprovalTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/{approval_id}/reject",
    response_model=ApprovalRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject pending request and permanently block action",
)
async def reject_request(
    company_id: str,
    approval_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    body: ApprovalDecisionRequest | None = None,
) -> ApprovalRequestResponse:
    """Reject a consequential action or tool invocation. Action will remain permanently blocked."""
    service = ApprovalService(db=db)
    decision = ApprovalDecisionInput(decision_reason=body.decision_reason if body else None)

    try:
        approval = await service.reject_request(
            company_id=company_id,
            user_id=current_user.id,
            approval_id=approval_id,
            decision_input=decision,
            is_agent=False,
        )
        return _format_approval_response(approval)
    except ApprovalAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ApprovalAlreadyProcessedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AgentCannotApproveError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidApprovalTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
