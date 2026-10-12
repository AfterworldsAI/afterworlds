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
    "Operation",
    "RefusalKind",
    "certify",
    "governing_fingerprint",
]

MANIFEST_VERSION = "15c-manifest-1"
ADAPTER_VERSION = "15c-d20-1"


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


class CapabilityStatus(StrEnum):
    EXECUTABLE = "executable"
    #: Needs semantic authority that awaits independent review and Owner
    #: acceptance (CRD Issue 15c candidate C1); refused as missing authority.
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

#: The release this adapter version was certified against: accepted G1
#: (oracle SHA-256 ``2ccbaeba…1258``) as published.
CERTIFIED_RELEASE: tuple[UUID, str, UUID] = (
    UUID("1299484e-c72d-509b-bd8d-d0169ee1f8d2"),
    "5.2.1-corpus.8781d4e0-a3b",
    UUID("efab27a9-5d44-52ba-ad74-47940d5fd717"),
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

_HELD_C1A = "candidate C1-A (rules, weapon rows, tools)"

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
        CapabilityStatus.HELD,
        inputs="ability or skill; a GameMaster-selected Typical DC identity",
        effects="success or failure",
        held_by=_HELD_C1A,
    ),
    Operation.SAVING_THROW: Capability(
        Operation.SAVING_THROW,
        CapabilityStatus.HELD,
        inputs="ability; a DC from the causing effect",
        effects="success or failure and the causing effect's consequence",
        held_by=_HELD_C1A + " (no admitted save identity states its own effect)",
    ),
    Operation.TOOL_CHECK: Capability(
        Operation.TOOL_CHECK,
        CapabilityStatus.HELD,
        inputs="a record-backed tool; its ability; a Utilize DC or difficulty",
        effects="success or failure",
        held_by=_HELD_C1A,
    ),
    Operation.INITIATIVE: Capability(
        Operation.INITIATIVE,
        CapabilityStatus.HELD,
        inputs="Dexterity check; Advantage/Disadvantage",
        effects="an initiative total; `undetermined` outcome; no order management",
        held_by=_HELD_C1A,
    ),
    Operation.WEAPON_ATTACK: Capability(
        Operation.WEAPON_ATTACK,
        CapabilityStatus.HELD,
        inputs="one of the 38 weapons, held; target; mastery eligibility",
        effects="damage, masteries, zero-HP consequences across subjects",
        held_by=_HELD_C1A + "; C1-B (creature targets); C1-C (character targets)",
    ),
    Operation.DEATH_SAVING_THROW: Capability(
        Operation.DEATH_SAVING_THROW,
        CapabilityStatus.HELD,
        inputs="a dying subject at the start of its turn",
        effects="death-save counters, Stable, death, recovery",
        held_by=_HELD_C1A + " and explicit actor-turn authority",
    ),
    Operation.STABILIZE: Capability(
        Operation.STABILIZE,
        CapabilityStatus.HELD,
        inputs="Help; Wisdom (Medicine) DC 10 on a subject at 0 HP",
        effects="Stable",
        held_by=_HELD_C1A,
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


def _governing(index: AuthorityIndex) -> Iterable[tuple[str, str]]:
    yield from FIXED_DC_CHECKS
    yield from _CHECK_PROCEDURE
    for record_key in CONDITION_RECORDS:
        record = index.record(record_key)
        if record is None:
            raise AdjudicationRefusal(
                RefusalKind.MISSING_AUTHORITY,
                f"governing record {record_key!r} is absent from the binding",
            )
        for c in record.components:
            yield record_key, c.semantic_key


def governing_fingerprint(index: AuthorityIndex) -> str:
    """Fingerprint of every component governing the executable check."""
    entries = []
    for record_key, component_key in _governing(index):
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
            RefusalKind.MISSING_AUTHORITY,
            f"{operation.value} needs accepted authority not yet available: "
            f"{capability.held_by}",
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
    fingerprint = governing_fingerprint(index)
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
