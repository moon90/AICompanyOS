"""Application service for Semantic / Vector Memory adhering to docs/Phases.md Section 24 and docs/Memory.md Section 40."""

import time
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.services.activity_service import ActivityService
from domain.semantic.exceptions import (
    SemanticAccessDeniedError,
    SemanticMemoryNotFoundError,
)
from domain.semantic.schemas import (
    BatchIndexRequest,
    BatchIndexResponse,
    SemanticContextBuildRequest,
    SemanticContextBuildResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResultItem,
    VectorMemoryStatsResponse,
)
from infrastructure.database.models import (
    Artifact,
    Company,
    CompanyDecision,
    CompanyKnowledge,
    CompanyMember,
    Task,
    VectorEmbedding,
)
from infrastructure.embeddings.engine import (
    EMBEDDING_DIMENSION,
    EmbeddingEngine,
    cosine_similarity,
    default_embedding_engine,
)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Ensure datetime is UTC-aware."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class SemanticService:
    """Authoritative semantic vector retrieval service.

    Implements pgvector-powered semantic search, entity embedding management,
    and agent context synthesis adhering to docs/Phases.md Section 24:
    Task → Generate Search Query → Semantic Search → Relevant Knowledge → Context Builder → Agent.
    """

    def __init__(
        self,
        db: AsyncSession,
        engine: EmbeddingEngine | None = None,
    ) -> None:
        self.db = db
        self.engine = engine or default_embedding_engine

    async def _verify_company_access(self, company_id: str, user_id: str) -> CompanyMember:
        """Verify user has active membership in the target company."""
        company_res = await self.db.execute(select(Company).where(Company.id == company_id))
        company = company_res.scalar_one_or_none()
        if not company:
            raise SemanticMemoryNotFoundError(f"Company {company_id} not found")

        result = await self.db.execute(
            select(CompanyMember).where(
                CompanyMember.company_id == company_id,
                CompanyMember.user_id == user_id,
                CompanyMember.status == "active",
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise SemanticAccessDeniedError(
                f"User {user_id} does not have access to company {company_id}"
            )
        return member

    async def index_entity(
        self,
        company_id: str,
        source_type: str,
        source_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
        chunk_index: int = 0,
    ) -> VectorEmbedding:
        """Index a single entity text chunk into vector memory."""
        embedding_vector = self.engine.generate_embedding(text)

        # Check for existing record
        res = await self.db.execute(
            select(VectorEmbedding).where(
                VectorEmbedding.company_id == company_id,
                VectorEmbedding.source_type == source_type,
                VectorEmbedding.source_id == source_id,
                VectorEmbedding.chunk_index == chunk_index,
            )
        )
        existing = res.scalar_one_or_none()

        now = datetime.now(UTC)
        if existing:
            existing.content = text
            existing.embedding = embedding_vector
            existing.embedding_metadata = metadata or {}
            existing.updated_at = now
            record = existing
        else:
            record = VectorEmbedding(
                id=str(uuid.uuid4()),
                company_id=company_id,
                source_type=source_type,
                source_id=source_id,
                chunk_index=chunk_index,
                content=text,
                embedding=embedding_vector,
                embedding_metadata=metadata or {},
                created_at=now,
                updated_at=now,
            )
            self.db.add(record)

        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def index_company_knowledge(
        self,
        company_id: str,
        user_id: str | None = None,
        request: BatchIndexRequest | None = None,
    ) -> BatchIndexResponse:
        """Batch index company structured entities (Knowledge, Decisions, Artifacts, Tasks) into vector memory."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        start_time = time.perf_counter()
        force = request.force_reindex if request else False
        allowed_sources = request.source_types if request and request.source_types else None

        indexed_count = 0
        updated_count = 0
        skipped_count = 0

        # Existing indexed mapping: (source_type, source_id) -> updated_at
        existing_res = await self.db.execute(
            select(
                VectorEmbedding.source_type,
                VectorEmbedding.source_id,
                VectorEmbedding.updated_at,
            ).where(VectorEmbedding.company_id == company_id)
        )
        existing_map = {(r[0], r[1]): r[2] for r in existing_res.all()}

        # 1. Index CompanyKnowledge
        if not allowed_sources or "KNOWLEDGE" in allowed_sources:
            kn_res = await self.db.execute(
                select(CompanyKnowledge).where(CompanyKnowledge.company_id == company_id)
            )
            knowledge_items = kn_res.scalars().all()
            for k in knowledge_items:
                key = ("KNOWLEDGE", k.id)
                text_to_embed = f"{k.title}\n{k.content}"
                kn_meta: dict[str, Any] = {
                    "title": k.title,
                    "category": k.category,
                    "confidence": k.confidence,
                    "project_id": k.project_id,
                    "tags": k.tags,
                }
                if key in existing_map and not force:
                    skipped_count += 1
                elif key in existing_map:
                    await self.index_entity(company_id, "KNOWLEDGE", k.id, text_to_embed, kn_meta)
                    updated_count += 1
                else:
                    await self.index_entity(company_id, "KNOWLEDGE", k.id, text_to_embed, kn_meta)
                    indexed_count += 1

        # 2. Index CompanyDecisions
        if not allowed_sources or "DECISION" in allowed_sources:
            dec_res = await self.db.execute(
                select(CompanyDecision).where(CompanyDecision.company_id == company_id)
            )
            decisions = dec_res.scalars().all()
            for d in decisions:
                key = ("DECISION", d.id)
                text_to_embed = (
                    f"Decision: {d.title}\nResolution: {d.decision}\nRationale: {d.rationale}"
                )
                dec_meta: dict[str, Any] = {
                    "title": d.title,
                    "status": d.status,
                    "project_id": d.project_id,
                }
                if key in existing_map and not force:
                    skipped_count += 1
                elif key in existing_map:
                    await self.index_entity(company_id, "DECISION", d.id, text_to_embed, dec_meta)
                    updated_count += 1
                else:
                    await self.index_entity(company_id, "DECISION", d.id, text_to_embed, dec_meta)
                    indexed_count += 1

        # 3. Index Artifacts
        if not allowed_sources or "ARTIFACT" in allowed_sources:
            art_res = await self.db.execute(
                select(Artifact).where(Artifact.company_id == company_id)
            )
            artifacts = art_res.scalars().all()
            for a in artifacts:
                key = ("ARTIFACT", a.id)
                content_excerpt = (a.content or "")[:1500]
                text_to_embed = f"Artifact: {a.name} ({a.artifact_type} v{a.version})\n{a.change_summary or ''}\n{content_excerpt}"
                art_meta: dict[str, Any] = {
                    "title": a.name,
                    "artifact_type": a.artifact_type,
                    "version": a.version,
                    "location": a.location,
                    "project_id": a.project_id,
                }
                if key in existing_map and not force:
                    skipped_count += 1
                elif key in existing_map:
                    await self.index_entity(company_id, "ARTIFACT", a.id, text_to_embed, art_meta)
                    updated_count += 1
                else:
                    await self.index_entity(company_id, "ARTIFACT", a.id, text_to_embed, art_meta)
                    indexed_count += 1

        # 4. Index Tasks
        if not allowed_sources or "TASK" in allowed_sources:
            task_res = await self.db.execute(select(Task).where(Task.company_id == company_id))
            tasks = task_res.scalars().all()
            for t in tasks:
                key = ("TASK", t.id)
                text_to_embed = (
                    f"Task: {t.title}\nStatus: {t.status}\nDescription: {t.description or ''}"
                )
                task_meta: dict[str, Any] = {
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "project_id": t.project_id,
                }
                if key in existing_map and not force:
                    skipped_count += 1
                elif key in existing_map:
                    await self.index_entity(company_id, "TASK", t.id, text_to_embed, task_meta)
                    updated_count += 1
                else:
                    await self.index_entity(company_id, "TASK", t.id, text_to_embed, task_meta)
                    indexed_count += 1

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        await ActivityService.record_event(
            session=self.db,
            company_id=company_id,
            event_type="semantic.indexed",
            message=f"Vector memory sync complete: {indexed_count} added, {updated_count} updated, {skipped_count} unchanged",
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            metadata={
                "indexed": indexed_count,
                "updated": updated_count,
                "duration_ms": duration_ms,
            },
        )

        return BatchIndexResponse(
            company_id=company_id,
            indexed_count=indexed_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            total_chunks=indexed_count + updated_count + skipped_count,
            duration_ms=duration_ms,
            timestamp=datetime.now(UTC),
        )

    async def search_semantic(
        self,
        company_id: str,
        user_id: str | None,
        request: SemanticSearchRequest,
    ) -> SemanticSearchResponse:
        """Execute semantic similarity search using pgvector cosine distance or SQLite fallback."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        start_time = time.perf_counter()
        query_vector = self.engine.generate_embedding(request.query)

        # Detect dialect to support native pgvector on Postgres and in-memory cosine fallback for SQLite test suites
        is_postgresql = False
        bind = self.db.bind
        if bind and bind.dialect and bind.dialect.name == "postgresql":
            is_postgresql = True

        results: list[SemanticSearchResultItem] = []

        if is_postgresql:
            # Native PostgreSQL pgvector cosine distance search
            query = select(
                VectorEmbedding,
                VectorEmbedding.embedding.cosine_distance(query_vector).label("distance"),
            ).where(VectorEmbedding.company_id == company_id)

            if request.source_types:
                query = query.where(VectorEmbedding.source_type.in_(request.source_types))

            candidate_limit = max(10, request.limit * 3)
            query = query.order_by("distance").limit(candidate_limit)

            rows = await self.db.execute(query)
            for emb, dist in rows.all():
                distance = float(dist)
                # Cosine similarity = 1.0 - distance
                similarity = max(-1.0, min(1.0, 1.0 - distance))
                if similarity >= request.min_similarity:
                    meta = dict(emb.embedding_metadata or {})
                    title = meta.get("title", f"{emb.source_type} {emb.source_id[:8]}")
                    results.append(
                        SemanticSearchResultItem(
                            id=emb.id,
                            source_type=emb.source_type,
                            source_id=emb.source_id,
                            title=title,
                            content_chunk=emb.content,
                            similarity_score=round(similarity, 4),
                            distance=round(distance, 4),
                            metadata=meta,
                        )
                    )
                    if len(results) >= request.limit:
                        break
        else:
            # Fallback: SQLite candidate scan with Python cosine similarity
            query = select(VectorEmbedding).where(VectorEmbedding.company_id == company_id)
            if request.source_types:
                query = query.where(VectorEmbedding.source_type.in_(request.source_types))

            res = await self.db.execute(query)
            candidates = res.scalars().all()

            scored_candidates: list[tuple[VectorEmbedding, float, float]] = []
            for c in candidates:
                sim = cosine_similarity(query_vector, c.embedding)
                dist = 1.0 - sim
                if sim >= request.min_similarity:
                    scored_candidates.append((c, sim, dist))

            # Sort descending by similarity
            scored_candidates.sort(key=lambda x: x[1], reverse=True)

            for emb, sim, dist in scored_candidates[: request.limit]:
                meta = dict(emb.embedding_metadata or {})
                title = meta.get("title", f"{emb.source_type} {emb.source_id[:8]}")
                results.append(
                    SemanticSearchResultItem(
                        id=emb.id,
                        source_type=emb.source_type,
                        source_id=emb.source_id,
                        title=title,
                        content_chunk=emb.content,
                        similarity_score=round(sim, 4),
                        distance=round(dist, 4),
                        metadata=meta,
                    )
                )

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return SemanticSearchResponse(
            query=request.query,
            results=results,
            total_matches=len(results),
            execution_time_ms=round(duration_ms, 2),
            timestamp=datetime.now(UTC),
        )

    async def build_semantic_context(
        self,
        company_id: str,
        user_id: str | None,
        request: SemanticContextBuildRequest,
    ) -> SemanticContextBuildResponse:
        """Synthesize selective, bounded context for an agent based on semantic search.

        Directly fulfills docs/Phases.md § 24 Retrieval Flow:
        Task → Generate Search Query → Semantic Search → Relevant Knowledge → Context Builder → Agent
        """
        search_req = SemanticSearchRequest(
            query=request.query,
            limit=request.limit,
            min_similarity=request.min_similarity,
            project_id=request.project_id,
        )
        search_resp = await self.search_semantic(company_id, user_id, search_req)

        lines = [
            "### Semantic Company Context (Retrieved via pgvector)",
            f"**Inquiry Target**: {request.query}",
            f"**Retrieved Chunks**: {len(search_resp.results)} candidates meeting relevance criteria\n",
        ]

        if search_resp.results:
            lines.append("#### Relevant Grounded Knowledge Chunks:")
            for idx, item in enumerate(search_resp.results, start=1):
                score_pct = int(item.similarity_score * 100)
                lines.append(
                    f"{idx}. [{item.source_type}] **{item.title}** (Relevance: {score_pct}%)\n"
                    f"   {item.content_chunk.strip()}\n"
                )
        else:
            lines.append("No semantic knowledge chunks exceeded the relevance threshold.")

        synthesized_text = "\n".join(lines)

        return SemanticContextBuildResponse(
            query=request.query,
            company_id=company_id,
            synthesized_context=synthesized_text,
            items_used=search_resp.results,
            total_items=len(search_resp.results),
            timestamp=datetime.now(UTC),
        )

    async def get_vector_stats(
        self,
        company_id: str,
        user_id: str | None = None,
    ) -> VectorMemoryStatsResponse:
        """Retrieve telemetry metrics for company vector embeddings."""
        if user_id:
            await self._verify_company_access(company_id, user_id)

        count_res = await self.db.execute(
            select(VectorEmbedding.source_type, func.count(VectorEmbedding.id))
            .where(VectorEmbedding.company_id == company_id)
            .group_by(VectorEmbedding.source_type)
        )
        breakdown = {r[0]: int(r[1]) for r in count_res.all()}
        total_vectors = sum(breakdown.values())

        is_postgresql = False
        bind = self.db.bind
        if bind and bind.dialect and bind.dialect.name == "postgresql":
            is_postgresql = True

        engine_name = (
            "PostgreSQL + pgvector (HNSW Index)"
            if is_postgresql
            else "In-Memory Vector Engine (SQLite Testing)"
        )
        index_type = (
            "HNSW (Hierarchical Navigable Small World)" if is_postgresql else "Exact Cosine Scan"
        )

        return VectorMemoryStatsResponse(
            company_id=company_id,
            total_embeddings=total_vectors,
            count_by_source=breakdown,
            dimension=EMBEDDING_DIMENSION,
            vector_engine=engine_name,
            index_type=index_type,
            timestamp=datetime.now(UTC),
        )
