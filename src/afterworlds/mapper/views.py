"""What the Sojourner may see (data model, The player view; issue #211).

The server builds the player view from the committed revision. The browser
is never sent the truth to hide: hidden features, pits and creatures are
taken out here, unexplored squares are blank, and other creatures appear only
while the party sees them. A secret door's line is already a wall in the wall
layer, so hiding the door leaves a plain wall; a hidden pit's squares show
its ``disguise``.

Previews, warnings, refusal reasons and the staleness hash are all computed
from :func:`player_snapshot`, so a map with hidden things gives the same bytes
as the same map without them (acceptance 4).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, field

from afterworlds.mapper import coords
from afterworlds.mapper.geometry import (
    distance_to_token_ft,
    is_door,
    lit_areas,
    sight_line,
    visible_squares,
)
from afterworlds.mapper.models import Snapshot, Square, Token, token_squares

PARTY = "party"


def party_sight(truth: Snapshot) -> frozenset[Square]:
    """Squares the party sees now: geometric sight from each party token,
    limited to lit areas and the squares beside the viewer (v1 light is all or
    nothing per room; senses beyond that are Sojourn's)."""
    lit = lit_areas(truth)
    seen: set[Square] = set()
    for t in truth.tokens:
        if t.side != PARTY or t.square is None or t.hidden:
            continue
        for s in visible_squares(truth, t.square):
            area = truth.area_at(s)
            near = max(abs(s[0] - t.square[0]), abs(s[1] - t.square[1])) <= 1
            if near or (area is not None and area.area_id in lit):
                seen.add(s)
    return frozenset(seen)


def player_snapshot(
    truth: Snapshot, *, sees: Iterable[Square] | None = None
) -> Snapshot:
    """The truth with everything the party doesn't know taken out.

    *sees* is the set of squares the party sees now (default
    :func:`party_sight`); party tokens are always shown, other creatures only
    when one of their squares is seen."""
    seen = frozenset(party_sight(truth) if sees is None else sees)
    known = {
        (c, r)
        for r in range(truth.height)
        for c in range(truth.width)
        if truth.is_explored((c, r)) or (c, r) in seen
    }

    terrain = [list(" " * truth.width) for _ in range(truth.height)]
    for c, r in known:
        terrain[r][c] = truth.terrain[r][c]
    pits = []
    for p in truth.pits:
        if p.hidden:
            for c, r in p.squares:
                if (c, r) in known:
                    terrain[r][c] = p.disguise
        elif any(s in known for s in p.squares):
            pits.append(p)

    def touches_known(a: Square, b: Square) -> bool:
        return a in known or b in known

    hwalls = [list(" " * truth.width) for _ in range(truth.height + 1)]
    for r in range(truth.height + 1):
        for c in range(truth.width):
            if truth.hwalls[r][c] == "-" and touches_known((c, r - 1), (c, r)):
                hwalls[r][c] = "-"
    vwalls = [list(" " * (truth.width + 1)) for _ in range(truth.height)]
    for r in range(truth.height):
        for c in range(truth.width + 1):
            if truth.vwalls[r][c] == "|" and touches_known((c - 1, r), (c, r)):
                vwalls[r][c] = "|"

    features = []
    for f in truth.features:
        if f.hidden:
            continue
        if f.edge is not None:
            if touches_known(*f.edge.sides()):
                features.append(f)
        elif any(s in known for s in f.squares):
            features.append(f)

    def shown(t: Token) -> bool:
        if t.hidden:
            return False
        if t.side == PARTY:
            return True
        return any(s in seen for s in token_squares(t))

    tokens = tuple(t for t in truth.tokens if shown(t))
    token_ids = {t.token_id for t in tokens}
    visible_ids = (
        {f.feature_id for f in features}
        | {p.pit_id for p in pits}
        | token_ids
        | {a.area_id for a in truth.areas}
        | {z.zone_id for z in truth.coarse.zones}
    )
    coarse = truth.coarse.model_copy(
        update={
            "relations": tuple(
                rel
                for rel in truth.coarse.relations
                if rel.subject in visible_ids
                and rel.object in visible_ids
                and (rel.via is None or rel.via in visible_ids)
            ),
            "placements": tuple(
                p for p in truth.coarse.placements if p.token_id in token_ids
            ),
        }
    )
    return truth.model_copy(
        update={
            "terrain": tuple("".join(r) for r in terrain),
            "hwalls": tuple("".join(r) for r in hwalls),
            "vwalls": tuple("".join(r) for r in vwalls),
            "features": tuple(features),
            "pits": tuple(pits),
            "levels": tuple(
                lv for lv in truth.levels if any(s in known for s in lv.squares)
            ),
            "tokens": tokens,
            "coarse": coarse,
        }
    )


@dataclass(frozen=True)
class Allowance:
    """The movement allowance Sojourn puts in the view for the Sojourner's own
    token (path drawing doc): reachable squares with their cost in feet, the
    route each cost was priced on, and warnings keyed by square label.
    Computed from player-visible facts."""

    token_id: str
    speed_ft: int
    dash_ft: int
    costs: dict[str, int] = field(default_factory=dict)
    warnings: dict[str, str] = field(default_factory=dict)
    #: The route, start square first, that each square's cost was priced on.
    #: Cost and Dash depend on the way taken, so the browser fills a far tap
    #: from this and never rebuilds a route from costs.
    routes: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def as_json(self) -> dict[str, object]:
        return {
            "token_id": self.token_id,
            "speed_ft": self.speed_ft,
            "dash_ft": self.dash_ft,
            "costs": dict(sorted(self.costs.items())),
            "warnings": dict(sorted(self.warnings.items())),
            "routes": {k: list(v) for k, v in sorted(self.routes.items())},
        }


def player_view(
    player: Snapshot,
    *,
    viewer: str,
    map_id: str,
    revision: int,
    label: str,
    allowance: Allowance | None = None,
) -> dict[str, object]:
    """The JSON the browser gets, with its staleness hash. *player* must
    already be a :func:`player_snapshot`."""
    body: dict[str, object] = {
        "map_id": map_id,
        "label": label,
        "revision": revision,
        "viewer": viewer,
        "snapshot": player.model_dump(mode="json"),
        "allowance": allowance.as_json() if allowance is not None else None,
    }
    body["view_hash"] = view_hash(body)
    return body


def view_hash(body: dict[str, object]) -> str:
    """sha256 over the canonical view, without its own hash. Keyed by viewer,
    so per-player fog can follow."""
    stripped = {k: v for k, v in body.items() if k != "view_hash"}
    encoded = json.dumps(stripped, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def text_view(player: Snapshot, *, label: str) -> str:
    """The scene as words for Turn preparation (the volatile suffix, which the
    Planner and the Writer share): the party-visible projection only."""
    lines = [f"[Scene map: {label}]"]
    for area in player.areas:
        detail = "squares" if area.level == "gridded" else "sketch"
        lines.append(f"Area {area.area_id}: {area.label} ({detail})")
    for t in player.tokens:
        where = (
            coords.label(t.square) if t.square is not None else _coarse_at(player, t)
        )
        lines.append(f"{t.side} {t.token_id} ({t.label or t.ref}) at {where}")
    for f in player.features:
        if is_door(f) and f.edge is not None:
            a, b = f.edge.sides()
            near = a if player.char(a) not in " " else b
            name, state = f.label or f.feature_id, f.state or "closed"
            lines.append(f"{name}: {state}, by {coords.label(near)}")
        elif f.squares:
            at = ", ".join(coords.label(s) for s in f.squares)
            lines.append(f"{f.label or f.feature_id} at {at}")
    for p in player.pits:
        at = ", ".join(coords.label(s) for s in p.squares)
        lines.append(f"pit {p.pit_id} at {at}, {p.depth_ft} ft deep")
    party = [t for t in player.tokens if t.side == PARTY and t.square is not None]
    for viewer in party:
        assert viewer.square is not None
        for other in player.tokens:
            if other.side == PARTY or other.square is None:
                continue
            line = sight_line(
                player, viewer.square, other.square, ignore=(viewer.token_id,)
            )
            dist = distance_to_token_ft(viewer.square, other)
            lines.append(
                f"{viewer.token_id} to {other.token_id}: {dist} ft,"
                f" line {'clear' if line.clear else 'blocked'},"
                f" obstruction {line.obstruction}"
            )
    for rel in player.coarse.relations:
        via = f" via {rel.via}" if rel.via else ""
        side = f" ({rel.side})" if rel.side else ""
        lines.append(f"{rel.subject} {rel.relation} {rel.object}{via}{side}")
    return "\n".join(lines)


def _coarse_at(player: Snapshot, token: Token) -> str:
    for p in player.coarse.placements:
        if p.token_id == token.token_id:
            return p.text or p.zone_id
    return "somewhere unplaced"
