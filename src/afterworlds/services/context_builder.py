"""Context Builder service — CRD Issue 8.

Assembles the full context payload for each pipeline pass.  The stable prefix
is assembled exactly once per turn and stored on the returned AssembledContext;
the pipeline (Issue 12) shares it across all passes without rebuilding it.

Key constraints from the issue spec:
  - Stable prefix assembled once per turn, never per pass (CRD Item 12,
    Principle 6).
  - Story Bible and rolling summary in stable prefix; recent turns in volatile
    suffix — never mixed.
  - Rule slice stored separately from stable prefix (see ADR-0010) so that
    query-dependent slice changes between turns do not bust the cache window.
  - RecentTurnsProvider and RetrievalMemoryProvider are Protocol seams.
    Neither is hard-coded to a concrete implementation.  ChromaDB integration
    lands in Issue 18.
  - NullRetrievalMemoryProvider returns empty until Issue 18.
  - No pipeline calls, no Writer invocation, no Story Bible writes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.models.context import (
    AssembledContext,
    PassForwardLedger,
    StablePrefix,
    VolatileSuffix,
)
from afterworlds.models.enums import (
    IntentType,
    MechanicalEntityTypeEnum,
    RuleSubsystemEnum,
    normalize_legacy_intent_type,
)
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.rolling_summary import RollingSummary
from afterworlds.models.rules_package import ActiveRuleSlice, RuleSliceRequest
from afterworlds.models.story_bible import StoryBibleContext
from afterworlds.models.turn import Turn
from afterworlds.persistence.orm.node import NodeORM, TurnORM
from afterworlds.persistence.orm.story import ArcORM, ChapterORM

# ---------------------------------------------------------------------------
# Configurable constant
# ---------------------------------------------------------------------------

#: Maximum number of recent turns to include in the volatile suffix.
#: Start at 10 (matching the CRD cost-model estimate of ~5,000 tokens for
#: ~10 verbatim turns).  Tune once the Writer path (Issue 9) provides real
#: turn-length data.
RECENT_TURNS_LIMIT: int = 10


# ---------------------------------------------------------------------------
# Protocol seams
# ---------------------------------------------------------------------------


class RecentTurnsProvider(Protocol):
    """Protocol for retrieving recent turns from a story's history.

    The concrete SQLite implementation is :class:`SQLiteRecentTurnsProvider`.
    Tests and future implementations may supply any compatible class.
    """

    def get_recent_turns(self, story_id: UUID, limit: int) -> list[Turn]:
        """Return up to *limit* most-recent turns for *story_id*, oldest-first."""
        ...


class RetrievalMemoryProvider(Protocol):
    """Protocol for the vector retrieval memory seam (ChromaDB, Issue 18).

    Returns retrieved context text for the current query.  Until Issue 18
    is implemented, use :class:`NullRetrievalMemoryProvider` which always
    returns an empty string.

    The provider is called by the Context Builder on every turn so that:
      - The seam is exercised and verifiable in tests.
      - Issue 18 can plug in ChromaDB without changing the service.
    """

    def retrieve(self, story_id: UUID, query: str) -> str:
        """Return retrieved context text for *query* in *story_id*, or empty."""
        ...


# ---------------------------------------------------------------------------
# Narrow service protocols (injectable seams for the three service deps)
# ---------------------------------------------------------------------------


class _StoryBibleServiceLike(Protocol):
    def get_active_context_window(self, story_id: UUID) -> StoryBibleContext: ...


class _RollingSummaryServiceLike(Protocol):
    def get_current_summary(self, story_id: UUID) -> RollingSummary | None: ...


class _RulesPackageServiceLike(Protocol):
    def get_active_rule_slice(
        self,
        package_id: UUID,
        subsystem_tags: list[RuleSubsystemEnum],
        entity_refs: list[tuple[MechanicalEntityTypeEnum, str]],
        include_non_published: bool = ...,
    ) -> ActiveRuleSlice: ...


# ---------------------------------------------------------------------------
# Null retrieval memory provider (placeholder until Issue 18)
# ---------------------------------------------------------------------------


class NullRetrievalMemoryProvider:
    """Retrieval memory provider that always returns empty.

    Used until ChromaDB integration (Issue 18) provides a real implementation.
    The Context Builder still calls retrieve() on every turn so the seam is
    exercised and the call site does not need to change in Issue 18.
    """

    def retrieve(self, story_id: UUID, query: str) -> str:
        return ""


# ---------------------------------------------------------------------------
# SQLite-backed recent turns provider
# ---------------------------------------------------------------------------


def _orm_turn_to_model(row: TurnORM) -> Turn:
    return Turn(
        turn_id=UUID(row.turn_id),
        user_input=row.user_input,
        assistant_output=row.assistant_output,
        timestamp=(
            datetime.fromisoformat(row.timestamp).replace(tzinfo=UTC)
            if datetime.fromisoformat(row.timestamp).tzinfo is None
            else datetime.fromisoformat(row.timestamp)
        ),
        intent_classification=IntentType(
            normalize_legacy_intent_type(row.intent_classification)
        ),
        node_id=UUID(row.node_id) if row.node_id else None,
    )


class SQLiteRecentTurnsProvider:
    """Fetches recent turns from SQLite via the full persisted lineage.

    Resolves attribution via: Turn → Node → Chapter → Arc → Story.
    Returns turns in oldest-first order (required for correct prompt assembly).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_recent_turns(self, story_id: UUID, limit: int) -> list[Turn]:
        """Return up to *limit* most-recent turns for *story_id*, oldest-first."""
        rows = (
            self._session.execute(
                select(TurnORM)
                .join(NodeORM, TurnORM.node_id == NodeORM.node_id)
                .join(ChapterORM, NodeORM.chapter_id == ChapterORM.chapter_id)
                .join(ArcORM, ChapterORM.arc_id == ArcORM.arc_id)
                .where(ArcORM.story_id == str(story_id))
                .order_by(TurnORM.timestamp.desc())
                .limit(limit)
            )
            .scalars()
            .all()
        )
        # Reverse DESC results so oldest turn is first in the prompt
        return [_orm_turn_to_model(r) for r in reversed(rows)]


# ---------------------------------------------------------------------------
# Context Builder service
# ---------------------------------------------------------------------------


class ContextBuilderService:
    """Assembles the full context payload for one pipeline turn.

    Stable prefix is assembled exactly once per call to :meth:`assemble` and
    stored on the returned :class:`AssembledContext`.  The pipeline (Issue 12)
    passes the same AssembledContext to all five passes without calling this
    service again — the stable-prefix-once-per-turn invariant is maintained
    by the caller, not enforced internally.

    Args:
        story_bible_service: service with get_active_context_window.
        rolling_summary_service: service with get_current_summary.
        recent_turns_provider: Protocol seam for recent turn retrieval.
        retrieval_memory: Protocol seam for vector retrieval (empty until
            Issue 18; use NullRetrievalMemoryProvider).
        rules_package_service: optional service for RPG rule slice retrieval.
            Required when assemble() is called with a RuleSliceRequest.
    """

    def __init__(
        self,
        story_bible_service: _StoryBibleServiceLike,
        rolling_summary_service: _RollingSummaryServiceLike,
        recent_turns_provider: RecentTurnsProvider,
        retrieval_memory: RetrievalMemoryProvider,
        rules_package_service: _RulesPackageServiceLike | None = None,
    ) -> None:
        self._story_bible_service = story_bible_service
        self._rolling_summary_service = rolling_summary_service
        self._recent_turns_provider = recent_turns_provider
        self._retrieval_memory = retrieval_memory
        self._rules_package_service = rules_package_service

    def assemble(
        self,
        story_id: UUID,
        system_prompt: str,
        current_input: str,
        classified_intent: IntentClassificationResult,
        rule_slice_request: RuleSliceRequest | None = None,
    ) -> AssembledContext:
        """Assemble the full context payload for one pipeline turn.

        Assembly order (matches CRD §Item 8 stable-prefix-first contract):
          Stable prefix: system_prompt → Story Bible → rolling summary
          Rule slice:    separate from stable prefix (see ADR-0010)
          Volatile suffix: recent turns (oldest-first) → current input + intent

        The retrieval memory seam is called on every turn.  Its result is
        currently empty (NullRetrievalMemoryProvider) and is not yet wired
        into the assembled context — Issue 18 will expand this seam.

        Args:
            story_id: UUID of the story this turn belongs to.
            system_prompt: fully composed system prompt including mode contract.
            current_input: raw player input string for this turn.
            classified_intent: typed result from IntentClassifierService.
            rule_slice_request: optional parameter bundle for RPG rule slice.
                Requires rules_package_service to have been injected.

        Returns:
            AssembledContext with stable prefix, optional rule slice, volatile
            suffix, and an empty PassForwardLedger ready for pipeline use.

        Raises:
            ValueError: if rule_slice_request is provided but
                rules_package_service was not injected.
        """
        # 1. Assemble stable prefix — once per turn, not per pass.
        bible_context = self._story_bible_service.get_active_context_window(story_id)
        rolling_summary = self._rolling_summary_service.get_current_summary(story_id)
        rolling_summary_text = rolling_summary.text if rolling_summary else None

        stable_prefix = StablePrefix(
            system_prompt=system_prompt,
            story_bible_context=bible_context,
            rolling_summary_text=rolling_summary_text,
        )

        # 2. Retrieve rule slice (separate from stable prefix per ADR-0010).
        rule_slice: ActiveRuleSlice | None = None
        if rule_slice_request is not None:
            if self._rules_package_service is None:
                raise ValueError(
                    "rule_slice_request provided but rules_package_service was not "
                    "injected into ContextBuilderService"
                )
            rule_slice = self._rules_package_service.get_active_rule_slice(
                package_id=rule_slice_request.package_id,
                subsystem_tags=rule_slice_request.subsystem_tags,
                entity_refs=rule_slice_request.entity_refs,
                include_non_published=rule_slice_request.include_non_published,
            )

        # 3. Retrieve recent turns (oldest-first from provider).
        recent_turns = self._recent_turns_provider.get_recent_turns(
            story_id, limit=RECENT_TURNS_LIMIT
        )

        # 4. Call retrieval memory seam — empty until Issue 18.
        #    Called on every turn so the seam is exercised and Issue 18 can
        #    wire in results without changing the service or tests.
        self._retrieval_memory.retrieve(story_id, current_input)

        # 5. Assemble volatile suffix.
        volatile_suffix = VolatileSuffix(
            recent_turns=recent_turns,
            current_input=current_input,
            classified_intent=classified_intent,
        )

        return AssembledContext(
            stable_prefix=stable_prefix,
            rule_slice=rule_slice,
            volatile_suffix=volatile_suffix,
            pass_forward_ledger=PassForwardLedger(),
        )
