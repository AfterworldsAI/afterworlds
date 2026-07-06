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
    Neither is hard-coded to a concrete implementation.
  - StablePrefix.retrieval_memory is populated only when the caller supplies
    a ``retrieval_query_request`` (CRD Issue 18 / ADR-018 D8); the Context
    Builder performs no query composition or eligibility inference itself.
    It sits inside the existing cacheable stable block, under the existing
    breakpoint (ADR-018 D9 resolves ADR-0010 Decision 4).
  - NullRetrievalMemoryProvider is the default when no real provider is
    injected (e.g. tests, or ChromaDB not configured).
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
from afterworlds.models.retrieval import RetrievalQueryRequest
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

#: Extra candidate rows fetched beyond ``limit`` in get_recent_turns().
#: TurnORM.timestamp is a String(64) ISO column.  Strings stored as UTC
#: (+00:00 or naive-UTC) sort lexicographically correctly; the buffer adds
#: headroom for any rows stored with non-UTC offsets that could be
#: lexicographically misplaced near the limit boundary.  Python datetime sort
#: on the candidate set then selects the correct most-recent limit turns.
#: In practice (all application writes use UTC) the SQL ORDER BY is exact and
#: the buffer is never consumed.
_TIMESTAMP_SAFETY_BUFFER: int = 10

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

    Issue 12c extension: ``exclude_ooc`` defaults to True so the Context
    Builder's narrative recent-turn window never contains OOC Turns (those
    are routed through the OOC short-circuit handler and do not advance the
    story).  Callers needing the full prose history may pass ``False``.
    Filtering happens at read time against the existing
    ``intent_classification`` column; no schema migration is required.
    """

    def get_recent_turns(
        self,
        story_id: UUID,
        limit: int,
        *,
        exclude_ooc: bool = True,
    ) -> list[Turn]:
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

    def get_recent_turns(
        self,
        story_id: UUID,
        limit: int,
        *,
        exclude_ooc: bool = True,
    ) -> list[Turn]:
        """Return up to *limit* most-recent turns for *story_id*, oldest-first.

        When ``exclude_ooc`` is True (Issue 12c default), OOC Turns are
        filtered out at read time using the existing
        ``TurnORM.intent_classification`` column.  OOC Turns remain in the
        database for audit; they simply do not appear in the narrative
        recent-turn window the Context Builder feeds to downstream passes.
        Pass ``False`` for full-history reads.
        """
        # Fetch a bounded candidate set: SQL ORDER BY on the ISO timestamp string
        # is correct for rows stored as UTC (+00:00 or naive), which covers all
        # application write paths.  The buffer extends the window so any row
        # stored with a non-UTC offset that is lexicographically misplaced near
        # the limit boundary is still included as a candidate.  Python datetime
        # sort on this bounded set then selects the correct most-recent limit
        # turns without materializing the full story history.
        stmt = (
            select(TurnORM)
            .join(NodeORM, TurnORM.node_id == NodeORM.node_id)
            .join(ChapterORM, NodeORM.chapter_id == ChapterORM.chapter_id)
            .join(ArcORM, ChapterORM.arc_id == ArcORM.arc_id)
            .where(ArcORM.story_id == str(story_id))
        )
        if exclude_ooc:
            stmt = stmt.where(TurnORM.intent_classification != IntentType.OOC.value)
        rows = (
            self._session.execute(
                stmt.order_by(TurnORM.timestamp.desc(), TurnORM.turn_id.desc()).limit(
                    limit + _TIMESTAMP_SAFETY_BUFFER
                )
            )
            .scalars()
            .all()
        )
        turns = [_orm_turn_to_model(r) for r in rows]
        # Re-sort by actual parsed datetime to correct any offset-induced
        # misordering within the candidate set.
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
        retrieval_query_request: RetrievalQueryRequest | None = None,
    ) -> StablePrefix:
        """Assemble the stable prefix for one pipeline turn.

        Assembly order (canonical Issue 8 field order):
          1. system_prompt — mode contract loaded from docs/prompts/
          2. story_bible_context — ratified Story Bible canon
          3. rolling_summary_text — compressed narrative history (if present)
          4. rules_package_slice — RPG rule slice (mode×intent policy gate)
          5. retrieval_memory — vector retrieval payload (CRD Issue 18 /
             ADR-018). Populated only when ``retrieval_query_request`` is
             supplied; empty otherwise. Retrieval memory sits inside the
             existing StablePrefix envelope, under the existing cache
             breakpoint (ADR-018 D9) — shared, unmodified, by every
             provider-backed pass that renders this StablePrefix, not
             Writer-only.

        Args:
            story_id: UUID of the story this turn belongs to.
            mode: StoryMode for the current session (governs rule slice policy
                and mode contract loading).
            intent_classification: typed result from IntentClassifierService.
                Used for mode×intent rule slice gate.
            rule_slice_request: optional parameter bundle for RPG rule slice.
                Only honoured when mode is RPG and intent qualifies.
            retrieval_query_request: optional orchestrator-constructed
                request (``RetrievalQueryBuilder``, ADR-018 D8). The Context
                Builder performs no query composition or eligibility
                inference itself — it only forwards ``story_id``/
                ``query_text`` to the injected ``RetrievalMemoryProvider``.

        Returns:
            Frozen StablePrefix ready to share across all pipeline passes.

        Raises:
            UnknownModeError: if no prompt file exists for the given mode.
            ValueError: if a qualifying RPG rule_slice_request is provided but
                rules_package_service was not injected, or if
                retrieval_query_request.story_id does not match story_id
                (ADR-018 D1 mandatory story_id gate — never query another
                story's Retrieval Memory).
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

        # 5. Retrieval memory (CRD Issue 18 / ADR-018 D8). Empty when no
        # request is supplied (mirrors the pre-Issue-18 placeholder
        # behavior exactly — same empty typed payload, same omitted
        # rendering, same cache-key neutrality).
        retrieval_memory = RetrievalMemoryPayload()
        if retrieval_query_request is not None:
            if retrieval_query_request.story_id != story_id:
                raise ValueError(
                    f"retrieval_query_request.story_id "
                    f"({retrieval_query_request.story_id}) does not match the "
                    f"active story_id ({story_id}) being assembled; refusing to "
                    "query another story's Retrieval Memory (ADR-018 D1 mandatory "
                    "story_id gate)."
                )
            retrieval_memory = self._retrieval_memory.retrieve(
                story_id, retrieval_query_request.query_text
            )

        return StablePrefix(
            system_prompt=system_prompt,
            story_bible_context=bible_context,
            rolling_summary_text=rolling_summary_text,
            rules_package_slice=rules_package_slice,
            retrieval_memory=retrieval_memory,
        )

    def build_volatile_suffix(
        self,
        story_id: UUID,
        raw_input: str,
        intent_classification: IntentClassificationResult,
    ) -> VolatileSuffix:
        """Assemble the volatile suffix for one pipeline turn.

        OOC-window policy (Codex P2 #87 round 8): the Context Builder
        chooses ``exclude_ooc`` explicitly based on the classified intent,
        so the policy is unambiguous and does not depend on the provider's
        default.

        - Narrative intents → ``exclude_ooc=True``: OOC Turns must not
          pollute the story's narrative recent-turn window.
        - OOC intent → ``exclude_ooc=False``: the OOC handler needs the
          prior OOC exchanges as context so multi-turn OOC flows stay
          coherent (e.g. "what does HP mean?" → "remind me which spells
          I can still cast" should still see the earlier exchange).

        ``RecentTurnsProvider`` retains ``exclude_ooc=True`` as its
        provider default so other (non-orchestrator) callers continue to
        get OOC-free narrative windows by default; the Context Builder
        overrides explicitly per intent.

        Args:
            story_id: UUID of the story this turn belongs to.
            raw_input: raw player input string for this turn.
            intent_classification: typed result from IntentClassifierService.

        Returns:
            Frozen VolatileSuffix containing recent turns (oldest-first),
            current input, and classified intent.
        """
        exclude_ooc = intent_classification.intent_type is not IntentType.OOC
        recent_turns = self._recent_turns_provider.get_recent_turns(
            story_id, limit=RECENT_TURNS_LIMIT, exclude_ooc=exclude_ooc
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
        retrieval_query_request: RetrievalQueryRequest | None = None,
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
            retrieval_query_request: optional orchestrator-constructed
                retrieval query request (ADR-018 D8).

        Returns:
            AssembledContext with stable prefix, volatile suffix, and an empty
            PassForwardLedger ready for pipeline use.

        Raises:
            UnknownModeError: if no prompt file exists for the given mode.
            ValueError: if a qualifying RPG rule_slice_request is provided but
                rules_package_service was not injected, or if
                retrieval_query_request.story_id does not match story_id
                (ADR-018 D1 mandatory story_id gate).
        """
        stable_prefix = self.build_stable_prefix(
            story_id,
            mode,
            classified_intent,
            rule_slice_request,
            retrieval_query_request,
        )
        volatile_suffix = self.build_volatile_suffix(
            story_id, current_input, classified_intent
        )
        return AssembledContext(
            stable_prefix=stable_prefix,
            volatile_suffix=volatile_suffix,
            pass_forward_ledger=PassForwardLedger(),
        )
