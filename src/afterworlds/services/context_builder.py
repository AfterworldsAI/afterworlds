"""Context Builder service — CRD Issue 8.

Assembles the full context payload for each pipeline pass.  The stable prefix
is assembled exactly once per turn via build_stable_prefix() and stored on the
returned AssembledContext; the pipeline (Issue 12) shares it across all passes
without rebuilding it.

Key constraints from the issue spec:
  - Stable prefix assembled once per turn, never per pass (CRD Item 14,
    architectural invariant #10).
  - Story Bible, rolling summary, and rules_package_slice live inside
    StablePrefix.  Recent turns live in volatile suffix.
  - Rule slice uses a mode×intent policy gate: RPG mode +
    (IN_CHARACTER_ACTION | DIALOGUE | LORE_QUESTION) + request → retrieve;
    all other cases → omit.
  - RecentTurnsProvider and RetrievalMemoryProvider are Protocol seams.
    Neither is hard-coded to a concrete implementation.  ChromaDB integration
    lands in Issue 18.
  - StablePrefix.retrieval_memory is a reserved typed placeholder.  Issue 8
    preserves the injectable seam and typed contract but does NOT materialize
    query-dependent retrieval results inside the cacheable stable block.  Real
    retrieval placement is deferred to Issue 18 (ADR-0010 Decision 4).
  - NullRetrievalMemoryProvider is the default until Issue 18.
  - No pipeline calls, no Writer invocation, no Story Bible writes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.models.context import (
    AssembledContext,
    PassForwardLedger,
    RetrievalMemoryPayload,
    StablePrefix,
    VolatileSuffix,
)
from afterworlds.models.enums import (
    IntentType,
    MechanicalEntityTypeEnum,
    RuleSubsystemEnum,
    StoryMode,
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
# Mode contract loading
# ---------------------------------------------------------------------------

#: Root directory for mode prompt files.  Patchable in tests.
_PROMPT_DIR: Path = Path(__file__).parents[3] / "docs" / "prompts"


class UnknownModeError(ValueError):
    """Raised by load_mode_contract when no prompt file exists for the mode."""


def load_mode_contract(mode: StoryMode) -> str:
    """Load the versioned mode contract from docs/prompts/{mode}_mode.md.

    Raises:
        UnknownModeError: if the expected prompt file does not exist.
    """
    prompt_path = _PROMPT_DIR / f"{mode.value}_mode.md"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise UnknownModeError(
            f"No mode contract file found for mode {mode!r} at {prompt_path}"
        ) from exc


# ---------------------------------------------------------------------------
# Mode × intent rule-slice policy
# ---------------------------------------------------------------------------

#: Intent types that qualify for rule slice retrieval in RPG mode.
_RPG_QUALIFYING_INTENTS: frozenset[IntentType] = frozenset(
    {
        IntentType.IN_CHARACTER_ACTION,
        IntentType.DIALOGUE,
        IntentType.LORE_QUESTION,
    }
)


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

    Issue 8 preserves this injectable seam and the typed contract but does NOT
    call retrieve() from build_stable_prefix().  Query-dependent retrieval
    results must not enter the cacheable stable block.  The seam is injected
    so Issue 18 can wire real retrieval without changing the service constructor
    signature.  Actual retrieval placement is deferred to Issue 18
    (ADR-0010 Decision 4).
    """

    def retrieve(self, story_id: UUID, query: str) -> RetrievalMemoryPayload:
        """Return retrieval payload for *query* in *story_id*, or empty."""
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
    """Retrieval memory provider that always returns an empty payload.

    Default provider until ChromaDB integration (Issue 18).  Issue 18 replaces
    this with a real provider; the service constructor signature is unchanged.
    """

    def retrieve(self, story_id: UUID, query: str) -> RetrievalMemoryPayload:
        return RetrievalMemoryPayload()


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
                # No SQL ORDER BY timestamp: TurnORM.timestamp is a String(64)
                # column; lexicographic ordering diverges from chronological order
                # when rows have mixed UTC offsets.  Sort by actual parsed datetime
                # in Python instead (see ADR-0010 P2 fix).
            )
            .scalars()
            .all()
        )
        turns = [_orm_turn_to_model(r) for r in rows]
        # Sort newest-first by parsed datetime; turn_id tiebreaks deterministically.
        turns.sort(key=lambda t: (t.timestamp, str(t.turn_id)), reverse=True)
        return turns[:limit][::-1]


# ---------------------------------------------------------------------------
# Context Builder service
# ---------------------------------------------------------------------------


class ContextBuilderService:
    """Assembles the full context payload for one pipeline turn.

    Public builder contract (Issue 8):
      build_stable_prefix(story_id, mode, intent_classification,
                          rule_slice_request=None) -> StablePrefix
      build_volatile_suffix(story_id, raw_input, intent_classification)
                          -> VolatileSuffix
      assemble(...) -> AssembledContext   # convenience; delegates to both

    Stable prefix is assembled exactly once per call to :meth:`build_stable_prefix`
    (and therefore once per call to :meth:`assemble`).  The pipeline (Issue 12)
    passes the same AssembledContext to all five passes without calling this
    service again — the stable-prefix-once-per-turn invariant is maintained
    by the caller, not enforced internally.

    Args:
        story_bible_service: service with get_active_context_window.
        rolling_summary_service: service with get_current_summary.
        recent_turns_provider: Protocol seam for recent turn retrieval.
        retrieval_memory: Protocol seam for vector retrieval (empty payload
            until Issue 18; use NullRetrievalMemoryProvider).
        rules_package_service: optional service for RPG rule slice retrieval.
            Required when build_stable_prefix() is called in RPG mode with a
            qualifying intent and a RuleSliceRequest.
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

    def build_stable_prefix(
        self,
        story_id: UUID,
        mode: StoryMode,
        intent_classification: IntentClassificationResult,
        rule_slice_request: RuleSliceRequest | None = None,
    ) -> StablePrefix:
        """Assemble the stable prefix for one pipeline turn.

        Assembly order (canonical Issue 8 field order):
          1. system_prompt — mode contract loaded from docs/prompts/
          2. story_bible_context — ratified Story Bible canon
          3. rolling_summary_text — compressed narrative history (if present)
          4. rules_package_slice — RPG rule slice (mode×intent policy gate)
          5. retrieval_memory — reserved typed placeholder; always empty in
             Issue 8.  Query-dependent retrieval must not enter the cacheable
             stable block (ADR-0010 Decision 4).  Issue 18 owns placement.

        Args:
            story_id: UUID of the story this turn belongs to.
            mode: StoryMode for the current session (governs rule slice policy
                and mode contract loading).
            intent_classification: typed result from IntentClassifierService.
                Used for mode×intent rule slice gate.
            rule_slice_request: optional parameter bundle for RPG rule slice.
                Only honoured when mode is RPG and intent qualifies.

        Returns:
            Frozen StablePrefix ready to share across all pipeline passes.

        Raises:
            UnknownModeError: if no prompt file exists for the given mode.
            ValueError: if a qualifying RPG rule_slice_request is provided but
                rules_package_service was not injected.
        """
        # 1. Load mode contract.
        system_prompt = load_mode_contract(mode)

        # 2. Story Bible.
        bible_context = self._story_bible_service.get_active_context_window(story_id)

        # 3. Rolling summary.
        rolling_summary = self._rolling_summary_service.get_current_summary(story_id)
        rolling_summary_text = rolling_summary.text if rolling_summary else None

        # 4. Rule slice — mode × intent policy gate.
        rules_package_slice: ActiveRuleSlice | None = None
        if (
            mode is StoryMode.RPG
            and intent_classification.intent_type in _RPG_QUALIFYING_INTENTS
            and rule_slice_request is not None
        ):
            if self._rules_package_service is None:
                raise ValueError(
                    "rule_slice_request provided but rules_package_service was not "
                    "injected into ContextBuilderService"
                )
            rules_package_slice = self._rules_package_service.get_active_rule_slice(
                package_id=rule_slice_request.package_id,
                subsystem_tags=rule_slice_request.subsystem_tags,
                entity_refs=rule_slice_request.entity_refs,
                include_non_published=rule_slice_request.include_non_published,
            )

        # 5. Retrieval memory — reserved placeholder; not materialized in Issue 8.
        # Query-dependent retrieval must not enter the cacheable stable block
        # (ADR-0010 Decision 4).  self._retrieval_memory seam is injected for
        # Issue 18 to wire without changing the constructor signature.
        return StablePrefix(
            system_prompt=system_prompt,
            story_bible_context=bible_context,
            rolling_summary_text=rolling_summary_text,
            rules_package_slice=rules_package_slice,
            retrieval_memory=RetrievalMemoryPayload(),
        )

    def build_volatile_suffix(
        self,
        story_id: UUID,
        raw_input: str,
        intent_classification: IntentClassificationResult,
    ) -> VolatileSuffix:
        """Assemble the volatile suffix for one pipeline turn.

        Args:
            story_id: UUID of the story this turn belongs to.
            raw_input: raw player input string for this turn.
            intent_classification: typed result from IntentClassifierService.

        Returns:
            Frozen VolatileSuffix containing recent turns (oldest-first),
            current input, and classified intent.
        """
        recent_turns = self._recent_turns_provider.get_recent_turns(
            story_id, limit=RECENT_TURNS_LIMIT
        )
        return VolatileSuffix(
            recent_turns=recent_turns,
            current_input=raw_input,
            classified_intent=intent_classification,
        )

    def assemble(
        self,
        story_id: UUID,
        mode: StoryMode,
        current_input: str,
        classified_intent: IntentClassificationResult,
        rule_slice_request: RuleSliceRequest | None = None,
    ) -> AssembledContext:
        """Assemble the full context payload for one pipeline turn.

        Convenience method that delegates to build_stable_prefix() and
        build_volatile_suffix(), then wraps both in an AssembledContext with
        an empty PassForwardLedger.

        Args:
            story_id: UUID of the story this turn belongs to.
            mode: StoryMode for the current session.
            current_input: raw player input string for this turn.
            classified_intent: typed result from IntentClassifierService.
            rule_slice_request: optional parameter bundle for RPG rule slice.

        Returns:
            AssembledContext with stable prefix, volatile suffix, and an empty
            PassForwardLedger ready for pipeline use.

        Raises:
            UnknownModeError: if no prompt file exists for the given mode.
            ValueError: if a qualifying RPG rule_slice_request is provided but
                rules_package_service was not injected.
        """
        stable_prefix = self.build_stable_prefix(
            story_id, mode, classified_intent, rule_slice_request
        )
        volatile_suffix = self.build_volatile_suffix(
            story_id, current_input, classified_intent
        )
        return AssembledContext(
            stable_prefix=stable_prefix,
            volatile_suffix=volatile_suffix,
            pass_forward_ledger=PassForwardLedger(),
        )
