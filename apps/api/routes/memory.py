"""FastAPI route handlers for Company Memory, Decisions, and Grounded Operational State.

Adheres strictly to docs/Phases.md Section 15 and docs/Memory.md Sections 33-34.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.memory_service import MemoryService
from apps.api.dependencies.auth import get_current_user
from apps.api.schemas.memory import (
    CeoInquiryApiRequest,
    CeoInquiryApiResponse,
    CeoInquiryCitationItem,
    CompanyDecisionCreateRequest,
    CompanyDecisionItemResponse,
    CompanyDecisionListResponse,
    CompanyStateResponse,
    TaskContextResponse,
)
from domain.memory.exceptions import (
    DecisionAlreadySupersededError,
    DecisionNotFoundError,
    InvalidDecisionStateError,
    MemoryAccessDeniedError,
)
from domain.memory.schemas import (
    CeoInquiryRequest,
    CompanyDecisionCreate,
    CompanyDecisionFilter,
    DecisionStatus,
)
from domain.work.exceptions import ProjectNotFoundError, TaskNotFoundError
from infrastructure.database.models import CompanyDecision, User
from infrastructure.database.session import get_db_session

router = APIRouter(prefix="/api/v1/companies/{company_id}", tags=["Company Memory & Decisions"])


def _format_decision_response(dec: CompanyDecision) -> CompanyDecisionItemResponse:
    return CompanyDecisionItemResponse(
        id=dec.id,
        company_id=dec.company_id,
        project_id=dec.project_id,
        task_id=dec.task_id,
        title=dec.title,
        decision=dec.decision,
        rationale=dec.rationale,
        evidence=dec.evidence or {},
        status=dec.status,
        decided_by_user_id=dec.decided_by_user_id,
        decided_by_agent_id=dec.decided_by_agent_id,
        superseded_by_decision_id=dec.superseded_by_decision_id,
        created_at=dec.created_at,
        updated_at=dec.updated_at,
    )


@router.get(
    "/memory/state",
    response_model=CompanyStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full authoritative company operational state snapshot",
)
async def get_company_state(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CompanyStateResponse:
    """Retrieve synthesized live state memory across all company entities."""
    service = MemoryService(db=db)
    try:
        packet = await service.get_company_state(
            company_id=company_id,
            user_id=current_user.id,
        )
        return CompanyStateResponse(
            company=packet.company,
            departments=packet.departments,
            agents=packet.agents,
            projects=packet.projects,
            tasks_summary=packet.tasks_summary,
            recent_approvals=packet.recent_approvals,
            decisions=packet.decisions,
            generated_at=packet.generated_at,
        )
    except MemoryAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get(
    "/memory/decisions",
    response_model=CompanyDecisionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List company decisions",
)
async def list_decisions(
    company_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: Annotated[
        DecisionStatus | None,
        Query(alias="status", description="Filter by decision status"),
    ] = None,
    project_id: Annotated[
        str | None,
        Query(description="Filter by associated project ID"),
    ] = None,
    task_id: Annotated[
        str | None,
        Query(description="Filter by associated task ID"),
    ] = None,
) -> CompanyDecisionListResponse:
    """List historical and active decisions recorded in company memory."""
    service = MemoryService(db=db)
    filter_params = CompanyDecisionFilter(
        status=status_filter,
        project_id=project_id,
        task_id=task_id,
    )
    try:
        decisions = await service.list_decisions(
            company_id=company_id,
            user_id=current_user.id,
            filter_params=filter_params,
        )
        items = [_format_decision_response(d) for d in decisions]
        return CompanyDecisionListResponse(items=items, total=len(items))
    except MemoryAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post(
    "/memory/decisions",
    response_model=CompanyDecisionItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an authoritative company decision",
)
async def record_decision(
    company_id: str,
    body: CompanyDecisionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CompanyDecisionItemResponse:
    """Record an authoritative new decision in company memory adhering to docs/Memory.md § 33."""
    service = MemoryService(db=db)
    create_dto = CompanyDecisionCreate(
        title=body.title,
        decision=body.decision,
        rationale=body.rationale,
        evidence=body.evidence,
        project_id=body.project_id,
        task_id=body.task_id,
        decided_by_agent_id=body.decided_by_agent_id,
    )
    try:
        created = await service.record_decision(
            company_id=company_id,
            user_id=current_user.id,
            data=create_dto,
        )
        return _format_decision_response(created)
    except MemoryAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (ProjectNotFoundError, TaskNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/memory/decisions/{decision_id}",
    response_model=CompanyDecisionItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific company decision",
)
async def get_decision(
    company_id: str,
    decision_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CompanyDecisionItemResponse:
    """Retrieve an individual decision record by ID within company tenancy."""
    service = MemoryService(db=db)
    try:
        decision = await service.get_decision(
            company_id=company_id,
            user_id=current_user.id,
            decision_id=decision_id,
        )
        return _format_decision_response(decision)
    except MemoryAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except DecisionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/memory/decisions/{decision_id}/supersede",
    response_model=CompanyDecisionItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Supersede an existing decision",
)
async def supersede_decision(
    company_id: str,
    decision_id: str,
    body: CompanyDecisionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CompanyDecisionItemResponse:
    """Supersede a previous decision, preserving historical immutability."""
    service = MemoryService(db=db)
    create_dto = CompanyDecisionCreate(
        title=body.title,
        decision=body.decision,
        rationale=body.rationale,
        evidence=body.evidence,
        project_id=body.project_id,
        task_id=body.task_id,
        decided_by_agent_id=body.decided_by_agent_id,
    )
    try:
        new_decision = await service.supersede_decision(
            company_id=company_id,
            user_id=current_user.id,
            old_decision_id=decision_id,
            data=create_dto,
        )
        return _format_decision_response(new_decision)
    except MemoryAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except DecisionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (DecisionAlreadySupersededError, InvalidDecisionStateError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get(
    "/memory/context/task/{task_id}",
    response_model=TaskContextResponse,
    status_code=status.HTTP_200_OK,
    summary="Get task-scoped context bundle",
)
async def get_task_context(
    company_id: str,
    task_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TaskContextResponse:
    """Retrieve operational context bundle scoped to a task."""
    service = MemoryService(db=db)
    try:
        data = await service.get_context_for_task(
            company_id=company_id,
            user_id=current_user.id,
            task_id=task_id,
        )
        return TaskContextResponse(
            task=data["task"],
            project=data["project"],
            company=data["company"],
            decisions=data["decisions"],
            execution_history=data["execution_history"],
            synthesized_prompt=data["synthesized_prompt"],
        )
    except MemoryAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/ceo/inquire",
    response_model=CeoInquiryApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Inquire CEO using grounded company memory",
)
async def ceo_inquire(
    company_id: str,
    body: CeoInquiryApiRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CeoInquiryApiResponse:
    """Query the CEO agent with deterministic factual responses grounded exclusively in persistent state."""
    service = MemoryService(db=db)
    try:
        inquiry_dto = CeoInquiryRequest(question=body.question)
        domain_res = await service.ceo_inquire(
            company_id=company_id,
            user_id=current_user.id,
            inquiry=inquiry_dto,
        )
        citations = [
            CeoInquiryCitationItem(
                source_type=c.source_type,
                source_id=c.source_id,
                reference=c.reference,
            )
            for c in domain_res.citations
        ]
        return CeoInquiryApiResponse(
            answer=domain_res.answer,
            citations=citations,
            grounded_state_timestamp=domain_res.grounded_state_timestamp,
        )
    except MemoryAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
