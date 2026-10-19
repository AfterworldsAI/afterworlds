"""Retrieval Memory ownership guard -- prerequisite #205 §2/§6, ADR-018 note.

Wraps the shared ``story_memory`` read and write services so every remote
read, write and reindex first requires the current trusted scope's account to
own the Story, the account to be active and the Story unsuppressed, before
the existing ``story_id`` metadata filter. A refused call raises
:class:`StoryAccessDenied` and touches nothing in Chroma. Deletion is bound
to an explicit :class:`DelayedWorkScope`: it is the enforcement of a
suppression, so it requires the owning account, not an unsuppressed Story.
``create_app`` installs the guard only remotely.
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from afterworlds.models.context import RetrievalMemoryPayload
from afterworlds.pipeline.retrieval.write_service import RetrievalMemoryWriteService
from afterworlds.remote.access import (
    AccessPolicy,
    DelayedWorkScope,
    StoryAccessDenied,
    current_scope,
    story_owner,
)
from afterworlds.remote.fence import FenceBusy
from afterworlds.services.context_builder import RetrievalMemoryProvider


class _Guard:
    def __init__(
        self, policy: AccessPolicy, session_factory: sessionmaker[Session]
    ) -> None:
        self._policy = policy
        self._factory = session_factory

    def _guarded[T](self, story_id: UUID, effect: Callable[[], T]) -> T:
        """Run *effect* under the current trusted scope with the account fence
        held for its whole lifetime (re-entrant inside a request or scoped
        call), so closure or suppression waits for it or refuses it and no
        late vector effect lands after they return."""
        if not self._policy.remote:
            return effect()
        scope = current_scope()
        if scope is None:
            raise StoryAccessDenied("unscoped")
        try:
            with self._policy.fence.held(scope.account_id):
                with self._factory() as session:
                    self._policy.check_current(session, story_id)
                return effect()
        except FenceBusy:
            raise StoryAccessDenied("fenced") from None


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
        return self._guarded(story_id, lambda: self._inner.retrieve(story_id, query))


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
        self._guarded(
            story_id,
            lambda: self._inner.ingest_turn(
                story_id, turn_id, node_id, mode, delivered_output, created_at
            ),
        )

    def delete_turn(self, story_id: UUID, turn_id: UUID) -> None:
        self._guarded(story_id, lambda: self._inner.delete_turn(story_id, turn_id))

    def count_for_story(self, story_id: UUID) -> int:
        return self._guarded(story_id, lambda: self._inner.count_for_story(story_id))

    def delete_story(self, story_id: UUID) -> int:
        """Reindex's wipe step: under the current scope, like any write."""
        return self._guarded(story_id, lambda: self._inner.delete_story(story_id))

    def delete_story_for(self, scope: DelayedWorkScope) -> int:
        """Delete a Story's chunks for its owning account (may be suppressed).

        The suppression enforcer's path: it takes no shared fence, because the
        enforcer may run while holding the account's fence exclusive, and a
        deletion cannot recreate content."""
        if scope.story_id is None:
            raise StoryAccessDenied(scope.operation)
        with self._factory() as session:
            if story_owner(session, scope.story_id) != str(scope.account_id):
                raise StoryAccessDenied(scope.operation)
        return self._inner.delete_story(scope.story_id)
