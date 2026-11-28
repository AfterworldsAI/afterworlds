"""Movement adjudication over mapper queries (issue #211, Movement Rules doc).

Sojourn's rules, not the mapper's: the mapper reports geometry and this module
decides legality, cost and consequences in code, with no model call per
square. Rules meaning comes from the active Rules Package (SRD 5.2.1 in this
repository). Structured facts are read from the package; rules the package
holds only as prose are encoded here, each citing its record, and
``tests/pipeline/rpg/test_movement_rules.py`` fails if either changes.

A route is resolved twice over the same code. The preview walks it over the
player snapshot, so nothing hidden shapes a cost, a warning or a refusal.
Resolution walks it over the truth, with the player snapshot saying what the
mover knew: an unspotted pit ends the move there (a planned jump needs a pit
the mover can see), and a creature the mover couldn't see stops it short.

M1 stand-ins (issue #211): no Reactions, so Disengage is recorded but changes
nothing yet; a move is priced against the mover's whole movement for its turn
until encounter state has an owner (CRD Issue 15c); a Dash is reported in the
outcome but not spent on the coordination document.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field, replace
from heapq import heappop, heappush
from typing import Any

from afterworlds.mapper import coords
from afterworlds.mapper.geometry import chebyshev, edge_between, edge_fact, is_door
from afterworlds.mapper.models import (
    FEET_PER_SQUARE,
    SIZES,
    Feature,
    MarkExplored,
    MoveToken,
    Pit,
    SetFeatureState,
    SetHidden,
    Snapshot,
    SpatialUpdate,
    Square,
    Token,
    token_squares,
)
from afterworlds.mapper.updates import footprint_free
from afterworlds.mapper.views import Allowance, party_sight
from afterworlds.models.enums import RollPurpose
from afterworlds.pipeline.rpg.dice import DiceService, RollRequest, request

#: ``(record, component) -> typed facts`` of the active Rules Package.
FactLookup = Callable[[str, str], Sequence[object]]

# -- citations -------------------------------------------------------------

#: Every movement rule and the Rules Package record it comes from
#: (record › component in the accepted oracle).
CITATIONS: dict[str, tuple[str, str]] = {
    "square_size": ("play.combat", "grid"),
    "entering_a_square": ("play.combat", "grid"),
    "corners": ("play.combat", "grid"),
    "creature_size": ("play.combat", "creature_size"),
    "moving_around_creatures": ("play.combat", "moving_around"),
    "ending_in_occupied_space": ("play.combat", "ending_in_occupied_space"),
    "breaking_up_move": ("play.combat", "breaking_up_move"),
    "difficult_terrain_cost": ("glossary.difficult_terrain", "extra_cost"),
    "difficult_spaces": ("glossary.difficult_terrain", "difficult_spaces"),
    "climbing_cost": ("glossary.climbing", "extra_cost"),
    "swimming_cost": ("glossary.swimming", "extra_cost"),
    "dash": ("glossary.dash", "extra_movement"),
    "disengage": ("glossary.disengage", "no_opportunity_attacks"),
    "long_jump": ("glossary.long_jump", "jump_distance"),
    "difficult_landing": ("glossary.long_jump", "difficult_landing"),
    "high_jump": ("glossary.high_jump", "jump_height"),
    "fall_damage": ("glossary.falling", "fall_damage"),
    "prone_on_landing": ("glossary.falling", "prone_on_landing"),
}

#: Rules the package holds only as prose: the qualified prose source and the
#: sentence each rule encodes. A test reads the source and fails if a sentence
#: is gone.
PROSE: dict[str, tuple[str, str]] = {
    "square_size": ("playing-the-game.md", "Each square represents 5 feet."),
    "entering_a_square": (
        "playing-the-game.md",
        "It costs 1 square of movement to enter an unoccupied square that's"
        " adjacent to your space (orthogonally or diagonally adjacent).",
    ),
    "corners": (
        "playing-the-game.md",
        "Diagonal movement can't cross the corner of a wall, a large tree, or"
        " another terrain feature that fills its space.",
    ),
    "moving_around_creatures": (
        "playing-the-game.md",
        "Another creature's space is Difficult Terrain for you unless that"
        " creature is Tiny or your ally.",
    ),
    "difficult_spaces": (
        "rules-glossary.md",
        "- A narrow opening sized for a creature one size smaller than you",
    ),
    "difficult_spaces_liquid": (
        "rules-glossary.md",
        "- Liquid that's between shin- and waist-deep",
    ),
    "long_jump": (
        "rules-glossary.md",
        "When you make a standing Long Jump, you can leap only half that"
        " distance. Either way, each foot you jump costs a foot of movement.",
    ),
    "high_jump": (
        "rules-glossary.md",
        "you leap into the air a number of feet equal to 3 plus your Strength"
        " modifier (minimum of 0 feet) if you move at least 10 feet on foot"
        " immediately before the jump.",
    ),
}

#: The Owner's house rule (Nov 26): the 2014 squeezing penalty. Its movement
#: half is the Package's own (a narrow opening one size smaller is Difficult
#: Terrain); the combat half is not in the Package.
HOUSE_RULE_SQUEEZING = (
    "House rule (Owner, Nov 26): while squeezing, the creature has Disadvantage"
    " on attack rolls and Dexterity saving throws, and attack rolls against it"
    " have Advantage."
)

# Player-safe refusal reasons: a fixed list, each from player-visible facts.
WALL = "wall in the way"
CORNER = "corner cut"
SOLID = "solid square"
LOCKED = "door locked"
SECOND_DOOR = "second door needs an action"
OCCUPIED_END = "square occupied at the end"
NO_ROOM = "no room to end there"
OVER_BUDGET = "over the movement budget"
OFF_MAP = "off the map"
STALE = "the scene changed since you looked"
NOT_YOURS = "not your character"
TOO_FAR_TO_JUMP = "too far to jump"
TOO_NARROW = "too narrow"
NOT_A_STEP = "not a step"
NOT_AT_START = "the route doesn't start at your character"
REFUSALS = frozenset(
    {
        WALL,
        CORNER,
        SOLID,
        LOCKED,
        SECOND_DOOR,
        OCCUPIED_END,
        OVER_BUDGET,
        OFF_MAP,
        STALE,
        NOT_YOURS,
        TOO_FAR_TO_JUMP,
        TOO_NARROW,
        NOT_A_STEP,
        NOT_AT_START,
    }
)


class RulesChanged(Exception):
    """The Rules Package no longer states a movement fact as encoded."""


@dataclass(frozen=True)
class MovementRules:
    """The movement facts read from the active Rules Package."""

    difficult_extra_per_ft: int
    climb_extra_per_ft: int
    swim_extra_per_ft: int
    dash_adds_own_speed: bool
    disengage_avoids_opportunity_attacks: bool
    fall_die: str
    fall_dice_per_ft: int
    fall_max_dice: int
    fall_leaves_prone: bool
    difficult_landing_dc: int
    #: Prose-encoded (see :data:`PROSE`).
    square_ft: int = FEET_PER_SQUARE
    jump_run_up_ft: int = 10
    high_jump_base_ft: int = 3


def lookup_from_index(index: object) -> FactLookup:
    """The runtime lookup over a character's effective authority index."""
    from afterworlds.pipeline.rpg.defense import facts_of

    def lookup(record: str, component: str) -> Sequence[object]:
        return facts_of(index, record, component)  # type: ignore[arg-type]

    return lookup


def _one(lookup: FactLookup, rule: str, family: str) -> Any:
    record, component = CITATIONS[rule]
    facts = [f for f in lookup(record, component) if _family(f) == family]
    if len(facts) != 1:
        raise RulesChanged(f"{record} › {component}: expected one {family} fact")
    return facts[0]


def _family(fact: object) -> str:
    fam = getattr(type(fact), "FAMILY", None)
    return str(fam) if fam is not None else ""


def _attr(fact: object, name: str) -> object:
    value = getattr(fact, name)
    return getattr(value, "value", value)


def _surcharge(lookup: FactLookup, rule: str) -> int:
    fact = _one(lookup, rule, "movement_cost")
    if _attr(fact, "kind") != "per_foot_surcharge" or _attr(fact, "amount") != "feet":
        raise RulesChanged(f"{CITATIONS[rule]}: not a per-foot surcharge")
    feet = fact.feet
    if not isinstance(feet, int):
        raise RulesChanged(f"{CITATIONS[rule]}: no surcharge in feet")
    return feet


def load_rules(lookup: FactLookup) -> MovementRules:
    """Read every structured movement fact; :class:`RulesChanged` when one is
    missing or says something else."""
    dash = _one(lookup, "dash", "movement_allowance")
    if _attr(dash, "basis") != "own_speed":
        raise RulesChanged("glossary.dash › extra_movement: not the mover's own Speed")
    disengage = _one(lookup, "disengage", "reaction_provocation")
    if _attr(disengage, "reaction") != "opportunity_attack" or disengage.provokes:
        raise RulesChanged("glossary.disengage: still provokes Opportunity Attacks")
    fall = _one(lookup, "fall_damage", "damage")
    dice, per = fall.dice, fall.per
    if dice is None or per is None or fall.maximum_dice is None:
        raise RulesChanged("glossary.falling › fall_damage: not dice per distance")
    if _attr(per, "basis") != "distance_fallen" or _attr(per, "unit") != "foot":
        raise RulesChanged("glossary.falling › fall_damage: not per foot fallen")
    prone = _one(lookup, "prone_on_landing", "condition_effect")
    landing = _one(lookup, "difficult_landing", "ability_check")
    return MovementRules(
        difficult_extra_per_ft=_surcharge(lookup, "difficult_terrain_cost"),
        climb_extra_per_ft=_surcharge(lookup, "climbing_cost"),
        swim_extra_per_ft=_surcharge(lookup, "swimming_cost"),
        dash_adds_own_speed=True,
        disengage_avoids_opportunity_attacks=True,
        fall_die=f"d{str(_attr(dice, 'die')).lstrip('d')}",
        fall_dice_per_ft=int(per.amount),
        fall_max_dice=int(fall.maximum_dice),
        fall_leaves_prone=(
            _attr(prone, "condition") == "prone" and _attr(prone, "effect") == "applies"
        ),
        difficult_landing_dc=int(landing.dc_value),
    )


# -- the mover -------------------------------------------------------------


@dataclass(frozen=True)
class MoverProfile:
    """What adjudication reads about the mover: from the character sheet for
    a Sojourner, from the creature's state for Sojourn's own creatures."""

    token_id: str
    walk_ft: int
    strength: int
    size: str = "medium"
    swim_ft: int = 0
    climb_ft: int = 0

    @property
    def strength_mod(self) -> int:
        return (self.strength - 10) // 2


def profile_from_state(token_id: str, state: object) -> MoverProfile | None:
    """A profile from a ``Dnd5eCharacterState``; ``None`` when it records no
    walking Speed or Strength (the move then can't be priced)."""
    speeds = getattr(state, "speeds", None) or ()
    scores = getattr(state, "ability_scores", None)
    feet = {str(_attr(s, "mode")): int(s.feet) for s in speeds}
    if "walk" not in feet or scores is None:
        return None
    size = getattr(state, "size", None)
    return MoverProfile(
        token_id=token_id,
        walk_ft=feet["walk"],
        strength=int(scores.strength),
        size=str(getattr(size, "value", size)) if size is not None else "medium",
        swim_ft=feet.get("swim", 0),
        climb_ft=feet.get("climb", 0),
    )


@dataclass(frozen=True)
class MoveIntent:
    route: tuple[Square, ...]
    dash: bool = False
    disengage: bool = False
    #: ``drawn`` or ``words``: recorded, never changes the resolution.
    source: str = "drawn"


# -- walking ---------------------------------------------------------------


@dataclass(frozen=True)
class Step:
    square: Square
    cost_ft: int
    cumulative_ft: int
    difficult: bool = False
    squeezing: bool = False
    jump_ft: int = 0
    climb_ft: int = 0
    door_opened: str | None = None
    uses_dash: bool = False
    #: Squares passed over on the way to *square* (a jumped pit), so the
    #: saved move stays a chain of adjacent squares; they cost nothing more.
    through: tuple[Square, ...] = ()


@dataclass(frozen=True)
class Walk:
    steps: tuple[Step, ...]
    refused: str | None = None
    refused_at: Square | None = None
    stopped_by: str | None = None
    stopped_at: Square | None = None
    pit_id: str | None = None
    warnings: tuple[tuple[str, str], ...] = ()

    @property
    def cost_ft(self) -> int:
        return self.steps[-1].cumulative_ft if self.steps else 0


def _feature_on(snap: Snapshot, square: Square) -> Feature | None:
    return next(
        (f for f in snap.features if square in f.squares and f.blocks_step), None
    )


def _fits_on(snap: Snapshot, a: Square, b: Square) -> str | None:
    """The size a step's narrowest opening is built for, if any."""
    fits = [f.fits for f in snap.features if f.fits and b in f.squares]
    if a[0] == b[0] or a[1] == b[1]:
        door = snap.door_at(edge_between(a, b))
        if door is not None and door.fits:
            fits.append(door.fits)
    known = [s for s in fits if s is not None]
    return min(known, key=SIZES.index) if known else None


def _corner_cut(snap: Snapshot, a: Square, b: Square) -> bool:
    n1, n2 = (b[0], a[1]), (a[0], b[1])
    lines = (
        edge_between(a, n1),
        edge_between(a, n2),
        edge_between(n1, b),
        edge_between(n2, b),
    )
    if any(edge_fact(snap, e).wall or snap.door_at(e) is not None for e in lines):
        return True
    return any(
        snap.char(n) in "# " or _feature_on(snap, n) is not None for n in (n1, n2)
    )


def walk(
    truth: Snapshot,
    known: Snapshot,
    profile: MoverProfile,
    rules: MovementRules,
    intent: MoveIntent,
) -> Walk:
    """Walk *intent* over *truth*, with *known* saying what the mover knows.

    The preview passes the player snapshot as both; resolution passes the
    truth and the player snapshot."""
    mover = truth.token(profile.token_id)
    route = intent.route
    if mover is None or mover.square is None:
        return Walk(steps=(), refused=NOT_YOURS)
    if route[0] != mover.square:
        return Walk(steps=(), refused=NOT_AT_START, refused_at=route[0])
    budget = profile.walk_ft * (2 if intent.dash else 1)
    steps: list[Step] = []
    warnings: list[tuple[str, str]] = []
    total = 0
    doors_opened = 0
    i = 0
    travelled = 0  # squares moved since the move began, for a run-up

    def refuse(reason: str, at: Square) -> Walk:
        return Walk(
            steps=tuple(steps), refused=reason, refused_at=at, warnings=tuple(warnings)
        )

    def cross(a: Square, b: Square) -> tuple[str | None, str | None]:
        """``(refusal, closed door opened)`` for one step from *a* to *b*:
        the geometry the record itself checks, judged on what is known."""
        nonlocal doors_opened
        if chebyshev(a, b) != 1:
            return NOT_A_STEP, None
        if not known.on_map(b):
            return OFF_MAP, None
        if known.char(b) in "# " or _feature_on(known, b) is not None:
            return SOLID, None
        if a[0] != b[0] and a[1] != b[1]:
            return (CORNER if _corner_cut(known, a, b) else None), None
        fact = edge_fact(known, edge_between(a, b))
        door = fact.door if fact.door is not None and not fact.door.hidden else None
        if door is None:
            return (WALL if fact.wall else None), None
        if door.state == "locked":
            return LOCKED, None
        if door.state != "closed":
            return None, None
        if doors_opened:
            return SECOND_DOOR, None
        doors_opened += 1
        return None, door.feature_id

    def cover(square: Square) -> set[Square]:
        """The squares the mover's whole footprint takes at *square*."""
        assert mover is not None  # noqa: S101 — checked above
        return set(token_squares(mover.model_copy(update={"square": square})))

    def room(a: Square, b: Square) -> bool:
        """Whether the mover's whole footprint fits at *b*, judged on what is
        known; a squeeze through an opening narrower than the mover is the
        house rule's to price, so it passes here (the end still needs room)."""
        here = cover(b)
        if len(here) == 1:
            return True  # the step itself was checked square by square
        if all(known.on_map(sq) and known.char(sq) not in "# " for sq in here):
            return True
        return _enter_cost(known, profile, rules, b, a)[2] is not False

    def unseen_at(square: Square) -> list[Token]:
        here = cover(square)
        return [
            t
            for t in truth.tokens
            if t.token_id != profile.token_id
            and here.intersection(token_squares(t))
            and known.token(t.token_id) is None
        ]

    def stop_for(creature: Token) -> Walk:
        """An unseen creature ends the move before it, on the last square
        passed where the mover fits: passing an ally is fine, ending on one
        is not, and the record refuses it."""
        assert mover is not None  # noqa: S101 — checked above
        kept = list(steps)
        while kept and footprint_free(truth, mover, kept[-1].square) is not None:
            kept.pop()
        return Walk(
            steps=tuple(kept),
            stopped_by=f"creature:{creature.token_id}",
            stopped_at=kept[-1].square if kept else route[0],
            warnings=tuple(warnings),
        )

    def hidden_pit_at(square: Square) -> Pit | None:
        pit = truth.pit_at(square)
        return pit if pit is not None and known.pit_at(square) is None else None

    while i + 1 < len(route):
        a, b = route[i], route[i + 1]
        refusal, door_opened = cross(a, b)
        if refusal is not None:
            return refuse(refusal, b)
        if known.pit_at(b) is None and not room(a, b):
            # A footprint can't pass through rock, so wherever the move is
            # cut short the record can hold the mover there.
            return refuse(NO_ROOM, b)

        # Hidden facts end the move; they never refuse it.
        if truth is not known:
            unseen = unseen_at(b)
            if unseen:
                return stop_for(unseen[0])
            hidden_pit = hidden_pit_at(b)
            if hidden_pit is not None:
                cost = rules.square_ft
                total += cost
                steps.append(
                    Step(
                        square=b,
                        cost_ft=cost,
                        cumulative_ft=total,
                        door_opened=door_opened,
                    )
                )
                return Walk(
                    steps=tuple(steps),
                    stopped_by=f"pit:{hidden_pit.pit_id}",
                    stopped_at=b,
                    pit_id=hidden_pit.pit_id,
                    warnings=tuple(warnings),
                )

        # A visible pit: a planned Long Jump over every pit square in a row.
        pit = known.pit_at(b)
        if pit is not None:
            j = i + 1
            while j < len(route) and known.pit_at(route[j]) is not None:
                j += 1
            if j >= len(route):
                return refuse(TOO_FAR_TO_JUMP, a)
            # Every step of the jump crosses the same geometry as a walk, so
            # a wall or a door between the pit squares or at the landing
            # counts too (the record refuses any it would not save).
            for k in range(i + 1, j):
                refusal, opened = cross(route[k], route[k + 1])
                if refusal is not None:
                    return refuse(refusal, route[k + 1])
                door_opened = door_opened or opened
            jump_ft = (j - i - 1) * rules.square_ft
            running = travelled * rules.square_ft >= rules.jump_run_up_ft
            reach = profile.strength if running else profile.strength // 2
            if jump_ft > reach:
                return refuse(TOO_FAR_TO_JUMP, a)
            landing = route[j]
            if not room(route[j - 1], landing):
                return refuse(NO_ROOM, landing)
            if truth is not known and unseen_at(landing):
                # Something unseen holds the landing: the mover stops before
                # the take-off, as before any unseen creature.
                return stop_for(unseen_at(landing)[0])
            cost = (
                jump_ft + _enter_cost(known, profile, rules, landing, route[j - 1])[0]
            )
            total += cost
            if total > budget:
                return refuse(OVER_BUDGET, landing)
            steps.append(
                Step(
                    square=landing,
                    cost_ft=cost,
                    cumulative_ft=total,
                    jump_ft=jump_ft,
                    door_opened=door_opened,
                    uses_dash=total > profile.walk_ft,
                    through=tuple(route[i + 1 : j]),
                )
            )
            landed_in = hidden_pit_at(landing) if truth is not known else None
            if landed_in is not None:
                return Walk(
                    steps=tuple(steps),
                    stopped_by=f"pit:{landed_in.pit_id}",
                    stopped_at=landing,
                    pit_id=landed_in.pit_id,
                    warnings=tuple(warnings),
                )
            travelled += j - i
            i = j
            continue

        cost, difficult, squeezing = _enter_cost(known, profile, rules, b, a)
        if squeezing is None:
            return refuse(TOO_NARROW, b)
        climb_ft = 0
        rise = known.height_at(b) - known.height_at(a)
        if abs(rise) > 1:
            running = travelled * rules.square_ft >= rules.jump_run_up_ft
            high = max(0, rules.high_jump_base_ft + profile.strength_mod)
            high = high if running else high // 2
            if rise > 0 and rise <= high:
                cost += rise
            else:
                extra = 0 if profile.climb_ft else rules.climb_extra_per_ft
                cost += abs(rise) * (1 + extra)
                climb_ft = abs(rise)
        total += cost
        if total > budget:
            return refuse(OVER_BUDGET, b)
        if difficult:
            warnings.append((coords.label(b), "difficult terrain"))
        steps.append(
            Step(
                square=b,
                cost_ft=cost,
                cumulative_ft=total,
                difficult=difficult,
                squeezing=squeezing,
                climb_ft=climb_ft,
                door_opened=door_opened,
                uses_dash=total > profile.walk_ft,
            )
        )
        travelled += 1
        i += 1

    end = route[-1]
    if len(route) > 1:
        # The whole footprint has to fit where the move ends, as the record
        # checks: judged on what is known, so a refusal reveals nothing.
        here = cover(end)
        if any(not known.on_map(sq) or known.char(sq) in "# " for sq in here):
            steps.pop()
            return refuse(NO_ROOM, end)
        for t in known.tokens:
            if t.token_id != profile.token_id and here.intersection(token_squares(t)):
                steps.pop()
                return refuse(OCCUPIED_END, end)
    return Walk(steps=tuple(steps), warnings=tuple(warnings))


def _enter_cost(
    snap: Snapshot,
    profile: MoverProfile,
    rules: MovementRules,
    square: Square,
    came_from: Square,
) -> tuple[int, bool, bool | None]:
    """``(feet, difficult, squeezing)``; squeezing ``None`` means the opening
    is closed to the mover (more than one size smaller)."""
    base = rules.square_ft
    ch = snap.char(square)
    difficult = ch in ",~"
    mover = snap.token(profile.token_id)
    for t in snap.tokens:
        if t.token_id == profile.token_id or square not in token_squares(t):
            continue
        ally = mover is not None and t.side == mover.side
        if not ally:
            difficult = True
    squeezing = False
    fits = _fits_on(snap, came_from, square)
    if fits is not None:
        gap = SIZES.index(profile.size) - SIZES.index(fits)
        if gap > 1:
            return base, difficult, None
        if gap == 1:
            squeezing = True
            difficult = True
    if ch == "=":
        extra = 0 if profile.swim_ft else rules.swim_extra_per_ft
        return base * (1 + extra), difficult, squeezing
    if difficult:
        return base * (1 + rules.difficult_extra_per_ft), True, squeezing
    return base, False, squeezing


def squeeze_effects(squeezing: bool) -> tuple[tuple[str, str], ...]:
    """The house rule's combat half, for the dice rails to apply."""
    if not squeezing:
        return ()
    return (
        ("attack_rolls", "disadvantage"),
        ("dexterity_saving_throws", "disadvantage"),
        ("attacks_against", "advantage"),
    )


# -- preview and allowance -------------------------------------------------


@dataclass(frozen=True)
class Preview:
    cost_ft: int
    refused: str | None
    refused_at: str | None
    warnings: tuple[tuple[str, str], ...]
    uses_dash: bool


def preview(
    player: Snapshot, profile: MoverProfile, rules: MovementRules, intent: MoveIntent
) -> Preview:
    """The player-safe preview: walked over the player snapshot only."""
    w = walk(player, player, profile, rules, intent)
    return Preview(
        cost_ft=w.cost_ft,
        refused=w.refused,
        refused_at=coords.label(w.refused_at) if w.refused_at is not None else None,
        warnings=w.warnings,
        uses_dash=any(s.uses_dash for s in w.steps),
    )


def allowance(
    player: Snapshot, profile: MoverProfile, rules: MovementRules
) -> Allowance:
    """The squares the mover can reach this turn and their cost, with Dash,
    from player-visible facts (the view's movement allowance)."""
    mover = player.token(profile.token_id)
    out = Allowance(
        token_id=profile.token_id, speed_ft=profile.walk_ft, dash_ft=profile.walk_ft
    )
    if mover is None or mover.square is None:
        return out
    best = _reachable(player, profile, rules, mover.square, profile.walk_ft * 2)
    ends = {s: c for s, (c, _, end) in best.items() if end and s != mover.square}
    costs = {coords.label(s): c for s, c in ends.items()}
    warnings: dict[str, str] = {}
    for s, c in ends.items():
        if c > profile.walk_ft:
            warnings[coords.label(s)] = "uses your Dash"
    return replace(out, costs=costs, warnings=warnings)


_NEIGHBOURS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def _reachable(
    snap: Snapshot,
    profile: MoverProfile,
    rules: MovementRules,
    start: Square,
    budget: int,
) -> dict[Square, tuple[int, tuple[Square, ...], bool]]:
    """Cheapest ``(cost, route, can_end_there)`` to each square within
    *budget*, single steps only (jumps are planned by drawing over the pit).
    Ties prefer fewer diagonal steps, then the earlier neighbour order."""
    best: dict[Square, tuple[int, tuple[Square, ...], bool]] = {
        start: (0, (start,), True)
    }
    heap: list[tuple[int, int, tuple[Square, ...]]] = [(0, 0, (start,))]
    while heap:
        cost, diag, route = heappop(heap)
        here = route[-1]
        if best[here][0] < cost:
            continue
        for dc, dr in _NEIGHBOURS:
            nxt = (here[0] + dc, here[1] + dr)
            if nxt in route or snap.pit_at(nxt) is not None:
                continue
            step = _step_cost(snap, profile, rules, route, nxt)
            if step is None:
                continue
            total = cost + step[0]
            if total > budget:
                continue
            nd = diag + (1 if dc and dr else 0)
            prior = best.get(nxt)
            if prior is None or total < prior[0]:
                best[nxt] = (total, (*route, nxt), step[1])
                heappush(heap, (total, nd, (*route, nxt)))
    return best


def _step_cost(
    snap: Snapshot,
    profile: MoverProfile,
    rules: MovementRules,
    route: tuple[Square, ...],
    nxt: Square,
) -> tuple[int, bool] | None:
    """``(cost, can_end_there)`` of extending *route* by one step, or
    ``None`` if the step is refused."""
    probe = MoveIntent(route=(*route, nxt))
    shifted = _with_mover_at(snap, profile.token_id, route[0])
    roomy = replace(profile, walk_ft=10**6)
    w = walk(shifted, shifted, roomy, rules, probe)
    if w.refused == OCCUPIED_END:
        cost, _, squeezing = _enter_cost(shifted, roomy, rules, nxt, route[-1])
        return (cost, False) if squeezing is not None else None
    if w.refused is not None or not w.steps:
        return None
    return w.steps[-1].cost_ft, True


def _with_mover_at(snap: Snapshot, token_id: str, square: Square) -> Snapshot:
    token = snap.token(token_id)
    if token is None or token.square == square:
        return snap
    return snap.model_copy(
        update={
            "tokens": tuple(
                t.model_copy(update={"square": square}) if t.token_id == token_id else t
                for t in snap.tokens
            )
        }
    )


# -- routes from words -----------------------------------------------------

_VIA = re.compile(r"\b(?:via|through|by way of|past)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class WordsRoute:
    route: tuple[Square, ...]
    destination: str
    waypoints: tuple[str, ...]
    dash: bool
    disengage: bool


def _targets(player: Snapshot) -> list[tuple[str, Square | Feature]]:
    names: list[tuple[str, Square | Feature]] = []
    for f in player.features:
        if f.label:
            names.append((f.label.lower(), f))
    return sorted(names, key=lambda n: -len(n[0]))


def route_from_words(
    text: str, player: Snapshot, profile: MoverProfile, rules: MovementRules
) -> WordsRoute | None:
    """A route from a move described in words, using only player-visible
    labels (squares like ``H5`` and named features like "the mill door").

    Deterministic, no model call: the destination is the last place named,
    places after "via", "through", "by way of" or "past" are waypoints, and
    each leg is the straight line (diagonals first) where it is legal, else
    the cheapest legal route. ``None`` when the words name no place."""
    mover = player.token(profile.token_id)
    if mover is None or mover.square is None:
        return None
    lowered = text.lower()
    found: list[tuple[int, str, Square, bool]] = []
    taken: list[tuple[int, int]] = []
    for name, target in _targets(player):
        for m in re.finditer(re.escape(name), lowered):
            if any(s < m.end() and m.start() < e for s, e in taken):
                continue
            taken.append((m.start(), m.end()))
            square = (
                target
                if isinstance(target, tuple)
                else _approach(player, target, mover.square)
            )
            if square is None:
                continue
            via = bool(_VIA.search(lowered[: m.start()].rstrip(" the")))
            found.append((m.start(), name, square, via))
    for m in re.finditer(r"\b([a-z]{1,2}\d{1,3})\b", lowered):
        if any(s < m.end() and m.start() < e for s, e in taken):
            continue
        square = coords.parse(m.group(1))
        if not player.on_map(square):
            continue
        via = bool(_VIA.search(lowered[: m.start()]))
        found.append((m.start(), m.group(1).upper(), square, via))
    found.sort()
    goals = [f for f in found if not f[3]]
    if not goals:
        return None
    dest = goals[-1]
    waypoints = [f for f in found if f[3]]
    route: tuple[Square, ...] = (mover.square,)
    for _, _, square, _ in [*waypoints, dest]:
        leg = _leg(player, profile, rules, route, square)
        route = (*route, *leg)
    return WordsRoute(
        route=route,
        destination=dest[1],
        waypoints=tuple(w[1] for w in waypoints),
        dash=bool(re.search(r"\bdash", lowered)),
        disengage=bool(re.search(r"\bdisengag", lowered)),
    )


def _approach(player: Snapshot, feature: Feature, origin: Square) -> Square | None:
    """The square a mover heads for to reach *feature*: beside a door on the
    mover's side, else the nearest open square beside the feature."""
    if feature.edge is not None:
        a, b = feature.edge.sides()
        options = [s for s in (a, b) if player.on_map(s) and player.char(s) not in "# "]
        if not options:
            return None
        return min(options, key=lambda s: (chebyshev(s, origin), s))
    near = {
        (s[0] + dc, s[1] + dr) for s in feature.squares for dc, dr in _NEIGHBOURS
    } - set(feature.squares)
    open_ = [s for s in near if player.on_map(s) and player.char(s) not in "# _"]
    return min(open_, key=lambda s: (chebyshev(s, origin), s)) if open_ else None


def _line(a: Square, b: Square) -> tuple[Square, ...]:
    out: list[Square] = []
    c, r = a
    while (c, r) != b:
        c += (b[0] > c) - (b[0] < c)
        r += (b[1] > r) - (b[1] < r)
        out.append((c, r))
    return tuple(out)


def _leg(
    player: Snapshot,
    profile: MoverProfile,
    rules: MovementRules,
    so_far: tuple[Square, ...],
    goal: Square,
) -> tuple[Square, ...]:
    start = so_far[-1]
    if start == goal:
        return ()
    line = _line(start, goal)
    shifted = _with_mover_at(player, profile.token_id, so_far[0])
    roomy = replace(profile, walk_ft=10**6)
    trial = walk(shifted, shifted, roomy, rules, MoveIntent(route=(*so_far, *line)))
    if trial.refused is None:
        return line
    moved = _with_mover_at(player, profile.token_id, start)
    best = _reachable(moved, roomy, rules, start, 10**6)
    if goal in best:
        return best[goal][1][1:]
    return line  # refused at Send with a player-safe reason


# -- resolution ------------------------------------------------------------


@dataclass(frozen=True)
class Consequence:
    kind: str
    detail: str
    roll_total: int | None = None
    rolls: tuple[int, ...] = ()
    citation: tuple[str, str] | None = None


@dataclass(frozen=True)
class FallRoll:
    """A fall's roll, for Sojourn's Turn to record on the dice rails' audit
    and the mover's sheet (ADR-015). The mapper never writes either."""

    depth_ft: int
    expression: str  # "" when the fall is too short to roll
    raw_rolls: tuple[int, ...]
    total: int
    prone: bool


@dataclass(frozen=True)
class MoveOutcome:
    """What adjudication settled, for the record, the Writer and the ledger."""

    token_id: str
    status: str  # "completed", "stopped" or "refused"
    route: tuple[Square, ...]
    travelled: tuple[Square, ...]
    distance_ft: int
    movement_spent_ft: int
    final_square: Square
    stopped_by: str | None
    refused: str | None
    dash: bool
    disengage: bool
    source: str
    consequences: tuple[Consequence, ...] = ()
    updates: tuple[SpatialUpdate, ...] = ()
    warnings: tuple[tuple[str, str], ...] = ()
    squeezing: bool = False
    citations: tuple[tuple[str, str], ...] = field(default=())
    fall: FallRoll | None = None

    def writer_facts(self) -> dict[str, object]:
        """The Writer's spatial facts: distance travelled, any interruption
        point, the consequences and the final position (acceptance 7)."""
        return {
            "status": self.status,
            "distance_travelled_ft": self.distance_ft,
            "final_position": coords.label(self.final_square),
            "interruption_point": (
                coords.label(self.final_square) if self.status == "stopped" else None
            ),
            "stopped_by": _player_reason(self.stopped_by),
            "refused": self.refused,
            "dash": self.dash,
            "consequences": [
                {"kind": c.kind, "detail": c.detail, "total": c.roll_total}
                for c in self.consequences
            ],
        }


def _player_reason(stopped_by: str | None) -> str | None:
    if stopped_by is None:
        return None
    kind = stopped_by.split(":", 1)[0]
    return {"pit": "a hidden pit", "creature": "an unseen creature"}.get(kind, kind)


def resolve(
    truth: Snapshot,
    player: Snapshot,
    profile: MoverProfile,
    rules: MovementRules,
    intent: MoveIntent,
    *,
    dice: DiceService,
    roller: tuple[str, str],
    revision: int,
) -> MoveOutcome:
    """Resolve *intent* against the true scene and return the outcome with
    the typed updates to stage with the Turn."""
    # What the mover could have known refuses the route first (the server
    # pre-checks the same preview); hidden things only stop it.
    w = walk(player, player, profile, rules, intent)
    if w.refused is None:
        w = walk(truth, player, profile, rules, intent)
    mover = truth.token(profile.token_id)
    start = (
        mover.square
        if mover is not None and mover.square is not None
        else intent.route[0]
    )
    # Every square passed over, jumped ones included: the record only saves a
    # move made of adjacent steps.
    travelled = (start, *(sq for s in w.steps for sq in (*s.through, s.square)))
    if w.refused is not None:
        return MoveOutcome(
            token_id=profile.token_id,
            status="refused",
            route=intent.route,
            travelled=(start,),
            distance_ft=0,
            movement_spent_ft=0,
            final_square=start,
            stopped_by=None,
            refused=w.refused,
            dash=False,
            disengage=intent.disengage,
            source=intent.source,
            warnings=w.warnings,
        )
    consequences: list[Consequence] = []
    updates: list[SpatialUpdate] = []
    # A door the route opens is opened first: the record refuses a step
    # through a closed door, and updates apply in order.
    for s in w.steps:
        if s.door_opened is not None:
            updates.append(
                SetFeatureState(
                    base_revision=revision, feature_id=s.door_opened, state="open"
                )
            )
            consequences.append(Consequence(kind="door_opened", detail=s.door_opened))
    if len(travelled) > 1:
        updates.append(
            MoveToken(
                base_revision=revision, token_id=profile.token_id, route=travelled
            )
        )
    citations = [CITATIONS["entering_a_square"]]
    if any(s.difficult for s in w.steps):
        citations.append(CITATIONS["difficult_terrain_cost"])
    if any(s.jump_ft for s in w.steps):
        citations.append(CITATIONS["long_jump"])
    fall: FallRoll | None = None
    if w.pit_id is not None:
        pit = truth.pit_at(travelled[-1])
        assert pit is not None
        updates.append(
            SetHidden(base_revision=revision, thing_id=pit.pit_id, hidden=False)
        )
        landed, fall = _fall(pit.depth_ft, rules, dice, roller)
        consequences.extend(landed)
        citations.extend([CITATIONS["fall_damage"], CITATIONS["prone_on_landing"]])
    if w.stopped_by is not None and w.stopped_by.startswith("creature:"):
        thing = w.stopped_by.split(":", 1)[1]
        updates.append(SetHidden(base_revision=revision, thing_id=thing, hidden=False))
        consequences.append(Consequence(kind="blocked_by_unseen", detail=thing))
    squeezing = bool(w.steps) and w.steps[-1].squeezing
    if squeezing:
        consequences.append(Consequence(kind="squeezing", detail=HOUSE_RULE_SQUEEZING))
    return MoveOutcome(
        token_id=profile.token_id,
        status="stopped" if w.stopped_by is not None else "completed",
        route=intent.route,
        travelled=travelled,
        distance_ft=sum(rules.square_ft + s.jump_ft for s in w.steps),
        movement_spent_ft=w.cost_ft,
        final_square=travelled[-1],
        stopped_by=w.stopped_by,
        refused=None,
        dash=intent.dash,
        disengage=intent.disengage,
        source=intent.source,
        consequences=tuple(consequences),
        updates=tuple(updates),
        warnings=w.warnings,
        squeezing=squeezing,
        citations=tuple(dict.fromkeys(citations)),
        fall=fall,
    )


def _fall(
    depth_ft: int, rules: MovementRules, dice: DiceService, roller: tuple[str, str]
) -> tuple[list[Consequence], FallRoll]:
    count = min(rules.fall_max_dice, depth_ft // rules.fall_dice_per_ft)
    out: list[Consequence] = []
    rolled = FallRoll(
        depth_ft=depth_ft,
        expression="",
        raw_rolls=(),
        total=0,
        prone=rules.fall_leaves_prone and count > 0,
    )
    if count:
        result = request(
            dice,
            f"{count}{rules.fall_die}",
            RollRequest(
                purpose=RollPurpose.DAMAGE,
                roller=roller,
                label=f"Falling {depth_ft} ft",
                source_refs=("glossary.falling",),
            ),
        )
        out.append(
            Consequence(
                kind="fall_damage",
                detail=f"{count}{rules.fall_die} bludgeoning from a {depth_ft}-ft fall",
                roll_total=result.chosen,
                rolls=tuple(result.raw_rolls),
                citation=CITATIONS["fall_damage"],
            )
        )
        rolled = replace(
            rolled,
            expression=f"{count}{rules.fall_die}",
            raw_rolls=tuple(result.raw_rolls),
            total=result.chosen,
        )
    if rules.fall_leaves_prone and count:
        # Prone only if the fall deals damage (``prone_on_landing`` applies
        # on any damage); Sojourn's record says whether it did.
        out.append(
            Consequence(
                kind="prone",
                detail="lands Prone unless it avoids all the damage",
                citation=CITATIONS["prone_on_landing"],
            )
        )
    return out, rolled


def explored_after(truth: Snapshot, revision: int) -> MarkExplored | None:
    """The squares the party now sees that it hadn't explored."""
    seen = [s for s in sorted(party_sight(truth)) if not truth.is_explored(s)]
    if not seen:
        return None
    return MarkExplored(base_revision=revision, squares=tuple(seen))


def tokens_of(snap: Snapshot, side: str) -> Iterable[Token]:
    return (t for t in snap.tokens if t.side == side)


__all__ = [
    "CITATIONS",
    "HOUSE_RULE_SQUEEZING",
    "PROSE",
    "REFUSALS",
    "Consequence",
    "FactLookup",
    "MoveIntent",
    "MoveOutcome",
    "MoverProfile",
    "MovementRules",
    "Preview",
    "RulesChanged",
    "Walk",
    "WordsRoute",
    "allowance",
    "explored_after",
    "is_door",
    "load_rules",
    "lookup_from_index",
    "preview",
    "profile_from_state",
    "resolve",
    "route_from_words",
    "squeeze_effects",
    "walk",
]
