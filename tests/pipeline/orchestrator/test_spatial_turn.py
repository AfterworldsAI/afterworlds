"""The mapper inside the Sojourn Turn (issue #211, M1 acceptance 1, 2, 5-7, 9, 12).

Two routes lead from B5 to the mill door: straight along row 5, which crosses
an unspotted pit at E5 and stops there, and by way of E3, which reaches the
door. Each runs once drawn and once described in words.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.mapper import coords, fixture, store
from afterworlds.models.context import AssembledContext
from afterworlds.models.enums import (
    DiceHandling,
    IntentType,
    RpgPlayStatus,
    StoryMode,
)
from afterworlds.models.node import (
    BranchingNodeMetadata,
    Node,
    NodeMetadata,
    StateDelta,
)
from afterworlds.models.session import RpgSessionState
from afterworlds.models.story import Arc, Chapter, Story
from afterworlds.persistence.crud.node import create_node
from afterworlds.persistence.crud.story import create_arc, create_chapter, create_story
from afterworlds.pipeline.orchestrator import (
    CapabilityProfileAwareSafetyPolicy,
    OrchestrationResult,
    OrchestratorService,
    PipelineDisposition,
)
from afterworlds.pipeline.planner.models import PlannerResult
from afterworlds.pipeline.provider._routing import (
    EligibleModelRoute,
    SafetyWhitelistStatus,
    TurnProviderBinding,
)
from afterworlds.pipeline.rpg.dice import SystemRandomDiceService
from afterworlds.pipeline.rpg.movement import MoverProfile
from afterworlds.pipeline.rpg.spatial_turn import (
    DrawnRoute,
    Mover,
    SpatialTurnService,
    mover_from_token_ref,
)
from afterworlds.pipeline.writer.models import WriterResult
from tests.pipeline.orchestrator.conftest import (
    FakeContextBuilder,
    FakeContradictionService,
    FakeExtractorService,
    FakeIntentClassifier,
    FakePlannerService,
    FakeSafetyService,
    FakeWriterService,
    fixed_mode_resolver,
    make_intent,
)
from tests.pipeline.rpg.movement_support import rules

NOW = datetime(2026, 11, 27, tzinfo=UTC)
SOJOURNER = uuid4()
HERO = MoverProfile(token_id="hero", walk_ft=30, strength=14)

STRAIGHT = ("B5", "C5", "D5", "E5", "F5", "G5", "H5")
BY_E3 = ("B5", "C4", "D3", "E3", "F4", "G5", "H5")
ROUTES = {
    "straight": (STRAIGHT, "I walk over to the mill door."),
    "by_e3": (BY_E3, "I walk over to the mill door by way of E3."),
}


@dataclass
class _LedgerAtCall:
    """What each pass saw in the ledger when it ran (the ledger is mutated
    in place as the Turn goes on)."""

    planner: list[tuple[str, str]] = field(default_factory=list)
    writer: list[tuple[str, str]] = field(default_factory=list)


class _Planner(FakePlannerService):
    seen: _LedgerAtCall

    def plan(
        self, built_context: AssembledContext, *, provider: Any = None
    ) -> PlannerResult:
        self.seen.planner = [
            (e.pass_name, e.content) for e in built_context.pass_forward_ledger.entries
        ]
        return super().plan(built_context, provider=provider)


class _Writer(FakeWriterService):
    seen: _LedgerAtCall

    def write(self, built_context: AssembledContext, *a: Any, **k: Any) -> WriterResult:
        self.seen.writer = [
            (e.pass_name, e.content) for e in built_context.pass_forward_ledger.entries
        ]
        return super().write(built_context, *a, **k)


def _binding() -> object:
    route = EligibleModelRoute(
        provider_name="fake",
        model_identifier="fake:model",
        whitelist_status=SafetyWhitelistStatus.NOT_WHITELISTED,
        supports_required_capabilities=False,
    )

    class _Adapter:
        provider_name = "fake"

        def call(self, request: object) -> object:
            raise AssertionError("no provider call in these tests")

    binding = TurnProviderBinding(
        adapter=_Adapter(),  # type: ignore[arg-type]
        primary_writer_route=route,
        eligible_writer_routes=(route,),
        access_path=RuntimeAccessPath.HOSTED,
    )

    class _Resolver:
        def resolve_for_turn(self, access_path: object, sojourner_id: object) -> object:
            return binding

    return _Resolver()


def _session_state(story_id: UUID) -> RpgSessionState:
    return RpgSessionState(
        story_id=story_id,
        character_sheet_id=uuid4(),
        dice_handling=DiceHandling.AI_ROLLS,
        play_status=RpgPlayStatus.IN_PLAY,
    )


def _mover(story_id: UUID, truth: object) -> Mover:
    return Mover(profile=HERO, rules=rules(), roller=("character", "hero"))


@dataclass
class _Rig:
    orch: OrchestratorService
    spatial: SpatialTurnService
    seen: _LedgerAtCall
    story_id: UUID
    node_id: UUID
    session_factory: Any

    def turn(self, text: str, drawn: DrawnRoute | None = None) -> OrchestrationResult:
        return self.orch.orchestrate_turn(
            self.story_id,
            self.node_id,
            text,
            SOJOURNER,
            RuntimeAccessPath.HOSTED,
            drawn_route=drawn,
        )

    def revisions(self) -> list[Any]:
        with self.session_factory() as s:
            scene = store.active_scene(s, self.story_id)
            assert scene is not None
            return store.revisions(s, scene[0].map_id)


def _seed_story(session_factory: Any) -> tuple[UUID, UUID]:
    """A fresh Story / Arc / Chapter / Node chain, as ``seeded_story``."""
    with session_factory() as s:
        story = Story(title="Mill", mode=StoryMode.RPG, created_at=NOW, updated_at=NOW)
        create_story(s, story)
        arc = Arc(story_id=story.story_id, title="Arc", order=0)
        create_arc(s, arc)
        chapter = Chapter(arc_id=arc.arc_id, title="Chapter", order=0)
        create_chapter(s, chapter)
        node = Node(
            chapter_id=chapter.chapter_id,
            content="",
            state_delta=StateDelta(),
            branching_logic=[],
            intent_type=IntentType.IN_CHARACTER_ACTION,
            metadata=NodeMetadata(timestamp=NOW),
            mode_metadata=BranchingNodeMetadata(),
        )
        create_node(s, node)
        s.commit()
        return story.story_id, node.node_id


def _make_rig(session_factory: Any) -> _Rig:
    story_id, node_id = _seed_story(session_factory)
    with session_factory() as s:
        store.begin_scene(
            s,
            story_id=story_id,
            place_key=fixture.PLACE_KEY,
            label=fixture.LABEL,
            snapshot=fixture.build(),
            seed=fixture.SEED,
            now=NOW,
        )
        s.commit()
    seen = _LedgerAtCall()
    planner, writer = _Planner(), _Writer()
    planner.seen = writer.seen = seen
    spatial = SpatialTurnService(session_factory, _mover, clock=lambda: NOW)
    orch = OrchestratorService(
        intent_classifier=FakeIntentClassifier(
            make_intent(IntentType.IN_CHARACTER_ACTION)
        ),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=planner,
        writer_service=writer,
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_binding(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.RPG),
        rpg_session_resolver=_session_state,
        rpg_dice_service=SystemRandomDiceService(7),
        spatial_turn_service=spatial,
    )
    return _Rig(orch, spatial, seen, story_id, node_id, session_factory)


@pytest.fixture()
def rig(session_factory: Any) -> Any:
    r = _make_rig(session_factory)
    yield r
    r.orch.close()


def _facts(seen: list[tuple[str, str]]) -> dict[str, Any]:
    [content] = [c for name, c in seen if name == "rpg_movement"]
    return dict(json.loads(content))


# -- acceptance 6: two routes, drawn and in words ---------------------------


@pytest.mark.parametrize("way", ["drawn", "words"])
@pytest.mark.parametrize("route_name", list(ROUTES))
def test_each_route_resolves_alike_drawn_or_in_words(
    rig: _Rig, way: str, route_name: str
) -> None:
    squares, words = ROUTES[route_name]
    drawn = DrawnRoute(squares=squares) if way == "drawn" else None
    text = "I go." if way == "drawn" else words
    result = rig.turn(text, drawn)
    assert result.disposition is PipelineDisposition.DELIVERED
    facts = _facts(rig.seen.writer)
    if route_name == "straight":
        assert facts["status"] == "stopped"
        assert facts["final_position"] == "E5"
        assert facts["interruption_point"] == "E5"
        assert facts["stopped_by"] == "a hidden pit"
        assert facts["distance_travelled_ft"] == 15
        assert [c["kind"] for c in facts["consequences"]] == ["fall_damage", "prone"]
    else:
        assert facts["status"] == "completed"
        assert facts["final_position"] == "H5"
        assert facts["interruption_point"] is None
        assert facts["distance_travelled_ft"] == 30
    latest = rig.revisions()[-1]
    hero = latest.snapshot.token(fixture.HERO)
    assert hero is not None and coords.label(hero.square) == facts["final_position"]
    assert latest.turn_id == result.turn_id


@pytest.mark.parametrize("route_name", list(ROUTES))
def test_drawn_and_words_give_the_same_facts_and_record(
    session_factory: Any, route_name: str
) -> None:
    """Same route, same dice seed: identical facts and identical record."""
    squares, words = ROUTES[route_name]
    outcomes = []
    for drawn in (DrawnRoute(squares=squares), None):
        r = _make_rig(session_factory)
        r.turn(words, drawn)
        outcomes.append((_facts(r.seen.writer), r.revisions()[-1].snapshot))
        r.orch.close()
    (facts_a, snap_a), (facts_b, snap_b) = outcomes
    assert facts_a == facts_b
    assert snap_a == snap_b


def test_the_two_routes_have_different_consequences(session_factory: Any) -> None:
    """The route itself matters: same door, different outcome."""
    finals = []
    for squares, _ in ROUTES.values():
        r = _make_rig(session_factory)
        r.turn("I go.", DrawnRoute(squares=squares))
        finals.append(_facts(r.seen.writer)["final_position"])
        r.orch.close()
    assert finals == ["E5", "H5"]


# -- acceptance 7: who sees what -------------------------------------------


def test_planner_sees_scene_and_intent_but_no_outcome(rig: _Rig) -> None:
    rig.turn("I walk over to the mill door.")
    names = [n for n, _ in rig.seen.planner]
    assert names == ["spatial_scene"]
    scene_text = rig.seen.planner[0][1]
    assert "Intended move (words): hero along B5 C5 D5 E5 F5 G5 H5" in scene_text
    assert "mill door: closed, by H5" in scene_text
    for leak in ("pit hidden", "hidden-pit", "lurker", "secret", "stopped", "fall"):
        assert leak not in scene_text
    writer_names = [n for n, _ in rig.seen.writer]
    assert writer_names[:3] == ["spatial_scene", "planner", "rpg_movement"]


def test_a_turn_without_a_move_gets_the_scene_and_changes_nothing(rig: _Rig) -> None:
    before = rig.revisions()
    result = rig.turn("I look around the yard.")
    assert result.disposition is PipelineDisposition.DELIVERED
    assert [n for n, _ in rig.seen.planner] == ["spatial_scene"]
    assert "rpg_movement" not in [n for n, _ in rig.seen.writer]
    assert rig.revisions() == before


def test_naming_a_place_without_moving_is_not_a_move(rig: _Rig) -> None:
    rig.turn("I shout at the goblin by the barrels.")
    assert "rpg_movement" not in [n for n, _ in rig.seen.writer]


# -- acceptance 1, 2 and 12: the view is display only -----------------------


def test_opening_the_view_changes_nothing(rig: _Rig) -> None:
    before = rig.revisions()
    view = rig.spatial.view(rig.story_id)
    again = rig.spatial.view(rig.story_id)
    assert view is not None and view == again
    assert rig.revisions() == before


def test_open_and_closed_turns_resolve_alike(session_factory: Any) -> None:
    """A Turn after the view was opened (auto-open included) and one with it
    never opened produce the same facts and the same next revision."""
    results = []
    for opened in (True, False):
        r = _make_rig(session_factory)
        if opened:
            r.spatial.view(r.story_id)
        r.turn("I walk over to the mill door.")
        results.append((_facts(r.seen.writer), r.revisions()[-1].snapshot))
        r.orch.close()
    assert results[0] == results[1]


# -- the record commits with the Turn ---------------------------------------


def test_a_stale_drawn_route_is_refused_and_nothing_is_written(rig: _Rig) -> None:
    before = rig.revisions()
    result = rig.turn("I go.", DrawnRoute(squares=STRAIGHT, view_hash="0" * 64))
    assert result.disposition is PipelineDisposition.PIPELINE_ERROR
    assert "the scene changed since you looked" in (result.pipeline_error_summary or "")
    assert rig.revisions() == before


def test_a_current_view_hash_is_accepted(rig: _Rig) -> None:
    view = rig.spatial.view(rig.story_id)
    assert view is not None
    drawn = DrawnRoute(squares=BY_E3, view_hash=str(view["view_hash"]))
    assert rig.turn("I go.", drawn).disposition is PipelineDisposition.DELIVERED


def test_the_record_rolls_back_with_a_failed_turn(rig: _Rig) -> None:
    before = rig.revisions()
    writer = rig.orch._writer_service
    assert isinstance(writer, _Writer)
    writer.raise_exc = RuntimeError("writer down")
    result = rig.turn("I walk over to the mill door.")
    assert result.disposition is PipelineDisposition.PIPELINE_ERROR
    assert rig.revisions() == before


def test_a_drawn_route_wins_over_words_with_a_warning(rig: _Rig) -> None:
    rig.turn("I walk over to the mill door.", DrawnRoute(squares=STRAIGHT[:3]))
    assert _facts(rig.seen.writer)["final_position"] == "D5"
    scene_text = rig.seen.planner[0][1]
    assert "Route note: the drawn route ends at D5" in scene_text


def test_a_drawn_route_must_start_on_the_mover(rig: _Rig) -> None:
    result = rig.turn("I go.", DrawnRoute(squares=("C5", "D5")))
    assert result.disposition is PipelineDisposition.PIPELINE_ERROR
    assert rig.revisions()[-1].revision == 0


def test_the_pit_and_the_explored_squares_are_recorded(rig: _Rig) -> None:
    rig.turn("I walk over to the mill door.")
    latest = rig.revisions()[-1]
    ops = [u.op for u in latest.updates]
    assert ops[:2] == ["move_token", "set_hidden"]
    pit = next(p for p in latest.snapshot.pits if p.pit_id == fixture.HIDDEN_PIT)
    assert pit.hidden is False


def test_mover_from_token_ref_finds_the_characters_token() -> None:
    truth = fixture.build(fixture.FixtureRefs(hero_ref="character:sheet-1"))
    resolver = mover_from_token_ref(
        "character",
        lambda _sid: (
            MoverProfile(token_id="sheet-1", walk_ft=25, strength=8),
            rules(),
        ),
    )
    mover = resolver(uuid4(), truth)
    assert mover is not None
    assert mover.profile.token_id == fixture.HERO
    assert mover.profile.walk_ft == 25
    assert mover.roller == ("character", "sheet-1")
    assert mover_from_token_ref("character", lambda _sid: None)(uuid4(), truth) is None
