"""Cover and range claims checked against geometry (issue #211, acceptance 11;
movement doc, "Cover and range"; CRD Issue 15c OD-15c-1 note).

The mapper reports geometric facts only. Sojourn decides every rules outcome
(Cover degree, range band, Disadvantage) and may not contradict those facts.
This check refuses a claim that does; it decides nothing itself.

A claim contradicts geometry when (this module's reading, to surface in the
PR):

* its distance differs from the measured distance between the two tokens;
* it gives Total Cover while the line between them is clear, or less than
  Total Cover while the line is fully blocked;
* it gives any Cover while nothing at all stands in the line;
* it gives less Cover than an object in the line screens by itself.

A creature in the line screens half by geometry, but whether it gives Cover is
left to Sojourn, so a creature alone never makes a lower claim a
contradiction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from afterworlds.mapper.geometry import distance_ft, sight_line
from afterworlds.mapper.models import Snapshot, token_squares

CoverClaim = Literal["none", "half", "three_quarters", "total"]

_ORDER: tuple[CoverClaim, ...] = ("none", "half", "three_quarters", "total")
_FROM_GEOMETRY: dict[str, CoverClaim] = {
    "none": "none",
    "half": "half",
    "three_quarters": "three_quarters",
    "full": "total",
}


class ClaimContradictsGeometry(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class SpatialClaim:
    """What Sojourn's adjudication asserts about one attacker and target."""

    attacker: str
    target: str
    cover: CoverClaim | None = None
    distance_ft: int | None = None


def check_claim(truth: Snapshot, claim: SpatialClaim) -> None:
    """Raise :class:`ClaimContradictsGeometry` when *claim* contradicts the
    record's geometry; return quietly otherwise."""
    a, b = truth.token(claim.attacker), truth.token(claim.target)
    if a is None or b is None or a.square is None or b.square is None:
        raise ClaimContradictsGeometry("both creatures need squares on the map")
    if claim.distance_ft is not None:
        measured = min(
            distance_ft(x, y) for x in token_squares(a) for y in token_squares(b)
        )
        if claim.distance_ft != measured:
            raise ClaimContradictsGeometry(
                f"they are {measured} ft apart, not {claim.distance_ft} ft"
            )
    if claim.cover is None:
        return
    line = sight_line(truth, a.square, b.square, ignore=(a.token_id, b.token_id))
    rank = _ORDER.index(claim.cover)
    if not line.clear:
        if claim.cover != "total":
            raise ClaimContradictsGeometry("the line between them is fully blocked")
        return
    if claim.cover == "total":
        raise ClaimContradictsGeometry("the line between them is clear")
    if not line.passes_through:
        if rank > 0:
            raise ClaimContradictsGeometry("nothing stands between them")
        return
    objects: CoverClaim = "none"
    for item in line.passes_through:
        if item.startswith("feature:"):
            feature = truth.feature(item.split(":", 1)[1])
            if feature is not None:
                degree = _FROM_GEOMETRY[feature.cover_geometry]
                if _ORDER.index(degree) > _ORDER.index(objects):
                    objects = degree
    if rank < _ORDER.index(objects):
        raise ClaimContradictsGeometry(
            f"an object in the line screens {objects.replace('_', '-')}"
        )


__all__ = [
    "ClaimContradictsGeometry",
    "CoverClaim",
    "SpatialClaim",
    "check_claim",
]
