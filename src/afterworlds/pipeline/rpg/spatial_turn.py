"""Spatial coherence inside the Sojourn Turn (issue #211, milestone M1).

Sojourn consults the story's active scene on every RPG Turn, whether or not
the Sojourner has the map open: the consult reads the record and changes
nothing, so opening, closing or auto-opening the view can't change a Turn.

Order inside a Turn:

1. Turn preparation (:meth:`SpatialTurnService.prepare`): one read of the
   active scene, the party-visible scene as words, and the intended move (a
   drawn route, or a destination named in words), with no outcome.
2. Planner: sees the scene and the intended move only.
3. Adjudication (:meth:`SpatialTurnService.resolve`): code walks the route
   over the true scene; a fall rolls on the dice rails. No model call per
   square, and none at all here.
4. Writer: gets distance travelled, any interruption point, consequences and
   final position.
5. The record's next revision is staged in the Turn's transaction
   (:meth:`SpatialTurnService.stage`), so it commits or rolls back with the
   Turn.

A drawn route wins over a destination in words, with a warning when they
disagree (data model doc). Words become a route through a deterministic
route query over what the mover knows (movement doc, "my design").
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.mapper import coords, store
from afterworlds.mapper.models import MapRecord, Revision, Snapshot, SpatialUpdate
from afterworlds.mapper.updates import apply_all
from afterworlds.mapper.views import player_snapshot, player_view, text_view
from afterworlds.pipeline.rpg.dice import DiceService
from afterworlds.pipeline.rpg.movement import (
    EFFECT_HELD,
    NOT_AT_START,
    NOT_YOURS,
    STALE,
    MoveIntent,
    MovementRules,
    MoveOutcome,
    MoverProfile,
    Preview,
    allowance,
    explored_after,
    load_rules,
    lookup_from_index,
    preview,
    profile_from_state,
    resolve,
    route_from_words,
    under_conditions,
)
from afterworlds.services.dnd5e_state.turn import TurnCharacter

#: Words that ask to move. A place named without one of these (``"I shoot
#: the goblin by the barrels"``) is not a move.
_MOVE_VERBS = re.compile(
    r"\b(?:walk|move|go|goes|went|head|run|ran|step|dash|sprint|cross|"
    r"make (?:my|his|her|their) way|sneak|creep|hurry|rush|approach|"
    r"jog|stride|edge|retreat|back away|charge)(?:s|es|ed|ing)?\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DrawnRoute:
    """A route the Sojourner drew on the view, as square labels."""

    squares: tuple[str, ...]
    dash: bool = False
    disengage: bool = False
    #: The ``view_hash`` of the view the route was drawn on.
    view_hash: str | None = None


@dataclass(frozen=True)
class Mover:
    """The Sojourner's token on this map, and what prices its moves."""

    profile: MoverProfile
    rules: MovementRules
    #: The subject key whose dice a fall rolls (``("character", id)``).
    roller: tuple[str, str]


#: ``(story_id, truth) -> Mover`` for the Sojourner's own token, or ``None``
#: when the story has no priced token on the map.
MoverResolver = Callable[[UUID, Snapshot], "Mover | None"]


class RouteRefused(Exception):
    """A drawn route the server won't accept: player-safe ``reason``."""

    def __init__(self, reason: str, at: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.at = at


@dataclass(frozen=True)
class SceneTurn:
    """What Turn preparation read, for the rest of the Turn."""

    record: MapRecord
    revision: Revision
    player: Snapshot
    scene_text: str
    mover: Mover | None
    intent: MoveIntent | None
    warnings: tuple[str, ...] = ()

    @property
    def truth(self) -> Snapshot:
        return self.revision.snapshot

    def planner_text(self) -> str:
        """The scene and the intended move, with nothing about how it ends
        (acceptance 7)."""
        lines = [self.scene_text]
        if self.intent is not None and self.mover is not None:
            route = " ".join(coords.label(s) for s in self.intent.route)
            how = [
                word
                for word, on in (
                    ("Dash", self.intent.dash),
                    ("Disengage", self.intent.disengage),
                )
                if on
            ]
            extra = f", with {' and '.join(how)}" if how else ""
            lines.append(
                f"Intended move ({self.intent.source}): {self.mover.profile.token_id}"
                f" along {route}{extra}"
            )
        lines.extend(f"Route note: {w}" for w in self.warnings)
        return "\n".join(lines)


def outcome_text(outcome: MoveOutcome) -> str:
    """The Writer's spatial facts as the ledger entry (acceptance 7)."""
    return json.dumps(outcome.writer_facts(), sort_keys=True)


class SpatialTurnService:
    """The per-Turn consult, movement resolution and staging."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        mover_resolver: MoverResolver,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._mover_resolver = mover_resolver
        self._clock = clock or (lambda: datetime.now(UTC))

    # -- reads ---------------------------------------------------------------

    def _scene(self, story_id: UUID) -> tuple[MapRecord, Revision] | None:
        session = self._session_factory()
        try:
            return store.active_scene(session, story_id)
        finally:
            session.close()

    def view(self, story_id: UUID) -> dict[str, object] | None:
        """The player view the browser gets (read-only)."""
        scene = self._scene(story_id)
        if scene is None:
            return None
        record, revision = scene
        player = player_snapshot(revision.snapshot)
        mover = self._mover_resolver(story_id, revision.snapshot)
        return self._view(record, revision, player, mover)

    @staticmethod
    def _view(
        record: MapRecord,
        revision: Revision,
        player: Snapshot,
        mover: Mover | None,
    ) -> dict[str, object]:
        return player_view(
            player,
            viewer=mover.profile.token_id if mover is not None else "party",
            map_id=str(record.map_id),
            revision=revision.revision,
            label=record.label,
            allowance=(
                allowance(player, mover.profile, mover.rules)
                if mover is not None
                else None
            ),
        )

    # -- Turn preparation ------------------------------------------------------

    def prepare(
        self, story_id: UUID, user_input: str, drawn: DrawnRoute | None = None
    ) -> SceneTurn | None:
        """Read the active scene and the intended move. ``None`` when the
        story has no active scene. Raises :class:`RouteRefused` for a drawn
        route the server can't accept (stale view, wrong start, off map)."""
        scene = self._scene(story_id)
        if scene is None:
            if drawn is not None:
                raise RouteRefused(STALE)
            return None
        record, revision = scene
        truth = revision.snapshot
        player = player_snapshot(truth)
        mover = self._mover_resolver(story_id, truth)
        text = text_view(player, label=record.label)
        if mover is None:
            if drawn is not None:
                raise RouteRefused(NOT_YOURS)
            return SceneTurn(record, revision, player, text, None, None)
        words = (
            route_from_words(user_input, player, mover.profile, mover.rules)
            if _MOVE_VERBS.search(user_input)
            else None
        )
        warnings: list[str] = []
        intent: MoveIntent | None = None
        if drawn is not None:
            intent = self._drawn_intent(record, revision, player, mover, drawn)
            if words is not None and words.route[-1] != intent.route[-1]:
                warnings.append(
                    "the drawn route ends at"
                    f" {coords.label(intent.route[-1])}, not where the words"
                    f" say ({words.destination}); the drawn route is used"
                )
        elif words is not None and len(words.route) > 1:
            intent = MoveIntent(
                route=words.route,
                dash=words.dash,
                disengage=words.disengage,
                source="words",
            )
        return SceneTurn(record, revision, player, text, mover, intent, tuple(warnings))

    def check(self, story_id: UUID, drawn: DrawnRoute) -> tuple[MoveIntent, Preview]:
        """The route pre-check before a Turn exists: ownership, shape,
        staleness and what the mover could know. Raises
        :class:`RouteRefused` with a player-safe reason."""
        scene = self._scene(story_id)
        if scene is None:
            raise RouteRefused(STALE)
        record, revision = scene
        player = player_snapshot(revision.snapshot)
        mover = self._mover_resolver(story_id, revision.snapshot)
        if mover is None:
            raise RouteRefused(NOT_YOURS)
        intent = self._drawn_intent(record, revision, player, mover, drawn)
        result = preview(player, mover.profile, mover.rules, intent)
        if result.refused is not None:
            raise RouteRefused(result.refused, result.refused_at)
        return intent, result

    def _drawn_intent(
        self,
        record: MapRecord,
        revision: Revision,
        player: Snapshot,
        mover: Mover,
        drawn: DrawnRoute,
    ) -> MoveIntent:
        if drawn.view_hash is not None:
            current = self._view(record, revision, player, mover)["view_hash"]
            if drawn.view_hash != current:
                raise RouteRefused(STALE)
        try:
            route = tuple(coords.parse(s) for s in drawn.squares)
        except ValueError as exc:
            raise RouteRefused("not a square on this map") from exc
        token = player.token(mover.profile.token_id)
        if len(route) < 2:
            raise RouteRefused("a route needs at least two squares")
        if token is None or token.square != route[0]:
            raise RouteRefused(NOT_AT_START, coords.label(route[0]))
        return MoveIntent(
            route=route, dash=drawn.dash, disengage=drawn.disengage, source="drawn"
        )

    # -- adjudication and staging ----------------------------------------------

    def resolve(self, scene: SceneTurn, *, dice: DiceService) -> MoveOutcome | None:
        """Resolve the intended move against the true scene; ``None`` when
        the Turn has no move."""
        if scene.intent is None or scene.mover is None:
            return None
        return resolve(
            scene.truth,
            scene.player,
            scene.mover.profile,
            scene.mover.rules,
            scene.intent,
            dice=dice,
            roller=scene.mover.roller,
            revision=scene.revision.revision,
        )

    @staticmethod
    def updates_for(scene: SceneTurn, outcome: MoveOutcome) -> list[SpatialUpdate]:
        """The outcome's typed updates plus the squares the party now sees."""
        updates: list[SpatialUpdate] = list(outcome.updates)
        if not updates:
            return updates
        base = scene.revision.revision
        after = apply_all(
            scene.truth, updates, current_revision=base, seed=scene.record.seed
        )
        explored = explored_after(after, base)
        if explored is not None:
            updates.append(explored)
        return updates

    def stage(
        self,
        session: Session,
        scene: SceneTurn,
        outcome: MoveOutcome,
        *,
        turn_id: UUID,
        node_id: UUID | None = None,
    ) -> Revision | None:
        """Stage the next revision in the Turn's transaction. Raises
        ``UpdateRefused`` when the record moved on since preparation."""
        updates = self.updates_for(scene, outcome)
        if not updates:
            return None
        return store.stage_revision(
            session,
            map_id=scene.record.map_id,
            updates=updates,
            base_revision=scene.revision.revision,
            now=self._clock(),
            turn_id=turn_id,
            node_id=node_id,
        )


#: Reviewed effects that never change Speed (the Sap and Vex masteries).
_NOT_SPEED = frozenset({"equipment.weapons.sap", "equipment.weapons.vex"})


def price_character(
    character: TurnCharacter,
) -> tuple[MoverProfile, MovementRules] | None:
    """The Sojourner's movement profile and rules from its recorded state and
    exact authority: its Speeds and Strength, limited by its conditions
    (Speed 0, Exhaustion, Prone's crawling). ``None`` when the move can't be
    priced."""
    if character.index is None:
        return None
    profile = profile_from_state(str(character.sheet_id), character.stored.state)
    if profile is None:
        return None
    limited = under_conditions(profile, character)
    if limited is None:
        return None
    if any(
        e.source.record_key not in _NOT_SPEED
        for e in character.stored.state.active_effects or ()
    ):
        # A spell, feature or item in effect may change Speed (Longstrider,
        # Haste, the Slow mastery), and none is executed here or stated as a
        # typed fact: held, as checks hold an unexecuted effect.
        limited = replace(limited, held=EFFECT_HELD)
    return limited, load_rules(lookup_from_index(character.index))


def mover_from_token_ref(
    ref_prefix: str,
    profile_for: Callable[[UUID], tuple[MoverProfile, MovementRules] | None],
) -> MoverResolver:
    """A resolver that finds the party token whose ``ref`` names the story's
    character (``"character:<sheet id>"``) and prices it from the sheet."""

    def resolve_mover(story_id: UUID, truth: Snapshot) -> Mover | None:
        priced = profile_for(story_id)
        if priced is None:
            return None
        profile, rules = priced
        for t in truth.tokens:
            if t.side == "party" and t.ref == f"{ref_prefix}:{profile.token_id}":
                return Mover(
                    profile=replace(profile, token_id=t.token_id),
                    rules=rules,
                    roller=(ref_prefix, profile.token_id),
                )
        return None

    return resolve_mover


__all__ = [
    "DrawnRoute",
    "Mover",
    "MoverResolver",
    "RouteRefused",
    "SceneTurn",
    "SpatialTurnService",
    "mover_from_token_ref",
    "outcome_text",
    "price_character",
]
