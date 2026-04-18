"""Tests for ContextBuilderService — CRD Issue 8.

Coverage targets:
  - Stable prefix assembly order (CRD Item 12 architectural invariant)
  - Partition separation (Story Bible vs. prose history; stable vs. volatile)
  - Content correctness across minimal / moderate / complex Story Bible scenarios
  - Protocol seam exercise (RecentTurnsProvider and RetrievalMemoryProvider)
  - Rule slice placement (separate from stable prefix, per ADR-0010)
  - Rolling summary inclusion / absence
  - SQLiteRecentTurnsProvider integration (oldest-first ordering)
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

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
    StablePrefix,
)
from afterworlds.models.enums import (
    CastRole,
    EventSignificance,
    IntentType,
    RelationshipType,
    StoryMode,
)
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.rolling_summary import RollingSummary
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
    ContextBuilderService,
    NullRetrievalMemoryProvider,
    SQLiteRecentTurnsProvider,
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
    """Stub that counts calls and returns a fixed list of Turns oldest-first."""

    def __init__(self, turns: list[Turn] | None = None) -> None:
        self._turns: list[Turn] = turns or []
        self.call_count: int = 0
        self.last_story_id: UUID | None = None
        self.last_limit: int | None = None

    def get_recent_turns(self, story_id: UUID, limit: int) -> list[Turn]:
        self.call_count += 1
        self.last_story_id = story_id
        self.last_limit = limit
        return self._turns[:limit]


class _CountingRetrievalMemoryProvider:
    """Stub that counts calls and returns empty string."""

    def __init__(self) -> None:
        self.call_count: int = 0
        self.last_query: str | None = None

    def retrieve(self, story_id: UUID, query: str) -> str:
        self.call_count += 1
        self.last_query = query
        return ""


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_STORY_ID = uuid4()
_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_SYSTEM_PROMPT = "You are Afterworlds — an AI narrator for interactive stories."


def _make_classified_intent(
    intent: IntentType = IntentType.IN_CHARACTER_ACTION,
) -> IntentClassificationResult:
    return IntentClassificationResult(
        intent_type=intent,
        confidence=0.95,
        raw_input="test input",
        ambiguous=False,
        secondary_intent=None,
    )


def _minimal_bible() -> StoryBibleContext:
    return StoryBibleContext(
        story_id=_STORY_ID,
        setting=None,
        cast=[],
        locked_facts=[],
        forbidden_facts=[],
        relationship_ledger=[],
        active_plot_threads=[],
        events=[],
    )


def _moderate_bible() -> StoryBibleContext:
    cast_entry = CastEntry(
        story_id=_STORY_ID,
        name="Aldric",
        role=CastRole.PROTAGONIST,
        traits=["brave", "reckless"],
        goals=["find the artifact"],
        secrets=["killed his brother"],
        background="Former soldier",
        created_at=_NOW,
    )
    setting = StoryBibleSetting(
        story_id=_STORY_ID,
        summary="A dark fantasy realm where magic is forbidden.",
        world_rules=["Magic is forbidden", "The dead stay dead"],
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
        created_at=_NOW,
    )
    return StoryBibleContext(
        story_id=_STORY_ID,
        setting=setting,
        cast=[cast_entry],
        locked_facts=[locked_fact],
        forbidden_facts=[],
        relationship_ledger=[],
        active_plot_threads=[],
        events=[event],
    )


def _complex_bible() -> StoryBibleContext:
    protagonist_id = uuid4()
    antagonist_id = uuid4()
    protagonist = CastEntry(
        cast_id=protagonist_id,
        story_id=_STORY_ID,
        name="Zara",
        role=CastRole.PROTAGONIST,
        traits=["cunning", "ruthless"],
        goals=["overthrow the empire"],
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
        traits=["calculating", "merciless"],
        goals=["maintain imperial order"],
        background="High inquisitor",
        is_alive=True,
        created_at=_NOW,
    )
    setting = StoryBibleSetting(
        story_id=_STORY_ID,
        summary="An empire teetering on the edge of revolution.",
        world_rules=["Rebellion is punishable by death", "Magic requires a license"],
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
        created_at=_NOW,
    )
    event2 = Event(
        story_id=_STORY_ID,
        description="Rebel cell at the docks compromised.",
        significance=EventSignificance.MAJOR_PLOT_TURN,
        created_at=_NOW,
    )
    return StoryBibleContext(
        story_id=_STORY_ID,
        setting=setting,
        cast=[protagonist, antagonist],
        locked_facts=[locked],
        forbidden_facts=[forbidden],
        relationship_ledger=[relationship],
        active_plot_threads=[thread],
        events=[event1, event2],
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


# ===========================================================================
# CRD Item 12 architectural invariant
# ===========================================================================


def test_stable_prefix_components_in_canonical_order() -> None:
    """CRD Item 12: stable prefix assembled once per turn in documented order.

    Canonical order: system_prompt → Story Bible → rolling summary.
    Structural contract: assembled context contains exactly one StablePrefix;
    all three components are present and appear in the documented order.
    """
    summary_text = "ROLLING_SUMMARY_SENTINEL"
    bible = _moderate_bible()
    service = _make_service(bible=bible, summary=_make_rolling_summary(summary_text))

    assembled = service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
        current_input="I search the room.",
        classified_intent=_make_classified_intent(),
    )

    assert isinstance(assembled, AssembledContext)
    assert isinstance(assembled.stable_prefix, StablePrefix)

    rendered = assembled.stable_prefix.render()

    sys_pos = rendered.find(_SYSTEM_PROMPT)
    bible_pos = rendered.find("## Story Bible")
    summary_pos = rendered.find(summary_text)

    assert sys_pos != -1, "system_prompt missing from stable prefix render"
    assert bible_pos != -1, "Story Bible section missing from stable prefix render"
    assert summary_pos != -1, "rolling summary missing from stable prefix render"
    assert sys_pos < bible_pos, "system_prompt must appear before Story Bible"
    assert bible_pos < summary_pos, "Story Bible must appear before rolling summary"


# ===========================================================================
# Partition separation tests
# ===========================================================================


def test_partition_story_bible_is_in_stable_prefix_not_volatile() -> None:
    """Story Bible is a structural attribute of StablePrefix, not VolatileSuffix."""
    service = _make_service(bible=_moderate_bible())
    assembled = service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
        current_input="I look around.",
        classified_intent=_make_classified_intent(),
    )

    # StablePrefix carries story_bible_context; VolatileSuffix carries recent_turns
    assert hasattr(assembled.stable_prefix, "story_bible_context")
    assert isinstance(assembled.stable_prefix.story_bible_context, StoryBibleContext)
    assert hasattr(assembled.volatile_suffix, "recent_turns")
    # VolatileSuffix has no story_bible_context attribute
    assert not hasattr(assembled.volatile_suffix, "story_bible_context")


def test_partition_recent_turns_in_volatile_suffix_not_stable_prefix() -> None:
    """Recent turns are in VolatileSuffix; StablePrefix carries no prose history."""
    turns = [_make_turn("What do I see?", "A dark corridor.")]
    service = _make_service(turns=turns)
    assembled = service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
        current_input="I go forward.",
        classified_intent=_make_classified_intent(),
    )

    assert assembled.volatile_suffix.recent_turns == turns
    # StablePrefix must have no recent_turns attribute
    assert not hasattr(assembled.stable_prefix, "recent_turns")


def test_partition_story_bible_content_not_in_volatile_suffix_render() -> None:
    """Story Bible content must not appear in volatile suffix rendered text."""
    bible = _moderate_bible()
    service = _make_service(bible=bible)
    assembled = service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
        current_input="I act.",
        classified_intent=_make_classified_intent(),
    )

    volatile_rendered = assembled.volatile_suffix.render()
    assert "## Story Bible" not in volatile_rendered
    # The setting summary is in the stable prefix, not volatile suffix
    assert "dark fantasy" not in volatile_rendered


def test_partition_recent_turns_not_in_stable_prefix_render() -> None:
    """Recent turn prose must not appear in stable prefix rendered text."""
    unique_turn_text = "UNIQUE_TURN_PROSE_SENTINEL"
    turns = [_make_turn(unique_turn_text, "Narrator response.")]
    service = _make_service(turns=turns)
    assembled = service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
        current_input="Next action.",
        classified_intent=_make_classified_intent(),
    )

    assert unique_turn_text not in assembled.stable_prefix.render()
    assert unique_turn_text in assembled.volatile_suffix.render()


# ===========================================================================
# Content correctness — Story Bible scenarios
# ===========================================================================


def test_assemble_minimal_story_bible() -> None:
    """Minimal Bible (no setting, no cast): context assembles without error."""
    service = _make_service(bible=_minimal_bible())
    assembled = service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
        current_input="Hello.",
        classified_intent=_make_classified_intent(IntentType.OOC),
    )

    assert assembled.stable_prefix.story_bible_context.setting is None
    assert assembled.stable_prefix.story_bible_context.cast == []
    rendered = assembled.stable_prefix.render()
    assert _SYSTEM_PROMPT in rendered
    assert "## Story Bible" in rendered
    # No setting section when setting is None
    assert "### Setting" not in rendered


def test_assemble_moderate_story_bible() -> None:
    """Moderate Bible: setting, one cast member, one event, one locked fact."""
    bible = _moderate_bible()
    service = _make_service(bible=bible)
    assembled = service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
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


def test_assemble_complex_story_bible() -> None:
    """Complex Bible: full content including relationships, threads, forbidden facts."""
    bible = _complex_bible()
    service = _make_service(bible=bible)
    assembled = service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
        current_input="I slip into the shadows.",
        classified_intent=_make_classified_intent(IntentType.IN_CHARACTER_ACTION),
    )

    rendered = assembled.stable_prefix.render()
    assert "Zara" in rendered
    assert "Lord Vane" in rendered
    assert "### Forbidden Facts" in rendered
    assert "Zara must not die" in rendered
    assert "### Relationships" in rendered
    # Relationship: Zara → Lord Vane
    assert "Zara" in rendered and "Lord Vane" in rendered
    assert "### Active Plot Threads" in rendered
    assert "betrayed" in rendered


def test_cast_sorted_alphabetically_for_determinism() -> None:
    """Cast entries are rendered alphabetically for deterministic output."""
    bible = _complex_bible()  # has Zara and Lord Vane
    service = _make_service(bible=bible)
    assembled = service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    rendered = assembled.stable_prefix.render()
    # "Lord Vane" sorts before "Zara" alphabetically
    assert rendered.index("Lord Vane") < rendered.index("Zara")


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
        system_prompt=_SYSTEM_PROMPT,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )

    assert provider.call_count == 1
    assert provider.last_story_id == _STORY_ID
    assert provider.last_limit is not None and provider.last_limit > 0


def test_retrieval_memory_provider_is_called() -> None:
    """RetrievalMemoryProvider.retrieve is called on every assemble() call."""
    retrieval = _CountingRetrievalMemoryProvider()
    service = ContextBuilderService(
        story_bible_service=_FixedStoryBibleService(_minimal_bible()),
        rolling_summary_service=_FixedRollingSummaryService(),
        recent_turns_provider=_CountingRecentTurnsProvider(),
        retrieval_memory=retrieval,
    )
    user_input = "What do I see ahead?"
    service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
        current_input=user_input,
        classified_intent=_make_classified_intent(),
    )

    assert retrieval.call_count == 1
    assert retrieval.last_query == user_input


def test_retrieval_memory_called_with_current_input_as_query() -> None:
    """retrieve() receives the current player input as the query string."""
    retrieval = _CountingRetrievalMemoryProvider()
    service = _make_service(retrieval=retrieval)
    specific_input = "Where is the Ember Court located?"
    service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
        current_input=specific_input,
        classified_intent=_make_classified_intent(IntentType.LORE_QUESTION),
    )
    assert retrieval.last_query == specific_input


def test_null_retrieval_memory_provider_returns_empty() -> None:
    """NullRetrievalMemoryProvider.retrieve always returns an empty string."""
    null_provider = NullRetrievalMemoryProvider()
    result = null_provider.retrieve(_STORY_ID, "any query")
    assert result == ""


# ===========================================================================
# Rule slice — separate from stable prefix
# ===========================================================================


def test_rule_slice_is_none_when_not_requested() -> None:
    """AssembledContext.rule_slice is None when no RuleSliceRequest is given."""
    service = _make_service()
    assembled = service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    assert assembled.rule_slice is None


def test_rule_slice_is_separate_from_stable_prefix() -> None:
    """rule_slice is a field on AssembledContext, NOT inside stable_prefix."""
    service = _make_service()
    assembled = service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
        current_input="test",
        classified_intent=_make_classified_intent(),
    )
    # rule_slice on AssembledContext
    assert hasattr(assembled, "rule_slice")
    # StablePrefix does NOT have rule_slice
    assert not hasattr(assembled.stable_prefix, "rule_slice")


def test_rule_slice_request_without_service_raises() -> None:
    """Providing a RuleSliceRequest without injecting rules_package_service raises."""
    from afterworlds.models.rules_package import RuleSliceRequest

    service = ContextBuilderService(
        story_bible_service=_FixedStoryBibleService(_minimal_bible()),
        rolling_summary_service=_FixedRollingSummaryService(),
        recent_turns_provider=_CountingRecentTurnsProvider(),
        retrieval_memory=_CountingRetrievalMemoryProvider(),
        rules_package_service=None,
    )
    req = RuleSliceRequest(package_id=uuid4())
    with pytest.raises(ValueError, match="rules_package_service"):
        service.assemble(
            story_id=_STORY_ID,
            system_prompt=_SYSTEM_PROMPT,
            current_input="I attack.",
            classified_intent=_make_classified_intent(),
            rule_slice_request=req,
        )


# ===========================================================================
# Rolling summary tests
# ===========================================================================


def test_rolling_summary_included_in_stable_prefix_when_present() -> None:
    """Rolling summary text is in the stable prefix when service returns one."""
    summary_sentinel = "SUMMARY_SENTINEL_UNIQUE_TEXT"
    service = _make_service(summary=_make_rolling_summary(summary_sentinel))
    assembled = service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
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
        system_prompt=_SYSTEM_PROMPT,
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
        system_prompt=_SYSTEM_PROMPT,
        current_input=unique_input,
        classified_intent=_make_classified_intent(),
    )
    assert unique_input in assembled.volatile_suffix.render()


def test_volatile_suffix_contains_classified_intent() -> None:
    """Classified intent type appears in the volatile suffix render."""
    service = _make_service()
    assembled = service.assemble(
        story_id=_STORY_ID,
        system_prompt=_SYSTEM_PROMPT,
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
        system_prompt=_SYSTEM_PROMPT,
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
        system_prompt=_SYSTEM_PROMPT,
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
        system_prompt=_SYSTEM_PROMPT,
        current_input=volatile_input,
        classified_intent=_make_classified_intent(),
    )
    assembled.pass_forward_ledger.add("planner", "PLANNER_SENTINEL")

    full = assembled.render_for_pass()

    sys_pos = full.find(_SYSTEM_PROMPT)
    bible_pos = full.find("## Story Bible")
    summary_pos = full.find(summary_text)
    planner_pos = full.find("PLANNER_SENTINEL")
    volatile_pos = full.find(volatile_input)

    assert sys_pos < bible_pos < summary_pos
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
