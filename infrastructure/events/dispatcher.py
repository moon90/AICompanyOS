"""Event dispatcher coordinating real-time operations per docs/Phases.md Section 21."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from domain.realtime.schemas import RealtimeEventPayload, RealtimeStatusResponse

logger = logging.getLogger(__name__)


class EventDispatcher:
    """In-memory multi-tenant asynchronous event dispatcher for real-time operations."""

    _instance: "EventDispatcher | None" = None
    _lock = asyncio.Lock()

    def __init__(self, queue_maxsize: int = 100) -> None:
        self.queue_maxsize = queue_maxsize
        self._subscribers: dict[str, set[asyncio.Queue[RealtimeEventPayload]]] = {}
        self._event_counters: dict[str, int] = {}
        self._sync_lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "EventDispatcher":
        """Retrieve or initialize the global singleton dispatcher instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (primarily for isolated test fixtures)."""
        cls._instance = None

    async def register_subscriber(self, company_id: str) -> asyncio.Queue[RealtimeEventPayload]:
        """Register a new SSE client subscriber queue for a specific company."""
        queue: asyncio.Queue[RealtimeEventPayload] = asyncio.Queue(maxsize=self.queue_maxsize)
        async with self._sync_lock:
            if company_id not in self._subscribers:
                self._subscribers[company_id] = set()
            self._subscribers[company_id].add(queue)
            if company_id not in self._event_counters:
                self._event_counters[company_id] = 0

        logger.debug(
            "Registered subscriber for company %s (active: %d)",
            company_id,
            len(self._subscribers[company_id]),
        )
        return queue

    async def unregister_subscriber(
        self, company_id: str, queue: asyncio.Queue[RealtimeEventPayload]
    ) -> None:
        """Unregister an SSE client subscriber queue on connection closure."""
        async with self._sync_lock:
            if company_id in self._subscribers:
                self._subscribers[company_id].discard(queue)
                if not self._subscribers[company_id]:
                    del self._subscribers[company_id]

        logger.debug("Unregistered subscriber for company %s", company_id)

    async def broadcast(self, company_id: str, event: RealtimeEventPayload) -> int:
        """Broadcast an event payload to all active subscribers for the company.

        Returns the number of subscribers that received the event.
        """
        async with self._sync_lock:
            self._event_counters[company_id] = self._event_counters.get(company_id, 0) + 1
            subscribers = set(self._subscribers.get(company_id, set()))

        if not subscribers:
            return 0

        dispatched_count = 0
        for queue in subscribers:
            try:
                if queue.full():
                    with contextlib.suppress(asyncio.QueueEmpty):
                        # Drop oldest event to make room for newest real-time state
                        queue.get_nowait()
                queue.put_nowait(event)
                dispatched_count += 1
            except Exception as exc:
                logger.warning(
                    "Failed to deliver event %s to subscriber queue: %s",
                    event.id,
                    exc,
                )

        return dispatched_count

    async def broadcast_event(
        self,
        company_id: str,
        event_type: str,
        message: str,
        actor_type: str = "system",
        actor_id: str | None = None,
        actor_name: str | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RealtimeEventPayload:
        """Construct and broadcast a RealtimeEventPayload conveniently."""
        event = RealtimeEventPayload(
            company_id=company_id,
            event_type=event_type,
            message=message,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=actor_name,
            project_id=project_id,
            task_id=task_id,
            metadata=metadata or {},
            timestamp=datetime.now(UTC),
        )
        await self.broadcast(company_id, event)
        return event

    async def stream_events(self, company_id: str) -> AsyncGenerator[RealtimeEventPayload, None]:
        """Asynchronously stream events for a company, yielding as they arrive."""
        queue = await self.register_subscriber(company_id)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            await self.unregister_subscriber(company_id, queue)

    async def get_status(self, company_id: str) -> RealtimeStatusResponse:
        """Fetch active real-time subscriber and dispatch telemetry for a company."""
        async with self._sync_lock:
            subscribers = self._subscribers.get(company_id, set())
            active_count = len(subscribers)
            dispatched = self._event_counters.get(company_id, 0)

        return RealtimeStatusResponse(
            company_id=company_id,
            active_subscribers=active_count,
            channel_status="active" if active_count > 0 else "idle",
            events_dispatched=dispatched,
            timestamp=datetime.now(UTC),
        )
