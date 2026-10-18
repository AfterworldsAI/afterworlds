"""Retrieval Memory ownership guard -- prerequisite #205 §2/§6, ADR-018 note.

Wraps the shared ``story_memory`` read and write services so every remote
read, write and reindex first binds the Story to an active owning account
with no deletion suppression, before the existing ``story_id`` metadata
filter. A refused call raises :class:`StoryAccessDenied` and touches nothing
in Chroma. Deletion is bound to an explicit :class:`DelayedWorkScope`: it is
the enforcement of a suppression, so it requires the owning account, not an
unsuppressed Story. ``create_app`` installs the guard only remotely.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from afterworlds.models.context import RetrievalMemoryPayload
from afterworlds.pipeline.retrieval.write_service import RetrievalMemoryWriteService
from afterworlds.remote.access import (
    AccessPolicy,
    DelayedWorkScope,
    StoryAccessDenied,
    story_owner,
)
from afterworlds.services.context_builder import RetrievalMemoryProvider


class _Guard:
    def __init__(
        self, policy: AccessPolicy, session_factory: sessionmaker[Session]
    ) -> None:
        self._policy = policy
        self._factory = session_factory

    def _require_servable(self, story_id: UUID) -> None:
        with self._factory() as session:
            if not self._policy.story_servable(session, story_id):
                raise StoryAccessDenied("retrieval")


class GuardedRetrievalMemory(_Guard):
    """Read side (``RetrievalMemoryProvider``)."""

    def __init__(
        self,
        inner: RetrievalMemoryProvider,
        policy: AccessPolicy,
        session_factory: sessionmaker[Session],
    ) -> None:
        super().__init__(policy, session_factory)
        self._inner = inner

    def retrieve(self, story_id: UUID, query: str) -> RetrievalMemoryPayload:
        self._require_servable(story_id)
        return self._inner.retrieve(story_id, query)


class GuardedRetrievalWrites(_Guard):
    """Write side used by turn ingestion, backfill/reindex and deletion."""

    def __init__(
        self,
        inner: RetrievalMemoryWriteService,
        policy: AccessPolicy,
        session_factory: sessionmaker[Session],
    ) -> None:
        super().__init__(policy, session_factory)
        self._inner = inner

    def ingest_turn(
        self,
        story_id: UUID,
        turn_id: UUID,
        node_id: UUID | None,
        mode: str,
        delivered_output: str,
        created_at: str,
    ) -> None:
        self._require_servable(story_id)
        self._inner.ingest_turn(
            story_id, turn_id, node_id, mode, delivered_output, created_at
        )

    def delete_turn(self, story_id: UUID, turn_id: UUID) -> None:
        self._require_servable(story_id)
        self._inner.delete_turn(story_id, turn_id)

    def count_for_story(self, story_id: UUID) -> int:
        self._require_servable(story_id)
        return self._inner.count_for_story(story_id)

    def delete_story_for(self, scope: DelayedWorkScope) -> int:
        """Delete a Story's chunks for its owning account (may be suppressed)."""
        with self._factory() as session:
            if story_owner(session, scope.story_id) != str(scope.account_id):
                raise StoryAccessDenied(scope.operation)
        return self._inner.delete_story(scope.story_id)
