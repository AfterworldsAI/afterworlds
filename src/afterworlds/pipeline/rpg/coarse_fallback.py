"""Coarse fallback for a move into an area that won't refine (issue #211,
acceptance 8; map generation doc, Draft 3; movement doc, "Coarse fallback").

When refinement fails twice, Sojourn resolves a move on coarse facts only if
those facts settle its outcome. A move whose outcome they don't settle is held
with the record unchanged, and no reaction is awarded or lost.

What counts as settled is this module's reading of the docs (an inference to
surface in the PR):

* exactly one recorded way between the two areas (a ``joined_by`` relation);
* no creature other than the mover in either area, so leaving a reach can't
  be in play;
* the way is a door whose recorded state is open (the mover arrives in the
  far area), or one whose recorded state is anything else (the mover reaches
  the door and stops there, door unchanged), or an opening with no door.

Coarse moves count no movement cost: no squares exist to price.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from afterworlds.mapper.models import (
    CoarsePlacement,
    PlaceCoarse,
    RefineArea,
    Relation,
    RemoveToken,
    Snapshot,
    SpatialUpdate,
    Token,
)
from afterworlds.mapper.refine import refine_with_retry

#: Player-safe reasons a coarse move is held.
NOT_PLACED = "the mover isn't placed in an area"
NO_WAY = "no recorded way between those areas"
SEVERAL_WAYS = "more than one way there, and the sketch doesn't say which"
SOMEONE_THERE = "someone else is in the way, and the sketch can't say where"
NO_ZONE = "the far side has no recorded place to stand"


@dataclass(frozen=True)
class CoarseMove:
    """A move from the mover's area to another area, by coarse facts."""

    token_id: str
    to_area: str


@dataclass(frozen=True)
class CoarseOutcome:
    status: str  # "arrived", "stopped" or "held"
    token_id: str
    held: str | None = None
    stopped_by: str | None = None
    updates: tuple[SpatialUpdate, ...] = field(default=())

    def writer_facts(self) -> dict[str, object]:
        return {
            "status": self.status,
            "coarse": True,
            "held": self.held,
            "stopped_by": self.stopped_by,
        }


def _area_of(truth: Snapshot, token_id: str) -> str | None:
    token = truth.token(token_id)
    if token is None:
        return None
    if token.square is not None:
        area = truth.area_at(token.square)
        return area.area_id if area is not None else None
    zones = {z.zone_id: z.area_id for z in truth.coarse.zones}
    for p in truth.coarse.placements:
        if p.token_id == token_id:
            return zones.get(p.zone_id)
    return None


def _ways(truth: Snapshot, a: str, b: str) -> list[Relation]:
    return [
        r
        for r in truth.coarse.relations
        if r.relation == "joined_by" and {r.subject, r.object} == {a, b}
    ]


def resolve_coarse(
    truth: Snapshot, move: CoarseMove, *, revision: int
) -> CoarseOutcome:
    """Settle *move* on coarse facts, or hold it with nothing changed."""

    def held(reason: str) -> CoarseOutcome:
        return CoarseOutcome(status="held", token_id=move.token_id, held=reason)

    token = truth.token(move.token_id)
    here = _area_of(truth, move.token_id)
    if token is None or here is None:
        return held(NOT_PLACED)
    ways = _ways(truth, here, move.to_area)
    if not ways:
        return held(NO_WAY)
    if len(ways) > 1:
        return held(SEVERAL_WAYS)
    others = [
        t.token_id
        for t in truth.tokens
        if t.token_id != move.token_id
        and _area_of(truth, t.token_id) in (here, move.to_area)
    ]
    if others:
        return held(SOMEONE_THERE)
    way = ways[0]
    door = truth.feature(way.via) if way.via is not None else None
    bare = token.model_copy(update={"square": None})
    if door is not None and door.state != "open":
        zone = next(
            (
                p.zone_id
                for p in truth.coarse.placements
                if p.token_id == token.token_id
            ),
            None,
        ) or next(
            (z.zone_id for z in truth.coarse.zones if z.area_id == here),
            None,
        )
        if zone is None:
            return held(NO_ZONE)
        label = door.label or door.feature_id
        return CoarseOutcome(
            status="stopped",
            token_id=move.token_id,
            stopped_by=f"the {label} is {door.state or 'closed'}",
            updates=_place(bare, zone, door.feature_id, f"at the {label}", revision),
        )
    target = next(
        (z.zone_id for z in truth.coarse.zones if z.area_id == move.to_area), None
    )
    if target is None:
        return held(NO_ZONE)
    return CoarseOutcome(
        status="arrived",
        token_id=move.token_id,
        updates=_place(bare, target, None, "", revision),
    )


def _place(
    token: Token, zone: str, at: str | None, text: str, revision: int
) -> tuple[SpatialUpdate, ...]:
    return (
        RemoveToken(base_revision=revision, token_id=token.token_id),
        PlaceCoarse(
            base_revision=revision,
            token=token,
            placement=CoarsePlacement(
                token_id=token.token_id, zone_id=zone, at=at, text=text
            ),
        ),
    )


@dataclass(frozen=True)
class RefineOrSettle:
    """Either the refined snapshot, or the coarse outcome after two refused
    refinements (with their reasons)."""

    refined: Snapshot | None
    coarse: CoarseOutcome | None
    reasons: tuple[str, ...] = ()


def refine_or_settle(
    truth: Snapshot,
    refine: RefineArea,
    move: CoarseMove,
    *,
    seed: int,
    revision: int,
) -> RefineOrSettle:
    """Refine the area a move needs; after two refusals, settle the move on
    coarse facts or hold it."""
    refined, reasons = refine_with_retry(truth, refine, seed=seed)
    if refined is not None:
        return RefineOrSettle(refined=refined, coarse=None)
    return RefineOrSettle(
        refined=None,
        coarse=resolve_coarse(truth, move, revision=revision),
        reasons=reasons,
    )


__all__ = [
    "NOT_PLACED",
    "NO_WAY",
    "NO_ZONE",
    "SEVERAL_WAYS",
    "SOMEONE_THERE",
    "CoarseMove",
    "CoarseOutcome",
    "RefineOrSettle",
    "refine_or_settle",
    "resolve_coarse",
]
