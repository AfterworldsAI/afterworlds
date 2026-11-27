"""Refine a coarse area into squares (map generation doc, issue #211).

Fixed facts go down first (what the story and earlier Turns established, and
what this update specifies); seeded fill supplies only what nothing
specified: python-tcod BSP indoors, tcod noise outdoors. Each area's fill
uses a seed derived from the map's seed and the area's id, so the same seed
and Turns give the same squares.

A refinement is refused, with a reason, when it would contradict a coarse
fact, name something unknown, put a door between areas that don't touch,
leave a creature no room, or leave parts of the area unreachable. Committed
detail is never moved or reshaped: only the area's unspecified squares are
filled.
"""

from __future__ import annotations

import hashlib
from collections import deque

import tcod.bsp
import tcod.noise
import tcod.random

from afterworlds.mapper import coords
from afterworlds.mapper.geometry import edge_between, edge_fact, sight_line
from afterworlds.mapper.models import (
    TERRAIN_CHARS,
    Area,
    Edge,
    RefineArea,
    Snapshot,
    Square,
    Token,
    token_squares,
)

GENERATOR_VERSION = "mapper-m1-1"


class RefinementFailed(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def area_seed(map_seed: int, area_id: str, attempt: int = 0) -> int:
    digest = hashlib.sha256(f"{map_seed}:{area_id}:{attempt}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def refine_area(
    snap: Snapshot, update: RefineArea, *, seed: int, attempt: int = 0
) -> Snapshot:
    """*snap* with *update*'s area gridded, or :class:`UpdateRefused`."""
    from afterworlds.mapper.updates import UpdateRefused

    try:
        return _refine(snap, update, area_seed(seed, update.area, attempt))
    except RefinementFailed as exc:
        raise UpdateRefused(exc.reason) from exc


def _refine(snap: Snapshot, u: RefineArea, seed: int) -> Snapshot:
    area = snap.area(u.area)
    if area is None:
        raise RefinementFailed(f"nothing called {u.area}")
    if area.level != "coarse":
        raise RefinementFailed(f"{area.label} already has squares")
    c0, r0, w, h = area.bounds
    if c0 < 0 or r0 < 0 or c0 + w > snap.width or r0 + h > snap.height:
        raise RefinementFailed("the map would exceed its bounds")
    setting = u.setting or area.setting

    rows = [list(r) for r in snap.terrain]
    # 1. Fixed terrain this update states.
    if u.terrain is not None:
        if len(u.terrain) != h or any(len(line) != w for line in u.terrain):
            raise RefinementFailed(f"the terrain doesn't fit {area.label}")
        for dr, line in enumerate(u.terrain):
            for dc, ch in enumerate(line):
                if ch not in TERRAIN_CHARS:
                    raise RefinementFailed(f"{ch!r} is not terrain")
                if ch != " ":
                    rows[r0 + dr][c0 + dc] = ch
    # 2. Pits: every pit inside the area, with its depth (pydantic requires it).
    for pit in u.pits:
        for s in pit.squares:
            if not area.contains(s):
                raise RefinementFailed(f"pit {pit.pit_id} doesn't fit {area.label}")
            rows[s[1]][s[0]] = "_"
    # 3. Seeded fill of what nothing specified.
    fill = _fill(area, setting, seed)
    for (c, r), ch in fill.items():
        if rows[r][c] == " ":
            rows[r][c] = ch
    terrain = tuple("".join(r) for r in rows)

    # 4. Walls: indoors, the area's boundary, then any the update names.
    hwalls = [list(r) for r in snap.hwalls]
    vwalls = [list(r) for r in snap.vwalls]
    walls = list(u.walls)
    if area.indoors:
        walls.extend(_boundary(area))
    for e in walls:
        _set_wall(snap, hwalls, vwalls, e)

    # 5. Features and doors.
    features = list(snap.features)
    known_ids = {f.feature_id for f in features}
    for f in u.features:
        if f.feature_id in known_ids:
            raise RefinementFailed(f"{f.feature_id} already exists")
        for s in f.squares:
            if not area.contains(s):
                raise RefinementFailed(f"{f.label or f.feature_id} doesn't fit")
        if f.edge is not None:
            _check_door_joins(snap, area, f.edge)
            _set_wall(snap, hwalls, vwalls, f.edge)
        features.append(f)
    # Doors the coarse layer already named in this area's walls keep a line.
    for f in snap.features:
        if f.edge is not None and _touches(area, f.edge):
            _set_wall(snap, hwalls, vwalls, f.edge)

    gridded = area.model_copy(update={"level": "gridded", "setting": setting})
    staged = snap.model_copy(
        update={
            "terrain": terrain,
            "hwalls": tuple("".join(r) for r in hwalls),
            "vwalls": tuple("".join(r) for r in vwalls),
            "areas": tuple(
                gridded if a.area_id == area.area_id else a for a in snap.areas
            ),
            "features": tuple(features),
            "pits": (*snap.pits, *u.pits),
            "levels": (*snap.levels, *u.levels),
        }
    )
    if u.light is not None:
        staged = _with_light(staged, area, u.light)

    # 6. Placements of coarse tokens.
    zone_area = {z.zone_id: z.area_id for z in snap.coarse.zones}
    placed = dict(u.placements)
    for token_id in placed:
        if staged.token(token_id) is None:
            raise RefinementFailed(f"nothing called {token_id}")
    tokens = []
    for t in staged.tokens:
        if t.token_id not in placed:
            tokens.append(t)
            continue
        sq = placed[t.token_id]
        if not area.contains(sq):
            raise RefinementFailed(f"{coords.label(sq)} isn't in {area.label}")
        tokens.append(t.model_copy(update={"square": sq}))
    staged = staged.model_copy(update={"tokens": tuple(tokens)})
    for t in staged.tokens:
        if t.token_id in placed:
            _check_room(staged, t)
    for p in snap.coarse.placements:
        in_area = zone_area.get(p.zone_id) == area.area_id
        if in_area and p.token_id not in placed:
            raise RefinementFailed(f"{p.token_id} has no square in {area.label}")
    remaining = tuple(p for p in staged.coarse.placements if p.token_id not in placed)
    staged = staged.model_copy(
        update={"coarse": staged.coarse.model_copy(update={"placements": remaining})}
    )

    # 7. Every coarse fact still holds.
    _check_coarse(snap, staged, area, placed)
    # 8. The area's open squares reach each other.
    _check_reachable(staged, area)
    return staged


def _fill(area: Area, setting: str, seed: int) -> dict[Square, str]:
    c0, r0, w, h = area.bounds
    out: dict[Square, str] = {(c, r): "." for c, r in area.squares()}
    rng = tcod.random.Random(tcod.random.MERSENNE_TWISTER, seed)
    if area.indoors:
        # BSP: split the room and leave a little rubble in one leaf, away
        # from the walls, so the fill varies with the seed but never blocks.
        bsp = tcod.bsp.BSP(x=c0, y=r0, width=w, height=h)
        bsp.split_recursive(
            depth=2,
            min_width=3,
            min_height=3,
            max_horizontal_ratio=1.5,
            max_vertical_ratio=1.5,
            seed=rng,
        )
        leaves = [n for n in bsp.inverted_level_order() if not n.children]
        if leaves and setting == "natural":
            leaf = leaves[rng.randint(0, len(leaves) - 1)]
            for c in range(leaf.x + 1, leaf.x + leaf.width - 1):
                for r in range(leaf.y + 1, leaf.y + leaf.height - 1):
                    out[(c, r)] = ","
    else:
        noise = tcod.noise.Noise(dimensions=2, seed=rng)
        for c, r in area.squares():
            if noise.get_point(c / 4.0, r / 4.0) > 0.45:
                out[(c, r)] = ","
    return out


def _boundary(area: Area) -> list[Edge]:
    c0, r0, w, h = area.bounds
    edges = [Edge(orient="h", col=c, row=r0) for c in range(c0, c0 + w)]
    edges += [Edge(orient="h", col=c, row=r0 + h) for c in range(c0, c0 + w)]
    edges += [Edge(orient="v", col=c0, row=r) for r in range(r0, r0 + h)]
    edges += [Edge(orient="v", col=c0 + w, row=r) for r in range(r0, r0 + h)]
    return edges


def _touches(area: Area, edge: Edge) -> bool:
    a, b = edge.sides()
    return area.contains(a) or area.contains(b)


def _set_wall(
    snap: Snapshot, hw: list[list[str]], vw: list[list[str]], e: Edge
) -> None:
    if e.orient == "h":
        if not (0 <= e.row <= snap.height and 0 <= e.col < snap.width):
            raise RefinementFailed("a wall is off the map")
        hw[e.row][e.col] = "-"
    else:
        if not (0 <= e.row < snap.height and 0 <= e.col <= snap.width):
            raise RefinementFailed("a wall is off the map")
        vw[e.row][e.col] = "|"


def _check_door_joins(snap: Snapshot, area: Area, edge: Edge) -> None:
    """A door sits on a line with a square on each side, one of them in the
    area being refined."""
    a, b = edge.sides()
    if not (snap.on_map(a) and snap.on_map(b)) or not (
        area.contains(a) or area.contains(b)
    ):
        raise RefinementFailed("a door joins areas that don't touch")


def _with_light(snap: Snapshot, area: Area, lit: bool) -> Snapshot:
    from afterworlds.mapper.models import Feature

    fid = f"light:{area.area_id}"
    features = tuple(f for f in snap.features if f.feature_id != fid)
    if lit:
        c0, r0, _, _ = area.bounds
        features = (
            *features,
            Feature(
                feature_id=fid,
                kind="light_source",
                label=f"light in {area.label}",
                squares=((c0, r0),),
                emits_light=True,
            ),
        )
    return snap.model_copy(update={"features": features})


def _check_room(snap: Snapshot, token: Token) -> None:
    for s in token_squares(token):
        if not snap.on_map(s) or snap.char(s) in "# _":
            raise RefinementFailed(
                f"{token.label or token.token_id} has no room at {coords.label(s)}"
            )
        for other in snap.tokens:
            if other.token_id != token.token_id and s in token_squares(other):
                raise RefinementFailed(
                    f"{token.label or token.token_id} has no room at {coords.label(s)}"
                )


def _check_coarse(
    before: Snapshot, after: Snapshot, area: Area, placed: dict[str, Square]
) -> None:
    zones = {z.zone_id: z for z in before.coarse.zones}
    for p in before.coarse.placements:
        if p.token_id not in placed:
            continue
        sq = placed[p.token_id]
        zone = zones.get(p.zone_id)
        if zone is not None and zone.area_id != area.area_id:
            raise RefinementFailed(f"{p.token_id} would leave {zone.label}")
        if p.at is not None and not _beside(after, sq, p.at):
            raise RefinementFailed(f"{p.token_id} would no longer be at {p.at}")
    for rel in before.coarse.relations:
        if rel.relation == "across" and rel.via is not None:
            a, b = after.token(rel.subject), after.token(rel.object)
            if a is None or b is None or a.square is None or b.square is None:
                continue
            line = sight_line(after, a.square, b.square)
            if f"feature:{rel.via}" not in line.passes_through:
                raise RefinementFailed(
                    f"{rel.via} would no longer lie between {rel.subject} and"
                    f" {rel.object}"
                )
        elif rel.relation == "in_wall" and rel.side is not None:
            f = after.feature(rel.subject)
            target = after.area(rel.object)
            if f is None or f.edge is None or target is None:
                continue
            if target.area_id == area.area_id and _side_of(target, f.edge) != rel.side:
                raise RefinementFailed(
                    f"{f.label or f.feature_id} would leave the {rel.side} wall"
                )
        elif rel.relation == "beside":
            t = after.token(rel.subject)
            placed_here = (
                t is not None and t.square is not None and rel.subject in placed
            )
            if placed_here and not _beside(after, t.square, rel.object):  # type: ignore[union-attr,arg-type]
                raise RefinementFailed(
                    f"{rel.subject} would no longer be beside {rel.object}"
                )


def _beside(snap: Snapshot, square: Square, thing: str) -> bool:
    f = snap.feature(thing)
    if f is not None:
        near = set(f.squares)
        if f.edge is not None:
            near |= set(f.edge.sides())
        return any(max(abs(square[0] - s[0]), abs(square[1] - s[1])) <= 1 for s in near)
    t = snap.token(thing)
    if t is not None and t.square is not None:
        return any(
            max(abs(square[0] - s[0]), abs(square[1] - s[1])) <= 1
            for s in token_squares(t)
        )
    return False


def _side_of(area: Area, edge: Edge) -> str | None:
    c0, r0, w, h = area.bounds
    if edge.orient == "h" and edge.row == r0:
        return "north"
    if edge.orient == "h" and edge.row == r0 + h:
        return "south"
    if edge.orient == "v" and edge.col == c0:
        return "west"
    if edge.orient == "v" and edge.col == c0 + w:
        return "east"
    return None


def _check_reachable(snap: Snapshot, area: Area) -> None:
    open_squares = [s for s in area.squares() if snap.char(s) not in "# "]
    if not open_squares:
        raise RefinementFailed(f"{area.label} has no floor")
    start = open_squares[0]
    seen = {start}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (cur[0] + dc, cur[1] + dr)
            if nxt in seen or not area.contains(nxt) or snap.char(nxt) in "# ":
                continue
            fact = edge_fact(snap, edge_between(cur, nxt))
            if fact.wall and fact.door is None:
                continue
            seen.add(nxt)
            queue.append(nxt)
    if len(seen) != len(open_squares):
        raise RefinementFailed("the areas are unreachable from each other")


#: Refinement is tried this many times, each with a fresh derived seed,
#: before Sojourn falls back to coarse facts (map generation doc).
REFINE_ATTEMPTS = 2


def refine_with_retry(
    snap: Snapshot, update: RefineArea, *, seed: int
) -> tuple[Snapshot | None, tuple[str, ...]]:
    """*snap* with *update*'s area gridded, trying up to
    :data:`REFINE_ATTEMPTS` derived seeds. ``(None, reasons)`` when every
    attempt was refused; the caller then works from coarse facts only."""
    reasons: list[str] = []
    for attempt in range(REFINE_ATTEMPTS):
        try:
            return _refine(snap, update, area_seed(seed, update.area, attempt)), ()
        except RefinementFailed as exc:
            reasons.append(exc.reason)
    return None, tuple(reasons)
