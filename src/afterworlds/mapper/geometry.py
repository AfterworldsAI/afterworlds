"""Geometric queries over one revision (issue #211). Decides nothing.

Every query reads one :class:`~afterworlds.mapper.models.Snapshot`. Callers
that must see only what the Sojourner knows pass the player projection
(:func:`afterworlds.mapper.views.player_snapshot`) instead of the truth, so a
preview and the true resolution run the same code.

Sight runs on a doubled grid: square ``(c, r)`` is cell ``(2c+1, 2r+1)``,
the line above it ``(2c+1, 2r)``, the line left of it ``(2c, 2r+1)`` and
grid points ``(2c, 2r)``, so walls on grid lines block it (data model, Light
and sight). python-tcod computes field of view and lines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import numpy.typing as npt
import tcod.los
import tcod.map
from tcod import libtcodpy

from afterworlds.mapper.models import (
    DOOR_KINDS,
    FEET_PER_SQUARE,
    Edge,
    Feature,
    Snapshot,
    Square,
    Token,
    token_squares,
)

_SOLID = frozenset("# ")
_PASSABLE_DOOR_STATES = frozenset({"open", "broken"})
_COVER_ORDER = ("none", "half", "three_quarters", "full")


def chebyshev(a: Square, b: Square) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def distance_ft(a: Square, b: Square) -> int:
    """Grid distance: every step, diagonal or not, is one 5-ft square."""
    return chebyshev(a, b) * FEET_PER_SQUARE


def distance_to_token_ft(square: Square, token: Token) -> int | None:
    squares = token_squares(token)
    if not squares:
        return None
    return min(distance_ft(square, s) for s in squares)


def edge_between(a: Square, b: Square) -> Edge:
    """The grid line between two orthogonally adjacent squares."""
    (ac, ar), (bc, br) = a, b
    if br == ar and bc == ac + 1:
        return Edge(orient="v", col=bc, row=ar)
    if br == ar and bc == ac - 1:
        return Edge(orient="v", col=ac, row=ar)
    if bc == ac and br == ar + 1:
        return Edge(orient="h", col=ac, row=br)
    if bc == ac and br == ar - 1:
        return Edge(orient="h", col=ac, row=ar)
    raise ValueError(f"{a} and {b} are not orthogonally adjacent")


@dataclass(frozen=True)
class EdgeFact:
    edge: Edge
    wall: bool
    door: Feature | None

    @property
    def blocks(self) -> bool:
        """Blocks a step geometrically: a wall with no door, or a door that is
        not open or broken, or a hidden secret door (still a wall)."""
        if self.door is not None and not self.door.hidden:
            return self.door.state not in _PASSABLE_DOOR_STATES
        return self.wall


def edge_fact(snap: Snapshot, edge: Edge) -> EdgeFact:
    in_range = (
        0 <= edge.row <= snap.height and 0 <= edge.col < snap.width
        if edge.orient == "h"
        else 0 <= edge.row < snap.height and 0 <= edge.col <= snap.width
    )
    wall = snap.wall(edge) if in_range else False
    return EdgeFact(edge=edge, wall=wall, door=snap.door_at(edge))


@dataclass(frozen=True)
class StepFacts:
    """What one step touches. ``crossed`` is the line an orthogonal step
    crosses; ``corner`` the four lines meeting at the grid point a diagonal
    step passes, and ``flanks`` its two orthogonal neighbours."""

    start: Square
    end: Square
    diagonal: bool
    crossed: EdgeFact | None
    corner: tuple[EdgeFact, ...]
    flanks: tuple[Square, Square] | None
    end_char: str
    on_map: bool
    rise_ft: int
    pit_id: str | None
    occupants: tuple[str, ...]


def step_facts(snap: Snapshot, start: Square, end: Square) -> StepFacts:
    dx, dy = end[0] - start[0], end[1] - start[1]
    if max(abs(dx), abs(dy)) != 1:
        raise ValueError(f"{start} -> {end} is not one step")
    diagonal = dx != 0 and dy != 0
    crossed: EdgeFact | None = None
    corner: tuple[EdgeFact, ...] = ()
    flanks: tuple[Square, Square] | None = None
    if diagonal:
        n1 = (start[0] + dx, start[1])
        n2 = (start[0], start[1] + dy)
        flanks = (n1, n2)
        corner = tuple(
            edge_fact(snap, edge_between(a, b))
            for a, b in ((start, n1), (start, n2), (n1, end), (n2, end))
        )
    else:
        crossed = edge_fact(snap, edge_between(start, end))
    pit = snap.pit_at(end)
    return StepFacts(
        start=start,
        end=end,
        diagonal=diagonal,
        crossed=crossed,
        corner=corner,
        flanks=flanks,
        end_char=snap.char(end),
        on_map=snap.on_map(end),
        rise_ft=snap.height_at(end) - snap.height_at(start),
        pit_id=pit.pit_id if pit is not None else None,
        occupants=tuple(t.token_id for t in snap.tokens if end in token_squares(t)),
    )


def route_facts(snap: Snapshot, route: tuple[Square, ...]) -> list[StepFacts]:
    """Per-step geometry of a route that starts at ``route[0]``."""
    return [step_facts(snap, a, b) for a, b in zip(route, route[1:], strict=False)]


def leaves_distance(
    route: tuple[Square, ...], around: Token, distance_ft_: int
) -> int | None:
    """The index of the first step that takes the route from within
    *distance_ft_* of *around* to beyond it (Sojourn supplies the distance and
    decides what crossing it means)."""
    for i, (a, b) in enumerate(zip(route, route[1:], strict=False)):
        da, db = distance_to_token_ft(a, around), distance_to_token_ft(b, around)
        if da is None or db is None:
            return None
        if da <= distance_ft_ < db:
            return i
    return None


# -- sight -----------------------------------------------------------------


def _square_cell(square: Square) -> tuple[int, int]:
    return 2 * square[0] + 1, 2 * square[1] + 1


def transparency(snap: Snapshot) -> npt.NDArray[np.bool_]:
    """The doubled grid, indexed ``[y, x]``; True where sight passes."""
    w2, h2 = 2 * snap.width + 1, 2 * snap.height + 1
    grid = np.ones((h2, w2), dtype=bool)
    for r in range(snap.height):
        for c in range(snap.width):
            if snap.terrain[r][c] in _SOLID:
                grid[2 * r + 1, 2 * c + 1] = False
    for f in snap.features:
        if f.blocks_sight == "full":
            for c, r in f.squares:
                grid[2 * r + 1, 2 * c + 1] = False
    for r in range(snap.height + 1):
        for c in range(snap.width):
            if not edge_fact(snap, Edge(orient="h", col=c, row=r)).blocks:
                continue
            grid[2 * r, 2 * c + 1] = False
            grid[2 * r, 2 * c] = False
            grid[2 * r, 2 * c + 2] = False
    for r in range(snap.height):
        for c in range(snap.width + 1):
            if not edge_fact(snap, Edge(orient="v", col=c, row=r)).blocks:
                continue
            grid[2 * r + 1, 2 * c] = False
            grid[2 * r, 2 * c] = False
            grid[2 * r + 2, 2 * c] = False
    return grid


def visible_squares(snap: Snapshot, viewer: Square) -> frozenset[Square]:
    """Squares geometrically visible from *viewer* (light and senses are
    Sojourn's)."""
    grid = transparency(snap)
    vx, vy = _square_cell(viewer)
    seen = tcod.map.compute_fov(
        grid,
        (vy, vx),
        radius=0,
        light_walls=True,
        algorithm=libtcodpy.FOV_SYMMETRIC_SHADOWCAST,
    )
    return frozenset(
        (c, r)
        for r in range(snap.height)
        for c in range(snap.width)
        if seen[2 * r + 1, 2 * c + 1]
    )


def lit_areas(snap: Snapshot) -> frozenset[str]:
    """v1 light: an area is lit when any light source or torch is in it
    (Owner decision, Nov 26). Outdoor areas count as lit."""
    lit: set[str] = set()
    for area in snap.areas:
        if not area.indoors:
            lit.add(area.area_id)
            continue
        if any(
            f.emits_light and any(area.contains(s) for s in f.squares)
            for f in snap.features
        ) or any(
            t.carries_light and t.square is not None and area.contains(t.square)
            for t in snap.tokens
        ):
            lit.add(area.area_id)
    return frozenset(lit)


@dataclass(frozen=True)
class SightLine:
    """Geometry from placement only (issue #211, Cover and range): Sojourn
    decides Cover degree, range band and Disadvantage, and may not contradict
    these facts."""

    clear: bool
    passes_through: tuple[str, ...]
    #: How much of the target the line's obstructions screen.
    obstruction: Literal["none", "half", "three_quarters", "full"]
    distance_ft: int
    corners: int = 0
    creatures: tuple[str, ...] = field(default=())


def sight_line(
    snap: Snapshot, origin: Square, target: Square, *, ignore: tuple[str, ...] = ()
) -> SightLine:
    grid = transparency(snap)
    ox, oy = _square_cell(origin)
    tx, ty = _square_cell(target)
    cells = tcod.los.bresenham((ox, oy), (tx, ty)).tolist()
    through: list[str] = []
    creatures: list[str] = []
    worst = "none"
    clear = True
    corners = 0
    for x, y in cells[1:-1]:
        if x % 2 == 0 and y % 2 == 0:
            if not grid[y, x]:
                corners += 1
                through.append("corner")
            continue
        if not grid[y, x]:
            clear = False
            through.append("wall" if (x % 2 == 0 or y % 2 == 0) else "solid")
            continue
        if x % 2 == 1 and y % 2 == 1:
            sq = ((x - 1) // 2, (y - 1) // 2)
            for f in snap.features:
                if sq in f.squares and f.cover_geometry != "none":
                    through.append(f"feature:{f.feature_id}")
                    worst = _worse(worst, f.cover_geometry)
            for t in snap.tokens:
                if t.token_id in ignore or sq not in token_squares(t):
                    continue
                creatures.append(t.token_id)
                through.append(f"creature:{t.token_id}")
                worst = _worse(worst, "half")
    if not clear:
        worst = "full"
    return SightLine(
        clear=clear,
        passes_through=tuple(dict.fromkeys(through)),
        obstruction=worst,  # type: ignore[arg-type]
        distance_ft=distance_ft(origin, target),
        corners=corners,
        creatures=tuple(dict.fromkeys(creatures)),
    )


def _worse(a: str, b: str) -> str:
    return a if _COVER_ORDER.index(a) >= _COVER_ORDER.index(b) else b


def is_door(feature: Feature) -> bool:
    return feature.kind in DOOR_KINDS
