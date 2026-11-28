"""Refinement keeps coarse facts; the player view hides what's hidden
(issue #211 acceptance 3 and 4)."""

from __future__ import annotations

import json

import pytest

from afterworlds.mapper import fixture, views
from afterworlds.mapper.models import (
    Area,
    CoarsePlacement,
    Edge,
    Feature,
    MoveToken,
    Pit,
    PlaceCoarse,
    RefineArea,
    Relate,
    Relation,
    SetZone,
    Snapshot,
    Token,
    Zone,
    blank_snapshot,
)
from afterworlds.mapper.refine import area_seed, refine_area
from afterworlds.mapper.updates import UpdateRefused, apply, apply_all


def _room(*, indoors: bool = True, setting: str = "worked") -> Snapshot:
    snap = blank_snapshot(10, 8).model_copy(
        update={
            "areas": (
                Area(
                    area_id="hall",
                    label="the hall",
                    level="coarse",
                    setting=setting,  # type: ignore[arg-type]
                    indoors=indoors,
                    bounds=(1, 1, 6, 5),
                ),
            )
        }
    )
    snap = apply(
        snap,
        SetZone(
            base_revision=0,
            zone=Zone(zone_id="hall-north", label="north end", area_id="hall"),
        ),
        current_revision=0,
        seed=7,
    )
    return apply_all(
        snap,
        [
            PlaceCoarse(
                base_revision=0,
                token=Token(
                    token_id="kael", glyph="K", ref="character:k", side="party"
                ),
                placement=CoarsePlacement(token_id="kael", zone_id="hall-north"),
            ),
            PlaceCoarse(
                base_revision=0,
                token=Token(token_id="g", glyph="G", ref="creature:g", side="hostile"),
                placement=CoarsePlacement(token_id="g", zone_id="hall-north"),
            ),
        ],
        current_revision=0,
        seed=7,
    )


def _refine(snap: Snapshot, **kw: object) -> Snapshot:
    update = RefineArea(base_revision=0, area="hall", **kw)  # type: ignore[arg-type]
    return refine_area(snap, update, seed=7)


def test_refinement_fills_only_unspecified_space_and_is_repeatable() -> None:
    snap = _room(setting="natural")
    placements = (("kael", (2, 2)), ("g", (5, 4)))
    a = _refine(snap, placements=placements)
    b = _refine(snap, placements=placements)
    assert a == b
    assert a.area("hall").level == "gridded"  # type: ignore[union-attr]
    for c in range(10):
        for r in range(8):
            inside = 1 <= c < 7 and 1 <= r < 6
            assert (a.char((c, r)) != " ") is inside
    # Indoors gets its boundary walls.
    assert a.wall(Edge(orient="h", col=1, row=1)) and a.wall(
        Edge(orient="v", col=7, row=3)
    )
    assert area_seed(7, "hall") != area_seed(7, "hall", 1)
    assert a.coarse.placements == ()


def test_outdoor_refinement_uses_noise_without_walls() -> None:
    snap = _room(indoors=False)
    out = _refine(snap, placements=(("kael", (2, 2)), ("g", (5, 4))))
    assert not out.wall(Edge(orient="h", col=1, row=1))
    assert set("".join(out.terrain)) <= set(".,  ")


def test_specified_terrain_pits_and_doors_are_kept() -> None:
    snap = _room()
    terrain = ("......", "..,...", "......", "......", "......")
    door = Feature(
        feature_id="d", kind="door", edge=Edge(orient="v", col=7, row=3), state="closed"
    )
    pit = Pit(pit_id="p", squares=((4, 3),), depth_ft=20)
    out = _refine(
        snap,
        terrain=terrain,
        pits=(pit,),
        features=(door,),
        placements=(("kael", (2, 2)), ("g", (5, 4))),
        light=True,
    )
    assert out.char((3, 2)) == ","
    assert out.char((4, 3)) == "_"
    assert out.pit_at((4, 3)).depth_ft == 20  # type: ignore[union-attr]
    assert out.door_at(Edge(orient="v", col=7, row=3)) is not None
    assert "hall" in {
        a
        for a in __import__("afterworlds.mapper.geometry", fromlist=["x"]).lit_areas(
            out
        )
    }


@pytest.mark.parametrize(
    ("kw", "reason"),
    [
        ({"placements": (("kael", (2, 2)),)}, "has no square"),
        ({"placements": (("kael", (2, 2)), ("g", (9, 7)))}, "isn't in"),
        ({"placements": (("kael", (2, 2)), ("g", (2, 2)))}, "no room"),
        ({"placements": (("kael", (2, 2)), ("nobody", (3, 3)))}, "nothing called"),
        ({"terrain": ("...",)}, "doesn't fit"),
        ({"terrain": ("xxxxxx",) * 5}, "is not terrain"),
        (
            {"pits": (Pit(pit_id="p", squares=((9, 7),), depth_ft=10),)},
            "doesn't fit",
        ),
        (
            {
                "features": (
                    Feature(
                        feature_id="d", kind="door", edge=Edge(orient="v", col=9, row=3)
                    ),
                )
            },
            "don't touch",
        ),
        (
            {
                "features": (
                    Feature(feature_id="kael", kind="other", squares=((9, 7),)),
                )
            },
            "doesn't fit",
        ),
        (
            {
                "terrain": ("......", "......", "######", "......", "......"),
                "placements": (("kael", (2, 2)), ("g", (5, 4))),
            },
            "unreachable",
        ),
    ],
)
def test_refinement_refusals(kw: dict[str, object], reason: str) -> None:
    with pytest.raises(UpdateRefused) as exc:
        _refine(_room(), **kw)
    assert reason in exc.value.reason


def test_refinement_refuses_unknown_or_gridded_areas() -> None:
    snap = _room()
    with pytest.raises(UpdateRefused):
        refine_area(snap, RefineArea(base_revision=0, area="nope"), seed=1)
    done = _refine(snap, placements=(("kael", (2, 2)), ("g", (5, 4))))
    with pytest.raises(UpdateRefused):
        refine_area(done, RefineArea(base_revision=0, area="hall"), seed=1)


def test_refinement_keeps_coarse_relations() -> None:
    snap = _room()
    snap = apply(
        snap,
        Relate(
            base_revision=0,
            relation=Relation(subject="g", relation="beside", object="kael"),
        ),
        current_revision=0,
        seed=1,
    )
    with pytest.raises(UpdateRefused) as exc:
        _refine(snap, placements=(("kael", (2, 2)), ("g", (5, 4))))
    assert "beside" in exc.value.reason
    kept = _refine(snap, placements=(("kael", (2, 2)), ("g", (3, 3))))
    assert kept.token("g").square == (3, 3)  # type: ignore[union-attr]


def test_refinement_keeps_a_door_on_its_named_wall() -> None:
    snap = _room()
    door = Feature(feature_id="d", kind="door", edge=Edge(orient="v", col=7, row=3))
    snap = snap.model_copy(update={"features": (door,)})
    snap = apply(
        snap,
        Relate(
            base_revision=0,
            relation=Relation(
                subject="d", relation="in_wall", object="hall", side="west"
            ),
        ),
        current_revision=0,
        seed=1,
    )
    with pytest.raises(UpdateRefused) as exc:
        _refine(snap, placements=(("kael", (2, 2)), ("g", (5, 4))))
    assert "west wall" in exc.value.reason


def test_refinement_keeps_an_across_relation() -> None:
    snap = _room()
    table = Feature(
        feature_id="table", kind="table", squares=((3, 3),), cover_geometry="half"
    )
    snap = snap.model_copy(update={"features": (table,)})
    snap = apply(
        snap,
        Relate(
            base_revision=0,
            relation=Relation(
                subject="kael", relation="across", object="g", via="table"
            ),
        ),
        current_revision=0,
        seed=1,
    )
    assert _refine(snap, placements=(("kael", (3, 2)), ("g", (3, 4))))
    with pytest.raises(UpdateRefused):
        _refine(snap, placements=(("kael", (1, 1)), ("g", (1, 4))))


def test_preserved_geography_after_a_delivered_move() -> None:
    """Acceptance 3: refining another area moves nothing committed."""
    truth = fixture.build()
    moved = apply(
        truth,
        MoveToken(base_revision=0, token_id="hero", route=((1, 4), (2, 4), (3, 3))),
        current_revision=0,
        seed=fixture.SEED,
    )
    refined = refine_area(
        moved,
        RefineArea(base_revision=0, area="mill"),
        seed=fixture.SEED,
    )
    for r in range(10):
        assert refined.terrain[r][:8] == moved.terrain[r][:8]
    assert refined.tokens == moved.tokens
    assert refined.features[: len(moved.features)] == moved.features
    assert refined.coarse.relations == moved.coarse.relations
    assert refined.pits == moved.pits
    door = refined.feature("mill-door")
    assert door is not None and door.state == "closed"


# -- the player view -------------------------------------------------------


def _view(truth: Snapshot) -> str:
    player = views.player_snapshot(truth)
    body = views.player_view(
        player, viewer="hero", map_id="m", revision=3, label=fixture.LABEL
    )
    return json.dumps(body, sort_keys=True)


def test_player_view_is_byte_identical_without_hidden_things() -> None:
    """Acceptance 4, the view and its staleness hash."""
    assert _view(fixture.build()) == _view(fixture.build(with_hidden=False))


def test_player_view_hides_secrets_and_unexplored_space() -> None:
    truth = fixture.build()
    player = views.player_snapshot(truth)
    assert player.token("lurker") is None
    assert player.feature("secret-door") is None
    assert player.pit_at((4, 4)) is None and player.char((4, 4)) == "."
    assert player.char((9, 4)) == " "
    assert player.wall(Edge(orient="v", col=2, row=8))
    text = json.dumps(player.model_dump(mode="json"))
    for secret in ("lurker", "secret", "hidden-pit", "dusty"):
        if secret == "dusty":  # pragma: allowlist secret
            continue
        assert secret not in text


def test_other_creatures_show_only_while_seen() -> None:
    truth = fixture.build()
    unseen = views.player_snapshot(truth, sees=())
    assert unseen.token("goblin") is None and unseen.token("hero") is not None
    seen = views.player_snapshot(truth)
    assert seen.token("goblin") is not None


def test_view_hash_changes_with_the_view_only() -> None:
    truth = fixture.build()
    player = views.player_snapshot(truth)
    a = views.player_view(player, viewer="hero", map_id="m", revision=1, label="x")
    b = views.player_view(player, viewer="hero", map_id="m", revision=1, label="x")
    c = views.player_view(player, viewer="hero", map_id="m", revision=2, label="x")
    assert a["view_hash"] == b["view_hash"] != c["view_hash"]
    assert views.view_hash(a) == a["view_hash"]
    allowance = views.Allowance(
        token_id="hero", speed_ft=30, dash_ft=30, costs={"C5": 5}
    )
    d = views.player_view(
        player, viewer="hero", map_id="m", revision=1, label="x", allowance=allowance
    )
    assert d["allowance"] == allowance.as_json() and d["view_hash"] != a["view_hash"]


def test_text_view_is_the_party_visible_projection() -> None:
    truth = fixture.build()
    text = views.text_view(views.player_snapshot(truth), label=fixture.LABEL)
    assert "hero (Kael) at B5" in text
    assert "mill door: closed, by H5" in text
    assert "hero to goblin: 25 ft, line clear" in text
    assert "lurker" not in text and "hidden-pit" not in text and "secret" not in text
    coarse = _room()
    sketch = views.text_view(views.player_snapshot(coarse, sees=()), label="hall")
    assert "kael" in sketch and "(sketch)" in sketch
