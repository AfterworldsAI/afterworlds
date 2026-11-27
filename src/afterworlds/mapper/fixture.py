"""The M1 hand-built encounter: the mill yard (issue #211, milestone M1).

Geography goes in through the same typed updates production uses; creatures
come from ``create_creature`` and are passed in by reference. The yard is
gridded; the mill beyond its door stays a coarse sketch.

Layout (12 by 10 squares, A1 top left)::

    yard  A1-H10, outdoors, worked ground
    mill  I1-L10, indoors, coarse, joined by the mill door on the line
          between H5 and I5 (closed)
    hero  B5; goblin warrior at G8 behind barrels at F7 (half obstruction)
    pit   B8, visible, 10 ft deep
    hidden: a 10-ft pit at E5 that looks like the ground around it, a goblin
            in the brush at A10, and a secret door in the garden wall
            between B9 and C9

Two routes lead from B5 to the mill door (acceptance 6): straight along row
5, over the hidden pit, or by way of E3, which reaches the door.
"""

from __future__ import annotations

from dataclasses import dataclass

from afterworlds.mapper.models import (
    Area,
    CoarsePlacement,
    Edge,
    Feature,
    Pit,
    PlaceCoarse,
    PlaceToken,
    RefineArea,
    Relate,
    Relation,
    Snapshot,
    SpatialUpdate,
    Token,
    Zone,
    blank_snapshot,
)
from afterworlds.mapper.updates import apply_all

WIDTH, HEIGHT = 12, 10
SEED = 211
PLACE_KEY = "mill-yard"
LABEL = "The mill yard"
HERO = "hero"
GOBLIN = "goblin"
LURKER = "lurker"
HIDDEN_PIT = "hidden-pit"
SECRET_DOOR = "secret-door"
MILL_DOOR = "mill-door"


@dataclass(frozen=True)
class FixtureRefs:
    hero_ref: str = "character:hero"
    goblin_ref: str = "creature:goblin"
    lurker_ref: str = "creature:lurker"


def base_snapshot(*, with_hidden: bool = True) -> Snapshot:
    """The empty map with the two areas, before any update."""
    blank = blank_snapshot(WIDTH, HEIGHT)
    return blank.model_copy(
        update={
            "areas": (
                Area(
                    area_id="yard",
                    label="the yard",
                    level="coarse",
                    setting="worked",
                    indoors=False,
                    bounds=(0, 0, 8, 10),
                ),
                Area(
                    area_id="mill",
                    label="the mill",
                    level="coarse",
                    setting="worked",
                    indoors=True,
                    bounds=(8, 0, 4, 10),
                    description="a dusty mill room",
                ),
            ),
        }
    )


def updates(refs: FixtureRefs, *, with_hidden: bool = True) -> list[SpatialUpdate]:
    """The typed updates that build the encounter, revision by revision
    (each list item is applied at ``base_revision`` 0 in one revision)."""
    terrain = tuple("." * 8 for _ in range(HEIGHT))
    mill_door = Feature(
        feature_id=MILL_DOOR,
        kind="door",
        label="mill door",
        edge=Edge(orient="v", col=8, row=4),
        state="closed",
        fits="medium",
        blocks_sight="full",
    )
    features: list[Feature] = [
        Feature(
            feature_id="barrels",
            kind="other",
            label="barrels",
            squares=((5, 6),),
            blocks_step=True,
            cover_geometry="half",
            blocks_sight="partial",
        ),
    ]
    walls = [Edge(orient="v", col=2, row=r) for r in (7, 9)]
    pits = [Pit(pit_id="open-pit", squares=((1, 7),), depth_ft=10)]
    if with_hidden:
        features.append(
            Feature(
                feature_id=SECRET_DOOR,
                kind="secret_door",
                label="secret door",
                edge=Edge(orient="v", col=2, row=8),
                state="closed",
                hidden=True,
            )
        )
        pits.append(Pit(pit_id=HIDDEN_PIT, squares=((4, 4),), depth_ft=10, hidden=True))
    else:
        walls.append(Edge(orient="v", col=2, row=8))
    out: list[SpatialUpdate] = [
        PlaceCoarse(
            base_revision=0,
            token=Token(
                token_id=HERO, glyph="K", ref=refs.hero_ref, side="party", label="Kael"
            ),
            placement=CoarsePlacement(
                token_id=HERO, zone_id="yard-west", text="in the west of the yard"
            ),
        ),
        Relate(
            base_revision=0,
            relation=Relation(
                subject="yard", relation="joined_by", object="mill", via=MILL_DOOR
            ),
        ),
        RefineArea(
            base_revision=0,
            area="yard",
            terrain=terrain,
            walls=tuple(walls),
            pits=tuple(pits),
            features=(mill_door, *features),
            placements=((HERO, (1, 4)),),
        ),
        PlaceToken(
            base_revision=0,
            token=Token(
                token_id=GOBLIN,
                glyph="G",
                ref=refs.goblin_ref,
                side="hostile",
                label="goblin warrior",
                square=(6, 7),
            ),
        ),
    ]
    if with_hidden:
        out.append(
            PlaceToken(
                base_revision=0,
                token=Token(
                    token_id=LURKER,
                    glyph="g",
                    ref=refs.lurker_ref,
                    side="hostile",
                    label="goblin",
                    square=(0, 9),
                    hidden=True,
                ),
            )
        )
    return out


def zones() -> list[SpatialUpdate]:
    from afterworlds.mapper.models import SetZone

    return [
        SetZone(
            base_revision=0,
            zone=Zone(zone_id="yard-west", label="west yard", area_id="yard"),
        )
    ]


def build(refs: FixtureRefs | None = None, *, with_hidden: bool = True) -> Snapshot:
    """The encounter's truth as one snapshot (for tests and the seeder)."""
    refs = refs or FixtureRefs()
    snap = base_snapshot(with_hidden=with_hidden)
    snap = apply_all(snap, zones(), current_revision=0, seed=SEED)
    snap = apply_all(
        snap, updates(refs, with_hidden=with_hidden), current_revision=0, seed=SEED
    )
    from afterworlds.mapper.models import MarkExplored

    yard = [(c, r) for r in range(HEIGHT) for c in range(8)]
    return apply_all(
        snap,
        [MarkExplored(base_revision=0, squares=tuple(yard))],
        current_revision=0,
        seed=SEED,
    )
