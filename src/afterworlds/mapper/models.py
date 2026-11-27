"""The spatial record: one place's map as immutable revisions (issue #211).

The mapper is RPG-agnostic. It stores space at story precision and holds no
game rule: no range band, no climb check, no movement cost. Sojourn's
adjudication reads these facts and decides what they mean.

Coordinates are zero-based ``(col, row)`` integers, column A row 1 being
``(0, 0)``; :mod:`afterworlds.mapper.coords` converts to and from ``A1``.

Squares are one character each (``terrain``):

====  =================================  ===========  ===========
char  square                             blocks step  blocks sight
====  =================================  ===========  ===========
``.``  floor or open ground              no           no
``,``  rough ground                      no           no
``~``  shallow water                     no           no
``=``  deep water                        no           no
``_``  pit or chasm                      no (a fall)  no
``#``  solid                             yes          yes
space  outside the map, or coarse        yes          yes
====  =================================  ===========  ===========

A coarse area reserves its bounds with spaces until ``refine_area`` fills
them: unspecified space, never terrain.

Walls sit on grid lines. ``hwalls`` holds ``height + 1`` strings of
``width`` characters: ``hwalls[r][c] == "-"`` is a wall on the line above
square ``(c, r)`` (``r == height`` is the bottom edge). ``vwalls`` holds
``height`` strings of ``width + 1`` characters: ``vwalls[r][c] == "|"`` is a
wall on the line left of square ``(c, r)``.
"""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

#: The largest map, either way up (data model: "At most 40 by 60 squares").
MAX_SHORT_SIDE = 40
MAX_LONG_SIDE = 60
FEET_PER_SQUARE = 5

TERRAIN_CHARS = frozenset(".,~=_# ")
SIZES = ("tiny", "small", "medium", "large", "huge", "gargantuan")
Size = Literal["tiny", "small", "medium", "large", "huge", "gargantuan"]

Square = tuple[int, int]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Edge(_Frozen):
    """A grid line between two squares.

    ``h``: the line above square ``(col, row)``; ``v``: the line left of it.
    """

    orient: Literal["h", "v"]
    col: int = Field(ge=0)
    row: int = Field(ge=0)

    def sides(self) -> tuple[Square, Square]:
        """The two squares the line separates (one may be off the map)."""
        if self.orient == "h":
            return (self.col, self.row - 1), (self.col, self.row)
        return (self.col - 1, self.row), (self.col, self.row)


FeatureKind = Literal[
    "door",
    "secret_door",
    "portcullis",
    "bush",
    "boulder",
    "pillar",
    "table",
    "chest",
    "statue",
    "stairs",
    "trap",
    "light_source",
    "other",
]
DOOR_KINDS = frozenset({"door", "secret_door", "portcullis"})
DOOR_STATES = frozenset({"open", "closed", "locked", "broken"})
TRAP_STATES = frozenset({"armed", "sprung", "disarmed"})


class Feature(_Frozen):
    feature_id: str = Field(min_length=1)
    kind: FeatureKind
    label: str = ""
    squares: tuple[Square, ...] = ()
    #: A door's grid line.
    edge: Edge | None = None
    blocks_step: bool = False
    blocks_sight: Literal["none", "partial", "full"] = "none"
    #: How much of a creature-sized square it screens, as geometry; not a
    #: Cover degree (Sojourn decides those).
    cover_geometry: Literal["none", "half", "three_quarters", "full"] = "none"
    #: For a gap or tunnel, the largest creature size it was built for.
    fits: Size | None = None
    state: str | None = None
    emits_light: bool = False
    hidden: bool = False


class Pit(_Frozen):
    pit_id: str = Field(min_length=1)
    squares: tuple[Square, ...] = Field(min_length=1)
    #: Required (Owner decision, Nov 25).
    depth_ft: int = Field(gt=0)
    hidden: bool = False
    #: What a hidden pit's squares look like from above.
    disguise: Literal[".", ","] = "."
    trap_id: str | None = None


class Level(_Frozen):
    """A raised area: its squares stand ``height_ft`` above the floor."""

    level_id: str = Field(min_length=1)
    squares: tuple[Square, ...] = Field(min_length=1)
    height_ft: int = Field(ge=0)
    kind: Literal["dais", "stage", "ledge", "balcony", "platform"] = "ledge"
    label: str = ""
    surface: str = ""


class Token(_Frozen):
    """A creature's place on the map and nothing more (no HP, conditions or
    movement spent)."""

    token_id: str = Field(min_length=1)
    glyph: str = Field(min_length=1, max_length=2)
    ref: str = Field(min_length=1)
    side: Literal["party", "hostile", "neutral"]
    label: str = ""
    #: Top-left square; ``None`` while the token is placed only coarsely.
    square: Square | None = None
    footprint: int = Field(default=1, ge=1, le=4)
    carries_light: bool = False
    hidden: bool = False


class Area(_Frozen):
    area_id: str = Field(min_length=1)
    label: str
    level: Literal["coarse", "gridded"]
    #: Worked stone or natural rock: drawn differently, read by no rule.
    setting: Literal["worked", "natural"] = "worked"
    indoors: bool = True
    #: ``(col, row, width, height)`` reserved on the grid.
    bounds: tuple[int, int, int, int]
    description: str = ""

    def squares(self) -> list[Square]:
        c0, r0, w, h = self.bounds
        return [(c, r) for r in range(r0, r0 + h) for c in range(c0, c0 + w)]

    def contains(self, square: Square) -> bool:
        c0, r0, w, h = self.bounds
        return c0 <= square[0] < c0 + w and r0 <= square[1] < r0 + h


class Zone(_Frozen):
    zone_id: str = Field(min_length=1)
    label: str
    area_id: str
    size_hint: str = ""


class Relation(_Frozen):
    """A coarse fact between two things (zones, features or tokens), with a
    distance kept at the precision the story gave, never a rules band."""

    subject: str
    relation: Literal[
        "inside", "adjacent", "joined_by", "in_wall", "across", "beside", "near"
    ]
    object: str
    #: ``joined_by``: the door; ``across``: what lies between.
    via: str | None = None
    #: ``in_wall``: ``north``/``south``/``east``/``west``.
    side: Literal["north", "south", "east", "west"] | None = None
    distance_text: str = ""


class CoarsePlacement(_Frozen):
    token_id: str
    zone_id: str
    at: str | None = None
    text: str = ""


class CoarseLayer(_Frozen):
    zones: tuple[Zone, ...] = ()
    relations: tuple[Relation, ...] = ()
    placements: tuple[CoarsePlacement, ...] = ()


class Snapshot(_Frozen):
    """One revision's full state. Small: a 40 by 60 map is a few KB."""

    width: int = Field(ge=1)
    height: int = Field(ge=1)
    terrain: tuple[str, ...]
    hwalls: tuple[str, ...]
    vwalls: tuple[str, ...]
    areas: tuple[Area, ...] = ()
    features: tuple[Feature, ...] = ()
    pits: tuple[Pit, ...] = ()
    levels: tuple[Level, ...] = ()
    tokens: tuple[Token, ...] = ()
    coarse: CoarseLayer = CoarseLayer()
    #: ``"1"`` where the party has seen the square.
    explored: tuple[str, ...]

    # -- lookups -----------------------------------------------------------

    def on_map(self, square: Square) -> bool:
        return 0 <= square[0] < self.width and 0 <= square[1] < self.height

    def char(self, square: Square) -> str:
        return self.terrain[square[1]][square[0]] if self.on_map(square) else " "

    def wall(self, edge: Edge) -> bool:
        if edge.orient == "h":
            return self.hwalls[edge.row][edge.col] == "-"
        return self.vwalls[edge.row][edge.col] == "|"

    def feature(self, feature_id: str) -> Feature | None:
        return next((f for f in self.features if f.feature_id == feature_id), None)

    def token(self, token_id: str) -> Token | None:
        return next((t for t in self.tokens if t.token_id == token_id), None)

    def token_by_ref(self, ref: str) -> Token | None:
        return next((t for t in self.tokens if t.ref == ref), None)

    def area(self, area_id: str) -> Area | None:
        return next((a for a in self.areas if a.area_id == area_id), None)

    def area_at(self, square: Square) -> Area | None:
        return next((a for a in self.areas if a.contains(square)), None)

    def door_at(self, edge: Edge) -> Feature | None:
        return next(
            (f for f in self.features if f.kind in DOOR_KINDS and f.edge == edge),
            None,
        )

    def pit_at(self, square: Square) -> Pit | None:
        return next((p for p in self.pits if square in p.squares), None)

    def height_at(self, square: Square) -> int:
        return max(
            (lv.height_ft for lv in self.levels if square in lv.squares), default=0
        )

    def is_explored(self, square: Square) -> bool:
        return self.on_map(square) and self.explored[square[1]][square[0]] == "1"


def token_squares(token: Token) -> list[Square]:
    if token.square is None:
        return []
    c, r = token.square
    n = token.footprint
    return [(c + dc, r + dr) for dr in range(n) for dc in range(n)]


def blank_snapshot(width: int, height: int) -> Snapshot:
    """An empty map of *width* by *height* squares, all unspecified."""
    return Snapshot(
        width=width,
        height=height,
        terrain=tuple(" " * width for _ in range(height)),
        hwalls=tuple(" " * width for _ in range(height + 1)),
        vwalls=tuple(" " * (width + 1) for _ in range(height)),
        explored=tuple("0" * width for _ in range(height)),
    )


class MapRecord(_Frozen):
    map_id: UUID
    story_id: UUID
    place_key: str = Field(min_length=1)
    label: str
    status: Literal["active", "archived"] = "active"
    grid_type: Literal["square"] = "square"
    seed: int
    generator_version: str
    style: dict[str, str] = Field(default_factory=dict)
    revision: int = Field(ge=0)
    created_turn_id: UUID | None = None


class Revision(_Frozen):
    map_id: UUID
    revision: int = Field(ge=0)
    parent_revision: int | None
    turn_id: UUID | None
    node_id: UUID | None = None
    sequence_id: UUID | None = None
    updates: tuple[SpatialUpdate, ...] = ()
    snapshot: Snapshot
    content_hash: str


# -- typed spatial updates ------------------------------------------------


class _Update(_Frozen):
    base_revision: int = Field(ge=0)


class SetZone(_Update):
    op: Literal["set_zone"] = "set_zone"
    zone: Zone


class Relate(_Update):
    op: Literal["relate"] = "relate"
    relation: Relation


class PlaceCoarse(_Update):
    op: Literal["place_coarse"] = "place_coarse"
    token: Token
    placement: CoarsePlacement


class RefineArea(_Update):
    """Turn a coarse area into squares (map generation doc). Fixed facts go
    down first; seeded fill supplies only what nothing specified."""

    op: Literal["refine_area"] = "refine_area"
    area: str
    setting: Literal["worked", "natural"] | None = None
    #: Terrain rows for the area's bounds; spaces are left to seeded fill.
    terrain: tuple[str, ...] | None = None
    walls: tuple[Edge, ...] = ()
    pits: tuple[Pit, ...] = ()
    levels: tuple[Level, ...] = ()
    features: tuple[Feature, ...] = ()
    #: ``token_id -> square`` for tokens placed coarsely in the area.
    placements: tuple[tuple[str, Square], ...] = ()
    light: bool | None = None


class PlaceToken(_Update):
    op: Literal["place_token"] = "place_token"
    token: Token


class RemoveToken(_Update):
    op: Literal["remove_token"] = "remove_token"
    token_id: str


class MoveToken(_Update):
    """Geometry check only: each step adjacent, nothing solid entered, end
    square free. Legality and cost were Sojourn's."""

    op: Literal["move_token"] = "move_token"
    token_id: str
    route: tuple[Square, ...] = Field(min_length=1)


class SetFeatureState(_Update):
    op: Literal["set_feature_state"] = "set_feature_state"
    feature_id: str
    state: str


class AddFeature(_Update):
    op: Literal["add_feature"] = "add_feature"
    feature: Feature


class RemoveFeature(_Update):
    op: Literal["remove_feature"] = "remove_feature"
    feature_id: str


class SetTerrain(_Update):
    op: Literal["set_terrain"] = "set_terrain"
    squares: tuple[Square, ...] = Field(min_length=1)
    char: str = Field(min_length=1, max_length=1)


class SetHidden(_Update):
    """Only after adjudication decides; the Writer narrates no more than the
    reveal."""

    op: Literal["set_hidden"] = "set_hidden"
    thing_id: str
    hidden: bool


class SetLight(_Update):
    op: Literal["set_light"] = "set_light"
    thing_id: str
    lit: bool


class MarkExplored(_Update):
    op: Literal["mark_explored"] = "mark_explored"
    squares: tuple[Square, ...]


SpatialUpdate = Annotated[
    SetZone
    | Relate
    | PlaceCoarse
    | RefineArea
    | PlaceToken
    | RemoveToken
    | MoveToken
    | SetFeatureState
    | AddFeature
    | RemoveFeature
    | SetTerrain
    | SetHidden
    | SetLight
    | MarkExplored,
    Field(discriminator="op"),
]

Revision.model_rebuild()
