"""FastAPI route handlers for CEO Orchestration endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.ceo_service import CeoService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.ceo import (
    CeoContextResponse,
    PlanCreateRequest,
    PlanDetailResponse,
    PlanSummaryResponse,
)
from apps.api.schemas.delegation import (
    PlanDelegateRequest,
    PlanDelegationResultResponse,
)
from domain.ceo.exceptions import (
    CeoAccessDeniedError,
    CeoNotFoundError,
    InvalidGoalError,
    InvalidPlanGraphError,
    PlanDepthExceededError,
    PlanNotFoundError,
)
from infrastructure.database.models import User
from infrastructure.database.session import get_db_session
from orchestration.planner.schemas import GoalIntake

router = APIRouter(prefix="/api/v1/companies/{company_id}/ceo", tags=["CEO Orchestrator"])


def get_ceo_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> CeoService:
    """Dependency provider for CeoService."""
    return CeoService(db=session)


@router.get("/context", response_model=CeoContextResponse, status_code=status.HTTP_200_OK)
async def get_ceo_context(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CeoService, Depends(get_ceo_service)],
) -> CeoContextResponse:
    """Retrieve authoritative company context and resolved CEO agent identity."""
    try:
        context = await service.get_ceo_context(user_id=current_user.id, company_id=company_id)
        return CeoContextResponse(**context)
    except CeoAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.post("/plan", response_model=PlanDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    company_id: str,
    payload: PlanCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CeoService, Depends(get_ceo_service)],
) -> PlanDetailResponse:
    """Intake user goal, assemble context, generate structured plan and DAG proposal."""
    try:
        goal = GoalIntake(
            objective=payload.objective,
            requested_outcome=payload.requested_outcome,
            constraints=payload.constraints,
            priority=payload.priority,
            requirements=payload.requirements,
        )
        plan = await service.generate_plan(
            user_id=current_user.id,
            company_id=company_id,
            goal=goal,
        )
        return PlanDetailResponse(
            id=plan.id,
            company_id=plan.company_id,
            user_id=plan.user_id,
            ceo_agent_id=plan.ceo_agent_id,
            goal=plan.goal,
            requested_outcome=plan.requested_outcome,
            priority=plan.priority,
            status=plan.status,
            reasoning_summary=plan.reasoning_summary,
            context_snapshot=plan.context_snapshot,
            plan_steps=plan.plan_steps,
            delegation_proposals=plan.delegation_proposals,
            approval_requirements=plan.approval_requirements,
            risks=plan.risks,
            assumptions=plan.assumptions,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )
    except CeoAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except CeoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except InvalidGoalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except (InvalidPlanGraphError, PlanDepthExceededError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


@router.get("/plans", response_model=list[PlanSummaryResponse], status_code=status.HTTP_200_OK)
async def list_plans(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CeoService, Depends(get_ceo_service)],
    limit: int = 50,
    offset: int = 0,
) -> list[PlanSummaryResponse]:
    """List historical CEO plans generated for the company."""
    try:
        plans = await service.list_plans(
            user_id=current_user.id,
            company_id=company_id,
            limit=limit,
            offset=offset,
        )
        return [
            PlanSummaryResponse(
                id=p.id,
                company_id=p.company_id,
                user_id=p.user_id,
                ceo_agent_id=p.ceo_agent_id,
                goal=p.goal,
                requested_outcome=p.requested_outcome,
                priority=p.priority,
                status=p.status,
                reasoning_summary=p.reasoning_summary,
                step_count=len(p.plan_steps),
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in plans
        ]
    except CeoAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.get("/plans/{plan_id}", response_model=PlanDetailResponse, status_code=status.HTTP_200_OK)
async def get_plan(
    company_id: str,
    plan_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CeoService, Depends(get_ceo_service)],
) -> PlanDetailResponse:
    """Retrieve details of a specific CEO plan."""
    try:
        plan = await service.get_plan(
            user_id=current_user.id,
            company_id=company_id,
            plan_id=plan_id,
        )
        return PlanDetailResponse(
            id=plan.id,
            company_id=plan.company_id,
            user_id=plan.user_id,
            ceo_agent_id=plan.ceo_agent_id,
            goal=plan.goal,
            requested_outcome=plan.requested_outcome,
            priority=plan.priority,
            status=plan.status,
            reasoning_summary=plan.reasoning_summary,
            context_snapshot=plan.context_snapshot,
            plan_steps=plan.plan_steps,
            delegation_proposals=plan.delegation_proposals,
            approval_requirements=plan.approval_requirements,
            risks=plan.risks,
            assumptions=plan.assumptions,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )
    except CeoAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except PlanNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/plans/{plan_id}/delegate",
    response_model=PlanDelegationResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Delegate CEO Plan",
    description="Decompose a proposed CEO plan into a Project, Parent Task, Child Tasks, and DAG dependencies per docs/Phases.md Section 11.",
)
async def delegate_plan(
    company_id: str,
    plan_id: str,
    request: PlanDelegateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[CeoService, Depends(get_ceo_service)],
) -> PlanDelegationResultResponse:
    """Delegate a proposed CEO plan into executable projects, tasks, and delegations."""
    try:
        result = await service.delegate_plan(
            user_id=current_user.id,
            company_id=company_id,
            plan_id=plan_id,
            project_id=request.project_id,
            project_name=request.project_name,
        )
        return PlanDelegationResultResponse(**result)
    except CeoAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except PlanNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
