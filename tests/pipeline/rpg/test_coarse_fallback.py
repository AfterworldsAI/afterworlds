"""Coarse fallback after two failed refinements (issue #211, acceptance 8).

A move whose outcome the coarse facts settle resolves on them; a move with
materially different possible outcomes is held with the record unchanged.
"""

from __future__ import annotations

import pytest

from afterworlds.mapper.models import (
    Area,
    CoarsePlacement,
    Feature,
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
from afterworlds.mapper.refine import REFINE_ATTEMPTS, refine_with_retry
from afterworlds.mapper.updates import apply_all
from afterworlds.pipeline.rpg.coarse_fallback import (
    NO_WAY,
    NO_ZONE,
    NOT_PLACED,
    SEVERAL_WAYS,
    SOMEONE_THERE,
    CoarseMove,
    refine_or_settle,
    resolve_coarse,
)

SEED = 5


def _sketch(*, door_state: str | None = "closed", extra: list[object] = ()) -> Snapshot:  # type: ignore[assignment]
    snap = blank_snapshot(10, 6).model_copy(
        update={
            "areas": (
                Area(
                    area_id="hall",
                    label="the hall",
                    level="coarse",
                    bounds=(0, 0, 5, 6),
                ),
                Area(
                    area_id="vault",
                    label="the vault",
                    level="coarse",
                    bounds=(5, 0, 5, 6),
                ),
            ),
            "features": (
                (
                    Feature(
                        feature_id="vault-door",
                        kind="door",
                        label="vault door",
                        state=door_state,
                    ),
                )
                if door_state is not None
                else ()
            ),
        }
    )
    updates = [
        SetZone(
            base_revision=0,
            zone=Zone(zone_id="hall-main", label="the hall", area_id="hall"),
        ),
        SetZone(
            base_revision=0,
            zone=Zone(zone_id="vault-main", label="the vault", area_id="vault"),
        ),
        PlaceCoarse(
            base_revision=0,
            token=Token(token_id="kael", glyph="K", ref="character:k", side="party"),
            placement=CoarsePlacement(token_id="kael", zone_id="hall-main"),
        ),
        Relate(
            base_revision=0,
            relation=Relation(
                subject="hall",
                relation="joined_by",
                object="vault",
                via="vault-door" if door_state is not None else None,
            ),
        ),
        *extra,
    ]
    return apply_all(snap, updates, current_revision=0, seed=SEED)  # type: ignore[arg-type]


#: A refinement that can never succeed: its pit lies outside the vault.
BAD = RefineArea(
    base_revision=0,
    area="vault",
    pits=(Pit(pit_id="p", squares=((1, 1),), depth_ft=10),),
)
MOVE = CoarseMove(token_id="kael", to_area="vault")


def test_refinement_is_tried_twice_with_fresh_seeds_before_falling_back() -> None:
    refined, reasons = refine_with_retry(_sketch(), BAD, seed=SEED)
    assert refined is None
    assert len(reasons) == REFINE_ATTEMPTS == 2
    ok, none = refine_with_retry(
        _sketch(), RefineArea(base_revision=0, area="vault"), seed=SEED
    )
    assert ok is not None and none == ()
    assert ok.area("vault").level == "gridded"  # type: ignore[union-attr]


def test_a_closed_door_settles_the_move_at_the_door() -> None:
    snap = _sketch()
    result = refine_or_settle(snap, BAD, MOVE, seed=SEED, revision=0)
    assert result.refined is None and len(result.reasons) == 2
    outcome = result.coarse
    assert outcome is not None and outcome.status == "stopped"
    assert outcome.stopped_by == "the vault door is closed"
    after = apply_all(snap, outcome.updates, current_revision=0, seed=SEED)
    placement = after.coarse.placements[-1]
    assert (placement.zone_id, placement.at) == ("hall-main", "vault-door")
    assert after.feature("vault-door").state == "closed"  # type: ignore[union-attr]
    assert outcome.writer_facts()["coarse"] is True


@pytest.mark.parametrize("door_state", ["open", None])
def test_an_open_way_settles_the_move_in_the_far_area(door_state: str | None) -> None:
    snap = _sketch(door_state=door_state)
    outcome = resolve_coarse(snap, MOVE, revision=0)
    assert outcome.status == "arrived"
    after = apply_all(snap, outcome.updates, current_revision=0, seed=SEED)
    assert [p.zone_id for p in after.coarse.placements if p.token_id == "kael"] == [
        "vault-main"
    ]


def _goblin() -> PlaceCoarse:
    return PlaceCoarse(
        base_revision=0,
        token=Token(
            token_id="g", glyph="G", ref="creature:g", side="hostile", hidden=True
        ),
        placement=CoarsePlacement(token_id="g", zone_id="vault-main"),
    )


def _second_way() -> Relate:
    return Relate(
        base_revision=0,
        relation=Relation(subject="vault", relation="joined_by", object="hall"),
    )


@pytest.mark.parametrize(
    ("extra", "reason"),
    [([_goblin()], SOMEONE_THERE), ([_second_way()], SEVERAL_WAYS)],
    ids=["a-creature-could-react", "two-routes"],
)
def test_unsettled_moves_are_held_with_nothing_changed(
    extra: list[object], reason: str
) -> None:
    snap = _sketch(extra=extra)
    result = refine_or_settle(snap, BAD, MOVE, seed=SEED, revision=0)
    assert result.coarse is not None
    assert (result.coarse.status, result.coarse.held) == ("held", reason)
    assert result.coarse.updates == ()


def test_other_holds() -> None:
    snap = _sketch()
    assert (
        resolve_coarse(snap, CoarseMove("nobody", "vault"), revision=0).held
        == NOT_PLACED
    )
    assert resolve_coarse(snap, CoarseMove("kael", "attic"), revision=0).held == NO_WAY
    no_zone = snap.model_copy(
        update={
            "coarse": snap.coarse.model_copy(
                update={
                    "zones": tuple(z for z in snap.coarse.zones if z.area_id != "vault")
                }
            )
        }
    )
    opened = no_zone.model_copy(
        update={"features": (no_zone.features[0].model_copy(update={"state": "open"}),)}
    )
    assert resolve_coarse(opened, MOVE, revision=0).held == NO_ZONE
