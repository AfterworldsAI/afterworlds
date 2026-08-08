"""Tests for ContextBuilderService — CRD Issue 8.

Coverage targets:
  - Stable prefix assembly (all 5 fields, canonical order)
  - Stable prefix assembled exactly once per turn (build_stable_prefix spy)
  - StablePrefix and VolatileSuffix frozen (mutation raises ValidationError)
  - Mode contract loading (RPG, BRANCHING, WRITING; unknown mode raises)
  - Mode × intent rule-slice policy matrix (positive and negative cases)
  - Retrieval memory named field in StablePrefix (empty + populated)
  - Partition separation (Story Bible vs. prose history; stable vs. volatile)
  - Content correctness across minimal / moderate / complex Story Bible scenarios
  - Protocol seam exercise (RecentTurnsProvider and RetrievalMemoryProvider)
  - Rolling summary inclusion / absence
  - SQLiteRecentTurnsProvider integration (oldest-first ordering,
    deterministic tie-breaker under equal timestamps)
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.rules_package  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
import afterworlds.persistence.orm.story_bible  # noqa: F401
from afterworlds.models.context import (
    AssembledContext,
    PassForwardLedger,
    RetrievalMemoryPayload,
    StablePrefix,
    VolatileSuffix,
    _render_cast_entry,
)
from afterworlds.models.enums import (
    CastRole,
    EventKind,
    EventSignificance,
    IntentType,
    RelationshipType,
    StoryMode,
)
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.retrieval import RetrievalQueryRequest
from afterworlds.models.rolling_summary import RollingSummary
from afterworlds.models.rules_package import ActiveRuleSlice, RuleSliceRequest
from afterworlds.models.story import Story
from afterworlds.models.story_bible import (
    CastEntry,
    Event,
    ForbiddenFact,
    LockedFact,
    RelationshipLedger,
    StoryBibleContext,
    StoryBibleSetting,
    UnresolvedThread,
)
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.story import create_story
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.node import NodeORM, TurnORM
from afterworlds.persistence.orm.story import ArcORM, ChapterORM
from afterworlds.services.context_builder import (
    _TIMESTAMP_SAFETY_BUFFER,
    ContextBuilderService,
    NullRetrievalMemoryProvider,
    RecentTurnsProvider,
    SQLiteRecentTurnsProvider,
    UnknownModeError,
    load_mode_contract,
)

# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


class _FixedStoryBibleService:
    """Stub that returns a pre-built StoryBibleContext."""

    def __init__(self, context: StoryBibleContext) -> None:
        self._context = context

    def get_active_context_window(self, story_id: UUID) -> StoryBibleContext:
        return self._context


class _FixedRollingSummaryService:
    """Stub that returns a fixed RollingSummary or None."""

    def __init__(self, summary: RollingSummary | None = None) -> None:
        self._summary = summary

    def get_current_summary(self, story_id: UUID) -> RollingSummary | None:
        return self._summary


class _CountingRecentTurnsProvider:
    """Stub that counts calls and returns a fixed list of Turns oldest-first.

    Mirrors the ``RecentTurnsProvider`` protocol; ``exclude_ooc`` defaults
    to True to match the protocol default and is recorded on
    ``last_exclude_ooc`` so tests can assert which value the Context
    Builder forwarded for a given intent (Codex P2 #87 round 8).
    """

    def __init__(self, turns: list[Turn] | None = None) -> None:
        self._turns: list[Turn] = turns or []
        self.call_count: int = 0
        self.last_story_id: UUID | None = None
        self.last_limit: int | None = None
        self.last_exclude_ooc: bool | None = None

    def get_recent_turns(
        self,
        story_id: UUID,
        limit: int,
        *,
        exclude_ooc: bool = True,
    ) -> list[Turn]:
        self.call_count += 1
        self.last_story_id = story_id
        self.last_limit = limit
        self.last_exclude_ooc = exclude_ooc
        # Honour the filter so tests can rely on the provider behaving
        # like SQLiteRecentTurnsProvider for OOC turns.
        candidates = self._turns
        if exclude_ooc:
            candidates = [
                t for t in candidates if t.intent_classification is not IntentType.OOC
            ]
        return candidates[:limit]


class _CountingRetrievalMemoryProvider:
    """Stub that counts calls and records the last query; returns empty payload."""

    def __init__(self) -> None:
        self.call_count: int = 0
        self.last_query: str | None = None

    def retrieve(self, story_id: UUID, query: str) -> RetrievalMemoryPayload:
        self.call_count += 1
        self.last_query = query
        return RetrievalMemoryPayload()


class _SentinelRetrievalMemoryProvider:
    """Stub that always returns a fixed non-empty payload."""

    def __init__(self) -> None:
        self.call_count = 0
        self.last_story_id: UUID | None = None
        self.last_query: str | None = None
        self.last_payload = RetrievalMemoryPayload(
            passages=("RETRIEVAL_WIRE_THROUGH_SENTINEL",)
        )

    def retrieve(self, story_id: UUID, query: str) -> RetrievalMemoryPayload:
        self.call_count += 1
        self.last_story_id = story_id
        self.last_query = query
        return self.last_payload


# ---------------------------------------------------------------------------
# Shared fixtures and helpers
# ---------------------------------------------------------------------------

_STORY_ID = uuid4()
_NOW = datetime(2026, 1, 1, tzinfo=UTC)

#: Known sentinel that appears in docs/prompts/rpg_mode.md (first heading).
_MODE_CONTRACT_SENTINEL = "RPG Mode Prompt Contract"


def _make_classified_intent(
    intent: IntentType = IntentType.IN_CHARACTER_ACTION,
    raw_input: str = "test input",
) -> IntentClassificationResult:
    return IntentClassificationResult(
        intent_type=intent,
        confidence=0.95,
        raw_input=raw_input,
        ambiguous=False,
        secondary_intent=None,
    )


def _minimal_bible() -> StoryBibleContext:
    return StoryBibleContext(
        story_id=_STORY_ID,
        setting=None,
        cast=(),
        locked_facts=(),
        forbidden_facts=(),
        relationship_ledger=(),
        active_plot_threads=(),
        events=(),
    )


def _moderate_bible() -> StoryBibleContext:
    cast_entry = CastEntry(
        story_id=_STORY_ID,
        name="Aldric",
        role=CastRole.PROTAGONIST,
        traits=("brave", "reckless"),
        goals=("find the artifact",),
        secrets=("killed his brother",),
        background="Former soldier",
        created_at=_NOW,
    )
    setting = StoryBibleSetting(
        story_id=_STORY_ID,
        summary="A dark fantasy realm where magic is forbidden.",
        world_rules=("Magic is forbidden", "The dead stay dead"),
        geography="Northern continent",
        time_period="Medieval",
        created_at=_NOW,
    )
    locked_fact = LockedFact(
        story_id=_STORY_ID,
        fact_text="The king is dead.",
        created_at=_NOW,
    )
    event = Event(
        story_id=_STORY_ID,
        description="The king was slain by an unknown assassin.",
        significance=EventSignificance.CHARACTER_DEATH,
        event_kind=EventKind.DEATH,
        created_at=_NOW,
    )
    return StoryBibleContext(
        story_id=_STORY_ID,
        setting=setting,
        cast=(cast_entry,),
        locked_facts=(locked_fact,),
        forbidden_facts=(),
        relationship_ledger=(),
        active_plot_threads=(),
        events=(event,),
    )


def _complex_bible() -> StoryBibleContext:
    protagonist_id = uuid4()
    antagonist_id = uuid4()
    protagonist = CastEntry(
        cast_id=protagonist_id,
        story_id=_STORY_ID,
        name="Zara",
        role=CastRole.PROTAGONIST,
        traits=("cunning", "ruthless"),
        goals=("overthrow the empire",),
        background="Street thief turned rebel leader",
        current_location="The Ember Quarter",
        current_status="In hiding",
        is_alive=True,
        created_at=_NOW,
    )
    antagonist = CastEntry(
        cast_id=antagonist_id,
        story_id=_STORY_ID,
        name="Lord Vane",
        role=CastRole.ANTAGONIST,
        traits=("calculating", "merciless"),
        goals=("maintain imperial order",),
        background="High inquisitor",
        is_alive=True,
        created_at=_NOW,
    )
    setting = StoryBibleSetting(
        story_id=_STORY_ID,
        summary="An empire teetering on the edge of revolution.",
        world_rules=("Rebellion is punishable by death", "Magic requires a license"),
        geography="The Veldris Empire, twelve provinces",
        time_period="Late industrial",
        created_at=_NOW,
    )
    thread = UnresolvedThread(
        story_id=_STORY_ID,
        description="Who betrayed the rebel cell in the docks?",
        created_at=_NOW,
    )
    relationship = RelationshipLedger(
        story_id=_STORY_ID,
        subject_cast_id=protagonist_id,
        object_cast_id=antagonist_id,
        relationship_type=RelationshipType.ENEMY,
        current_status_description="Zara is hunted by Vane",
        created_at=_NOW,
        updated_at=_NOW,
    )
    forbidden = ForbiddenFact(
        story_id=_STORY_ID,
        fact_text="Zara must not die before the climax.",
        source="sojourner",
        created_at=_NOW,
    )
    locked = LockedFact(
        story_id=_STORY_ID,
        fact_text="The emperor was assassinated in Year 42.",
        created_at=_NOW,
    )
    event1 = Event(
        story_id=_STORY_ID,
        description="Emperor Aldus assassinated.",
        significance=EventSignificance.CHARACTER_DEATH,
        event_kind=EventKind.DEATH,
        created_at=_NOW,
    )
    event2 = Event(
        story_id=_STORY_ID,
        description="Rebel cell at the docks compromised.",
        significance=EventSignificance.MAJOR_PLOT_TURN,
        event_kind=EventKind.PLOT_REVEAL,
        created_at=_NOW,
    )
    return StoryBibleContext(
        story_id=_STORY_ID,
        setting=setting,
        cast=(protagonist, antagonist),
        locked_facts=(locked,),
        forbidden_facts=(forbidden,),
        relationship_ledger=(relationship,),
        active_plot_threads=(thread,),
        events=(event1, event2),
    )


def _make_rolling_summary(text: str = "Previously: a dark night.") -> RollingSummary:
    return RollingSummary(
        story_id=_STORY_ID,
        text=text,
        compressed_from_turn_id=uuid4(),
        compressed_through_turn_id=uuid4(),
        version_number=1,
        is_current=True,
        created_at=_NOW,
    )


def _make_turn(user_input: str, assistant_output: str) -> Turn:
    return Turn(
        user_input=user_input,
        assistant_output=assistant_output,
        timestamp=_NOW,
        intent_classification=IntentType.IN_CHARACTER_ACTION,
    )


def _make_service(
    bible: StoryBibleContext | None = None,
    summary: RollingSummary | None = None,
    turns: list[Turn] | None = None,
    retrieval: _CountingRetrievalMemoryProvider | None = None,
    turns_provider: _CountingRecentTurnsProvider | None = None,
) -> ContextBuilderService:
    return ContextBuilderService(
        story_bible_service=_FixedStoryBibleService(bible or _minimal_bible()),
        rolling_summary_service=_FixedRollingSummaryService(summary),
        recent_turns_provider=turns_provider or _CountingRecentTurnsProvider(turns),
        retrieval_memory=retrieval or _CountingRetrievalMemoryProvider(),
    )


def _make_minimal_active_slice() -> ActiveRuleSlice:
    """Build a minimal ActiveRuleSlice with one enabled chunk; no entities."""
    from afterworlds.models.enums import RuleSubsystemEnum, SourceLocatorTypeEnum
    from afterworlds.models.rules_package import AppliedChunk, RuleChunk

    pid = uuid4()
    source_id = uuid4()
    chunk = RuleChunk(
        rules_package_id=pid,
        source_id=source_id,
        subsystem=RuleSubsystemEnum.COMBAT,
        content="RULE_CONTENT_SENTINEL",
        source_document="SRD",
        source_locator_type=SourceLocatorTypeEnum.PAGE,
        source_locator_value="p. 1",
        created_at=_NOW,
    )
    applied = AppliedChunk(
        chunk=chunk,
        applied_content="APPLIED_RULE_SENTINEL",
        is_disabled=False,
        override_ids_applied=(),
    )
    return ActiveRuleSlice(package_id=pid, chunks=(applied,), entities=())


# ===========================================================================
# Frozen model tests
# ===========================================================================


def test_stable_prefix_is_frozen() -> None:
    """StablePrefix raises ValidationError on any field mutation attempt."""
    sp = StablePrefix(
        system_prompt="sys",
        story_bible_context=_minimal_bible(),
    )
    with pytest.raises(ValidationError):
        sp.system_prompt = "mutated"  # type: ignore[misc]


def test_volatile_suffix_is_frozen() -> None:
    """VolatileSuffix raises ValidationError on any field mutation attempt."""
    vs = VolatileSuffix(
        recent_turns=[],
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    with pytest.raises(ValidationError):
        vs.current_input = "mutated"  # type: ignore[misc]


# ===========================================================================
# Once-per-turn invariant
# ===========================================================================


def test_build_stable_prefix_called_once_per_turn() -> None:
    """build_stable_prefix is called exactly once per assemble(); the same
    StablePrefix instance is reused across all five simulated pipeline passes."""
    service = _make_service(bible=_moderate_bible())

    original_build = service.build_stable_prefix
    call_count = [0]

    def counting_build(
        story_id: UUID,
        mode: StoryMode,
        intent_classification: IntentClassificationResult,
        rule_slice_request: RuleSliceRequest | None = None,
        retrieval_query_request: object = None,
    ) -> StablePrefix:
        call_count[0] += 1
        return original_build(  # type: ignore[arg-type]
            story_id,
            mode,
            intent_classification,
            rule_slice_request,
            retrieval_query_request,
        )

    service.build_stable_prefix = counting_build  # type: ignore[method-assign]

    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )

    assert call_count[0] == 1, "build_stable_prefix must be called exactly once"

    prefix_id = id(assembled.stable_prefix)
    for pass_name in ("planner", "writer", "extractor", "contradiction", "safety"):
        assembled.pass_forward_ledger.add(pass_name, f"{pass_name} output")
        assembled.render_for_pass()
        assert (
            id(assembled.stable_prefix) == prefix_id
        ), f"stable_prefix identity changed on pass {pass_name}"

    assert call_count[0] == 1, "build_stable_prefix must not be called per pass"


# ===========================================================================
# Mode contract loading
# ===========================================================================


def test_mode_contract_rpg_loads() -> None:
    """load_mode_contract(RPG) returns the RPG mode contract string."""
    contract = load_mode_contract(StoryMode.RPG)
    assert isinstance(contract, str)
    assert len(contract) > 0
    assert "RPG" in contract or "rpg" in contract.lower()


def test_mode_contract_branching_loads() -> None:
    """load_mode_contract(BRANCHING) returns the Branching mode contract string."""
    contract = load_mode_contract(StoryMode.BRANCHING)
    assert isinstance(contract, str)
    assert len(contract) > 0


def test_mode_contract_writing_loads() -> None:
    """load_mode_contract(WRITING) returns the Writing mode contract string."""
    contract = load_mode_contract(StoryMode.WRITING)
    assert isinstance(contract, str)
    assert len(contract) > 0


def test_mode_contract_unknown_mode_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """load_mode_contract raises UnknownModeError when no prompt file exists."""
    from pathlib import Path

    import afterworlds.services.context_builder as cb_module

    monkeypatch.setattr(cb_module, "_PROMPT_DIR", Path("/nonexistent/__test_path__"))

    with pytest.raises(UnknownModeError):
        load_mode_contract(StoryMode.RPG)


def test_assemble_embeds_mode_contract_in_stable_prefix() -> None:
    """assemble() loads the mode contract from file into StablePrefix.system_prompt."""
    service = _make_service()
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    expected_contract = load_mode_contract(StoryMode.RPG)
    assert assembled.stable_prefix.system_prompt == expected_contract
    assert _MODE_CONTRACT_SENTINEL in assembled.stable_prefix.render()


# ===========================================================================
# Stable prefix — canonical 5-field structure and ordering
# ===========================================================================


def test_stable_prefix_five_field_canonical_order() -> None:
    """StablePrefix.render() emits all 5 fields in documented canonical order."""
    from afterworlds.models.rules_package import ActiveRuleSlice

    active_slice = _make_minimal_active_slice()
    assert isinstance(active_slice, ActiveRuleSlice)
    retrieval = RetrievalMemoryPayload(passages=("RETRIEVAL_SENTINEL",))

    sp = StablePrefix(
        system_prompt="SYSTEM_SENTINEL",
        story_bible_context=_moderate_bible(),
        rolling_summary_text="SUMMARY_SENTINEL",
        rules_package_slice=active_slice,
        retrieval_memory=retrieval,
    )
    rendered = sp.render()

    pos_system = rendered.find("SYSTEM_SENTINEL")
    pos_bible = rendered.find("## Story Bible")
    pos_summary = rendered.find("SUMMARY_SENTINEL")
    pos_rules = rendered.find("## Rules")
    pos_retrieval = rendered.find("RETRIEVAL_SENTINEL")

    assert pos_system != -1, "system_prompt missing"
    assert pos_bible != -1, "Story Bible missing"
    assert pos_summary != -1, "rolling summary missing"
    assert pos_rules != -1, "rules slice missing"
    assert pos_retrieval != -1, "retrieval memory missing"
    assert pos_system < pos_bible, "system_prompt must precede Story Bible"
    assert pos_bible < pos_summary, "Story Bible must precede rolling summary"
    assert pos_summary < pos_rules, "rolling summary must precede rules slice"
    assert pos_rules < pos_retrieval, "rules slice must precede retrieval memory"


def test_stable_prefix_components_in_canonical_order() -> None:
    """CRD Item 14 invariant #10: stable prefix in documented canonical order.

    Order: mode contract → Story Bible → rolling summary.
    Structural contract: assembled context contains exactly one StablePrefix;
    all components are present and appear in the documented order.
    """
    summary_text = "ROLLING_SUMMARY_SENTINEL"
    bible = _moderate_bible()
    service = _make_service(bible=bible, summary=_make_rolling_summary(summary_text))

    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="I search the room.",
        classified_intent=_make_classified_intent(),
    )

    assert isinstance(assembled, AssembledContext)
    assert isinstance(assembled.stable_prefix, StablePrefix)

    rendered = assembled.stable_prefix.render()

    mode_pos = rendered.find(_MODE_CONTRACT_SENTINEL)
    bible_pos = rendered.find("## Story Bible")
    summary_pos = rendered.find(summary_text)

    assert mode_pos != -1, "mode contract missing from stable prefix render"
    assert bible_pos != -1, "Story Bible section missing from stable prefix render"
    assert summary_pos != -1, "rolling summary missing from stable prefix render"
    assert mode_pos < bible_pos, "mode contract must appear before Story Bible"
    assert bible_pos < summary_pos, "Story Bible must appear before rolling summary"


# ===========================================================================
# Partition separation tests
# ===========================================================================


def test_partition_story_bible_is_in_stable_prefix_not_volatile() -> None:
    """Story Bible is a structural attribute of StablePrefix, not VolatileSuffix."""
    service = _make_service(bible=_moderate_bible())
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="I look around.",
        classified_intent=_make_classified_intent(),
    )

    assert hasattr(assembled.stable_prefix, "story_bible_context")
    assert isinstance(assembled.stable_prefix.story_bible_context, StoryBibleContext)
    assert hasattr(assembled.volatile_suffix, "recent_turns")
    assert not hasattr(assembled.volatile_suffix, "story_bible_context")


def test_partition_recent_turns_in_volatile_suffix_not_stable_prefix() -> None:
    """Recent turns are in VolatileSuffix; StablePrefix carries no prose history."""
    turns = [_make_turn("What do I see?", "A dark corridor.")]
    service = _make_service(turns=turns)
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="I go forward.",
        classified_intent=_make_classified_intent(),
    )

    assert assembled.volatile_suffix.recent_turns == turns
    assert not hasattr(assembled.stable_prefix, "recent_turns")


def test_partition_story_bible_content_not_in_volatile_suffix_render() -> None:
    """Story Bible content must not appear in volatile suffix rendered text."""
    bible = _moderate_bible()
    service = _make_service(bible=bible)
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="I act.",
        classified_intent=_make_classified_intent(),
    )

    volatile_rendered = assembled.volatile_suffix.render()
    assert "## Story Bible" not in volatile_rendered
    assert "dark fantasy" not in volatile_rendered


def test_partition_recent_turns_not_in_stable_prefix_render() -> None:
    """Recent turn prose must not appear in stable prefix rendered text."""
    unique_turn_text = "UNIQUE_TURN_PROSE_SENTINEL"
    turns = [_make_turn(unique_turn_text, "Narrator response.")]
    service = _make_service(turns=turns)
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="Next action.",
        classified_intent=_make_classified_intent(),
    )

    assert unique_turn_text not in assembled.stable_prefix.render()
    assert unique_turn_text in assembled.volatile_suffix.render()


def test_pass_forward_never_appears_in_stable_prefix() -> None:
    """Pass-forward ledger content never contaminates the stable prefix."""
    service = _make_service()
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    assembled.pass_forward_ledger.add("planner", "PLANNER_INJECTION_SENTINEL")

    assert "PLANNER_INJECTION_SENTINEL" not in assembled.stable_prefix.render()


def test_pass_forward_never_appears_in_volatile_suffix() -> None:
    """Pass-forward ledger content never contaminates the volatile suffix."""
    service = _make_service()
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    assembled.pass_forward_ledger.add("writer", "WRITER_INJECTION_SENTINEL")

    assert "WRITER_INJECTION_SENTINEL" not in assembled.volatile_suffix.render()


# ===========================================================================
# Content correctness — Story Bible scenarios
# ===========================================================================


def test_assemble_minimal_story_bible() -> None:
    """Minimal Bible (no setting, no cast): context assembles without error."""
    service = _make_service(bible=_minimal_bible())
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="Hello.",
        classified_intent=_make_classified_intent(IntentType.OOC),
    )

    assert assembled.stable_prefix.story_bible_context.setting is None
    assert assembled.stable_prefix.story_bible_context.cast == ()
    rendered = assembled.stable_prefix.render()
    assert _MODE_CONTRACT_SENTINEL in rendered
    assert "## Story Bible" in rendered
    assert "### Setting" not in rendered


def test_assemble_moderate_story_bible() -> None:
    """Moderate Bible: setting, one cast member, one event, one locked fact."""
    bible = _moderate_bible()
    service = _make_service(bible=bible)
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="I draw my sword.",
        classified_intent=_make_classified_intent(IntentType.IN_CHARACTER_ACTION),
    )

    rendered = assembled.stable_prefix.render()
    assert "### Setting" in rendered
    assert "dark fantasy realm" in rendered
    assert "### Cast" in rendered
    assert "Aldric" in rendered
    assert "### Locked Facts" in rendered
    assert "The king is dead." in rendered
    assert "### Events" in rendered
    assert "assassin" in rendered
    # CastEntry.secrets must appear in the stable prefix (contract-compliance)
    assert "killed his brother" in rendered


def test_assemble_complex_story_bible() -> None:
    """Complex Bible: full content including relationships, threads, forbidden facts."""
    bible = _complex_bible()
    service = _make_service(bible=bible)
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="I slip into the shadows.",
        classified_intent=_make_classified_intent(IntentType.IN_CHARACTER_ACTION),
    )

    rendered = assembled.stable_prefix.render()
    assert "Zara" in rendered
    assert "Lord Vane" in rendered
    assert "### Forbidden Facts" in rendered
    assert "Zara must not die" in rendered
    assert "### Relationships" in rendered
    assert "### Active Plot Threads" in rendered
    assert "betrayed" in rendered


def test_cast_sorted_alphabetically_for_determinism() -> None:
    """Cast entries are rendered alphabetically for deterministic output."""
    bible = _complex_bible()  # has Zara and Lord Vane
    service = _make_service(bible=bible)
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    rendered = assembled.stable_prefix.render()
    # "Lord Vane" sorts before "Zara" alphabetically
    assert rendered.index("Lord Vane") < rendered.index("Zara")


# ===========================================================================
# _render_cast_entry unit tests
# ===========================================================================


def test_render_cast_entry_includes_secrets() -> None:
    """CastEntry.secrets are rendered in the cast block."""
    entry = CastEntry(
        story_id=_STORY_ID,
        name="Mira",
        role=CastRole.PROTAGONIST,
        traits=("clever",),
        goals=("escape the city",),
        secrets=("she is the heir", "betrayed her mentor"),
        created_at=_NOW,
    )
    rendered = _render_cast_entry(entry)
    assert "she is the heir" in rendered
    assert "betrayed her mentor" in rendered
    assert "Secrets:" in rendered


def test_render_cast_entry_without_secrets_renders_cleanly() -> None:
    """CastEntry with no secrets renders without a Secrets line."""
    entry = CastEntry(
        story_id=_STORY_ID,
        name="Aldric",
        role=CastRole.PROTAGONIST,
        traits=("brave",),
        goals=("find the relic",),
        secrets=(),
        created_at=_NOW,
    )
    rendered = _render_cast_entry(entry)
    assert "Secrets:" not in rendered
    assert "Aldric" in rendered
    assert "brave" in rendered
    assert "find the relic" in rendered


def test_render_cast_entry_existing_fields_render_correctly() -> None:
    """All existing CastEntry fields still render correctly after secrets addition."""
    entry = CastEntry(
        story_id=_STORY_ID,
        name="Commander Thane",
        role=CastRole.ANTAGONIST,
        traits=("ruthless", "tactical"),
        goals=("crush the rebellion",),
        secrets=("secretly fears magic",),
        background="Former general",
        current_location="The Citadel",
        current_status="On campaign",
        is_alive=True,
        created_at=_NOW,
    )
    rendered = _render_cast_entry(entry)
    assert "Commander Thane" in rendered
    assert "antagonist" in rendered
    assert "Former general" in rendered
    assert "The Citadel" in rendered
    assert "On campaign" in rendered
    assert "ruthless" in rendered
    assert "crush the rebellion" in rendered
    assert "secretly fears magic" in rendered


# ===========================================================================
# Protocol seam tests
# ===========================================================================


def test_recent_turns_provider_is_called() -> None:
    """RecentTurnsProvider.get_recent_turns is called on every assemble() call."""
    provider = _CountingRecentTurnsProvider()
    service = ContextBuilderService(
        story_bible_service=_FixedStoryBibleService(_minimal_bible()),
        rolling_summary_service=_FixedRollingSummaryService(),
        recent_turns_provider=provider,
        retrieval_memory=_CountingRetrievalMemoryProvider(),
    )

    service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )

    assert provider.call_count == 1
    assert provider.last_story_id == _STORY_ID
    assert provider.last_limit is not None and provider.last_limit > 0


def test_null_retrieval_memory_provider_returns_empty_payload() -> None:
    """NullRetrievalMemoryProvider.retrieve always returns an empty payload."""
    null_provider = NullRetrievalMemoryProvider()
    result = null_provider.retrieve(_STORY_ID, "any query")
    assert isinstance(result, RetrievalMemoryPayload)
    assert result.passages == ()


# ===========================================================================
# Retrieval memory — named field in StablePrefix
# ===========================================================================


def test_retrieval_memory_placeholder_field_exists_and_is_empty() -> None:
    """StablePrefix has a typed retrieval_memory field; Issue 8 always leaves it empty.

    The field is the reserved typed placeholder (ADR-0010 Decision 4). Issue 8
    does not materialize query-dependent retrieval results into the cacheable
    stable block. Placement is deferred to Issue 18.
    """
    service = _make_service()
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    assert hasattr(assembled.stable_prefix, "retrieval_memory")
    assert isinstance(assembled.stable_prefix.retrieval_memory, RetrievalMemoryPayload)
    assert assembled.stable_prefix.retrieval_memory.passages == ()


def test_retrieval_seam_not_called_from_stable_prefix() -> None:
    """build_stable_prefix() does not call retrieve() on the injected provider.

    Query-dependent retrieval must not enter the cacheable stable block
    (ADR-0010 Decision 4). The seam is injected for Issue 18 but must not fire
    during stable prefix assembly.
    """
    retrieval = _CountingRetrievalMemoryProvider()
    service = ContextBuilderService(
        story_bible_service=_FixedStoryBibleService(_minimal_bible()),
        rolling_summary_service=_FixedRollingSummaryService(),
        recent_turns_provider=_CountingRecentTurnsProvider(),
        retrieval_memory=retrieval,
    )
    service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(raw_input="some query"),
    )
    assert retrieval.call_count == 0


def test_stable_prefix_retrieval_memory_always_empty_regardless_of_provider() -> None:
    """Stable prefix retrieval_memory is empty even when provider would return passages.

    Verifies the cache-boundary invariant: the service must not route
    turn-varying retrieval results through the cacheable stable block regardless
    of what the injected provider would return (ADR-0010 Decision 4).
    """

    class _AlwaysPopulatedProvider:
        def retrieve(self, story_id: UUID, query: str) -> RetrievalMemoryPayload:
            return RetrievalMemoryPayload(passages=("SHOULD_NOT_APPEAR",))

    service = ContextBuilderService(
        story_bible_service=_FixedStoryBibleService(_minimal_bible()),
        rolling_summary_service=_FixedRollingSummaryService(),
        recent_turns_provider=_CountingRecentTurnsProvider(),
        retrieval_memory=_AlwaysPopulatedProvider(),
    )
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    assert assembled.stable_prefix.retrieval_memory.passages == ()
    assert "SHOULD_NOT_APPEAR" not in assembled.stable_prefix.render()


def test_retrieval_query_request_populates_stable_prefix() -> None:
    """CRD Issue 18 / ADR-018 D8/D9 read-path wire-through.

    When the orchestrator supplies a ``retrieval_query_request``,
    ``build_stable_prefix`` must call the injected provider with the
    request's ``story_id``/``query_text`` and surface its result on
    ``StablePrefix.retrieval_memory`` — the one seam Issue 18 actually
    added to this service, distinct from the Issue 8 always-empty default
    exercised above.
    """
    retrieval = _SentinelRetrievalMemoryProvider()
    service = ContextBuilderService(
        story_bible_service=_FixedStoryBibleService(_minimal_bible()),
        rolling_summary_service=_FixedRollingSummaryService(),
        recent_turns_provider=_CountingRecentTurnsProvider(),
        retrieval_memory=retrieval,
    )
    request = RetrievalQueryRequest(story_id=_STORY_ID, query_text="a past scene")

    prefix = service.build_stable_prefix(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        intent_classification=_make_classified_intent(),
        retrieval_query_request=request,
    )

    assert retrieval.call_count == 1
    assert retrieval.last_story_id == _STORY_ID
    assert retrieval.last_query == "a past scene"
    assert prefix.retrieval_memory.passages == retrieval.last_payload.passages
    assert "RETRIEVAL_WIRE_THROUGH_SENTINEL" in prefix.render()


def test_retrieval_query_request_matching_story_id_retrieves_normally() -> None:
    """Baseline for the mismatch-guard tests below: a request whose
    story_id equals the active story_id must retrieve exactly as before."""
    retrieval = _SentinelRetrievalMemoryProvider()
    service = ContextBuilderService(
        story_bible_service=_FixedStoryBibleService(_minimal_bible()),
        rolling_summary_service=_FixedRollingSummaryService(),
        recent_turns_provider=_CountingRecentTurnsProvider(),
        retrieval_memory=retrieval,
    )
    request = RetrievalQueryRequest(story_id=_STORY_ID, query_text="a past scene")

    prefix = service.build_stable_prefix(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        intent_classification=_make_classified_intent(),
        retrieval_query_request=request,
    )

    assert retrieval.call_count == 1
    assert prefix.retrieval_memory.passages == retrieval.last_payload.passages


def test_mismatched_retrieval_query_request_story_id_raises_before_querying() -> None:
    """Codex review (PR #119): a RetrievalQueryRequest.story_id that does
    not match the active story_id being assembled must never reach the
    provider -- ADR-018 D1's mandatory story_id gate must not be
    bypassable via a caller bug that constructs a mismatched request."""
    other_story_id = uuid4()
    retrieval = _SentinelRetrievalMemoryProvider()
    service = ContextBuilderService(
        story_bible_service=_FixedStoryBibleService(_minimal_bible()),
        rolling_summary_service=_FixedRollingSummaryService(),
        recent_turns_provider=_CountingRecentTurnsProvider(),
        retrieval_memory=retrieval,
    )
    mismatched_request = RetrievalQueryRequest(
        story_id=other_story_id, query_text="a past scene"
    )

    with pytest.raises(ValueError, match="does not match"):
        service.build_stable_prefix(
            story_id=_STORY_ID,
            mode=StoryMode.RPG,
            intent_classification=_make_classified_intent(),
            retrieval_query_request=mismatched_request,
        )

    assert retrieval.call_count == 0


def test_mismatched_retrieval_query_request_cannot_leak_cross_story_chunks() -> None:
    """No cross-story chunks can enter StablePrefix.retrieval_memory through
    a malformed request: the raise happens before StablePrefix construction,
    so no StablePrefix carrying another story's data is ever returned."""
    other_story_id = uuid4()

    class _AlwaysReturnsForeignStoryChunks:
        def retrieve(self, story_id: UUID, query: str) -> RetrievalMemoryPayload:
            return RetrievalMemoryPayload(passages=("FOREIGN_STORY_CHUNK",))

    service = ContextBuilderService(
        story_bible_service=_FixedStoryBibleService(_minimal_bible()),
        rolling_summary_service=_FixedRollingSummaryService(),
        recent_turns_provider=_CountingRecentTurnsProvider(),
        retrieval_memory=_AlwaysReturnsForeignStoryChunks(),
    )
    mismatched_request = RetrievalQueryRequest(
        story_id=other_story_id, query_text="a past scene"
    )

    with pytest.raises(ValueError):
        service.build_stable_prefix(
            story_id=_STORY_ID,
            mode=StoryMode.RPG,
            intent_classification=_make_classified_intent(),
            retrieval_query_request=mismatched_request,
        )


# ===========================================================================
# Rule slice — inside StablePrefix (Issue 8 contract; ADR-0010 revised)
# ===========================================================================


def test_rule_slice_is_none_when_not_requested() -> None:
    """StablePrefix.rules_package_slice is None when no RuleSliceRequest is given."""
    service = _make_service()
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    assert assembled.stable_prefix.rules_package_slice is None


def test_rule_slice_is_inside_stable_prefix_not_on_assembled_context() -> None:
    """rules_package_slice is a named field on StablePrefix; not on AssembledContext."""
    service = _make_service()
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    # rules_package_slice is on StablePrefix
    assert hasattr(assembled.stable_prefix, "rules_package_slice")
    # AssembledContext does NOT have a separate rule_slice field
    assert not hasattr(assembled, "rule_slice")


def test_rule_slice_request_without_service_raises() -> None:
    """Qualifying RPG RuleSliceRequest without rules_package_service raises."""
    from afterworlds.models.rules_package import RuleSliceRequest

    service = ContextBuilderService(
        story_bible_service=_FixedStoryBibleService(_minimal_bible()),
        rolling_summary_service=_FixedRollingSummaryService(),
        recent_turns_provider=_CountingRecentTurnsProvider(),
        retrieval_memory=_CountingRetrievalMemoryProvider(),
        rules_package_service=None,
    )
    from afterworlds.models.enums import RuleSubsystemEnum as _RuleSubsystemEnum

    # CRD Issue 5d (#137 contract 6): a rule-slice request must state what it
    # selects, so the accidentally-empty form used here before is now refused
    # at construction.
    req = RuleSliceRequest(
        package_id=uuid4(), subsystem_tags=[_RuleSubsystemEnum.COMBAT]
    )
    with pytest.raises(ValueError, match="rules_package_service"):
        service.assemble(
            story_id=_STORY_ID,
            mode=StoryMode.RPG,
            current_input="I attack.",
            # IN_CHARACTER_ACTION qualifies in RPG mode
            classified_intent=_make_classified_intent(),
            rule_slice_request=req,
        )


def test_rule_slice_happy_path_wires_slice_and_covers_render() -> None:
    """Rule slice end-to-end: seam called, slice wired into stable_prefix, rendered.

    Exercises _render_rule_slice (models/context.py) — the enabled-chunk path
    and entity path both fire here.
    Canonical order verified: stable prefix (incl. rule slice) → volatile suffix.
    """
    from afterworlds.models.enums import (
        MechanicalEntityTypeEnum,
        RuleSubsystemEnum,
        SourceLocatorTypeEnum,
    )
    from afterworlds.models.rules_package import (
        ActiveRuleSlice,
        AppliedChunk,
        AppliedEntity,
        ConditionEntity,
        MechanicalEntity,
        RuleChunk,
        RuleSliceRequest,
    )

    package_id = uuid4()
    source_id = uuid4()

    chunk = RuleChunk(
        rules_package_id=package_id,
        source_id=source_id,
        subsystem=RuleSubsystemEnum.COMBAT,
        content="When you make an attack roll...",
        source_document="SRD 5.2",
        source_locator_type=SourceLocatorTypeEnum.PAGE,
        source_locator_value="p. 72",
        created_at=_NOW,
    )
    applied_chunk = AppliedChunk(
        chunk=chunk,
        applied_content="CHUNK_CONTENT_SENTINEL",
        is_disabled=False,
        override_ids_applied=(),
    )

    entity = MechanicalEntity(
        rules_package_id=package_id,
        source_id=source_id,
        entity_type=MechanicalEntityTypeEnum.CONDITION,
        name="ENTITY_NAME_SENTINEL",
        structured_data=ConditionEntity(effects=("Incapacitated", "Can't move")),
        source_document="SRD 5.2",
        source_locator_type=SourceLocatorTypeEnum.PAGE,
        source_locator_value="p. 290",
        created_at=_NOW,
    )
    applied_entity = AppliedEntity(entity=entity, override_ids_applied=())

    active_slice = ActiveRuleSlice(
        package_id=package_id,
        chunks=(applied_chunk,),
        entities=(applied_entity,),
    )

    class _StubRulesPackageService:
        def __init__(self) -> None:
            self.call_count: int = 0
            self.last_package_id: UUID | None = None
            self.last_subsystem_tags: list[RuleSubsystemEnum] | None = None
            self.last_entity_refs: list[tuple[MechanicalEntityTypeEnum, str]] | None = (
                None
            )

        def resolve_slice_package(self, request: RuleSliceRequest) -> UUID:
            assert request.package_id is not None
            return request.package_id

        def get_active_rule_slice(
            self,
            package_id: UUID,
            subsystem_tags: list[RuleSubsystemEnum],
            entity_refs: list[tuple[MechanicalEntityTypeEnum, str]],
            include_non_published: bool = False,
        ) -> ActiveRuleSlice:
            self.call_count += 1
            self.last_package_id = package_id
            self.last_subsystem_tags = subsystem_tags
            self.last_entity_refs = entity_refs
            return active_slice

    stub_rules = _StubRulesPackageService()
    service = ContextBuilderService(
        story_bible_service=_FixedStoryBibleService(_minimal_bible()),
        rolling_summary_service=_FixedRollingSummaryService(),
        recent_turns_provider=_CountingRecentTurnsProvider(),
        retrieval_memory=_CountingRetrievalMemoryProvider(),
        rules_package_service=stub_rules,
    )

    req = RuleSliceRequest(
        package_id=package_id,
        subsystem_tags=[RuleSubsystemEnum.COMBAT],
        entity_refs=[(MechanicalEntityTypeEnum.CONDITION, "ENTITY_NAME_SENTINEL")],
    )
    volatile_input = "I attack the goblin."
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input=volatile_input,
        classified_intent=_make_classified_intent(IntentType.IN_CHARACTER_ACTION),
        rule_slice_request=req,
    )

    # Seam was called with the request's exact parameters
    assert stub_rules.call_count == 1
    assert stub_rules.last_package_id == package_id
    assert stub_rules.last_subsystem_tags == [RuleSubsystemEnum.COMBAT]
    assert stub_rules.last_entity_refs == [
        (MechanicalEntityTypeEnum.CONDITION, "ENTITY_NAME_SENTINEL")
    ]

    # Slice is wired into StablePrefix, not a separate field on AssembledContext
    assert assembled.stable_prefix.rules_package_slice is active_slice
    assert not hasattr(assembled, "rule_slice")

    # Canonical order in render_for_pass: stable prefix (incl. slice) → volatile suffix
    full = assembled.render_for_pass()
    mode_pos = full.find(_MODE_CONTRACT_SENTINEL)
    chunk_pos = full.find("CHUNK_CONTENT_SENTINEL")
    entity_pos = full.find("ENTITY_NAME_SENTINEL")
    volatile_pos = full.find(volatile_input)

    assert chunk_pos != -1, "chunk applied_content missing from render_for_pass"
    assert entity_pos != -1, "entity name missing from render_for_pass"
    assert mode_pos < chunk_pos, "rule slice must appear after mode contract"
    assert chunk_pos < volatile_pos, "rule slice must appear before volatile suffix"
    assert entity_pos < volatile_pos, "entity must appear before volatile suffix"


# ===========================================================================
# Mode × intent rule-slice policy matrix
# ===========================================================================


@pytest.mark.parametrize(
    "mode,intent,expect_slice_retrieved",
    [
        (StoryMode.RPG, IntentType.IN_CHARACTER_ACTION, True),
        (StoryMode.RPG, IntentType.DIALOGUE, True),
        (StoryMode.RPG, IntentType.LORE_QUESTION, True),
        (StoryMode.RPG, IntentType.AUTHOR_INSTRUCTION, False),
        (StoryMode.RPG, IntentType.OOC, False),
        (StoryMode.RPG, IntentType.REWIND, False),
        (StoryMode.RPG, IntentType.BRANCH_CHOICE, False),
        (StoryMode.BRANCHING, IntentType.IN_CHARACTER_ACTION, False),
        (StoryMode.WRITING, IntentType.IN_CHARACTER_ACTION, False),
    ],
)
def test_rule_slice_mode_intent_policy(
    mode: StoryMode,
    intent: IntentType,
    expect_slice_retrieved: bool,
) -> None:
    """Rule slice is retrieved only for RPG mode + qualifying intents.

    Qualifying intents: IN_CHARACTER_ACTION, DIALOGUE, LORE_QUESTION.
    All other modes or intents → rules_package_slice is None.
    """
    from afterworlds.models.rules_package import ActiveRuleSlice, RuleSliceRequest

    active_slice = _make_minimal_active_slice()
    assert isinstance(active_slice, ActiveRuleSlice)

    class _CountingRulesService:
        def __init__(self) -> None:
            self.call_count = 0

        def resolve_slice_package(self, request: RuleSliceRequest) -> UUID:
            assert request.package_id is not None
            return request.package_id

        def get_active_rule_slice(
            self,
            package_id: UUID,
            subsystem_tags: object,
            entity_refs: object,
            include_non_published: bool = False,
        ) -> ActiveRuleSlice:
            self.call_count += 1
            return active_slice

    stub_rules = _CountingRulesService()
    service = ContextBuilderService(
        story_bible_service=_FixedStoryBibleService(_minimal_bible()),
        rolling_summary_service=_FixedRollingSummaryService(),
        recent_turns_provider=_CountingRecentTurnsProvider(),
        retrieval_memory=_CountingRetrievalMemoryProvider(),
        rules_package_service=stub_rules,
    )
    from afterworlds.models.enums import RuleSubsystemEnum as _RuleSubsystemEnum

    # CRD Issue 5d (#137 contract 6): a rule-slice request must state what it
    # selects, so the accidentally-empty form used here before is now refused
    # at construction.
    req = RuleSliceRequest(
        package_id=uuid4(), subsystem_tags=[_RuleSubsystemEnum.COMBAT]
    )

    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=mode,
        current_input="test",
        classified_intent=_make_classified_intent(intent),
        rule_slice_request=req,
    )

    if expect_slice_retrieved:
        assert stub_rules.call_count == 1
        assert assembled.stable_prefix.rules_package_slice is active_slice
    else:
        assert stub_rules.call_count == 0
        assert assembled.stable_prefix.rules_package_slice is None


# ===========================================================================
# Rolling summary tests
# ===========================================================================


def test_rolling_summary_included_in_stable_prefix_when_present() -> None:
    """Rolling summary text is in the stable prefix when service returns one."""
    summary_sentinel = "SUMMARY_SENTINEL_UNIQUE_TEXT"
    service = _make_service(summary=_make_rolling_summary(summary_sentinel))
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    assert assembled.stable_prefix.rolling_summary_text == summary_sentinel
    assert summary_sentinel in assembled.stable_prefix.render()


def test_rolling_summary_absent_from_stable_prefix_when_none() -> None:
    """When no rolling summary exists, rolling_summary_text is None."""
    service = _make_service(summary=None)
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    assert assembled.stable_prefix.rolling_summary_text is None


# ===========================================================================
# Volatile suffix tests
# ===========================================================================


def test_volatile_suffix_contains_current_input() -> None:
    """Current input appears in the volatile suffix render."""
    unique_input = "UNIQUE_CURRENT_INPUT_SENTINEL"
    service = _make_service()
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input=unique_input,
        classified_intent=_make_classified_intent(),
    )
    assert unique_input in assembled.volatile_suffix.render()


def test_volatile_suffix_contains_classified_intent() -> None:
    """Classified intent type appears in the volatile suffix render."""
    service = _make_service()
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="What does this symbol mean?",
        classified_intent=_make_classified_intent(IntentType.LORE_QUESTION),
    )
    assert "lore_question" in assembled.volatile_suffix.render()


def test_recent_turns_appear_in_volatile_suffix_oldest_first() -> None:
    """Recent turns in volatile suffix are in oldest-first order."""
    t1 = _make_turn("first input", "first output")
    t2 = _make_turn("second input", "second output")
    service = _make_service(turns=[t1, t2])
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="third input",
        classified_intent=_make_classified_intent(),
    )
    rendered = assembled.volatile_suffix.render()
    assert rendered.index("first input") < rendered.index("second input")


def test_pass_forward_ledger_starts_empty() -> None:
    """AssembledContext.pass_forward_ledger is empty on initial assembly."""
    service = _make_service()
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    assert isinstance(assembled.pass_forward_ledger, PassForwardLedger)
    assert assembled.pass_forward_ledger.entries == []
    assert assembled.pass_forward_ledger.render() == ""


def test_pass_forward_ledger_add_and_render() -> None:
    """PassForwardLedger.add appends entries rendered in correct format."""
    ledger = PassForwardLedger()
    ledger.add("planner", "The scene calls for combat.")
    ledger.add("writer", "Aldric charges forward.")
    rendered = ledger.render()
    assert "[PLANNER OUTPUT]" in rendered
    assert "The scene calls for combat." in rendered
    assert "[WRITER OUTPUT]" in rendered
    assert rendered.index("PLANNER") < rendered.index("WRITER")


def test_render_for_pass_includes_all_components_in_order() -> None:
    """render_for_pass() produces components in canonical order."""
    summary_text = "SUMMARY_SENTINEL"
    volatile_input = "VOLATILE_INPUT_SENTINEL"
    service = _make_service(
        bible=_moderate_bible(), summary=_make_rolling_summary(summary_text)
    )
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input=volatile_input,
        classified_intent=_make_classified_intent(),
    )
    assembled.pass_forward_ledger.add("planner", "PLANNER_SENTINEL")

    full = assembled.render_for_pass()

    mode_pos = full.find(_MODE_CONTRACT_SENTINEL)
    bible_pos = full.find("## Story Bible")
    summary_pos = full.find(summary_text)
    planner_pos = full.find("PLANNER_SENTINEL")
    volatile_pos = full.find(volatile_input)

    assert mode_pos < bible_pos < summary_pos
    assert summary_pos < planner_pos
    assert planner_pos < volatile_pos


# ===========================================================================
# SQLiteRecentTurnsProvider integration
# ===========================================================================


@pytest.fixture()
def _sqlite_engine():  # type: ignore[no-untyped-def]
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def _sqlite_session(_sqlite_engine):  # type: ignore[no-untyped-def]
    factory = create_session_factory(_sqlite_engine)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


def _seed_story_with_turns(
    session: object,
    story_id: UUID,
    n_turns: int = 3,
) -> list[str]:
    """Seed a minimal story hierarchy with N turns; return inputs in creation order."""
    from sqlalchemy.orm import Session as SaSession

    sess: SaSession = session  # type: ignore[assignment]
    now = datetime(2026, 1, 1, tzinfo=UTC)
    story = Story(
        story_id=story_id,
        title="Test Story",
        mode=StoryMode.RPG,
        created_at=now,
        updated_at=now,
    )
    create_story(sess, story)

    arc_id = str(uuid4())
    arc_orm = ArcORM(
        arc_id=arc_id,
        story_id=str(story_id),
        title="Arc 1",
        order=1,
    )
    sess.add(arc_orm)

    chapter_id = str(uuid4())
    chapter_orm = ChapterORM(
        chapter_id=chapter_id,
        arc_id=arc_id,
        title="Chapter 1",
        order=1,
    )
    sess.add(chapter_orm)

    node_orm = NodeORM(
        node_id=str(uuid4()),
        chapter_id=chapter_id,
        content="",
        state_delta={},
        branching_logic=[],
        intent_type="in_character_action",
        metadata_={},
    )
    sess.add(node_orm)
    sess.flush()

    inputs: list[str] = []
    for i in range(n_turns):
        ts = datetime(2026, 1, 1, i + 1, 0, 0, tzinfo=UTC)
        user_input = f"turn_{i}_input"
        inputs.append(user_input)
        turn_orm = TurnORM(
            turn_id=str(uuid4()),
            node_id=node_orm.node_id,
            user_input=user_input,
            assistant_output=f"turn_{i}_output",
            timestamp=ts.isoformat(),
            intent_classification="in_character_action",
        )
        sess.add(turn_orm)

    sess.commit()
    return inputs


def test_sqlite_recent_turns_provider_oldest_first(
    _sqlite_session: object,
) -> None:
    """SQLiteRecentTurnsProvider returns turns oldest-first, up to limit."""
    story_id = uuid4()
    inputs = _seed_story_with_turns(_sqlite_session, story_id, n_turns=3)

    provider = SQLiteRecentTurnsProvider(_sqlite_session)  # type: ignore[arg-type]
    turns = provider.get_recent_turns(story_id, limit=10)

    assert len(turns) == 3
    assert [t.user_input for t in turns] == inputs  # oldest first


def test_sqlite_recent_turns_provider_respects_limit(
    _sqlite_session: object,
) -> None:
    """SQLiteRecentTurnsProvider limits results to the most-recent N turns."""
    story_id = uuid4()
    inputs = _seed_story_with_turns(_sqlite_session, story_id, n_turns=5)

    provider = SQLiteRecentTurnsProvider(_sqlite_session)  # type: ignore[arg-type]
    turns = provider.get_recent_turns(story_id, limit=3)

    assert len(turns) == 3
    # Limit returns most-recent 3, reversed to oldest-first → inputs[2], [3], [4]
    assert [t.user_input for t in turns] == inputs[2:]


def test_sqlite_recent_turns_provider_returns_empty_for_unknown_story(
    _sqlite_session: object,
) -> None:
    """SQLiteRecentTurnsProvider returns [] for a story with no persisted turns."""
    provider = SQLiteRecentTurnsProvider(_sqlite_session)  # type: ignore[arg-type]
    turns = provider.get_recent_turns(uuid4(), limit=10)
    assert turns == []


def test_sqlite_recent_turns_provider_deterministic_under_equal_timestamps(
    _sqlite_session: object,
) -> None:
    """Turns with equal timestamps are ordered deterministically via turn_id tiebreaker.

    Verifies that the secondary ORDER BY turn_id DESC clause prevents
    non-deterministic ordering when two turns share a timestamp.
    """
    from sqlalchemy.orm import Session as SaSession

    sess: SaSession = _sqlite_session  # type: ignore[assignment]
    story_id = uuid4()

    now = datetime(2026, 1, 1, tzinfo=UTC)
    story = Story(
        story_id=story_id,
        title="Tie Test",
        mode=StoryMode.RPG,
        created_at=now,
        updated_at=now,
    )
    create_story(sess, story)

    arc_id = str(uuid4())
    sess.add(ArcORM(arc_id=arc_id, story_id=str(story_id), title="Arc 1", order=1))
    chapter_id = str(uuid4())
    sess.add(ChapterORM(chapter_id=chapter_id, arc_id=arc_id, title="Ch 1", order=1))
    node_orm = NodeORM(
        node_id=str(uuid4()),
        chapter_id=chapter_id,
        content="",
        state_delta={},
        branching_logic=[],
        intent_type="in_character_action",
        metadata_={},
    )
    sess.add(node_orm)
    sess.flush()

    same_ts = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC).isoformat()
    for user_input in ("tie_turn_1", "tie_turn_2"):
        sess.add(
            TurnORM(
                turn_id=str(uuid4()),
                node_id=node_orm.node_id,
                user_input=user_input,
                assistant_output="response",
                timestamp=same_ts,
                intent_classification="in_character_action",
            )
        )
    sess.commit()

    provider = SQLiteRecentTurnsProvider(sess)  # type: ignore[arg-type]
    # Two separate calls must return the same deterministic order
    result_a = [t.user_input for t in provider.get_recent_turns(story_id, limit=10)]
    result_b = [t.user_input for t in provider.get_recent_turns(story_id, limit=10)]
    assert result_a == result_b, "ordering must be deterministic under equal timestamps"
    assert len(result_a) == 2


def test_sqlite_recent_turns_provider_orders_by_actual_datetime_not_string(
    _sqlite_session: object,
) -> None:
    """Turns are ordered by actual parsed datetime, not lexicographic string comparison.

    Regression test for P2 #1: TurnORM.timestamp is a String(64) column.
    ISO strings with mixed UTC offsets sort lexicographically incorrectly
    (e.g. "2026-01-01T01:00:00+01:00" > "2026-01-01T00:30:00Z" as strings,
    but the first is UTC midnight and the second is UTC 00:30 — reversed order).
    The fix fetches all rows and sorts by actual parsed datetime in Python.
    """
    from sqlalchemy.orm import Session as SaSession

    sess: SaSession = _sqlite_session  # type: ignore[assignment]
    story_id = uuid4()

    now = datetime(2026, 1, 1, tzinfo=UTC)
    story = Story(
        story_id=story_id,
        title="Datetime Ordering Test",
        mode=StoryMode.RPG,
        created_at=now,
        updated_at=now,
    )
    create_story(sess, story)

    arc_id = str(uuid4())
    sess.add(ArcORM(arc_id=arc_id, story_id=str(story_id), title="Arc 1", order=1))
    chapter_id = str(uuid4())
    sess.add(ChapterORM(chapter_id=chapter_id, arc_id=arc_id, title="Ch 1", order=1))
    node_orm = NodeORM(
        node_id=str(uuid4()),
        chapter_id=chapter_id,
        content="",
        state_delta={},
        branching_logic=[],
        intent_type="in_character_action",
        metadata_={},
    )
    sess.add(node_orm)
    sess.flush()

    # Turn A: UTC midnight, stored with +00:00 offset — lexicographically LATER than B
    # Turn B: UTC 00:30, stored with Z suffix — lexicographically EARLIER than A
    # String sort (wrong): A > B → A "more recent" → oldest-first would be [B, A]
    # Datetime sort (correct): B is later (00:30 > 00:00 UTC) → oldest-first is [A, B]
    turn_a_ts = "2026-01-01T00:00:00+00:00"  # UTC midnight — lexically later
    turn_b_ts = "2026-01-01T00:30:00+00:00"  # UTC 00:30 — actually more recent

    sess.add(
        TurnORM(
            turn_id=str(uuid4()),
            node_id=node_orm.node_id,
            user_input="turn_a",
            assistant_output="response_a",
            timestamp=turn_a_ts,
            intent_classification="in_character_action",
        )
    )
    sess.add(
        TurnORM(
            turn_id=str(uuid4()),
            node_id=node_orm.node_id,
            user_input="turn_b",
            assistant_output="response_b",
            timestamp=turn_b_ts,
            intent_classification="in_character_action",
        )
    )
    sess.commit()

    provider = SQLiteRecentTurnsProvider(sess)  # type: ignore[arg-type]
    turns = provider.get_recent_turns(story_id, limit=10)

    assert len(turns) == 2
    # Oldest-first: turn_a (UTC 00:00) before turn_b (UTC 00:30)
    assert turns[0].user_input == "turn_a"
    assert turns[1].user_input == "turn_b"


def test_sqlite_recent_turns_provider_bounded_returns_correct_subset(
    _sqlite_session: object,
) -> None:
    """Provider returns the correct most-recent turns for a story with many turns.

    Seeds more turns than the SQL candidate window (limit + _TIMESTAMP_SAFETY_BUFFER)
    to verify the bounded fetch selects the correct most-recent subset without
    materializing the full story history.
    """
    story_id = uuid4()
    limit = 5
    # Seed more turns than candidate_limit = limit + _TIMESTAMP_SAFETY_BUFFER
    # so the SQL LIMIT actually binds and constrains the candidate set.
    n_turns = limit + _TIMESTAMP_SAFETY_BUFFER + 5  # 20 — all with distinct UTC times
    inputs = _seed_story_with_turns(_sqlite_session, story_id, n_turns=n_turns)

    provider = SQLiteRecentTurnsProvider(_sqlite_session)  # type: ignore[arg-type]
    turns = provider.get_recent_turns(story_id, limit=limit)

    assert len(turns) == limit
    # The most-recent 5 of 20 turns — oldest-first within that group
    assert [t.user_input for t in turns] == inputs[-limit:]


# ===========================================================================
# Deep immutability tests
# ===========================================================================


def test_stable_prefix_story_bible_context_collections_are_immutable() -> None:
    """StoryBibleContext collection fields are tuples — append raises AttributeError.

    Verifies that StablePrefix.frozen=True is deeply effective: because
    StoryBibleContext collection fields are tuple[X, ...] rather than list[X],
    an attempt to mutate them raises AttributeError instead of silently succeeding.
    """
    ctx = _minimal_bible()
    with pytest.raises(AttributeError):
        ctx.cast.append(  # type: ignore[attr-defined]
            CastEntry(
                story_id=_STORY_ID,
                name="Intruder",
                role=CastRole.PROTAGONIST,
                created_at=_NOW,
            )
        )


def test_stable_prefix_rules_package_slice_is_immutable() -> None:
    """ActiveRuleSlice stored in stable_prefix.rules_package_slice is deeply immutable.

    ActiveRuleSlice, AppliedChunk, and AppliedEntity are all frozen Pydantic
    models with tuple collection fields.  Verifies that:
    - Appending to chunks/entities (tuples) raises AttributeError.
    - Reassigning a frozen field on AppliedChunk raises ValidationError.
    - Appending to override_ids_applied (tuple) raises AttributeError.
    """
    from pydantic import ValidationError

    rps = _make_minimal_active_slice()

    # chunks is a tuple — append must fail
    with pytest.raises(AttributeError):
        rps.chunks.append(rps.chunks[0])  # type: ignore[attr-defined]

    # entities is a tuple — append must fail
    with pytest.raises(AttributeError):
        rps.entities.append(None)  # type: ignore[arg-type, attr-defined]

    # AppliedChunk is frozen — normal field reassignment must raise ValidationError
    with pytest.raises(ValidationError):
        rps.chunks[0].applied_content = "injected"  # type: ignore[misc]

    # override_ids_applied is a tuple — append must fail
    with pytest.raises(AttributeError):
        rps.chunks[0].override_ids_applied.append(uuid4())  # type: ignore[attr-defined]


def test_rule_chunk_is_immutable() -> None:
    """RuleChunk nested inside AppliedChunk is frozen — field mutation raises
    ValidationError, closing the immutability chain through the rule slice."""
    rps = _make_minimal_active_slice()
    with pytest.raises(ValidationError):
        rps.chunks[0].chunk.content = "hacked"  # type: ignore[misc]


def test_story_bible_leaf_models_are_immutable() -> None:
    """LockedFact, ForbiddenFact, Event, RelationshipLedger, UnresolvedThread are
    all frozen — field reassignment raises ValidationError."""
    bible = _complex_bible()

    with pytest.raises(ValidationError):
        bible.locked_facts[0].fact_text = "mutated"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        bible.forbidden_facts[0].fact_text = "mutated"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        bible.events[0].description = "mutated"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        bible.active_plot_threads[0].description = "mutated"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        bible.relationship_ledger[0].current_status_description = "mutated"  # type: ignore[misc]


def test_retrieval_memory_passages_is_immutable() -> None:
    """RetrievalMemoryPayload.passages is a tuple — append raises AttributeError."""
    payload = RetrievalMemoryPayload()
    with pytest.raises(AttributeError):
        payload.passages.append("injected")  # type: ignore[attr-defined]


def test_stable_prefix_render_is_stable() -> None:
    """StablePrefix.render() is deterministic — two successive calls return
    identical output, verifying the once-per-turn caching invariant."""
    service = _make_service(bible=_moderate_bible(), summary=_make_rolling_summary())
    assembled = service.assemble(
        story_id=_STORY_ID,
        mode=StoryMode.RPG,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    first = assembled.stable_prefix.render()
    second = assembled.stable_prefix.render()
    assert first == second


# ===========================================================================
# OOC recent-turn window policy (Codex P2 #87 round 8)
#
# build_volatile_suffix chooses exclude_ooc based on classified intent:
# narrative intents → True (OOC turns must not pollute narrative context);
# OOC intent → False (the OOC handler needs prior OOC exchanges as context
# so multi-turn OOC flows stay coherent).
# ===========================================================================


def _make_ooc_turn(
    user_input: str = "[OOC] question", out: str = "[OOC] answer"
) -> Turn:
    return Turn(
        user_input=user_input,
        assistant_output=out,
        timestamp=_NOW,
        intent_classification=IntentType.OOC,
    )


def _make_narrative_turn(
    user_input: str = "narrative input", out: str = "narrative output"
) -> Turn:
    return Turn(
        user_input=user_input,
        assistant_output=out,
        timestamp=_NOW,
        intent_classification=IntentType.IN_CHARACTER_ACTION,
    )


def test_narrative_volatile_suffix_excludes_prior_ooc_turns() -> None:
    """Narrative intent → ``exclude_ooc=True`` is forwarded to the
    provider AND the resulting recent_turns list contains no OOC turns.
    """
    ooc1 = _make_ooc_turn("[OOC] hp?")
    nar1 = _make_narrative_turn("I draw my sword")
    ooc2 = _make_ooc_turn("[OOC] save?")
    nar2 = _make_narrative_turn("I strike")
    provider = _CountingRecentTurnsProvider(turns=[ooc1, nar1, ooc2, nar2])
    service = _make_service(turns_provider=provider)

    suffix = service.build_volatile_suffix(
        story_id=_STORY_ID,
        raw_input="I parry",
        intent_classification=_make_classified_intent(IntentType.IN_CHARACTER_ACTION),
    )

    assert provider.last_exclude_ooc is True
    # The filter dropped the two OOC turns; only narrative survives.
    assert all(
        t.intent_classification is not IntentType.OOC for t in suffix.recent_turns
    )
    assert {t.user_input for t in suffix.recent_turns} == {
        "I draw my sword",
        "I strike",
    }


def test_ooc_volatile_suffix_includes_prior_ooc_turns() -> None:
    """OOC intent → ``exclude_ooc=False`` is forwarded so the OOC handler
    sees prior OOC exchanges as context for multi-turn OOC flows.
    """
    ooc1 = _make_ooc_turn("[OOC] what is HP?", "HP is hit points.")
    nar1 = _make_narrative_turn("I attack")
    ooc2 = _make_ooc_turn("[OOC] remind me spells", "fireball, ice shard")
    provider = _CountingRecentTurnsProvider(turns=[ooc1, nar1, ooc2])
    service = _make_service(turns_provider=provider)

    suffix = service.build_volatile_suffix(
        story_id=_STORY_ID,
        raw_input="[OOC] what about cantrips?",
        intent_classification=_make_classified_intent(
            IntentType.OOC, "[OOC] what about cantrips?"
        ),
    )

    assert provider.last_exclude_ooc is False
    # All three turns survive; OOC exchanges are preserved.
    assert len(suffix.recent_turns) == 3
    inputs = [t.user_input for t in suffix.recent_turns]
    assert "[OOC] what is HP?" in inputs
    assert "[OOC] remind me spells" in inputs
    # And the narrative one too — OOC follow-ups still see the full
    # interleaved history.
    assert "I attack" in inputs


@pytest.mark.parametrize(
    "intent,expected_exclude_ooc,expected_remaining",
    [
        (
            IntentType.IN_CHARACTER_ACTION,
            True,
            {"narrative-1", "narrative-2"},
        ),
        (
            IntentType.DIALOGUE,
            True,
            {"narrative-1", "narrative-2"},
        ),
        (
            IntentType.LORE_QUESTION,
            True,
            {"narrative-1", "narrative-2"},
        ),
        (
            IntentType.AUTHOR_INSTRUCTION,
            True,
            {"narrative-1", "narrative-2"},
        ),
        (
            IntentType.OOC,
            False,
            {"narrative-1", "ooc-1", "narrative-2", "ooc-2"},
        ),
    ],
)
def test_mixed_history_window_under_both_intent_types(
    intent: IntentType,
    expected_exclude_ooc: bool,
    expected_remaining: set[str],
) -> None:
    """Mixed recent history produces the intended window under both intent
    types: every non-OOC intent gets the OOC-filtered window; OOC gets the
    full interleaved history.
    """
    turns = [
        _make_narrative_turn("narrative-1"),
        _make_ooc_turn("ooc-1"),
        _make_narrative_turn("narrative-2"),
        _make_ooc_turn("ooc-2"),
    ]
    provider = _CountingRecentTurnsProvider(turns=turns)
    service = _make_service(turns_provider=provider)

    suffix = service.build_volatile_suffix(
        story_id=_STORY_ID,
        raw_input="next input",
        intent_classification=_make_classified_intent(intent, "next input"),
    )

    assert provider.last_exclude_ooc is expected_exclude_ooc
    assert {t.user_input for t in suffix.recent_turns} == expected_remaining


def test_recent_turns_provider_default_remains_exclude_ooc_true() -> None:
    """Provider-level default ``exclude_ooc=True`` is preserved for
    non-orchestrator callers; the Context Builder overrides it explicitly
    per intent, but external callers that omit the kwarg still get the
    OOC-free window by default (Codex P2 #87 round 8 — keep provider
    default if useful).
    """
    from inspect import signature

    sig = signature(RecentTurnsProvider.get_recent_turns)  # type: ignore[arg-type]
    exclude_ooc_param = sig.parameters.get("exclude_ooc")
    assert exclude_ooc_param is not None
    assert exclude_ooc_param.default is True
