"""Movement adjudication over the mapper (issue #211 acceptance 4, 5, 6)."""

from __future__ import annotations

import json
from dataclasses import asdict
from types import SimpleNamespace

import pytest

from afterworlds.mapper import coords, fixture, views
from afterworlds.mapper.models import (
    Edge,
    Feature,
    Level,
    MoveToken,
    Pit,
    SetFeatureState,
    SetHidden,
    Snapshot,
    Square,
    Token,
)
from afterworlds.mapper.updates import apply_all
from afterworlds.pipeline.rpg import movement
from afterworlds.pipeline.rpg.dice import SystemRandomDiceService
from afterworlds.pipeline.rpg.movement import (
    MoveIntent,
    MoverProfile,
    allowance,
    preview,
    profile_from_state,
    resolve,
    route_from_words,
    walk,
)
from tests.pipeline.rpg.movement_support import rules

HERO = MoverProfile(token_id="hero", walk_ft=30, strength=14)
STRAIGHT: tuple[Square, ...] = ((1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4))
BY_E3: tuple[Square, ...] = ((1, 4), (2, 3), (3, 2), (4, 2), (5, 3), (6, 4), (7, 4))


def _truth(**kw: bool) -> Snapshot:
    return fixture.build(**kw)


def _resolve(
    truth: Snapshot, intent: MoveIntent, seed: int = 5, profile: MoverProfile = HERO
) -> movement.MoveOutcome:
    out = resolve(
        truth,
        views.player_snapshot(truth),
        profile,
        rules(),
        intent,
        dice=SystemRandomDiceService(seed),
        roller=("character", profile.token_id),
        revision=4,
    )
    if out.status != "refused" and profile.token_id == "hero":
        # Every move these tests resolve must also save: the Turn stages the
        # same updates through the record's validator.
        _staged(truth, out)
    return out


def _with(truth: Snapshot, *updates: object) -> Snapshot:
    return apply_all(truth, list(updates), current_revision=0, seed=1)  # type: ignore[arg-type]


def _staged(truth: Snapshot, out: movement.MoveOutcome) -> Snapshot:
    """Apply the outcome's updates as the Turn stages them; the record's own
    validator refuses anything it would not save."""
    after = apply_all(truth, out.updates, current_revision=4, seed=1)
    hero = after.token("hero")
    assert hero is not None and hero.square == out.final_square
    return after


# -- acceptance 5 and 6 ----------------------------------------------------


def test_hidden_pit_ends_the_move_and_the_fall_uses_the_dice_rails() -> None:
    out = _resolve(_truth(), MoveIntent(route=STRAIGHT))
    assert out.status == "stopped"
    assert out.final_square == (4, 4)
    assert out.travelled == STRAIGHT[:4]
    assert out.distance_ft == 15
    kinds = [c.kind for c in out.consequences]
    assert kinds == ["fall_damage", "prone"]
    fall = out.consequences[0]
    assert fall.detail == "1d6 bludgeoning from a 10-ft fall"
    assert fall.roll_total == SystemRandomDiceService(5).roll("1d6").chosen
    assert fall.citation == ("glossary.falling", "fall_damage")
    assert (
        MoveToken(base_revision=4, token_id="hero", route=STRAIGHT[:4]) in out.updates
    )
    assert (
        SetHidden(base_revision=4, thing_id="hidden-pit", hidden=False) in out.updates
    )
    facts = out.writer_facts()
    assert facts["final_position"] == "E5" and facts["interruption_point"] == "E5"
    assert facts["stopped_by"] == "a hidden pit"
    after = _staged(_truth(), out)
    assert not next(p for p in after.pits if p.pit_id == "hidden-pit").hidden


def test_the_other_route_reaches_the_door() -> None:
    out = _resolve(_truth(), MoveIntent(route=BY_E3))
    assert out.status == "completed"
    assert out.final_square == (7, 4)
    assert out.distance_ft == 30 and out.movement_spent_ft == 30
    assert out.consequences == ()
    assert out.writer_facts()["interruption_point"] is None


@pytest.mark.parametrize(
    ("words", "route", "final"),
    [
        ("I walk over to the mill door.", STRAIGHT, (4, 4)),
        ("I head for the mill door by way of E3.", BY_E3, (7, 4)),
        ("Kael goes via e3 to H5", BY_E3, (7, 4)),
    ],
)
def test_words_and_drawn_routes_resolve_alike(
    words: str, route: tuple[Square, ...], final: Square
) -> None:
    truth = _truth()
    player = views.player_snapshot(truth)
    spoken = route_from_words(words, player, HERO, rules())
    assert spoken is not None and spoken.route == route
    said = _resolve(truth, MoveIntent(route=spoken.route, source="words"))
    drawn = _resolve(truth, MoveIntent(route=route, source="drawn"))
    assert said.final_square == drawn.final_square == final
    assert said.updates == drawn.updates
    assert said.consequences == drawn.consequences
    assert said.writer_facts() == drawn.writer_facts()


def test_two_routes_to_the_door_keep_their_different_results() -> None:
    truth = _truth()
    a = _resolve(truth, MoveIntent(route=STRAIGHT))
    b = _resolve(truth, MoveIntent(route=BY_E3))
    assert (a.status, a.final_square) == ("stopped", (4, 4))
    assert (b.status, b.final_square) == ("completed", (7, 4))


def test_words_name_dash_and_disengage_and_nothing_else_is_parsed() -> None:
    player = views.player_snapshot(_truth())
    spoken = route_from_words(
        "I dash to the mill door and disengage", player, HERO, rules()
    )
    assert spoken is not None and spoken.dash and spoken.disengage
    assert spoken.destination == "mill door"
    assert route_from_words("I look around", player, HERO, rules()) is None
    nobody = MoverProfile(token_id="ghost", walk_ft=30, strength=10)
    assert route_from_words("to H5", player, nobody, rules()) is None


def test_words_route_around_what_blocks_the_line() -> None:
    player = views.player_snapshot(_truth())
    spoken = route_from_words("I go to G7", player, HERO, rules())
    assert spoken is not None
    assert spoken.route[-1] == (6, 6)
    assert (
        walk(player, player, HERO, rules(), MoveIntent(route=spoken.route)).refused
        is None
    )


# -- acceptance 4 ----------------------------------------------------------


def _player_facts(truth: Snapshot, route: tuple[Square, ...]) -> str:
    player = views.player_snapshot(truth)
    p = preview(player, HERO, rules(), MoveIntent(route=route))
    a = allowance(player, HERO, rules())
    return json.dumps([asdict(p), a.as_json()], sort_keys=True)


@pytest.mark.parametrize(
    "route",
    [
        STRAIGHT,
        BY_E3,
        (
            (1, 4),
            (0, 5),
            (0, 6),
            (0, 7),
            (1, 8),
            (2, 8),
        ),  # through the secret door's line
        ((1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (0, 9)),  # onto the lurker
        STRAIGHT + ((8, 4),),
    ],
)
def test_previews_allowance_and_refusals_ignore_hidden_things(
    route: tuple[Square, ...],
) -> None:
    assert _player_facts(_truth(), route) == _player_facts(
        _truth(with_hidden=False), route
    )


def test_the_hidden_creature_stops_a_move_it_could_not_refuse() -> None:
    truth = _truth()
    route = ((1, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9))
    assert (
        preview(
            views.player_snapshot(truth), HERO, rules(), MoveIntent(route=route)
        ).refused
        is None
    )
    out = _resolve(truth, MoveIntent(route=route))
    assert out.status == "stopped" and out.final_square == (0, 8)
    assert SetHidden(base_revision=4, thing_id="lurker", hidden=False) in out.updates
    assert out.writer_facts()["stopped_by"] == "an unseen creature"
    _staged(truth, out)


# -- the rules -------------------------------------------------------------


@pytest.mark.parametrize(
    ("route", "reason"),
    [
        (((2, 4), (3, 4)), movement.NOT_AT_START),
        (((1, 4), (3, 4)), movement.NOT_A_STEP),
        (((1, 4), (0, 4), (-1, 4)), movement.OFF_MAP),
        (((1, 4), (0, 5), (0, 6), (0, 7), (1, 8), (2, 8)), movement.WALL),
        (((1, 4), (2, 5), (3, 6), (4, 6), (5, 6)), movement.SOLID),
        (((1, 4), (2, 5), (3, 6), (4, 7), (5, 7), (6, 7)), movement.OCCUPIED_END),
        (STRAIGHT + ((8, 4),), movement.SOLID),
        (
            ((1, 4), (2, 5), (3, 6), (4, 7), (5, 8), (6, 9), (7, 9), (7, 8)),
            movement.OVER_BUDGET,
        ),
    ],
)
def test_player_visible_refusals(route: tuple[Square, ...], reason: str) -> None:
    player = views.player_snapshot(_truth(with_hidden=False))
    assert reason in movement.REFUSALS
    assert preview(player, HERO, rules(), MoveIntent(route=route)).refused == reason
    out = _resolve(_truth(), MoveIntent(route=route))
    assert out.status == "refused" and out.refused == reason
    assert out.updates == () and out.final_square == (1, 4)


def test_a_corner_is_not_cut() -> None:
    truth = _with(
        _truth(),
        movement_feature("crate", ((2, 3),)),
    )
    route = ((1, 4), (2, 3))
    player = views.player_snapshot(truth)
    assert (
        preview(player, HERO, rules(), MoveIntent(route=route)).refused
        == movement.SOLID
    )
    corner = ((1, 4), (2, 5), (3, 4))
    blocked = _with(truth, movement_feature("crate2", ((2, 4),)))
    p = views.player_snapshot(blocked)
    assert (
        preview(p, HERO, rules(), MoveIntent(route=corner)).refused == movement.CORNER
    )


def movement_feature(fid: str, squares: tuple[Square, ...]) -> object:
    from afterworlds.mapper.models import AddFeature

    return AddFeature(
        base_revision=0,
        feature=Feature(
            feature_id=fid, kind="boulder", squares=squares, blocks_step=True
        ),
    )


def test_dash_doubles_the_budget() -> None:
    route = ((1, 4), (2, 5), (3, 6), (4, 7), (5, 8), (6, 9), (7, 9), (7, 8))
    player = views.player_snapshot(_truth())
    p = preview(player, HERO, rules(), MoveIntent(route=route, dash=True))
    assert p.refused is None and p.uses_dash and p.cost_ft == 35
    out = _resolve(_truth(), MoveIntent(route=route, dash=True))
    assert out.status == "completed" and out.dash


def test_doors_open_as_the_route_passes_and_locked_ones_refuse() -> None:
    truth = _with(
        _truth(),
        SetFeatureState(base_revision=0, feature_id="mill-door", state="closed"),
    )
    # Refine a corridor of the mill so the hero can step through.
    from afterworlds.mapper.models import MarkExplored, RefineArea

    truth = _with(
        truth,
        RefineArea(base_revision=0, area="mill"),
        MarkExplored(
            base_revision=0,
            squares=tuple((c, r) for c in range(8, 12) for r in range(10)),
        ),
    )
    route = (*BY_E3, (8, 4))
    out = _resolve(truth, MoveIntent(route=route, dash=True))
    assert out.status == "completed"
    opened = SetFeatureState(base_revision=4, feature_id="mill-door", state="open")
    # The door opens before the move that crosses it, or the record refuses
    # the step through a closed door.
    assert out.updates.index(opened) < next(
        n for n, u in enumerate(out.updates) if isinstance(u, MoveToken)
    )
    after = _staged(truth, out)
    door = after.feature("mill-door")
    assert door is not None and door.state == "open"
    locked = _with(
        truth, SetFeatureState(base_revision=0, feature_id="mill-door", state="locked")
    )
    assert (
        _resolve(locked, MoveIntent(route=route, dash=True)).refused == movement.LOCKED
    )


def test_a_second_closed_door_needs_an_action() -> None:
    door = Feature(
        feature_id="gate",
        kind="door",
        edge=Edge(orient="v", col=3, row=0),
        state="closed",
    )
    from afterworlds.mapper.models import AddFeature

    truth = _with(
        _truth(),
        AddFeature(base_revision=0, feature=door),
        AddFeature(
            base_revision=0,
            feature=Feature(
                feature_id="gate2",
                kind="door",
                edge=Edge(orient="v", col=4, row=0),
                state="closed",
            ),
        ),
    )
    route = ((1, 4), (1, 3), (1, 2), (1, 1), (2, 0), (3, 0), (4, 0))
    assert _resolve(truth, MoveIntent(route=route)).refused == movement.SECOND_DOOR


def test_difficult_terrain_and_creature_spaces() -> None:
    from afterworlds.mapper.models import PlaceToken, SetTerrain

    truth = _with(
        _truth(),
        SetTerrain(base_revision=0, squares=((2, 4),), char=","),
        PlaceToken(
            base_revision=0,
            token=Token(
                token_id="ally", glyph="A", ref="c:a", side="party", square=(1, 3)
            ),
        ),
        PlaceToken(
            base_revision=0,
            token=Token(
                token_id="foe", glyph="F", ref="c:f", side="hostile", square=(2, 2)
            ),
        ),
    )
    player = views.player_snapshot(truth)
    rough = preview(player, HERO, rules(), MoveIntent(route=((1, 4), (2, 4), (3, 4))))
    assert rough.cost_ft == 15 and rough.warnings == (("C5", "difficult terrain"),)
    past_ally = preview(
        player, HERO, rules(), MoveIntent(route=((1, 4), (1, 3), (1, 2)))
    )
    assert past_ally.cost_ft == 10
    past_foe = preview(
        player, HERO, rules(), MoveIntent(route=((1, 4), (1, 3), (2, 2), (3, 2)))
    )
    assert past_foe.cost_ft == 20


def test_visible_pit_is_long_jumped_with_a_run_up() -> None:
    truth = _truth()
    player = views.player_snapshot(truth)
    running = ((1, 4), (1, 5), (1, 6), (1, 7), (1, 8))
    p = preview(player, HERO, rules(), MoveIntent(route=running))
    # 10 ft run-up, a 5-ft jump over B8 and the landing square.
    assert p.refused is None and p.cost_ft == 10 + 5 + 5
    out = _resolve(truth, MoveIntent(route=running))
    assert out.final_square == (1, 8) and out.distance_ft == 20
    assert ("glossary.long_jump", "jump_distance") in out.citations
    # The record keeps every square passed over, B8 included, so each step of
    # the saved move is adjacent; the cost is still the jump's.
    assert out.travelled == running
    assert MoveToken(base_revision=4, token_id="hero", route=running) in out.updates
    _staged(truth, out)
    standing = ((1, 6), (1, 7), (1, 8))
    moved = _with(
        truth,
        MoveToken(base_revision=0, token_id="hero", route=((1, 4), (1, 5), (1, 6))),
    )
    weak = MoverProfile(token_id="hero", walk_ft=30, strength=8)
    w = walk(
        views.player_snapshot(moved),
        views.player_snapshot(moved),
        weak,
        rules(),
        MoveIntent(route=standing),
    )
    assert w.refused == movement.TOO_FAR_TO_JUMP and w.refused_at == (1, 6)
    ends_in_pit = walk(player, player, HERO, rules(), MoveIntent(route=running[:-1]))
    assert ends_in_pit.refused == movement.TOO_FAR_TO_JUMP


def test_heights_jump_and_climb() -> None:
    truth = _truth(with_hidden=False)
    levels = (
        Level(level_id="step", squares=((3, 4),), height_ft=1),
        Level(level_id="crate", squares=((4, 3),), height_ft=4),
        Level(level_id="ledge", squares=((5, 3),), height_ft=14),
    )
    tall = truth.model_copy(update={"levels": levels})
    player = views.player_snapshot(tall)
    route = ((1, 4), (2, 4), (3, 4), (4, 3), (5, 3))
    # A rise of 1 ft is a plain step.
    assert preview(player, HERO, rules(), MoveIntent(route=route[:3])).cost_ft == 10
    # Up 3 ft after a 10-ft run: a High Jump (3 + Strength mod 2 = 5 ft).
    assert (
        preview(player, HERO, rules(), MoveIntent(route=route[:4])).cost_ft
        == 10 + 5 + 3
    )
    # Standing, the same 3 ft is beyond half the High Jump: a climb.
    moved = _with(
        tall,
        MoveToken(base_revision=0, token_id="hero", route=((1, 4), (2, 4), (3, 4))),
    )
    pm = views.player_snapshot(moved)
    assert (
        preview(pm, HERO, rules(), MoveIntent(route=((3, 4), (4, 3)))).cost_ft
        == 5 + 3 * 2
    )
    # Up 10 ft more is a climb: each foot costs 1 extra.
    long = replace_walk(HERO, 90)
    assert (
        preview(player, long, rules(), MoveIntent(route=route)).cost_ft
        == 18 + 5 + 10 * 2
    )
    climber = MoverProfile(token_id="hero", walk_ft=90, strength=14, climb_ft=30)
    assert (
        preview(player, climber, rules(), MoveIntent(route=route)).cost_ft
        == 18 + 5 + 10
    )


def replace_walk(profile: MoverProfile, feet: int) -> MoverProfile:
    from dataclasses import replace

    return replace(profile, walk_ft=feet)


def test_deep_water_costs_swimming() -> None:
    from afterworlds.mapper.models import SetTerrain

    truth = _with(_truth(), SetTerrain(base_revision=0, squares=((2, 4),), char="="))
    player = views.player_snapshot(truth)
    assert (
        preview(player, HERO, rules(), MoveIntent(route=((1, 4), (2, 4)))).cost_ft == 10
    )
    swimmer = MoverProfile(token_id="hero", walk_ft=30, strength=14, swim_ft=30)
    assert (
        preview(player, swimmer, rules(), MoveIntent(route=((1, 4), (2, 4)))).cost_ft
        == 5
    )


# -- squeezing: the Owner's house rule, with its four tests ----------------


def _doorway(fits: str) -> Snapshot:
    from afterworlds.mapper.models import AddFeature

    truth = _truth()
    gap = Feature(
        feature_id="gap",
        kind="other",
        label="gap",
        squares=((2, 2),),
        fits=fits,  # type: ignore[arg-type]
    )
    return _with(truth, AddFeature(base_revision=0, feature=gap))


def test_house_rule_squeezing_an_ogre_crosses_a_5ft_door_at_double_cost() -> None:
    ogre = MoverProfile(token_id="hero", walk_ft=40, strength=19, size="large")
    player = views.player_snapshot(_doorway("medium"))
    p = preview(player, ogre, rules(), MoveIntent(route=((1, 4), (1, 3), (2, 2))))
    assert p.refused is None and p.cost_ft == 5 + 10
    w = walk(player, player, ogre, rules(), MoveIntent(route=((1, 4), (1, 3), (2, 2))))
    assert w.steps[-1].squeezing
    out = _resolve(
        _doorway("medium"), MoveIntent(route=((1, 4), (1, 3), (2, 2))), profile=ogre
    )
    assert out.squeezing and out.final_square == (2, 2)


def test_house_rule_squeezing_the_ogre_is_refused_at_a_small_gap() -> None:
    ogre = MoverProfile(token_id="hero", walk_ft=40, strength=19, size="large")
    player = views.player_snapshot(_doorway("small"))
    p = preview(player, ogre, rules(), MoveIntent(route=((1, 4), (1, 3), (2, 2))))
    assert p.refused == movement.TOO_NARROW


def test_house_rule_squeezing_a_medium_character_in_a_small_tunnel() -> None:
    truth = _doorway("small")
    player = views.player_snapshot(truth)
    p = preview(player, HERO, rules(), MoveIntent(route=((1, 4), (1, 3), (2, 2))))
    assert p.cost_ft == 5 + 10
    out = _resolve(truth, MoveIntent(route=((1, 4), (1, 3), (2, 2))))
    assert out.squeezing
    assert movement.squeeze_effects(out.squeezing)[0] == (
        "attack_rolls",
        "disadvantage",
    )
    assert out.consequences[-1].detail == movement.HOUSE_RULE_SQUEEZING


def test_house_rule_squeezing_a_medium_character_at_a_5ft_door_pays_normally() -> None:
    truth = _doorway("medium")
    out = _resolve(truth, MoveIntent(route=((1, 4), (1, 3), (2, 2))))
    assert out.movement_spent_ft == 10 and not out.squeezing


# -- the allowance and the mover -------------------------------------------


def test_allowance_from_player_visible_facts() -> None:
    player = views.player_snapshot(_truth())
    a = allowance(player, HERO, rules())
    assert a.costs["H5"] == 30
    assert a.costs["E5"] == 15  # the hidden pit isn't known
    assert "G8" not in a.costs  # the goblin's square
    assert "F7" not in a.costs  # the barrels
    assert a.warnings == {}
    slow = allowance(player, replace_walk(HERO, 15), rules())
    assert slow.costs["H5"] == 30 and slow.warnings["H5"] == "uses your Dash"
    assert "E5" not in slow.warnings
    nobody = allowance(
        player, MoverProfile(token_id="x", walk_ft=30, strength=10), rules()
    )
    assert nobody.costs == {}


def test_profile_from_character_state() -> None:
    state = SimpleNamespace(
        speeds=(
            SimpleNamespace(mode=SimpleNamespace(value="walk"), feet=30),
            SimpleNamespace(mode=SimpleNamespace(value="swim"), feet=15),
        ),
        ability_scores=SimpleNamespace(strength=16),
        size=SimpleNamespace(value="small"),
    )
    p = profile_from_state("hero", state)
    assert p == MoverProfile(
        token_id="hero", walk_ft=30, strength=16, size="small", swim_ft=15
    )
    assert p.strength_mod == 3
    assert (
        profile_from_state("hero", SimpleNamespace(speeds=None, ability_scores=None))
        is None
    )


def test_not_your_character() -> None:
    truth = _truth()
    out = resolve(
        truth,
        views.player_snapshot(truth),
        MoverProfile(token_id="nobody", walk_ft=30, strength=10),
        rules(),
        MoveIntent(route=((0, 0), (1, 0))),
        dice=SystemRandomDiceService(1),
        roller=("character", "x"),
        revision=0,
    )
    assert out.refused == movement.NOT_YOURS


def test_deep_falls_cap_at_twenty_dice() -> None:
    truth = _truth()
    deep = truth.model_copy(
        update={
            "pits": tuple(
                (
                    p.model_copy(update={"depth_ft": 300})
                    if p.pit_id == "hidden-pit"
                    else p
                )
                for p in truth.pits
            )
        }
    )
    out = _resolve(deep, MoveIntent(route=STRAIGHT))
    assert out.consequences[0].detail.startswith("20d6")
    shallow = truth.model_copy(
        update={
            "pits": tuple(
                p.model_copy(update={"depth_ft": 5}) if p.pit_id == "hidden-pit" else p
                for p in truth.pits
            )
        }
    )
    # Prone applies on any damage from the fall; a 5-ft fall deals none
    # (Codex round 3), so it neither rolls nor lands Prone.
    short = _resolve(shallow, MoveIntent(route=STRAIGHT))
    assert short.consequences == ()
    assert short.fall is not None and short.fall.total == 0 and not short.fall.prone


def test_jumps_and_climbs_save_with_every_square_passed() -> None:
    """A wider pit and a climb both stage as adjacent steps on the record."""
    truth = _truth(with_hidden=False)
    wide = truth.model_copy(
        update={
            "pits": tuple(
                (
                    p.model_copy(update={"squares": ((1, 7), (1, 8))})
                    if p.pit_id == "open-pit"
                    else p
                )
                for p in truth.pits
            )
        }
    )
    route = ((1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9))
    out = _resolve(wide, MoveIntent(route=route, dash=True))
    assert out.status == "completed" and out.final_square == (1, 9)
    assert out.travelled == route
    assert [s for s in out.updates if isinstance(s, MoveToken)] == [
        MoveToken(base_revision=4, token_id="hero", route=route)
    ]
    levels = (Level(level_id="ledge", squares=((3, 4),), height_ft=14),)
    tall = truth.model_copy(update={"levels": levels})
    climb = ((1, 4), (2, 4), (3, 4))
    out = _resolve(tall, MoveIntent(route=climb, dash=True))
    assert out.status == "completed" and out.final_square == (3, 4)


def _with_hwall(truth: Snapshot, col: int, row: int) -> Snapshot:
    rows = list(truth.hwalls)
    rows[row] = rows[row][:col] + "-" + rows[row][col + 1 :]
    return truth.model_copy(update={"hwalls": tuple(rows)})


RUN_OVER_B8: tuple[Square, ...] = ((1, 4), (1, 5), (1, 6), (1, 7), (1, 8))


def test_a_jump_checks_every_line_it_crosses() -> None:
    """Sibling of the saved-route fix: the walk used to skip the lines after
    the first pit square, so a jump could pass a door or a wall that the
    record then refused."""
    from afterworlds.mapper.models import AddFeature

    truth = _truth(with_hidden=False)

    def door(state: str, row: int) -> Snapshot:
        return _with(
            truth,
            AddFeature(
                base_revision=0,
                feature=Feature(
                    feature_id="pit-door",
                    kind="door",
                    edge=Edge(orient="h", col=1, row=row),
                    state=state,  # type: ignore[arg-type]
                ),
            ),
        )

    # A closed door on the far side of the pit opens as the jump lands.
    out = _resolve(door("closed", 8), MoveIntent(route=RUN_OVER_B8))
    assert out.status == "completed" and out.final_square == (1, 8)
    opened = SetFeatureState(base_revision=4, feature_id="pit-door", state="open")
    assert out.updates[0] == opened
    # A locked one, or a wall, stops the jump before it starts.
    assert _resolve(door("locked", 8), MoveIntent(route=RUN_OVER_B8)).refused == (
        movement.LOCKED
    )
    walled = _resolve(_with_hwall(truth, 1, 8), MoveIntent(route=RUN_OVER_B8))
    assert walled.refused == movement.WALL


def test_a_hidden_pit_or_creature_at_the_landing_ends_the_jump() -> None:
    from afterworlds.mapper.models import PlaceToken

    truth = _truth(with_hidden=False)
    landing_pit = truth.pits[0].model_copy(
        update={"pit_id": "landing-pit", "squares": ((1, 8),), "hidden": True}
    )
    trapped = truth.model_copy(update={"pits": (*truth.pits, landing_pit)})
    out = _resolve(trapped, MoveIntent(route=RUN_OVER_B8))
    assert out.status == "stopped" and out.final_square == (1, 8)
    assert out.stopped_by == "pit:landing-pit"
    assert [c.kind for c in out.consequences][-1] == "prone"
    assert SetHidden(base_revision=4, thing_id="landing-pit", hidden=False) in (
        out.updates
    )
    lurking = _with(
        truth,
        PlaceToken(
            base_revision=0,
            token=Token(
                token_id="lurk2",
                glyph="L",
                ref="c:l",
                side="hostile",
                square=(1, 8),
                hidden=True,
            ),
        ),
    )
    out = _resolve(lurking, MoveIntent(route=RUN_OVER_B8))
    assert out.status == "stopped" and out.final_square == (1, 6)
    assert out.stopped_by == "creature:lurk2"


def _placed(truth: Snapshot, *tokens: Token) -> Snapshot:
    from afterworlds.mapper.models import PlaceToken

    return _with(truth, *(PlaceToken(base_revision=0, token=t) for t in tokens))


ALLY = Token(token_id="ally", glyph="A", ref="c:a", side="party", square=(2, 4))


def test_an_interrupted_move_never_ends_on_an_ally() -> None:
    """Passing through an ally is fine; ending there is not, also when an
    unseen creature cuts the move short (Codex round 2)."""
    lurker = Token(token_id="lurk2", glyph="L", ref="c:l", side="hostile", hidden=True)
    truth = _placed(
        _truth(with_hidden=False), ALLY, lurker.model_copy(update={"square": (3, 4)})
    )
    out = _resolve(truth, MoveIntent(route=((1, 4), (2, 4), (3, 4), (4, 4))))
    assert out.status == "stopped" and out.stopped_by == "creature:lurk2"
    assert out.final_square == (1, 4)
    assert not [u for u in out.updates if isinstance(u, MoveToken)]
    # The same at a jump's take-off: the ally holds B7, so the mover stops
    # at B6 when something unseen holds the landing at B9.
    jumping = _placed(
        _truth(with_hidden=False),
        ALLY.model_copy(update={"square": (1, 6)}),
        lurker.model_copy(update={"square": (1, 8)}),
    )
    out = _resolve(jumping, MoveIntent(route=RUN_OVER_B8))
    assert out.status == "stopped" and out.final_square == (1, 5)


def _big_hero(truth: Snapshot, square: Square) -> Snapshot:
    return truth.model_copy(
        update={
            "tokens": tuple(
                (
                    t.model_copy(update={"footprint": 2, "square": square})
                    if t.token_id == "hero"
                    else t
                )
                for t in truth.tokens
            )
        }
    )


def test_a_large_token_needs_room_for_its_whole_footprint_at_the_end() -> None:
    """Every square of a 2x2 token must fit where the move ends (Codex
    round 2); the record checks the whole footprint too."""
    big = MoverProfile(token_id="hero", walk_ft=40, strength=19, size="large")
    edge = _big_hero(_truth(with_hidden=False), (3, 7))
    to_edge = ((3, 7), (3, 8), (3, 9))
    player = views.player_snapshot(edge)
    assert preview(player, big, rules(), MoveIntent(route=to_edge)).refused == (
        movement.NO_ROOM
    )
    assert _resolve(edge, MoveIntent(route=to_edge), profile=big).refused == (
        movement.NO_ROOM
    )
    crowded = _placed(
        _big_hero(_truth(with_hidden=False), (3, 4)),
        ALLY.model_copy(update={"square": (6, 5)}),
    )
    beside = ((3, 4), (4, 4), (5, 4))
    out = _resolve(crowded, MoveIntent(route=beside), profile=big)
    assert out.refused == movement.OCCUPIED_END
    fine = _resolve(
        _big_hero(_truth(with_hidden=False), (3, 1)),
        MoveIntent(route=((3, 1), (4, 1), (5, 1))),
        profile=big,
    )
    assert fine.status == "completed" and fine.final_square == (5, 1)


def test_a_large_token_cannot_pass_through_rock_where_a_pit_may_stop_it() -> None:
    """A 2x2 footprint is checked at every step, not only the end (Codex
    round 3): otherwise a hidden pit could stop it overlapping rock, which
    the record refuses and the Turn would roll back."""
    big = MoverProfile(token_id="hero", walk_ft=40, strength=19, size="large")
    # Column 8 is the unexplored mill: rock as far as the mover knows.
    beside_mill = ((5, 1), (6, 1), (7, 1), (6, 2))
    truth = _big_hero(_truth(with_hidden=False), (5, 1))
    pit = Pit(pit_id="under", squares=((7, 1),), depth_ft=10, hidden=True)
    hidden = truth.model_copy(update={"pits": (*truth.pits, pit)})
    player = views.player_snapshot(hidden)
    p = preview(player, big, rules(), MoveIntent(route=beside_mill))
    assert (p.refused, p.refused_at) == (movement.NO_ROOM, coords.label((7, 1)))
    assert _resolve(hidden, MoveIntent(route=beside_mill), profile=big).refused == (
        movement.NO_ROOM
    )
