"""Apply typed spatial updates with coherence checks (issue #211).

Only Sojourn proposes updates. The mapper checks that each is coherent (the
door exists, the square is on the map, the revision is current) and either
applies it to the Turn's staged snapshot or refuses with a reason Sojourn can
act on. A refusal is not an error.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable
from typing import Any

from afterworlds.mapper import coords
from afterworlds.mapper.geometry import chebyshev, edge_between, edge_fact
from afterworlds.mapper.models import (
    DOOR_KINDS,
    DOOR_STATES,
    TERRAIN_CHARS,
    TRAP_STATES,
    AddFeature,
    CoarsePlacement,
    MarkExplored,
    MoveToken,
    PlaceCoarse,
    PlaceToken,
    RefineArea,
    Relate,
    RemoveFeature,
    RemoveToken,
    SetFeatureState,
    SetHidden,
    SetLight,
    SetTerrain,
    SetZone,
    Snapshot,
    SpatialUpdate,
    Square,
    Token,
    token_squares,
)


class UpdateRefused(Exception):
    """A typed update the record cannot take, with a player-safe reason."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


MAP_MOVED_ON = "the map moved on"


def content_hash(snapshot: Snapshot) -> str:
    encoded = json.dumps(
        snapshot.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def apply_all(
    snapshot: Snapshot,
    updates: Iterable[SpatialUpdate],
    *,
    current_revision: int,
    seed: int,
) -> Snapshot:
    """Every update in order, or :class:`UpdateRefused` for the first that
    fails (nothing is applied then: the caller keeps *snapshot*)."""
    for update in updates:
        snapshot = apply(snapshot, update, current_revision=current_revision, seed=seed)
    return snapshot


def apply(
    snapshot: Snapshot, update: SpatialUpdate, *, current_revision: int, seed: int
) -> Snapshot:
    if update.base_revision != current_revision:
        raise UpdateRefused(MAP_MOVED_ON)
    if isinstance(update, RefineArea):
        from afterworlds.mapper.refine import refine_area

        return refine_area(snapshot, update, seed=seed)
    handler = _HANDLERS[type(update)]
    return handler(snapshot, update)


# -- helpers ---------------------------------------------------------------


def _ids(snap: Snapshot) -> set[str]:
    return (
        {f.feature_id for f in snap.features}
        | {p.pit_id for p in snap.pits}
        | {t.token_id for t in snap.tokens}
        | {z.zone_id for z in snap.coarse.zones}
        | {a.area_id for a in snap.areas}
        | {lv.level_id for lv in snap.levels}
    )


def _require_on_map(snap: Snapshot, squares: Iterable[Square]) -> None:
    for s in squares:
        if not snap.on_map(s):
            raise UpdateRefused(
                f"{coords.label(s) if min(s) >= 0 else s} is off the map"
            )


def footprint_free(
    snap: Snapshot, token: Token, square: Square, *, ignore: str | None = None
) -> str | None:
    """``None`` when *token* fits at *square*, else a reason."""
    probe = token.model_copy(update={"square": square})
    for s in token_squares(probe):
        if not snap.on_map(s):
            who = token.label or token.token_id
            return f"{coords.label(square)} has no room for {who}"
        if snap.char(s) in "# ":
            return f"{coords.label(s)} is solid"
        for other in snap.tokens:
            if other.token_id in (token.token_id, ignore):
                continue
            if s in token_squares(other):
                return (
                    f"{coords.label(s)} is occupied by {other.label or other.token_id}"
                )
    return None


def _replace_token(snap: Snapshot, token: Token) -> Snapshot:
    return snap.model_copy(
        update={
            "tokens": tuple(
                token if t.token_id == token.token_id else t for t in snap.tokens
            )
        }
    )


# -- handlers --------------------------------------------------------------


def _set_zone(snap: Snapshot, u: SetZone) -> Snapshot:
    if snap.area(u.zone.area_id) is None:
        raise UpdateRefused(f"no area {u.zone.area_id}")
    zones = tuple(z for z in snap.coarse.zones if z.zone_id != u.zone.zone_id)
    coarse = snap.coarse.model_copy(update={"zones": (*zones, u.zone)})
    return snap.model_copy(update={"coarse": coarse})


def _relate(snap: Snapshot, u: Relate) -> Snapshot:
    rel = u.relation
    known = _ids(snap)
    for thing in (rel.subject, rel.object):
        if thing not in known:
            raise UpdateRefused(f"nothing called {thing}")
    for existing in snap.coarse.relations:
        same_pair = (existing.subject, existing.object, existing.relation) == (
            rel.subject,
            rel.object,
            rel.relation,
        )
        if same_pair and (existing.via, existing.side) != (rel.via, rel.side):
            raise UpdateRefused(
                f"{rel.subject} is already {existing.relation} {rel.object}"
            )
    coarse = snap.coarse.model_copy(update={"relations": (*snap.coarse.relations, rel)})
    return snap.model_copy(update={"coarse": coarse})


def _place_coarse(snap: Snapshot, u: PlaceCoarse) -> Snapshot:
    if u.token.token_id in _ids(snap):
        raise UpdateRefused(f"{u.token.token_id} is already on the map")
    if u.placement.zone_id not in {z.zone_id for z in snap.coarse.zones}:
        raise UpdateRefused(f"no zone {u.placement.zone_id}")
    if u.token.square is not None:
        raise UpdateRefused("a coarse placement has no square")
    placement = CoarsePlacement(
        token_id=u.token.token_id,
        zone_id=u.placement.zone_id,
        at=u.placement.at,
        text=u.placement.text,
    )
    coarse = snap.coarse.model_copy(
        update={"placements": (*snap.coarse.placements, placement)}
    )
    return snap.model_copy(update={"tokens": (*snap.tokens, u.token), "coarse": coarse})


def _place_token(snap: Snapshot, u: PlaceToken) -> Snapshot:
    if u.token.token_id in _ids(snap):
        raise UpdateRefused(f"{u.token.token_id} is already on the map")
    if u.token.square is None:
        raise UpdateRefused("place_token needs a square")
    reason = footprint_free(snap, u.token, u.token.square)
    if reason is not None:
        raise UpdateRefused(reason)
    return snap.model_copy(update={"tokens": (*snap.tokens, u.token)})


def _remove_token(snap: Snapshot, u: RemoveToken) -> Snapshot:
    if snap.token(u.token_id) is None:
        raise UpdateRefused(f"no token {u.token_id}")
    coarse = snap.coarse.model_copy(
        update={
            "placements": tuple(
                p for p in snap.coarse.placements if p.token_id != u.token_id
            )
        }
    )
    return snap.model_copy(
        update={
            "tokens": tuple(t for t in snap.tokens if t.token_id != u.token_id),
            "coarse": coarse,
        }
    )


def _move_token(snap: Snapshot, u: MoveToken) -> Snapshot:
    token = snap.token(u.token_id)
    if token is None:
        raise UpdateRefused(f"no token {u.token_id}")
    if token.square != u.route[0]:
        raise UpdateRefused(f"{token.token_id} is not at {coords.label(u.route[0])}")
    _require_on_map(snap, u.route)
    for a, b in zip(u.route, u.route[1:], strict=False):
        if chebyshev(a, b) != 1:
            raise UpdateRefused(f"{coords.label(a)} to {coords.label(b)} is not a step")
        if snap.char(b) in "# ":
            raise UpdateRefused(f"{coords.label(b)} is solid")
        if a[0] != b[0] and a[1] != b[1]:
            continue
        if edge_fact(snap, edge_between(a, b)).blocks:
            raise UpdateRefused(f"a wall is in the way at {coords.label(b)}")
    reason = footprint_free(snap, token, u.route[-1])
    if reason is not None:
        raise UpdateRefused(reason)
    coarse = snap.coarse.model_copy(
        update={
            "placements": tuple(
                p for p in snap.coarse.placements if p.token_id != u.token_id
            )
        }
    )
    moved = _replace_token(snap, token.model_copy(update={"square": u.route[-1]}))
    return moved.model_copy(update={"coarse": coarse})


def _set_feature_state(snap: Snapshot, u: SetFeatureState) -> Snapshot:
    feature = snap.feature(u.feature_id)
    if feature is None:
        raise UpdateRefused(f"no feature {u.feature_id}")
    valid = (
        DOOR_STATES
        if feature.kind in DOOR_KINDS
        else TRAP_STATES if feature.kind == "trap" else None
    )
    if valid is not None and u.state not in valid:
        raise UpdateRefused(f"{feature.kind} can't be {u.state}")
    changed = feature.model_copy(update={"state": u.state})
    return snap.model_copy(
        update={
            "features": tuple(
                changed if f.feature_id == u.feature_id else f for f in snap.features
            )
        }
    )


def _add_feature(snap: Snapshot, u: AddFeature) -> Snapshot:
    if u.feature.feature_id in _ids(snap):
        raise UpdateRefused(f"{u.feature.feature_id} already exists")
    _require_on_map(snap, u.feature.squares)
    if u.feature.edge is not None:
        a, b = u.feature.edge.sides()
        if not (snap.on_map(a) or snap.on_map(b)):
            raise UpdateRefused("that line is off the map")
    return snap.model_copy(update={"features": (*snap.features, u.feature)})


def _remove_feature(snap: Snapshot, u: RemoveFeature) -> Snapshot:
    if snap.feature(u.feature_id) is None:
        raise UpdateRefused(f"no feature {u.feature_id}")
    return snap.model_copy(
        update={
            "features": tuple(f for f in snap.features if f.feature_id != u.feature_id)
        }
    )


def _set_terrain(snap: Snapshot, u: SetTerrain) -> Snapshot:
    if u.char not in TERRAIN_CHARS or u.char == " ":
        raise UpdateRefused(f"{u.char!r} is not terrain")
    _require_on_map(snap, u.squares)
    rows = [list(r) for r in snap.terrain]
    for c, r in u.squares:
        area = snap.area_at((c, r))
        if area is not None and area.level == "coarse":
            raise UpdateRefused(f"{coords.label((c, r))} is in a coarse area")
        rows[r][c] = u.char
    return snap.model_copy(update={"terrain": tuple("".join(r) for r in rows)})


def _set_hidden(snap: Snapshot, u: SetHidden) -> Snapshot:
    if snap.feature(u.thing_id) is not None:
        return snap.model_copy(
            update={
                "features": tuple(
                    (
                        f.model_copy(update={"hidden": u.hidden})
                        if f.feature_id == u.thing_id
                        else f
                    )
                    for f in snap.features
                )
            }
        )
    if any(p.pit_id == u.thing_id for p in snap.pits):
        return snap.model_copy(
            update={
                "pits": tuple(
                    (
                        p.model_copy(update={"hidden": u.hidden})
                        if p.pit_id == u.thing_id
                        else p
                    )
                    for p in snap.pits
                )
            }
        )
    token = snap.token(u.thing_id)
    if token is not None:
        return _replace_token(snap, token.model_copy(update={"hidden": u.hidden}))
    raise UpdateRefused(f"nothing called {u.thing_id}")


def _set_light(snap: Snapshot, u: SetLight) -> Snapshot:
    token = snap.token(u.thing_id)
    if token is not None:
        return _replace_token(snap, token.model_copy(update={"carries_light": u.lit}))
    if snap.feature(u.thing_id) is not None:
        return snap.model_copy(
            update={
                "features": tuple(
                    (
                        f.model_copy(update={"emits_light": u.lit})
                        if f.feature_id == u.thing_id
                        else f
                    )
                    for f in snap.features
                )
            }
        )
    raise UpdateRefused(f"nothing called {u.thing_id}")


def _mark_explored(snap: Snapshot, u: MarkExplored) -> Snapshot:
    _require_on_map(snap, u.squares)
    rows = [list(r) for r in snap.explored]
    for c, r in u.squares:
        rows[r][c] = "1"
    return snap.model_copy(update={"explored": tuple("".join(r) for r in rows)})


_HANDLERS: dict[type, Callable[[Snapshot, Any], Snapshot]] = {
    SetZone: _set_zone,
    Relate: _relate,
    PlaceCoarse: _place_coarse,
    PlaceToken: _place_token,
    RemoveToken: _remove_token,
    MoveToken: _move_token,
    SetFeatureState: _set_feature_state,
    AddFeature: _add_feature,
    RemoveFeature: _remove_feature,
    SetTerrain: _set_terrain,
    SetHidden: _set_hidden,
    SetLight: _set_light,
    MarkExplored: _mark_explored,
}
