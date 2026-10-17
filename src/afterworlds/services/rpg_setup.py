"""RPG product startup -- the setup owner of ADR-015c.

Owns pre-play progress: the code-owned world confirmation target, the
Sojourner's Rules Package selection, the reviewable character candidate and
the typed phase operations (Confirm world, select package, Accept character,
Complete setup). Persistent mechanical state stays with the CRD Issue 2b
character service (``dnd5e_state.service``); this module only calls it.

Setup progress lives in ``RpgNodeMetadata.setup`` on the story's anchor Node
(existing JSON carrier, versioned) and in ``RpgSessionState`` phase/status.
Callers own the transaction: setup Writer turns apply envelopes inside the
orchestrator's outer transaction; the routes commit an operation's session.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.representation import RecordKind
from afterworlds.models.dnd5e_state import Dnd5eCharacterState
from afterworlds.models.enums import (
    RpgPlayStatus,
    RpgSetupPhase,
)
from afterworlds.models.node import (
    RpgCharacterCandidate,
    RpgConfigurationConfirmationTarget,
    RpgNodeMetadata,
    RpgSetupMetadata,
    RpgWorldConfirmationTarget,
)
from afterworlds.models.session import RpgSessionState
from afterworlds.persistence.crud.node import get_node, update_node
from afterworlds.persistence.crud.session_state import (
    get_rpg_session_state_by_story,
    update_rpg_session_state,
)
from afterworlds.persistence.orm.node import NodeORM
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from afterworlds.persistence.orm.story import ArcORM, ChapterORM
from afterworlds.pipeline.rpg.setup_writer import (
    CharacterProposalResult,
    ConfigurationSummaryResult,
    RpgSetupEnvelope,
    WorldConfirmationResult,
)
from afterworlds.services.dnd5e_state import service as character_service
from afterworlds.services.dnd5e_state import store as character_store
from afterworlds.services.dnd5e_state.authority import authority_index, current_binding
from afterworlds.services.dnd5e_state.errors import (
    BindingRefusedError,
    StateServiceError,
)
from afterworlds.services.dnd5e_state.validation import (
    character_readiness,
    validate_character,
)

#: The rules systems this release can adjudicate (D20RulesSystemAdapter).
SUPPORTED_SYSTEMS = frozenset({"d20"})
_MAX_PROBLEMS = 40


class SetupConflictError(Exception):
    """Wrong phase, stale revision or changed authority: nothing changed."""


class SetupInvalidError(Exception):
    """The request or the candidate is not acceptable: nothing changed."""

    def __init__(self, message: str, problems: list[str] | None = None) -> None:
        super().__init__(message)
        self.problems = problems or []


@dataclass(frozen=True)
class PackageOption:
    package_uuid: UUID
    name: str
    system: str
    version: str


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def available_packages(session: Session, *, now: str) -> list[PackageOption]:
    """Supported, enabled, published packages whose binding resolves now.

    Quarantined, unsupported, unpublished or unresolvable packages are never
    offered (CRD Issue 21 RPG startup contract, point 2).
    """
    rows = session.scalars(
        select(RulesPackageORM)
        .where(
            RulesPackageORM.is_enabled.is_(True),
            RulesPackageORM.publication_status == "published",
            RulesPackageORM.system.in_(sorted(SUPPORTED_SYSTEMS)),
        )
        .order_by(RulesPackageORM.name, RulesPackageORM.rules_package_id)
    ).all()
    out: list[PackageOption] = []
    for row in rows:
        try:
            current_binding(session, UUID(row.rules_package_id), now=now)
        except Exception:  # noqa: BLE001 -- refused authority is simply not offered
            continue
        out.append(
            PackageOption(UUID(row.rules_package_id), row.name, row.system, row.version)
        )
    return out


def anchor_node_id(session: Session, story_id: UUID) -> UUID | None:
    found = session.execute(
        select(NodeORM.node_id)
        .join(ChapterORM, NodeORM.chapter_id == ChapterORM.chapter_id)
        .join(ArcORM, ChapterORM.arc_id == ArcORM.arc_id)
        .where(ArcORM.story_id == str(story_id))
        .limit(1)
    ).first()
    return UUID(found[0]) if found is not None else None


def load_setup(session: Session, node_id: UUID | None) -> RpgSetupMetadata:
    node = get_node(session, node_id) if node_id is not None else None
    metadata = node.mode_metadata if node is not None else None
    if isinstance(metadata, RpgNodeMetadata) and metadata.setup is not None:
        return metadata.setup
    return RpgSetupMetadata()


def _save_setup(session: Session, node_id: UUID, setup: RpgSetupMetadata) -> None:
    node = get_node(session, node_id)
    if node is None:
        raise SetupConflictError(f"anchor node {node_id} not found")
    metadata = node.mode_metadata
    if not isinstance(metadata, RpgNodeMetadata):
        metadata = RpgNodeMetadata()
    node.mode_metadata = metadata.model_copy(update={"setup": setup})
    if update_node(session, node) is None:
        raise SetupConflictError(f"anchor node {node_id} could not be updated")


def _state(session: Session, story_id: UUID) -> RpgSessionState:
    state = get_rpg_session_state_by_story(session, story_id)
    if state is None:
        raise SetupInvalidError(f"no RPG session state for story {story_id}")
    return state


# ---------------------------------------------------------------------------
# Candidate validation
# ---------------------------------------------------------------------------


def validate_candidate(
    session: Session,
    package_uuid: UUID | None,
    proposal: dict[str, Any],
    unresolved: list[str],
    *,
    now: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    """``(binding, problems)`` for an untrusted character proposal.

    Problems name the unselected package, refused authority, schema errors,
    identity/choice failures and missing applicable families. Empty means the
    recorded inputs are complete and well formed for the binding -- not that
    every build choice is legal or every mechanic executable.
    """
    problems = [f"unresolved: {note}" for note in unresolved]
    if package_uuid is None:
        return None, [*problems, "select a supported Rules Package first"]
    try:
        binding = current_binding(session, package_uuid, now=now)
    except BindingRefusedError as exc:
        return None, [*problems, f"rules authority unavailable: {exc}"]
    try:
        state = Dnd5eCharacterState.model_validate(proposal)
    except ValidationError as exc:
        for error in exc.errors()[:_MAX_PROBLEMS]:
            where = ".".join(str(p) for p in error["loc"]) or "character"
            problems.append(f"invalid at {where}: {error['msg']}")
        return binding.model_dump(mode="json"), problems
    index = authority_index(session, binding, now=now)
    failures = validate_character(index, state) + character_readiness(index, state)
    problems += [str(f) for f in failures[:_MAX_PROBLEMS]]
    return binding.model_dump(mode="json"), problems


# ---------------------------------------------------------------------------
# Setup Writer turns (inside the orchestrator's transaction)
# ---------------------------------------------------------------------------


def apply_envelope(
    session: Session,
    story_id: UUID,
    node_id: UUID,
    phase: RpgSetupPhase,
    turn_id: UUID,
    envelope: RpgSetupEnvelope,
    *,
    now: str,
    state: RpgSessionState | None = None,
) -> None:
    """Record what a delivered setup turn proposed, with that turn.

    *state* is the session state the turn already resolved, when it has one.
    """
    setup = load_setup(session, node_id)
    result = envelope.result
    if phase is RpgSetupPhase.WORLD_SETUP:
        revision = setup.world_revision + 1
        setup = setup.model_copy(
            update={
                "world_revision": revision,
                # Any new world exchange supersedes an outstanding target.
                "world_target": (
                    RpgWorldConfirmationTarget(
                        turn_id=turn_id,
                        world_revision=revision,
                        understanding=result.understanding,
                    )
                    if isinstance(result, WorldConfirmationResult)
                    else None
                ),
            }
        )
    elif phase is RpgSetupPhase.CHARACTER_CREATION and isinstance(
        result, CharacterProposalResult
    ):
        binding, problems = validate_candidate(
            session,
            setup.selected_package_uuid,
            result.character,
            result.unresolved,
            now=now,
        )
        revision = setup.candidate_revision + 1
        setup = setup.model_copy(
            update={
                "candidate_revision": revision,
                "candidate": RpgCharacterCandidate(
                    revision=revision,
                    turn_id=turn_id,
                    path=result.path,
                    proposal=result.character,
                    unresolved=result.unresolved,
                    problems=problems,
                    binding=binding,
                ),
            }
        )
    elif phase is RpgSetupPhase.PLAY_CONFIGURATION:
        # The GM's summary binds Complete setup to exactly the configuration
        # it presented; a clarification leaves nothing to confirm.
        current = state or _state(session, story_id)
        setup = setup.model_copy(
            update={
                "configuration_target": (
                    RpgConfigurationConfirmationTarget(
                        turn_id=turn_id,
                        configuration_revision=setup.configuration_revision,
                        configuration=configuration_snapshot(current),
                        summary=envelope.gm_text,
                    )
                    if isinstance(result, ConfigurationSummaryResult)
                    else None
                )
            }
        )
    else:
        return
    _save_setup(session, node_id, setup)


def configuration_snapshot(state: RpgSessionState) -> dict[str, Any]:
    """The confirmable play configuration of *state*, JSON-shaped."""
    return {
        "dice_handling": state.dice_handling.value,
        "gm_cheating": state.gm_cheating,
        "tone": state.tone.value,
        "session_type": state.session_type.value,
        "genre_flavor": state.genre_flavor,
        "house_rules": state.house_rules,
        "acceptable_content": state.acceptable_content,
    }


def configuration_revision(session: Session, story_id: UUID) -> int:
    """The setup configuration revision an edit must name (ADR-015c)."""
    return load_setup(session, anchor_node_id(session, story_id)).configuration_revision


def configuration_changed(session: Session, story_id: UUID) -> None:
    """A configuration edit during setup invalidates any outstanding GM
    summary: Complete setup must confirm what was actually presented."""
    node_id = anchor_node_id(session, story_id)
    if node_id is None:
        return
    setup = load_setup(session, node_id)
    _save_setup(
        session,
        node_id,
        setup.model_copy(
            update={
                "configuration_revision": setup.configuration_revision + 1,
                "configuration_target": None,
            }
        ),
    )


@cache
def _character_schema() -> str:
    return json.dumps(
        Dnd5eCharacterState.model_json_schema(), separators=(",", ":"), sort_keys=True
    )


def render_setup_block(
    session: Session,
    story_id: UUID,
    node_id: UUID,
    *,
    now: str,
    state: RpgSessionState | None = None,
) -> tuple[RpgSetupPhase, str]:
    """The phase and the ``[RPG Setup]`` volatile block a setup turn renders.

    *state* is the session state the turn already resolved, when it has one.
    """
    state = state or _state(session, story_id)
    setup = load_setup(session, node_id)
    lines = ["[RPG Setup]", f"phase: {state.setup_phase.value}"]
    if state.setup_phase is RpgSetupPhase.WORLD_SETUP and setup.world_target:
        lines.append(
            f"outstanding_world_understanding: {setup.world_target.understanding}"
        )
    if state.setup_phase is RpgSetupPhase.CHARACTER_CREATION:
        options = {o.package_uuid: o for o in available_packages(session, now=now)}
        chosen = (
            options.get(setup.selected_package_uuid)
            if setup.selected_package_uuid
            else None
        )
        if chosen is None:
            lines.append("rules_package: not selected yet (the Sojourner selects it)")
        else:
            lines.append(
                f"rules_package: {chosen.name} ({chosen.system} {chosen.version})"
            )
            binding = current_binding(session, chosen.package_uuid, now=now)
            index = authority_index(session, binding, now=now)
            for kind, label in (
                (RecordKind.SPECIES, "species"),
                (RecordKind.BACKGROUND, "backgrounds"),
                (RecordKind.CLASS, "classes"),
            ):
                keys = sorted(k for k, r in index.records.items() if r.kind is kind)
                lines.append(f"{label}: {', '.join(keys)}")
            lines.append(f"character_schema: {_character_schema()}")
        if setup.candidate is not None:
            lines.append(f"current_candidate_revision: {setup.candidate.revision}")
            lines += [f"candidate_problem: {p}" for p in setup.candidate.problems]
    if state.setup_phase is RpgSetupPhase.PLAY_CONFIGURATION:
        lines += [
            f"session_type: {state.session_type.value}",
            f"tone: {state.tone.value}",
            f"dice_handling: {state.dice_handling.value}",
            f"gm_cheating: {'on' if state.gm_cheating else 'off'}",
            f"house_rules: {state.house_rules or 'none'}",
            f"acceptable_content: {state.acceptable_content or 'not stated'}",
        ]
    return state.setup_phase, "\n".join(lines)


# ---------------------------------------------------------------------------
# Typed phase operations (no provider call, no settlement)
# ---------------------------------------------------------------------------


def _require_node(session: Session, story_id: UUID) -> UUID:
    node_id = anchor_node_id(session, story_id)
    if node_id is None:
        raise SetupConflictError("this story has no setup exchange yet")
    return node_id


def confirm_world(
    session: Session, story_id: UUID, expected_world_revision: int
) -> None:
    state = _state(session, story_id)
    if state.setup_phase is not RpgSetupPhase.WORLD_SETUP:
        return  # already confirmed: a repeat returns the current state
    setup = load_setup(session, _require_node(session, story_id))
    target = setup.world_target
    if (
        target is None
        or target.world_revision != expected_world_revision
        or setup.world_revision != expected_world_revision
    ):
        raise SetupConflictError(
            "the world understanding changed or awaits clarification; review the"
            " latest GM response before confirming"
        )
    update_rpg_session_state(
        session,
        state.model_copy(update={"setup_phase": RpgSetupPhase.CHARACTER_CREATION}),
    )


def select_package(
    session: Session, story_id: UUID, package_uuid: UUID, *, now: str
) -> None:
    state = _state(session, story_id)
    if state.setup_phase is not RpgSetupPhase.CHARACTER_CREATION:
        raise SetupConflictError(
            f"a Rules Package is chosen during character creation, not"
            f" {state.setup_phase.value}"
        )
    if package_uuid not in {
        o.package_uuid for o in available_packages(session, now=now)
    }:
        raise SetupInvalidError(
            "that Rules Package is not an available, supported, published package"
        )
    node_id = _require_node(session, story_id)
    setup = load_setup(session, node_id)
    if setup.selected_package_uuid == package_uuid:
        return
    update: dict[str, Any] = {"selected_package_uuid": package_uuid}
    if setup.candidate is not None:
        # The displayed candidate is revalidated under the new authority.
        binding, problems = validate_candidate(
            session,
            package_uuid,
            setup.candidate.proposal,
            setup.candidate.unresolved,
            now=now,
        )
        revision = setup.candidate_revision + 1
        update["candidate_revision"] = revision
        update["candidate"] = setup.candidate.model_copy(
            update={"revision": revision, "binding": binding, "problems": problems}
        )
    _save_setup(session, node_id, setup.model_copy(update=update))


def accept_character(
    session: Session, story_id: UUID, expected_candidate_revision: int, *, now: str
) -> None:
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.services.dnd5e_state.turn import load_turn_character

    state = _state(session, story_id)
    if state.setup_phase in (
        RpgSetupPhase.PLAY_CONFIGURATION,
        RpgSetupPhase.COMPLETE,
    ) and character_store.get_character(session, state.character_sheet_id):
        return  # already accepted: a repeat returns the current state
    if state.setup_phase is not RpgSetupPhase.CHARACTER_CREATION:
        raise SetupConflictError(
            f"a character is accepted during character creation, not"
            f" {state.setup_phase.value}"
        )
    setup = load_setup(session, _require_node(session, story_id))
    candidate = setup.candidate
    if candidate is None or candidate.revision != expected_candidate_revision:
        raise SetupConflictError(
            "the character candidate changed; review the latest candidate first"
        )
    # The displayed candidate was validated under its recorded binding; if
    # the package's exact binding moved, the Sojourner must review again.
    if setup.selected_package_uuid is not None and candidate.binding is not None:
        try:
            moved = (
                current_binding(
                    session, setup.selected_package_uuid, now=now
                ).model_dump(mode="json")
                != candidate.binding
            )
        except BindingRefusedError as exc:
            raise SetupConflictError(f"rules authority unavailable: {exc}") from exc
        if moved:
            raise SetupConflictError(
                "the Rules Package authority changed since this candidate was shown"
            )
    binding, problems = validate_candidate(
        session,
        setup.selected_package_uuid,
        candidate.proposal,
        candidate.unresolved,
        now=now,
    )
    if binding != candidate.binding:
        raise SetupConflictError(
            "the Rules Package authority changed since this candidate was shown"
        )
    if problems:
        raise SetupInvalidError("the character is not ready to accept", problems)
    assert setup.selected_package_uuid is not None  # noqa: S101 -- no problems
    try:
        stored = character_service.create_character(
            session,
            state.character_sheet_id,
            setup.selected_package_uuid,
            Dnd5eCharacterState.model_validate(candidate.proposal),
            now=now,
        )
        failures = character_service.readiness(session, stored, now=now)
        if failures:
            raise SetupInvalidError(
                "the accepted character is not ready", [str(f) for f in failures]
            )
        character = load_turn_character(session, state.character_sheet_id, now=now)
    except StateServiceError as exc:
        raise SetupInvalidError(f"the character could not be recorded: {exc}") from exc
    if not D20RulesSystemAdapter().is_adjudicable(character):
        raise SetupInvalidError("the character is not adjudicable for its binding")
    update_rpg_session_state(
        session,
        state.model_copy(update={"setup_phase": RpgSetupPhase.PLAY_CONFIGURATION}),
    )


def complete_setup(
    session: Session,
    story_id: UUID,
    expected_configuration_revision: int,
    *,
    now: str,
) -> None:
    """Confirm the configuration the GM's delivered summary presented and
    enter play. An edit since that summary (a newer revision, or a snapshot
    that no longer matches) is refused; nothing changes."""
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.services.dnd5e_state.turn import load_turn_character

    state = _state(session, story_id)
    if (
        state.setup_phase is RpgSetupPhase.COMPLETE
        and state.play_status is RpgPlayStatus.IN_PLAY
    ):
        return  # already complete: a repeat returns the current state
    if state.setup_phase is not RpgSetupPhase.PLAY_CONFIGURATION:
        raise SetupConflictError(
            f"setup completes after play configuration, not {state.setup_phase.value}"
        )
    try:
        character = load_turn_character(session, state.character_sheet_id, now=now)
    except (StateServiceError, BindingRefusedError) as exc:
        raise SetupConflictError(
            f"the accepted character is no longer current: {exc}"
        ) from exc
    setup = load_setup(session, _require_node(session, story_id))
    target = setup.configuration_target
    if target is None:
        raise SetupConflictError(
            "ask the GM to summarize the configuration before completing setup"
        )
    if (
        target.configuration_revision != expected_configuration_revision
        or setup.configuration_revision != expected_configuration_revision
        or target.configuration != configuration_snapshot(state)
    ):
        raise SetupConflictError(
            "the configuration changed since the GM summarized it; review the"
            " latest summary before completing setup"
        )
    if character.readiness or not D20RulesSystemAdapter().is_adjudicable(character):
        raise SetupInvalidError(
            "the accepted character is not ready",
            [str(f) for f in character.readiness],
        )
    update_rpg_session_state(
        session,
        state.model_copy(
            update={
                "setup_phase": RpgSetupPhase.COMPLETE,
                "play_status": RpgPlayStatus.IN_PLAY,
            }
        ),
    )


__all__ = [
    "PackageOption",
    "SUPPORTED_SYSTEMS",
    "SetupConflictError",
    "SetupInvalidError",
    "accept_character",
    "anchor_node_id",
    "apply_envelope",
    "available_packages",
    "complete_setup",
    "configuration_changed",
    "configuration_snapshot",
    "confirm_world",
    "load_setup",
    "render_setup_block",
    "select_package",
    "validate_candidate",
]
