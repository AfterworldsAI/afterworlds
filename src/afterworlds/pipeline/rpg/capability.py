"""Bounded d20 capability manifest and certification — CRD Issue 15c.

The manifest declares, per roster operation, whether this adapter executes it,
holds it on named semantic authority not yet accepted, or excludes it. Only an
``EXECUTABLE`` operation can run, and only after :func:`certify` succeeds.

Certification binds an operation to the exact authority the adapter was
certified against: the release (package, release version, mechanical
projection), the adapter and manifest versions, and a fingerprint over the
content-derived schema identity (:func:`component_schema_id`, override-aware)
of every component that governs the operation. An override that changes any
governing component, a different projection, or a missing component makes the
operation uncertified for that binding; unrelated overrides do not.

Every refusal is an :class:`AdjudicationRefusal` carrying a
:class:`RefusalKind`, so unsupported capability is distinguishable from
missing state, missing or unpublished authority, a stale binding, an
incompatible certification and an invalid selection.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from afterworlds.pipeline.rpg.models import AdjudicationPassError
from afterworlds.services.dnd5e_state.authority import (
    AuthorityIndex,
    component_schema_id,
)

__all__ = [
    "ADAPTER_VERSION",
    "MANIFEST",
    "MANIFEST_VERSION",
    "AdjudicationRefusal",
    "Capability",
    "CapabilityStatus",
    "Certificate",
    "FIXED_DC_CHECKS",
    "TOOL_COMPONENTS",
    "Operation",
    "RefusalKind",
    "certify",
    "governing_fingerprint",
]

MANIFEST_VERSION = "15c-manifest-2"
ADAPTER_VERSION = "15c-d20-2"


class RefusalKind(StrEnum):
    """Why a proposed mechanic did not run (AC5)."""

    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    MISSING_STATE = "missing_state"
    MISSING_AUTHORITY = "missing_authority"
    STALE_BINDING = "stale_binding"
    INCOMPATIBLE_CERTIFICATION = "incompatible_certification"
    INVALID_SELECTION = "invalid_selection"
    PLAYER_ROLL_UNSUPPORTED = "player_roll_unsupported"


class AdjudicationRefusal(AdjudicationPassError):
    """A typed, visible refusal. Raised before any dice or effect."""

    def __init__(self, kind: RefusalKind, detail: str) -> None:
        self.kind = kind
        self.detail = detail
        super().__init__(f"[{kind.value}] {detail}")


class Operation(StrEnum):
    """The roster's operations, as the GameMaster may name them."""

    FIXED_DC_CHECK = "fixed_dc_check"
    DIFFICULTY_CHECK = "difficulty_check"
    SAVING_THROW = "saving_throw"
    TOOL_CHECK = "tool_check"
    INITIATIVE = "initiative"
    WEAPON_ATTACK = "weapon_attack"
    DEATH_SAVING_THROW = "death_saving_throw"
    STABILIZE = "stabilize"
    BEGIN_TURN = "begin_turn"
    END_TURN = "end_turn"
    STABLE_RECOVERY = "stable_recovery"
    KNOCKOUT_RECOVERY = "knockout_recovery"


class CapabilityStatus(StrEnum):
    EXECUTABLE = "executable"
    #: Its accepted authority exists (native C5), but this adapter version does
    #: not execute it yet; ``held_by`` names what it waits on. Refused as
    #: unsupported capability, never counted as coverage.
    HELD = "held"


@dataclass(frozen=True)
class Capability:
    operation: Operation
    status: CapabilityStatus
    inputs: str
    effects: str
    held_by: str = ""
    #: Expected :func:`governing_fingerprint` under the certified release.
    fingerprint: str = ""


#: The source-fixed-DC check identities admitted for execution: a typed
#: ``ability_check`` fact (``dc_kind`` fixed) that is the only fact on its
#: component, so success or failure is the whole mechanical result. Identities
#: whose component also states an effect (Difficult Landing's Prone, Falling
#: Off, Hide's Invisible, Starvation's Exhaustion) or a zero-HP target
#: (Stabilizing, Knocking Out) stay held with the operations that own them.
FIXED_DC_CHECKS: tuple[tuple[str, str], ...] = (
    ("glossary.climbing", "difficult_climb"),
    ("glossary.long_jump", "low_obstacle"),
    ("glossary.swimming", "rough_water"),
)

#: Every tool component of the accepted Tools catalogue (native C5): each has a
#: ``tool_entry`` and one ``tool_activity`` per printed Utilize activity, either
#: directly (one activity) or one option per activity.
TOOL_COMPONENTS: tuple[tuple[str, str], ...] = (
    *(
        ("equipment.tools", c)
        for c in (
            "brewers_supplies", "carpenters_tools", "cartographers_tools",
            "cobblers_tools", "cooks_utensils", "disguise_kit", "forgery_kit",
            "glassblowers_tools", "masons_tools", "navigators_tools",
            "painters_supplies", "potters_tools",
        )
    ),
    *(
        (f"equipment.tools.{c}", c)
        for c in (
            "alchemists_supplies", "calligraphers_supplies", "gaming_set",
            "herbalism_kit", "jewelers_tools", "leatherworkers_tools",
            "musical_instrument", "poisoners_kit", "smiths_tools",
            "thieves_tools", "tinkers_tools", "weavers_tools",
            "woodcarvers_tools",
        )
    ),
)  # fmt: skip

#: Per-operation procedure and tables beyond the shared check procedure.
_DIFFICULTY_TABLE = (("play.d20_tests", "typical_dcs"),)
_TOOL_PROCEDURE = (("play.proficiency", "tool_proficiency"), *TOOL_COMPONENTS)
_INITIATIVE_PROCEDURE = (("play.combat", "initiative_roll"),)
_DAMAGE = "play.damage_and_healing"
#: The weapon attack's procedure and tables beyond the check procedure; every
#: component of the weapon, armor and Rules Glossary condition records is
#: governing too (see :func:`_governing`).
_WEAPON_ATTACK_PROCEDURE: tuple[tuple[str, str], ...] = (
    ("play.d20_tests", "attack_ability_modifier"),
    ("play.d20_tests", "natural_1"),
    ("play.d20_tests", "natural_20"),
    ("play.d20_tests", "base_ac"),
    ("play.d20_tests", "only_one_base_ac"),
    ("play.proficiency", "weapon_proficiency"),
    ("play.combat", "cover_degrees"),
    ("play.combat", "cover_selection"),
    ("play.combat", "close_combat"),
    ("play.combat", "unseen_attacker"),
    ("play.combat", "unseen_target"),
    (_DAMAGE, "damage_rolls"),
    (_DAMAGE, "critical_hits"),
    (_DAMAGE, "lost_first"),
    (_DAMAGE, "hit_points"),
    (_DAMAGE, "falling_unconscious"),
    (_DAMAGE, "monster_death"),
    (_DAMAGE, "massive_damage"),
    (_DAMAGE, "damage_at_0_hit_points"),
    (_DAMAGE, "stable"),
    (_DAMAGE, "order_of_application"),
    (_DAMAGE, "knocking_out"),
    ("glossary.resistance", "halving"),
    ("glossary.vulnerability", "doubling"),
    ("glossary.immunity", "no_effect"),
)
_WEAPON_ATTACK_RECORD_PREFIXES = ("equipment.weapons", "equipment.armor")
#: First aid (the Help action): stabilizing a dying creature, or ending a
#: knockout's Unconscious; and the recovery attestations (OD-15c-2).
_FIRST_AID_PROCEDURE: tuple[tuple[str, str], ...] = (
    ("play.d20_tests", "check_dc"),
    ("glossary.help", "assistance"),
    (_DAMAGE, "stabilizing"),
    (_DAMAGE, "knocking_out"),
    (_DAMAGE, "stable"),
    (_DAMAGE, "death_saving_throws"),
    (_DAMAGE, "falling_unconscious"),
)
_RECOVERY_PROCEDURE: tuple[tuple[str, str], ...] = (
    (_DAMAGE, "stable"),
    (_DAMAGE, "knocking_out"),
    (_DAMAGE, "death_saving_throws"),
    (_DAMAGE, "falling_unconscious"),
    ("glossary.short_rest", "short_rest"),
    ("glossary.short_rest", "interruptions"),
)
#: Actor-turn edges (contract G1): the turn structure they mark.
_TURN_PROCEDURE: tuple[tuple[str, str], ...] = (("play.combat", "rounds_and_turns"),)
#: The death save a dying subject makes when its turn begins, and what its
#: results lead to (Stable and its recovery, regaining a Hit Point).
_DEATH_SAVE_PROCEDURE: tuple[tuple[str, str], ...] = (
    *_TURN_PROCEDURE,
    ("glossary.saving_throw", "saving_throw"),
    ("glossary.death_saving_throw", "death_saving_throw"),
    (_DAMAGE, "death_saving_throws"),
    (_DAMAGE, "falling_unconscious"),
    (_DAMAGE, "stable"),
)

#: The release this adapter version was certified against: the accepted CRD
#: Issue 15c native C5 successor (oracle SHA-256 ``23e5d8e0…4f69``), by the
#: projection identity it derives; a store must publish it before it binds.
#: Recertified from G1 (projection ``efab27a9-…``) by reviewing
#: every governing component: none changed, so the check fingerprint is G1's
#: (``.claude/review-notes/issue-15c-implementation/recert/``).
CERTIFIED_RELEASE: tuple[UUID, str, UUID] = (
    UUID("1299484e-c72d-509b-bd8d-d0169ee1f8d2"),
    "5.2.1-corpus.8781d4e0-a3b",
    UUID("44f212d5-32dd-5469-8f05-f0d236492347"),
)

#: Procedure components the check executor implements (ADR-005d D3/ADR-015 D7:
#: execution is hand-authored adapter code, governed by the component it
#: implements), plus the typed tables it reads.
_CHECK_PROCEDURE: tuple[tuple[str, str], ...] = (
    ("play.d20_tests", "roll_1d20"),
    ("play.d20_tests", "add_modifiers"),
    ("play.d20_tests", "compare_to_target"),
    ("play.d20_tests", "check_ability_modifier"),
    ("play.d20_tests", "check_proficiency"),
    ("play.d20_tests", "check_dc"),
    ("play.d20_tests", "advantage_disadvantage"),
    ("play.d20_tests", "roll_two_d20s"),
    ("play.d20_tests", "no_stacking"),
    ("play.six_abilities", "ability_modifiers"),
    ("play.six_abilities", "round_down"),
    ("play.proficiency.proficiency_bonus", "proficiency_bonus_bands"),
    ("play.proficiency.skill_proficiencies", "skill_proficiency"),
    ("glossary.expertise", "expertise"),
)

#: Conditions whose every component the executor consults (facts it applies)
#: or was reviewed as not touching the subject's own checks and saves.
CONDITION_RECORDS: tuple[str, ...] = tuple(
    f"glossary.{c}"
    for c in (
        "blinded", "charmed", "deafened", "exhaustion", "frightened", "grappled",
        "incapacitated", "invisible", "paralyzed", "petrified", "poisoned",
        "prone", "restrained", "stunned", "unconscious",
    )
)  # fmt: skip

MANIFEST: dict[Operation, Capability] = {
    Operation.FIXED_DC_CHECK: Capability(
        Operation.FIXED_DC_CHECK,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "an admitted source-fixed check identity; adjusted ability score; "
            "skill proficiency/expertise; proficiency-bonus band by level; "
            "Advantage/Disadvantage and automatic outcomes from recorded "
            "conditions"
        ),
        effects="success or failure against the typed DC; no state mutation",
        fingerprint="1bd59d78e2d1242114dc51bf2d0b87298647804aa0694c1299a4c0ff07f13363",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.DIFFICULTY_CHECK: Capability(
        Operation.DIFFICULTY_CHECK,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "an ability, optionally a skill it governs, and a GameMaster-selected "
            "difficulty identity of the typed Typical DCs table; the same "
            "character inputs as a fixed-DC check"
        ),
        effects="success or failure against the band's DC; no state mutation",
        fingerprint="fe3555814a3fd87e7fa2145fe0a803f158738079e0ef46c35ec56f452150ab96",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.SAVING_THROW: Capability(
        Operation.SAVING_THROW,
        CapabilityStatus.HELD,
        inputs="ability; a DC from the causing effect",
        effects="success or failure and the causing effect's consequence",
        held_by=(
            "a causing operation: a save is made by the mastery or creature "
            "effect that forces it (pipeline/rpg/saves.py), never named alone"
        ),
    ),
    Operation.TOOL_CHECK: Capability(
        Operation.TOOL_CHECK,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "a tool component and one of its typed activity identities; the "
            "tool held; validated tool proficiency (Gaming Set and Musical "
            "Instrument refuse: 2b records no variant)"
        ),
        effects="success or failure against the activity's printed DC",
        fingerprint="aac3b1c4aa0c4637a923ef28cc76772cdfac4a251ce231af833391394589ac94",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.INITIATIVE: Capability(
        Operation.INITIATIVE,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "the typed Initiative roll (a Dexterity check); Advantage/"
            "Disadvantage from typed condition facts, including Initiative's own"
        ),
        effects="an Initiative total with outcome `undetermined`; no order",
        fingerprint="1d2c49236f64495029f8b644bd35153925ff8c10fdf1bccfa88d7e7ae87f159d",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.WEAPON_ATTACK: Capability(
        Operation.WEAPON_ATTACK,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "a wielded weapon instance of an accepted weapon record; a target "
            "character or creature of the story; the GameMaster's approved "
            "contextual facts (range band, cover, light, a hostile within 5 feet "
            "for a ranged attack); validated proficiency and ability"
        ),
        effects=(
            "hit, miss or Critical Hit against the target's AC; damage with its "
            "responses, temporary HP and zero-HP consequences on the target. Not "
            "yet: masteries, ammunition, the Light extra attack, sight that needs "
            "a sense's range"
        ),
        fingerprint="7edaa48a05d2da0e57d6a3e8a60129f139412513b8113a09855dee3b48e64c17",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.DEATH_SAVING_THROW: Capability(
        Operation.DEATH_SAVING_THROW,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "made by begin_turn, never named alone: a dying subject (0 Hit "
            "Points, not Stable, not dead) whose turn begins; Advantage/"
            "Disadvantage from typed condition facts"
        ),
        effects=(
            "a success or failure (a natural 1 two failures); three successes "
            "Stable with a rolled recovery interval; three failures death; a "
            "natural 20 regains 1 Hit Point, ending Unconscious and leaving Prone"
        ),
        fingerprint="1bdb8493ff432c4f9e21b04a12c903fcb856a6aa02fdd5f37bfc831774d6a20a",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.STABILIZE: Capability(
        Operation.STABILIZE,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "the Help action's first aid: the acting character's typed Wisdom "
            "(Medicine) check against a dying subject (stabilizing) or a "
            "knocked-out one (knocking_out); the same character inputs as a check"
        ),
        effects=(
            "on a success, a dying subject becomes Stable with a rolled recovery "
            "interval, or a knockout's Unconscious ends, leaving it Prone"
        ),
        fingerprint="1107b3f8bfa6b399524378f84f8d916f06098dd250e138ff5cd2cac2c1f2955a",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.STABLE_RECOVERY: Capability(
        Operation.STABLE_RECOVERY,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "the GameMaster's attestation of the total hours elapsed since a "
            "named Stable recovery instance began (OD-15c-2)"
        ),
        effects=(
            "once the rolled interval has elapsed: 1 Hit Point regained, "
            "Unconscious ended, Prone; the instance consumed"
        ),
        fingerprint="5835069a1e2e4922c94d61c1d79717ff6aa0aea5f0c5c8c40077c9370a1f5e06",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.KNOCKOUT_RECOVERY: Capability(
        Operation.KNOCKOUT_RECOVERY,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "the GameMaster's attestation that the Short Rest a named knockout "
            "began was completed (OD-15c-2)"
        ),
        effects="the knockout's Unconscious ends, leaving the creature Prone",
        fingerprint="5835069a1e2e4922c94d61c1d79717ff6aa0aea5f0c5c8c40077c9370a1f5e06",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.BEGIN_TURN: Capability(
        Operation.BEGIN_TURN,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "a character or creature of the story the GameMaster names, when no "
            "turn is active; at most one per delivered Turn"
        ),
        effects=(
            "the subject's turn instance begins (an appended edge); a dying "
            "subject makes its death save"
        ),
        fingerprint="c40c89c6b64ddecf12226acf87c5b1eb2c2457525d231316731cef69bbc120e1",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.END_TURN: Capability(
        Operation.END_TURN,
        CapabilityStatus.EXECUTABLE,
        inputs="the subject whose turn is active",
        effects="its turn instance ends (an appended edge)",
        fingerprint="c40c89c6b64ddecf12226acf87c5b1eb2c2457525d231316731cef69bbc120e1",  # noqa: E501  # pragma: allowlist secret
    ),
}

#: Explicit exclusions (unsupported capability, never coverage).
EXCLUSIONS: tuple[str, ...] = (
    "contests and opposed checks",
    "monster stat-block actions",
    "general spell and feature execution",
    "general healing, rests and resurrection",
    "initiative order management and general encounter state",
    "player-rolled dice (CRD Issue 15b/19b)",
)


@dataclass(frozen=True)
class Certificate:
    """Provenance of one certified operation, recorded with its result."""

    manifest_version: str
    adapter_version: str
    operation: Operation
    package_uuid: UUID
    release_version: str
    projection_uuid: UUID
    override_set_uuid: UUID
    fingerprint: str

    def as_json(self) -> dict[str, str]:
        return {
            "manifest_version": self.manifest_version,
            "adapter_version": self.adapter_version,
            "operation": self.operation.value,
            "package_uuid": str(self.package_uuid),
            "release_version": self.release_version,
            "projection_uuid": str(self.projection_uuid),
            "override_set_uuid": str(self.override_set_uuid),
            "fingerprint": self.fingerprint,
        }


def _governing(
    index: AuthorityIndex, operation: Operation = Operation.FIXED_DC_CHECK
) -> Iterable[tuple[str, str]]:
    yield from FIXED_DC_CHECKS
    yield from _CHECK_PROCEDURE
    yield from {
        Operation.DIFFICULTY_CHECK: _DIFFICULTY_TABLE,
        Operation.TOOL_CHECK: _TOOL_PROCEDURE,
        Operation.INITIATIVE: _INITIATIVE_PROCEDURE,
        Operation.WEAPON_ATTACK: _WEAPON_ATTACK_PROCEDURE,
        Operation.BEGIN_TURN: _TURN_PROCEDURE,
        Operation.END_TURN: _TURN_PROCEDURE,
        Operation.DEATH_SAVING_THROW: _DEATH_SAVE_PROCEDURE,
        Operation.STABILIZE: _FIRST_AID_PROCEDURE,
        Operation.STABLE_RECOVERY: _RECOVERY_PROCEDURE,
        Operation.KNOCKOUT_RECOVERY: _RECOVERY_PROCEDURE,
    }.get(operation, ())
    if operation is Operation.WEAPON_ATTACK:
        for record_key in sorted(index.records):
            if record_key.startswith(_WEAPON_ATTACK_RECORD_PREFIXES):
                for c in index.records[record_key].components:
                    yield record_key, c.semantic_key
    for record_key in CONDITION_RECORDS:
        record = index.record(record_key)
        if record is None:
            raise AdjudicationRefusal(
                RefusalKind.MISSING_AUTHORITY,
                f"governing record {record_key!r} is absent from the binding",
            )
        for c in record.components:
            yield record_key, c.semantic_key


def governing_fingerprint(
    index: AuthorityIndex, operation: Operation = Operation.FIXED_DC_CHECK
) -> str:
    """Fingerprint of every component governing *operation*."""
    entries = []
    for record_key, component_key in _governing(index, operation):
        component = index.component(record_key, component_key)
        if component is None:
            raise AdjudicationRefusal(
                RefusalKind.MISSING_AUTHORITY,
                f"governing component {record_key}/{component_key} is absent "
                "from the binding",
            )
        entries.append([record_key, component_key, component_schema_id(component)])
    encoded = json.dumps(sorted(entries), separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def certify(operation: Operation, index: AuthorityIndex) -> Certificate:
    """The operation's certificate under *index*, or a typed refusal."""
    capability = MANIFEST[operation]
    if capability.status is CapabilityStatus.HELD:
        raise AdjudicationRefusal(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{operation.value} is not executable in adapter {ADAPTER_VERSION}; "
            f"it waits on {capability.held_by}",
        )
    binding = index.binding
    release = (
        binding.package_uuid,
        binding.release_version,
        binding.mechanical_projection_uuid,
    )
    if release != CERTIFIED_RELEASE:
        raise AdjudicationRefusal(
            RefusalKind.INCOMPATIBLE_CERTIFICATION,
            f"{operation.value} is certified for release {CERTIFIED_RELEASE[1]} "
            f"projection {CERTIFIED_RELEASE[2]}, not {binding.release_version} "
            f"projection {binding.mechanical_projection_uuid}",
        )
    fingerprint = governing_fingerprint(index, operation)
    if fingerprint != capability.fingerprint:
        raise AdjudicationRefusal(
            RefusalKind.INCOMPATIBLE_CERTIFICATION,
            f"{operation.value}: the binding's governing authority differs from "
            "the authority this adapter was certified against (an override "
            "changed a governing component)",
        )
    return Certificate(
        manifest_version=MANIFEST_VERSION,
        adapter_version=ADAPTER_VERSION,
        operation=operation,
        package_uuid=binding.package_uuid,
        release_version=binding.release_version,
        projection_uuid=binding.mechanical_projection_uuid,
        override_set_uuid=binding.override_set_uuid,
        fingerprint=fingerprint,
    )
