"""RetrievalQueryBuilder — CRD Issue 18 / ADR-018 D8.

Orchestration-owned and deterministic, mirroring CRD Issue 15's
``RuleSliceRequest`` precedent: composes query text from the current
Sojourner input, the already-classified intent, plus an optional bounded
recent-turn tail. The Context Builder gains no inference logic — this
request is built before context assembly and threaded through
``ContextBuilderService.assemble()`` / ``build_stable_prefix()`` unchanged
(D8's protocol-shape-unchanged rule); it forwards ``query_text`` verbatim
to ``RetrievalMemoryProvider.retrieve()``, it never composes or inspects it.

Query-context discipline (the direct trap from Issue #117's original
wording): ``RecentTurnReader``'s ``exclude_ooc=True`` alone is NOT
sufficient — it excludes only ``IntentType.OOC``, not e.g. a Writing turn
whose committed per-turn metadata is ``NON_CANON_SUPPORT``. This builder
reuses ``exclude_ooc=True`` for ordering/window mechanics and then applies
the full D6/D8 eligibility predicate on top before any tail turn's text
enters the composed query.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.models.enums import StoryMode
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.retrieval import RetrievalQueryRequest
from afterworlds.models.turn import Turn
from afterworlds.pipeline.retrieval.eligibility import gather_turn_eligibility

#: Default number of eligible recent turns folded into the query text.
DEFAULT_TAIL_WINDOW = 3


class _RecentTurnsProviderLike(Protocol):
    def get_recent_turns(
        self, story_id: UUID, limit: int, *, exclude_ooc: bool = True
    ) -> list[Turn]: ...


class RetrievalQueryBuilder:
    """Composes the deterministic retrieval query for one pipeline turn."""

    def __init__(
        self,
        recent_turns_provider: _RecentTurnsProviderLike,
        session_factory: object,
        tail_window: int = DEFAULT_TAIL_WINDOW,
    ) -> None:
        self._recent_turns_provider = recent_turns_provider
        self._session_factory = session_factory
        self._tail_window = tail_window

    def build_query_request(
        self,
        story_id: UUID,
        current_input: str,
        story_mode: StoryMode,
        classified_intent: IntentClassificationResult,
    ) -> RetrievalQueryRequest:
        """Return the composed :class:`RetrievalQueryRequest` for this turn.

        Recent-turn tail texts are prepended (oldest-first, matching
        ``RecentTurnsProvider`` order) only when the D6/D8 eligibility
        predicate accepts them; ineligible tail turns contribute no text at
        all, not a redacted placeholder.

        ``query_text`` is composed, in order: eligible tail texts, the
        current Sojourner input, then a small deterministic
        ``intent_type=<value>`` fragment (ADR-018 D8 requires the classified
        intent to inform query composition, not just current input). This
        is a fixed textual fragment, not a ``model_dump()`` of the full
        ``IntentClassificationResult`` — dumping the whole typed result
        would make query text depend on Pydantic field order/defaults
        rather than a stable, deliberately-chosen fragment.
        """
        tail_turns = self._recent_turns_provider.get_recent_turns(
            story_id, limit=self._tail_window, exclude_ooc=True
        )
        eligible_texts: list[str] = []
        if tail_turns:
            session: Session = self._session_factory()  # type: ignore[operator]
            try:
                for turn in tail_turns:
                    # Reload the full committed turn rather than trusting
                    # this projection's mode_metadata: production recent-turn
                    # providers (e.g. SQLiteRecentTurnsProvider) may return a
                    # lean Turn projection that omits mode_metadata, which
                    # would otherwise make an eligible EXTRACTOR_ELIGIBLE
                    # Writing turn look like missing metadata (Codex #119).
                    decision = gather_turn_eligibility(
                        session, turn.turn_id, story_mode
                    )
                    if decision.eligible:
                        eligible_texts.append(turn.assistant_output)
            finally:
                session.close()

        intent_fragment = f"intent_type={classified_intent.intent_type.value}"
        query_text = "\n\n".join([*eligible_texts, current_input, intent_fragment])
        return RetrievalQueryRequest(story_id=story_id, query_text=query_text)
