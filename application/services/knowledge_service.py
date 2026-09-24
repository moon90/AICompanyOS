"""Application service for company knowledge adhering to docs/Phases.md Section 23 and docs/Memory.md Sections 31-39."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.activity_service import ActivityService
from domain.artifacts.exceptions import ArtifactNotFoundError
from domain.knowledge.exceptions import (
    KnowledgeAccessDeniedError,
    KnowledgeNotFoundError,
)
from domain.knowledge.schemas import (
    KnowledgeCreatePayload,
    KnowledgeListResponse,
    KnowledgeQueryCitation,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    KnowledgeResponse,
    KnowledgeUpdatePayload,
    SelectiveContextRequest,
    SelectiveContextResponse,
)
from domain.memory.exceptions import DecisionNotFoundError
from domain.work.exceptions import ProjectNotFoundError, TaskNotFoundError
from infrastructure.database.models import (
    Artifact,
    CompanyDecision,
    CompanyKnowledge,
    CompanyMember,
    ExecutionRecord,
    Project,
    Task,
    User,
)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure datetime is UTC-aware, handling SQLite naive datetime values in tests."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class KnowledgeService:
    """Authoritative company knowledge service adhering to docs/Phases.md Section 23.

    Enables multi-tenant knowledge capture across research, strategies, policies,
    decision rationales, procedures, meeting notes, and historical results.
    Provides grounded Q&A and selective context synthesis for agents without loading
    the entire database.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _verify_company_access(self, company_id: str, user_id: str) -> CompanyMember:
        """Verify user is an active member of the target company."""
        result = await self.db.execute(
            select(CompanyMember).where(
                CompanyMember.company_id == company_id,
                CompanyMember.user_id == user_id,
                CompanyMember.status == "active",
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise KnowledgeAccessDeniedError(
                f"User {user_id} does not have access to company {company_id}"
            )
        return member

    def _to_response(self, item: CompanyKnowledge) -> KnowledgeResponse:
        """Convert ORM model to KnowledgeResponse domain schema."""
        created_at = _ensure_utc(item.created_at) or datetime.now(UTC)
        updated_at = _ensure_utc(item.updated_at) or datetime.now(UTC)
        return KnowledgeResponse(
            id=item.id,
            company_id=item.company_id,
            project_id=item.project_id,
            task_id=item.task_id,
            decision_id=item.decision_id,
            artifact_id=item.artifact_id,
            title=item.title,
            category=item.category,
            content=item.content,
            source_type=item.source_type,
            source_uri=item.source_uri,
            author_name=item.author_name,
            confidence=item.confidence,
            tags=list(item.tags or []),
            metadata=dict(item.knowledge_metadata or {}),
            created_at=created_at,
            updated_at=updated_at,
        )

    async def create_knowledge_item(
        self,
        company_id: str,
        payload: KnowledgeCreatePayload,
        user_id: str | None = None,
    ) -> KnowledgeResponse:
        """Create a new persistent company knowledge item."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        # Validate linked entities if provided
        if payload.project_id:
            proj_res = await self.db.execute(
                select(Project).where(
                    Project.id == payload.project_id,
                    Project.company_id == company_id,
                )
            )
            if not proj_res.scalar_one_or_none():
                raise ProjectNotFoundError(
                    f"Project {payload.project_id} not found in company {company_id}"
                )

        if payload.task_id:
            task_res = await self.db.execute(
                select(Task).where(
                    Task.id == payload.task_id,
                    Task.company_id == company_id,
                )
            )
            if not task_res.scalar_one_or_none():
                raise TaskNotFoundError(f"Task {payload.task_id} not found in company {company_id}")

        if payload.decision_id:
            dec_res = await self.db.execute(
                select(CompanyDecision).where(
                    CompanyDecision.id == payload.decision_id,
                    CompanyDecision.company_id == company_id,
                )
            )
            if not dec_res.scalar_one_or_none():
                raise DecisionNotFoundError(
                    f"Decision {payload.decision_id} not found in company {company_id}"
                )

        if payload.artifact_id:
            art_res = await self.db.execute(
                select(Artifact).where(
                    Artifact.id == payload.artifact_id,
                    Artifact.company_id == company_id,
                )
            )
            if not art_res.scalar_one_or_none():
                raise ArtifactNotFoundError(
                    f"Artifact {payload.artifact_id} not found in company {company_id}"
                )

        # Resolve author name
        author_name = payload.author_name
        if not author_name:
            if user_id:
                user_res = await self.db.execute(select(User).where(User.id == user_id))
                user = user_res.scalar_one_or_none()
                author_name = user.name or user.email if user else "Operator"
            else:
                author_name = "System Agent"

        item = CompanyKnowledge(
            id=str(uuid.uuid4()),
            company_id=company_id,
            project_id=payload.project_id,
            task_id=payload.task_id,
            decision_id=payload.decision_id,
            artifact_id=payload.artifact_id,
            title=payload.title,
            category=payload.category.value
            if hasattr(payload.category, "value")
            else str(payload.category),
            content=payload.content,
            source_type=payload.source_type.value
            if hasattr(payload.source_type, "value")
            else str(payload.source_type),
            source_uri=payload.source_uri,
            author_name=author_name,
            confidence=payload.confidence.value
            if hasattr(payload.confidence, "value")
            else str(payload.confidence),
            tags=payload.tags,
            knowledge_metadata=payload.metadata,
        )

        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            event_type="knowledge.created",
            message=f"Knowledge record created: '{item.title}' [{item.category}]",
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            project_id=item.project_id,
            task_id=item.task_id,
            metadata={"knowledge_id": item.id, "category": item.category},
        )

        return self._to_response(item)

    async def get_knowledge_item(
        self,
        company_id: str,
        item_id: str,
        user_id: str | None = None,
    ) -> KnowledgeResponse:
        """Retrieve a specific company knowledge record by ID."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        result = await self.db.execute(
            select(CompanyKnowledge).where(CompanyKnowledge.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise KnowledgeNotFoundError(f"Knowledge item {item_id} not found")

        if item.company_id != company_id:
            raise KnowledgeAccessDeniedError(
                f"Knowledge item {item_id} does not belong to company {company_id}"
            )

        return self._to_response(item)

    async def list_knowledge_items(
        self,
        company_id: str,
        user_id: str | None = None,
        category: str | None = None,
        project_id: str | None = None,
        decision_id: str | None = None,
        tags: list[str] | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> KnowledgeListResponse:
        """List and search paginated company knowledge items."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        query = select(CompanyKnowledge).where(CompanyKnowledge.company_id == company_id)

        if category:
            query = query.where(CompanyKnowledge.category == category)
        if project_id:
            query = query.where(CompanyKnowledge.project_id == project_id)
        if decision_id:
            query = query.where(CompanyKnowledge.decision_id == decision_id)
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    CompanyKnowledge.title.ilike(search_pattern),
                    CompanyKnowledge.content.ilike(search_pattern),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_res = await self.db.execute(count_query)
        total = total_res.scalar_one() or 0

        # Paginate
        offset = max(0, (page - 1) * page_size)
        paginated_query = (
            query.order_by(desc(CompanyKnowledge.created_at)).offset(offset).limit(page_size)
        )
        res = await self.db.execute(paginated_query)
        items = res.scalars().all()

        return KnowledgeListResponse(
            items=[self._to_response(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_knowledge_item(
        self,
        company_id: str,
        item_id: str,
        payload: KnowledgeUpdatePayload,
        user_id: str | None = None,
    ) -> KnowledgeResponse:
        """Update an existing company knowledge record."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        result = await self.db.execute(
            select(CompanyKnowledge).where(CompanyKnowledge.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise KnowledgeNotFoundError(f"Knowledge item {item_id} not found")

        if item.company_id != company_id:
            raise KnowledgeAccessDeniedError(
                f"Knowledge item {item_id} does not belong to company {company_id}"
            )

        if payload.project_id is not None:
            if payload.project_id != "":
                proj_res = await self.db.execute(
                    select(Project).where(
                        Project.id == payload.project_id,
                        Project.company_id == company_id,
                    )
                )
                if not proj_res.scalar_one_or_none():
                    raise ProjectNotFoundError(
                        f"Project {payload.project_id} not found in company {company_id}"
                    )
                item.project_id = payload.project_id
            else:
                item.project_id = None

        if payload.task_id is not None:
            if payload.task_id != "":
                task_res = await self.db.execute(
                    select(Task).where(
                        Task.id == payload.task_id,
                        Task.company_id == company_id,
                    )
                )
                if not task_res.scalar_one_or_none():
                    raise TaskNotFoundError(
                        f"Task {payload.task_id} not found in company {company_id}"
                    )
                item.task_id = payload.task_id
            else:
                item.task_id = None

        if payload.decision_id is not None:
            if payload.decision_id != "":
                dec_res = await self.db.execute(
                    select(CompanyDecision).where(
                        CompanyDecision.id == payload.decision_id,
                        CompanyDecision.company_id == company_id,
                    )
                )
                if not dec_res.scalar_one_or_none():
                    raise DecisionNotFoundError(
                        f"Decision {payload.decision_id} not found in company {company_id}"
                    )
                item.decision_id = payload.decision_id
            else:
                item.decision_id = None

        if payload.artifact_id is not None:
            if payload.artifact_id != "":
                art_res = await self.db.execute(
                    select(Artifact).where(
                        Artifact.id == payload.artifact_id,
                        Artifact.company_id == company_id,
                    )
                )
                if not art_res.scalar_one_or_none():
                    raise ArtifactNotFoundError(
                        f"Artifact {payload.artifact_id} not found in company {company_id}"
                    )
                item.artifact_id = payload.artifact_id
            else:
                item.artifact_id = None

        if payload.title is not None:
            item.title = payload.title
        if payload.category is not None:
            item.category = (
                payload.category.value
                if hasattr(payload.category, "value")
                else str(payload.category)
            )
        if payload.content is not None:
            item.content = payload.content
        if payload.source_type is not None:
            item.source_type = (
                payload.source_type.value
                if hasattr(payload.source_type, "value")
                else str(payload.source_type)
            )
        if payload.source_uri is not None:
            item.source_uri = payload.source_uri
        if payload.author_name is not None:
            item.author_name = payload.author_name
        if payload.confidence is not None:
            item.confidence = (
                payload.confidence.value
                if hasattr(payload.confidence, "value")
                else str(payload.confidence)
            )
        if payload.tags is not None:
            item.tags = payload.tags
        if payload.metadata is not None:
            item.knowledge_metadata = payload.metadata

        item.updated_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(item)

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            event_type="knowledge.updated",
            message=f"Knowledge record updated: '{item.title}'",
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            project_id=item.project_id,
            task_id=item.task_id,
            metadata={"knowledge_id": item.id},
        )

        return self._to_response(item)

    async def delete_knowledge_item(
        self,
        company_id: str,
        item_id: str,
        user_id: str | None = None,
    ) -> None:
        """Delete an existing company knowledge record."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        result = await self.db.execute(
            select(CompanyKnowledge).where(CompanyKnowledge.id == item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise KnowledgeNotFoundError(f"Knowledge item {item_id} not found")

        if item.company_id != company_id:
            raise KnowledgeAccessDeniedError(
                f"Knowledge item {item_id} does not belong to company {company_id}"
            )

        title = item.title
        await self.db.delete(item)
        await self.db.commit()

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            event_type="knowledge.deleted",
            message=f"Knowledge record deleted: '{title}'",
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            metadata={"knowledge_id": item_id},
        )

    async def query_knowledge(
        self,
        company_id: str,
        user_id: str | None,
        request: KnowledgeQueryRequest,
    ) -> KnowledgeQueryResponse:
        """Answer company inquiries adhering strictly to Section 23 canonical questions.

        Addresses:
        1. Why did we make this decision?
        2. What research supports it?
        3. What happened last time?
        4. Which projects depend on this decision?
        5. Which documents contain relevant information?
        """
        if user_id:
            await self._verify_company_access(company_id, user_id)

        q = request.question.strip().lower()
        now = datetime.now(UTC)

        citations: list[KnowledgeQueryCitation] = []
        related_decisions: list[dict[str, Any]] = []
        related_artifacts: list[dict[str, Any]] = []

        # 1. "Why did we make this decision?"
        if "why" in q and "decision" in q:
            # Query active decisions and decision rationales
            dec_query = select(CompanyDecision).where(CompanyDecision.company_id == company_id)
            if request.project_id:
                dec_query = dec_query.where(CompanyDecision.project_id == request.project_id)
            dec_res = await self.db.execute(
                dec_query.order_by(desc(CompanyDecision.created_at)).limit(5)
            )
            decisions = dec_res.scalars().all()

            kn_query = select(CompanyKnowledge).where(
                CompanyKnowledge.company_id == company_id,
                CompanyKnowledge.category.in_(["DECISION_RATIONALE", "STRATEGY"]),
            )
            kn_res = await self.db.execute(
                kn_query.order_by(desc(CompanyKnowledge.created_at)).limit(5)
            )
            knowledge_items = kn_res.scalars().all()

            lines = ["### Decision Rationale & Background\n"]
            if decisions:
                for d in decisions:
                    citations.append(
                        KnowledgeQueryCitation(
                            source_type="DECISION",
                            source_id=d.id,
                            title=d.title,
                            reference=f"Decision '{d.title}' [Status: {d.status}]",
                            confidence="HIGH",
                        )
                    )
                    related_decisions.append(
                        {
                            "id": d.id,
                            "title": d.title,
                            "topic": d.title,
                            "decision": d.decision,
                            "rationale": d.rationale,
                            "status": d.status,
                        }
                    )
                    lines.append(f"- **{d.title}**: {d.decision}\n  - *Rationale*: {d.rationale}")
            else:
                lines.append("No explicit recorded decisions matching this inquiry.")

            if knowledge_items:
                lines.append("\n#### Supporting Knowledge & Context:")
                for k in knowledge_items:
                    citations.append(
                        KnowledgeQueryCitation(
                            source_type="KNOWLEDGE",
                            source_id=k.id,
                            title=k.title,
                            reference=f"Knowledge [{k.category}]: {k.title}",
                            confidence=k.confidence,
                        )
                    )
                    lines.append(f"- **{k.title}**: {k.content[:200]}...")

            answer = "\n".join(lines)
            return KnowledgeQueryResponse(
                question=request.question,
                answer=answer,
                canonical_topic="Why did we make this decision?",
                citations=citations,
                related_decisions=related_decisions,
                related_artifacts=related_artifacts,
                timestamp=now,
            )

        # 2. "What research supports it?"
        if "research" in q or "support" in q:
            kn_query = select(CompanyKnowledge).where(
                CompanyKnowledge.company_id == company_id,
                or_(
                    CompanyKnowledge.category == "RESEARCH",
                    CompanyKnowledge.source_type == "RESEARCH",
                ),
            )
            if request.project_id:
                kn_query = kn_query.where(CompanyKnowledge.project_id == request.project_id)
            kn_res = await self.db.execute(
                kn_query.order_by(desc(CompanyKnowledge.created_at)).limit(5)
            )
            research_items = kn_res.scalars().all()

            art_query = select(Artifact).where(
                Artifact.company_id == company_id,
                Artifact.artifact_type.in_(
                    [
                        "REPORT",
                        "DOCUMENT",
                        "MARKDOWN",
                        "TEXT",
                        "research",
                        "document",
                        "markdown",
                        "report",
                    ]
                ),
            )
            art_res = await self.db.execute(art_query.order_by(desc(Artifact.created_at)).limit(5))
            artifacts = art_res.scalars().all()

            lines = ["### Supporting Research & Empirical Evidence\n"]
            if research_items:
                lines.append("#### Research Records:")
                for r in research_items:
                    citations.append(
                        KnowledgeQueryCitation(
                            source_type="KNOWLEDGE",
                            source_id=r.id,
                            title=r.title,
                            reference=f"Research [{r.confidence}]: {r.title}",
                            confidence=r.confidence,
                        )
                    )
                    lines.append(f"- **{r.title}** (Author: {r.author_name}): {r.content[:250]}")
            else:
                lines.append("No dedicated research knowledge records cataloged.")

            if artifacts:
                lines.append("\n#### Supporting Artifacts & Reports:")
                for a in artifacts:
                    citations.append(
                        KnowledgeQueryCitation(
                            source_type="ARTIFACT",
                            source_id=a.id,
                            title=a.name,
                            reference=f"Artifact '{a.name}' (v{a.version})",
                            confidence="HIGH",
                        )
                    )
                    related_artifacts.append(
                        {
                            "id": a.id,
                            "name": a.name,
                            "type": a.artifact_type,
                            "version": a.version,
                        }
                    )
                    lines.append(
                        f"- **{a.name}** [v{a.version}]: {a.change_summary or 'No change summary'}"
                    )

            answer = "\n".join(lines)
            return KnowledgeQueryResponse(
                question=request.question,
                answer=answer,
                canonical_topic="What research supports it?",
                citations=citations,
                related_decisions=related_decisions,
                related_artifacts=related_artifacts,
                timestamp=now,
            )

        # 3. "What happened last time?"
        if "last time" in q or "what happened" in q or "historical" in q or "precedent" in q:
            exec_query = select(ExecutionRecord).where(ExecutionRecord.company_id == company_id)
            exec_res = await self.db.execute(
                exec_query.order_by(desc(ExecutionRecord.created_at)).limit(5)
            )
            records = exec_res.scalars().all()

            hist_kn_query = select(CompanyKnowledge).where(
                CompanyKnowledge.company_id == company_id,
                CompanyKnowledge.category.in_(["HISTORICAL_RESULT", "PROCEDURE"]),
            )
            hist_res = await self.db.execute(
                hist_kn_query.order_by(desc(CompanyKnowledge.created_at)).limit(5)
            )
            hist_items = hist_res.scalars().all()

            lines = ["### Historical Results & Precedents\n"]
            if records:
                lines.append("#### Prior Task Execution Runs:")
                for ex in records:
                    citations.append(
                        KnowledgeQueryCitation(
                            source_type="EXECUTION",
                            source_id=ex.id,
                            title=f"Task Execution {ex.id[:8]}",
                            reference=f"Run status: {ex.status}, duration: {ex.duration_ms}ms",
                            confidence="HIGH",
                        )
                    )
                    summary = (
                        ex.result_summary
                        or ex.deliverable
                        or (
                            f"Error: {ex.error_details}"
                            if ex.error_details
                            else "No details recorded."
                        )
                    )
                    lines.append(f"- **Execution {ex.id[:8]}** [{ex.status}]: {summary[:200]}")
            else:
                lines.append("No historical execution records found.")

            if hist_items:
                lines.append("\n#### Historical Knowledge & Post-Mortems:")
                for h in hist_items:
                    citations.append(
                        KnowledgeQueryCitation(
                            source_type="KNOWLEDGE",
                            source_id=h.id,
                            title=h.title,
                            reference=f"Knowledge [{h.category}]: {h.title}",
                            confidence=h.confidence,
                        )
                    )
                    lines.append(f"- **{h.title}**: {h.content[:200]}")

            answer = "\n".join(lines)
            return KnowledgeQueryResponse(
                question=request.question,
                answer=answer,
                canonical_topic="What happened last time?",
                citations=citations,
                related_decisions=related_decisions,
                related_artifacts=related_artifacts,
                timestamp=now,
            )

        # 4. "Which projects depend on this decision?"
        if "depend" in q or "which projects" in q:
            dec_res = await self.db.execute(
                select(CompanyDecision).where(CompanyDecision.company_id == company_id)
            )
            all_decisions = dec_res.scalars().all()

            proj_res = await self.db.execute(
                select(Project).where(Project.company_id == company_id)
            )
            projects = proj_res.scalars().all()

            kn_res = await self.db.execute(
                select(CompanyKnowledge).where(
                    CompanyKnowledge.company_id == company_id,
                    CompanyKnowledge.project_id.isnot(None),
                )
            )
            linked_kn = kn_res.scalars().all()

            lines = ["### Project Dependencies & Decision Scope\n"]
            if all_decisions:
                for d in all_decisions:
                    citations.append(
                        KnowledgeQueryCitation(
                            source_type="DECISION",
                            source_id=d.id,
                            title=d.title,
                            reference=f"Decision {d.id[:8]}: {d.title}",
                            confidence="HIGH",
                        )
                    )
                    # Find projects linked to this decision directly or via knowledge
                    linked_projects = [
                        p.name
                        for p in projects
                        if (d.project_id and p.id == d.project_id)
                        or any(k.project_id == p.id and k.decision_id == d.id for k in linked_kn)
                    ]
                    scope_desc = (
                        f"Projects affected: {', '.join(linked_projects)}"
                        if linked_projects
                        else "Company-wide scope (all active projects)"
                    )
                    lines.append(
                        f"- **Decision '{d.title}'**: {d.decision}\n  - *Scope*: {scope_desc}"
                    )
            else:
                lines.append("No active decisions found affecting projects.")

            answer = "\n".join(lines)
            return KnowledgeQueryResponse(
                question=request.question,
                answer=answer,
                canonical_topic="Which projects depend on this decision?",
                citations=citations,
                related_decisions=related_decisions,
                related_artifacts=related_artifacts,
                timestamp=now,
            )

        # 5. "Which documents contain relevant information?"
        if "document" in q or "which documents" in q or "contain" in q:
            art_query = select(Artifact).where(Artifact.company_id == company_id)
            if request.project_id:
                art_query = art_query.where(Artifact.project_id == request.project_id)
            art_res = await self.db.execute(art_query.order_by(desc(Artifact.created_at)).limit(10))
            artifacts = art_res.scalars().all()

            kn_res = await self.db.execute(
                select(CompanyKnowledge)
                .where(
                    CompanyKnowledge.company_id == company_id,
                    CompanyKnowledge.category.in_(["POLICY", "PROCEDURE", "RESEARCH"]),
                )
                .limit(5)
            )
            doc_kn = kn_res.scalars().all()

            lines = ["### Document & Knowledge Inventory\n"]
            if artifacts:
                lines.append("#### Artifacts & Documentation Files:")
                for a in artifacts:
                    citations.append(
                        KnowledgeQueryCitation(
                            source_type="ARTIFACT",
                            source_id=a.id,
                            title=a.name,
                            reference=f"Document '{a.name}' (v{a.version}) at {a.location}",
                            confidence="HIGH",
                        )
                    )
                    related_artifacts.append(
                        {
                            "id": a.id,
                            "name": a.name,
                            "type": a.artifact_type,
                            "version": a.version,
                            "location": a.location,
                        }
                    )
                    lines.append(
                        f"- **{a.name}** [{a.artifact_type} v{a.version}]: Location: `{a.location}`"
                    )
            else:
                lines.append("No artifact documents found.")

            if doc_kn:
                lines.append("\n#### Company Knowledge Records:")
                for dk in doc_kn:
                    citations.append(
                        KnowledgeQueryCitation(
                            source_type="KNOWLEDGE",
                            source_id=dk.id,
                            title=dk.title,
                            reference=f"Knowledge record: {dk.title} [{dk.category}]",
                            confidence=dk.confidence,
                        )
                    )
                    lines.append(f"- **{dk.title}** [{dk.category}]: {dk.content[:180]}...")

            answer = "\n".join(lines)
            return KnowledgeQueryResponse(
                question=request.question,
                answer=answer,
                canonical_topic="Which documents contain relevant information?",
                citations=citations,
                related_decisions=related_decisions,
                related_artifacts=related_artifacts,
                timestamp=now,
            )

        # General inquiry fallback: Search across knowledge, decisions, artifacts
        search_words = [w for w in q.split() if len(w) > 3]
        kn_query = select(CompanyKnowledge).where(CompanyKnowledge.company_id == company_id)
        if search_words:
            filters = [CompanyKnowledge.title.ilike(f"%{w}%") for w in search_words] + [
                CompanyKnowledge.content.ilike(f"%{w}%") for w in search_words
            ]
            kn_query = kn_query.where(or_(*filters))
        kn_res = await self.db.execute(kn_query.limit(5))
        matched_kn = kn_res.scalars().all()

        lines = [f"### Context for: '{request.question}'\n"]
        if matched_kn:
            for m in matched_kn:
                citations.append(
                    KnowledgeQueryCitation(
                        source_type="KNOWLEDGE",
                        source_id=m.id,
                        title=m.title,
                        reference=f"Knowledge [{m.category}]: {m.title}",
                        confidence=m.confidence,
                    )
                )
                lines.append(f"- **{m.title}** ({m.category}): {m.content}")
        else:
            lines.append(
                "No specific knowledge entries matched your query terms. Try asking one of the canonical questions or checking specific project tags."
            )

        return KnowledgeQueryResponse(
            question=request.question,
            answer="\n".join(lines),
            canonical_topic="General Inquiry",
            citations=citations,
            related_decisions=related_decisions,
            related_artifacts=related_artifacts,
            timestamp=now,
        )

    async def get_selective_context(
        self,
        company_id: str,
        user_id: str | None,
        request: SelectiveContextRequest,
    ) -> SelectiveContextResponse:
        """Synthesize selective, bounded context for an agent run without loading the entire DB.

        Directly satisfies Section 23 Acceptance Criteria:
        'Agents can retrieve relevant historical company context without loading the entire database.'
        """
        if user_id:
            await self._verify_company_access(company_id, user_id)

        now = datetime.now(UTC)
        project_dict: dict[str, Any] | None = None
        task_dict: dict[str, Any] | None = None

        if request.project_id:
            p_res = await self.db.execute(
                select(Project).where(
                    Project.id == request.project_id,
                    Project.company_id == company_id,
                )
            )
            p = p_res.scalar_one_or_none()
            if p:
                project_dict = {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "status": p.status,
                }

        if request.task_id:
            t_res = await self.db.execute(
                select(Task).where(
                    Task.id == request.task_id,
                    Task.company_id == company_id,
                )
            )
            t = t_res.scalar_one_or_none()
            if t:
                task_dict = {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "priority": t.priority,
                }

        # 1. Bounded decisions (limit 5 active decisions)
        dec_query = select(CompanyDecision).where(
            CompanyDecision.company_id == company_id,
            CompanyDecision.status == "ACTIVE",
        )
        if request.project_id:
            dec_query = dec_query.where(
                or_(
                    CompanyDecision.project_id == request.project_id,
                    CompanyDecision.project_id.is_(None),
                )
            )
        dec_res = await self.db.execute(
            dec_query.order_by(desc(CompanyDecision.created_at)).limit(5)
        )
        decisions = dec_res.scalars().all()
        relevant_decisions = [
            {
                "id": d.id,
                "title": d.title,
                "topic": d.title,
                "decision": d.decision,
                "rationale": d.rationale,
            }
            for d in decisions
        ]

        # 2. Bounded knowledge items (limit max_items, filtered by keywords and links)
        kn_query = select(CompanyKnowledge).where(CompanyKnowledge.company_id == company_id)
        if request.project_id:
            kn_query = kn_query.where(
                or_(
                    CompanyKnowledge.project_id == request.project_id,
                    CompanyKnowledge.project_id.is_(None),
                )
            )
        if request.intent_keywords:
            kw_filters = []
            for kw in request.intent_keywords:
                pattern = f"%{kw.strip()}%"
                kw_filters.append(CompanyKnowledge.title.ilike(pattern))
                kw_filters.append(CompanyKnowledge.content.ilike(pattern))
            if kw_filters:
                kn_query = kn_query.where(or_(*kw_filters))

        kn_res = await self.db.execute(
            kn_query.order_by(desc(CompanyKnowledge.created_at)).limit(request.max_items)
        )
        kn_items = kn_res.scalars().all()
        relevant_knowledge = [self._to_response(k) for k in kn_items]

        # 3. Bounded artifacts (limit 5)
        art_query = select(Artifact).where(Artifact.company_id == company_id)
        if request.project_id:
            art_query = art_query.where(Artifact.project_id == request.project_id)
        art_res = await self.db.execute(art_query.order_by(desc(Artifact.created_at)).limit(5))
        artifacts = art_res.scalars().all()
        relevant_artifacts = [
            {
                "id": a.id,
                "name": a.name,
                "type": a.artifact_type,
                "version": a.version,
                "location": a.location,
            }
            for a in artifacts
        ]

        # 4. Bounded historical execution results (limit 3)
        exec_query = select(ExecutionRecord).where(ExecutionRecord.company_id == company_id)
        if request.task_id:
            exec_query = exec_query.where(ExecutionRecord.task_id == request.task_id)
        exec_res = await self.db.execute(
            exec_query.order_by(desc(ExecutionRecord.created_at)).limit(3)
        )
        exec_records = exec_res.scalars().all()
        historical_summary = [
            {
                "id": e.id,
                "status": e.status,
                "summary": e.result_summary or e.deliverable or e.error_details,
            }
            for e in exec_records
        ]

        # Synthesize concise bounded context string for agent consumption
        ctx_parts = ["### Selective Company Knowledge & Precedents"]
        if project_dict:
            ctx_parts.append(
                f"**Project**: {project_dict['name']} ({project_dict['status']}) - {project_dict.get('description', '')}"
            )
        if task_dict:
            ctx_parts.append(
                f"**Task**: {task_dict['title']} [{task_dict['priority']}] - {task_dict.get('description', '')}"
            )

        if relevant_decisions:
            ctx_parts.append("\n#### Active Architectural & Company Decisions:")
            for d in relevant_decisions:
                d_title = d.get("title") or d.get("topic", "Decision")
                ctx_parts.append(f"- **{d_title}**: {d['decision']} (Rationale: {d['rationale']})")

        if relevant_knowledge:
            ctx_parts.append("\n#### Targeted Policies, Research & Procedures:")
            for k in relevant_knowledge:
                ctx_parts.append(f"- [{k.category}] **{k.title}**: {k.content}")

        if historical_summary:
            ctx_parts.append("\n#### Prior Execution Precedents:")
            for h in historical_summary:
                hid = str(h.get("id") or "")[:8]
                h_status = h.get("status", "UNKNOWN")
                h_summary = h.get("summary") or "Completed"
                ctx_parts.append(f"- Run {hid} [{h_status}]: {h_summary}")

        synthesized_text = "\n".join(ctx_parts)
        total_items = (
            len(relevant_decisions)
            + len(relevant_knowledge)
            + len(relevant_artifacts)
            + len(historical_summary)
        )

        return SelectiveContextResponse(
            company_id=company_id,
            project=project_dict,
            task=task_dict,
            relevant_decisions=relevant_decisions,
            relevant_knowledge=relevant_knowledge,
            relevant_artifacts=relevant_artifacts,
            historical_results_summary=historical_summary,
            synthesized_context=synthesized_text,
            item_count=total_items,
            timestamp=now,
        )
