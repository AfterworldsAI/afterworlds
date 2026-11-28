"""The spatial record, its queries and typed updates (issue #211, M1)."""

from __future__ import annotations

import pytest

from afterworlds.mapper import coords, fixture
from afterworlds.mapper.geometry import (
    distance_ft,
    edge_between,
    edge_fact,
    leaves_distance,
    lit_areas,
    route_facts,
    sight_line,
    visible_squares,
)
from afterworlds.mapper.models import (
    AddFeature,
    Edge,
    Feature,
    MarkExplored,
    MoveToken,
    PlaceToken,
    Relate,
    Relation,
    RemoveFeature,
    RemoveToken,
    SetFeatureState,
    SetHidden,
    SetLight,
    SetTerrain,
    SetZone,
    Token,
    Zone,
    blank_snapshot,
)
from afterworlds.mapper.updates import (
    MAP_MOVED_ON,
    UpdateRefused,
    apply,
    apply_all,
    content_hash,
)


def _yard() -> object:
    return fixture.build()


def test_coords_round_trip() -> None:
    assert coords.label((0, 0)) == "A1"
    assert coords.label((7, 4)) == "H5"
    assert coords.label((26, 0)) == "AA1"
    assert coords.parse("h5") == (7, 4)
    assert coords.parse("AA1") == (26, 0)
    assert coords.is_label("C3") and not coords.is_label("door")
    with pytest.raises(ValueError):
        coords.parse("A0")
    with pytest.raises(ValueError):
        coords.parse("door")


def test_edge_sides_and_between() -> None:
    assert Edge(orient="v", col=8, row=4).sides() == ((7, 4), (8, 4))
    assert Edge(orient="h", col=2, row=3).sides() == ((2, 2), (2, 3))
    assert edge_between((7, 4), (8, 4)) == Edge(orient="v", col=8, row=4)
    assert edge_between((8, 4), (7, 4)) == Edge(orient="v", col=8, row=4)
    assert edge_between((2, 3), (2, 2)) == Edge(orient="h", col=2, row=3)
    with pytest.raises(ValueError):
        edge_between((0, 0), (1, 1))


def test_fixture_builds_through_typed_updates() -> None:
    truth = fixture.build()
    assert truth.area("yard").level == "gridded"  # type: ignore[union-attr]
    assert truth.area("mill").level == "coarse"  # type: ignore[union-attr]
    assert truth.token(fixture.HERO).square == (1, 4)  # type: ignore[union-attr]
    assert truth.pit_at((4, 4)).hidden  # type: ignore[union-attr]
    door = truth.door_at(Edge(orient="v", col=8, row=4))
    assert door is not None and door.state == "closed"
    assert all(truth.is_explored((c, r)) for c in range(8) for r in range(10))
    assert not truth.is_explored((9, 4))
    # The coarse placement went once the hero had a square.
    assert truth.coarse.placements == ()


def test_doors_walls_and_secret_doors_as_edges() -> None:
    truth = fixture.build()
    mill = edge_fact(truth, Edge(orient="v", col=8, row=4))
    assert mill.door is not None and mill.blocks
    secret = edge_fact(truth, Edge(orient="v", col=2, row=8))
    assert secret.wall and secret.blocks  # a hidden secret door is a wall
    opened = apply(
        truth,
        SetFeatureState(base_revision=0, feature_id="mill-door", state="open"),
        current_revision=0,
        seed=1,
    )
    assert not edge_fact(opened, Edge(orient="v", col=8, row=4)).blocks
    off = edge_fact(truth, Edge(orient="h", col=0, row=99))
    assert not off.wall


def test_route_facts_and_distance() -> None:
    truth = fixture.build()
    steps = route_facts(truth, ((1, 4), (2, 4), (3, 4), (4, 4)))
    assert [s.end for s in steps] == [(2, 4), (3, 4), (4, 4)]
    assert steps[-1].pit_id == "hidden-pit"
    diag = route_facts(truth, ((1, 4), (2, 3)))[0]
    assert diag.diagonal and len(diag.corner) == 4 and diag.flanks == ((2, 4), (1, 3))
    assert distance_ft((1, 4), (7, 4)) == 30
    assert distance_ft((0, 0), (3, 2)) == 15
    with pytest.raises(ValueError):
        route_facts(truth, ((0, 0), (2, 0)))


def test_leaves_distance_reports_the_step() -> None:
    goblin = Token(token_id="g", glyph="G", ref="r", side="hostile", square=(3, 4))
    route = ((3, 3), (3, 2), (3, 1))
    assert leaves_distance(route, goblin, 5) == 0
    assert leaves_distance(route, goblin, 10) == 1
    assert leaves_distance(((0, 0), (0, 1)), goblin, 5) is None
    unplaced = goblin.model_copy(update={"square": None})
    assert leaves_distance(route, unplaced, 5) is None


def test_sight_walls_and_obstruction() -> None:
    truth = fixture.build()
    seen = visible_squares(truth, (1, 4))
    assert (6, 7) in seen
    assert (9, 4) not in seen  # the mill, behind a closed door and solid sketch
    # The garden wall hides A10's neighbour across it.
    behind = sight_line(truth, (1, 8), (2, 8))
    assert not behind.clear and behind.obstruction == "full"
    through_barrels = sight_line(truth, (5, 5), (5, 7))
    assert through_barrels.clear
    assert "feature:barrels" in through_barrels.passes_through
    assert through_barrels.obstruction == "half"
    past_creature = sight_line(truth, (6, 5), (6, 9))
    assert past_creature.creatures == ("goblin",)
    assert past_creature.distance_ft == 20
    assert "yard" in lit_areas(truth) and "mill" not in lit_areas(truth)


def test_lit_by_a_torch() -> None:
    truth = fixture.build()
    lit = apply(
        truth,
        SetLight(base_revision=0, thing_id="hero", lit=True),
        current_revision=0,
        seed=1,
    )
    assert lit.token("hero").carries_light  # type: ignore[union-attr]
    feature = apply(
        truth,
        SetLight(base_revision=0, thing_id="barrels", lit=True),
        current_revision=0,
        seed=1,
    )
    assert feature.feature("barrels").emits_light  # type: ignore[union-attr]
    with pytest.raises(UpdateRefused):
        apply(
            truth,
            SetLight(base_revision=0, thing_id="x", lit=True),
            current_revision=0,
            seed=1,
        )


def test_stale_base_revision_is_refused() -> None:
    truth = fixture.build()
    with pytest.raises(UpdateRefused) as exc:
        apply(
            truth,
            MarkExplored(base_revision=3, squares=((0, 0),)),
            current_revision=4,
            seed=1,
        )
    assert exc.value.reason == MAP_MOVED_ON


def test_move_token_checks_geometry() -> None:
    truth = fixture.build()

    def move(route: tuple[tuple[int, int], ...]) -> object:
        return apply(
            truth,
            MoveToken(base_revision=0, token_id="hero", route=route),
            current_revision=0,
            seed=1,
        )

    moved = move(((1, 4), (2, 4), (3, 4)))
    assert moved.token("hero").square == (3, 4)  # type: ignore[attr-defined]
    for bad, reason in [
        (((2, 4), (3, 4)), "is not at"),
        (((1, 4), (3, 4)), "is not a step"),
        (((1, 4), (2, 4), (2, 4)), "is not a step"),
        (((7, 4), (8, 4)), "is not at"),
    ]:
        with pytest.raises(UpdateRefused) as exc:
            move(bad)
        assert reason in exc.value.reason
    at_door = move(((1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4)))
    with pytest.raises(UpdateRefused) as exc:
        apply(
            at_door,
            MoveToken(base_revision=0, token_id="hero", route=((7, 4), (8, 4))),
            current_revision=0,
            seed=1,
        )
    assert "solid" in exc.value.reason
    with pytest.raises(UpdateRefused):
        move(((1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (2, 8)))  # through a wall
    with pytest.raises(UpdateRefused):
        apply(
            truth,
            MoveToken(base_revision=0, token_id="x", route=((0, 0),)),
            current_revision=0,
            seed=1,
        )
    with pytest.raises(UpdateRefused):
        move(((1, 4), (0, 4), (-1, 4)))


def test_place_and_remove_tokens_and_features() -> None:
    truth = fixture.build()
    rat = Token(
        token_id="rat", glyph="r", ref="creature:rat", side="neutral", square=(3, 3)
    )
    with_rat = apply(
        truth, PlaceToken(base_revision=0, token=rat), current_revision=0, seed=1
    )
    assert with_rat.token("rat") is not None
    for bad in [
        rat,
        rat.model_copy(update={"token_id": "rat2", "square": (1, 4)}),
        rat.model_copy(update={"token_id": "rat3", "square": None}),
        rat.model_copy(update={"token_id": "rat4", "square": (9, 4)}),
    ]:
        with pytest.raises(UpdateRefused):
            apply(
                with_rat,
                PlaceToken(base_revision=0, token=bad),
                current_revision=0,
                seed=1,
            )
    gone = apply(
        with_rat,
        RemoveToken(base_revision=0, token_id="rat"),
        current_revision=0,
        seed=1,
    )
    assert gone.token("rat") is None
    with pytest.raises(UpdateRefused):
        apply(
            gone,
            RemoveToken(base_revision=0, token_id="rat"),
            current_revision=0,
            seed=1,
        )
    well = Feature(
        feature_id="well",
        kind="other",
        label="well",
        squares=((3, 1),),
        blocks_step=True,
    )
    with_well = apply(
        truth, AddFeature(base_revision=0, feature=well), current_revision=0, seed=1
    )
    assert with_well.feature("well") is not None
    with pytest.raises(UpdateRefused):
        apply(
            with_well,
            AddFeature(base_revision=0, feature=well),
            current_revision=0,
            seed=1,
        )
    with pytest.raises(UpdateRefused):
        apply(
            truth,
            AddFeature(
                base_revision=0,
                feature=well.model_copy(
                    update={"feature_id": "w2", "squares": ((99, 99),)}
                ),
            ),
            current_revision=0,
            seed=1,
        )
    with pytest.raises(UpdateRefused):
        apply(
            truth,
            AddFeature(
                base_revision=0,
                feature=Feature(
                    feature_id="d", kind="door", edge=Edge(orient="h", col=50, row=50)
                ),
            ),
            current_revision=0,
            seed=1,
        )
    removed = apply(
        with_well,
        RemoveFeature(base_revision=0, feature_id="well"),
        current_revision=0,
        seed=1,
    )
    assert removed.feature("well") is None
    with pytest.raises(UpdateRefused):
        apply(
            removed,
            RemoveFeature(base_revision=0, feature_id="well"),
            current_revision=0,
            seed=1,
        )


def test_feature_states_are_validated() -> None:
    truth = fixture.build()
    with pytest.raises(UpdateRefused):
        apply(
            truth,
            SetFeatureState(base_revision=0, feature_id="mill-door", state="armed"),
            current_revision=0,
            seed=1,
        )
    with pytest.raises(UpdateRefused):
        apply(
            truth,
            SetFeatureState(base_revision=0, feature_id="nope", state="open"),
            current_revision=0,
            seed=1,
        )
    trap = Feature(feature_id="t", kind="trap", squares=((3, 3),), state="armed")
    with_trap = apply(
        truth, AddFeature(base_revision=0, feature=trap), current_revision=0, seed=1
    )
    sprung = apply(
        with_trap,
        SetFeatureState(base_revision=0, feature_id="t", state="sprung"),
        current_revision=0,
        seed=1,
    )
    assert sprung.feature("t").state == "sprung"  # type: ignore[union-attr]
    barrels = apply(
        truth,
        SetFeatureState(base_revision=0, feature_id="barrels", state="toppled"),
        current_revision=0,
        seed=1,
    )
    assert barrels.feature("barrels").state == "toppled"  # type: ignore[union-attr]


def test_terrain_hidden_and_explored_updates() -> None:
    truth = fixture.build()
    rubble = apply(
        truth,
        SetTerrain(base_revision=0, squares=((3, 3),), char=","),
        current_revision=0,
        seed=1,
    )
    assert rubble.char((3, 3)) == ","
    for bad in [
        SetTerrain(base_revision=0, squares=((3, 3),), char="x"),
        SetTerrain(base_revision=0, squares=((3, 3),), char=" "),
        SetTerrain(base_revision=0, squares=((9, 3),), char="."),
        SetTerrain(base_revision=0, squares=((30, 3),), char="."),
    ]:
        with pytest.raises(UpdateRefused):
            apply(truth, bad, current_revision=0, seed=1)
    for thing in ("hidden-pit", "secret-door", "lurker"):
        shown = apply(
            truth,
            SetHidden(base_revision=0, thing_id=thing, hidden=False),
            current_revision=0,
            seed=1,
        )
        assert shown != truth
    with pytest.raises(UpdateRefused):
        apply(
            truth,
            SetHidden(base_revision=0, thing_id="nope", hidden=False),
            current_revision=0,
            seed=1,
        )
    explored = apply(
        truth,
        MarkExplored(base_revision=0, squares=((9, 4),)),
        current_revision=0,
        seed=1,
    )
    assert explored.is_explored((9, 4))


def test_zones_and_relations() -> None:
    truth = fixture.build()
    with pytest.raises(UpdateRefused):
        apply(
            truth,
            SetZone(base_revision=0, zone=Zone(zone_id="z", label="z", area_id="nope")),
            current_revision=0,
            seed=1,
        )
    with pytest.raises(UpdateRefused):
        apply(
            truth,
            Relate(
                base_revision=0,
                relation=Relation(subject="nope", relation="near", object="yard"),
            ),
            current_revision=0,
            seed=1,
        )
    with pytest.raises(UpdateRefused) as exc:
        apply(
            truth,
            Relate(
                base_revision=0,
                relation=Relation(
                    subject="yard", relation="joined_by", object="mill", via="barrels"
                ),
            ),
            current_revision=0,
            seed=1,
        )
    assert "already" in exc.value.reason


def test_content_hash_is_stable_and_sensitive() -> None:
    a, b = fixture.build(), fixture.build()
    assert content_hash(a) == content_hash(b)
    changed = apply_all(
        a,
        [MarkExplored(base_revision=0, squares=((9, 9),))],
        current_revision=0,
        seed=1,
    )
    assert content_hash(changed) != content_hash(a)


def test_blank_snapshot_is_all_unspecified() -> None:
    snap = blank_snapshot(3, 2)
    assert snap.terrain == ("   ", "   ")
    assert len(snap.hwalls) == 3 and len(snap.vwalls[0]) == 4
    assert not snap.is_explored((0, 0)) and not snap.is_explored((5, 5))
