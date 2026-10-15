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

#: CRD Issue 15b: the contest operation is added and every operation's dice
#: may be the Sojourner's (an action-resolution sequence). No other governing
#: set or fingerprint moved.
MANIFEST_VERSION = "15b-manifest-5"
ADAPTER_VERSION = "15b-d20-5"


class RefusalKind(StrEnum):
    """Why a proposed mechanic did not run (AC5)."""

    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    MISSING_STATE = "missing_state"
    MISSING_AUTHORITY = "missing_authority"
    STALE_BINDING = "stale_binding"
    INCOMPATIBLE_CERTIFICATION = "incompatible_certification"
    INVALID_SELECTION = "invalid_selection"
    #: A player-rolled die where no action-resolution sequence can be
    #: persisted (CRD Issue 15b's service is not wired).
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
    CREATURE_ATTACK = "creature_attack"
    CREATURE_SAVE_EFFECT = "creature_save_effect"
    KNOCKOUT_RECOVERY = "knockout_recovery"
    CREATURE_SPECIES = "creature_species"
    CONTEST = "contest"


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
    ("play.combat", "rounds_and_turns"),
    ("glossary.resistance", "halving"),
    ("glossary.vulnerability", "doubling"),
    ("glossary.immunity", "no_effect"),
)
_WEAPON_ATTACK_RECORD_PREFIXES = ("equipment.weapons", "equipment.armor")
#: The Bloodied predicate (``damage.bloodied``): the universal procedure and
#: the Hit Point rules it reads, for every operation a Bloodied trait,
#: hit-effect damage or save can turn on.
_BLOODIED_PROCEDURE: tuple[tuple[str, str], ...] = (
    ("glossary.bloodied", "bloodied"),
    ("play.damage_and_healing", "bloodied"),
    ("play.damage_and_healing", "hit_points"),
    ("play.damage_and_healing", "temporary_hit_points"),
)
#: The typed ammunition supplies a weapon attack fires (C7 ``ammunition_supply``).
_AMMUNITION_SUPPLIES: tuple[tuple[str, str], ...] = tuple(
    (f"equipment.adventuring_gear.{name}", name)
    for name in ("arrows", "bolts", "bullets_firearm", "bullets_sling", "needles")
)
#: The creature types a target predicate reads (C8): each species' type (a
#: character's, and the Humanoid species a source-open creature may record)
#: and Find Familiar's source-qualified type choice. A creature's own type is
#: on its template, certified per subject.
_CREATURE_TYPES: tuple[tuple[str, str], ...] = (
    *(
        (f"character_origins.{name}", "creature_type")
        for name in (
            "dragonborn", "dwarf", "elf", "gnome", "goliath", "halfling",
            "human", "orc", "tiefling",
        )
    ),
    ("spells.find_familiar", "effect"),
)  # fmt: skip
#: The save procedure (prose-bound universal components, certified with the
#: operation that causes the save) and the typed rules it reads.
SAVE_PROCEDURE: tuple[tuple[str, str], ...] = (
    ("play.d20_tests", "saving_throws"),
    ("play.d20_tests", "save_ability_modifier"),
    ("play.d20_tests", "save_proficiency"),
    ("play.d20_tests", "save_dc"),
    ("play.proficiency", "saving_throw_proficiency"),
    ("glossary.saving_throw", "saving_throw"),
)
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
#: A creature's printed attack: the attack-roll procedure it shares with
#: weapon attacks, plus range and the creature-specific rules it reads.
_CREATURE_ATTACK_PROCEDURE: tuple[tuple[str, str], ...] = (
    ("play.combat", "long_range"),
    ("play.combat", "melee"),
    ("play.combat", "ranged"),
    ("play.combat", "reach"),
)
#: Action accounting (pipeline/rpg/economy.py): the turn's one action, the
#: Attack action's attack roll and the one Bonus Action an operation spends.
_ECONOMY_PROCEDURE: tuple[tuple[str, str], ...] = (
    ("glossary.action", "action"),
    ("glossary.attack", "attack_roll"),
    ("play.actions", "one_bonus_action"),
)
#: A generic two-participant contest (ADR-015b Group 17): the Owner-adopted
#: SRD 5.1 supplement S1's authored component, which states the comparison
#: and the tie, applied only through a binding whose override set carries it.
#: Without it the contest refuses as missing authority; a changed S1 moves
#: the fingerprint (incompatible certification).
CONTEST_COMPONENT: tuple[str, str] = ("play.d20_tests", "contest")
_CONTEST_PROCEDURE: tuple[tuple[str, str], ...] = (CONTEST_COMPONENT,)

#: Actor-turn edges (contract G1): the turn structure they mark.
_TURN_PROCEDURE: tuple[tuple[str, str], ...] = (
    ("play.combat", "rounds_and_turns"),
    # The turn-bounded mastery effects an edge ends.
    ("equipment.weapons.sap", "sap"),
    ("equipment.weapons.slow", "slow"),
    ("equipment.weapons.vex", "vex"),
)
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
#: Issue 15b C9 successor (oracle SHA-256 ``01729b53…ec7b``, schema 22), by
#: the projection identity it derives; a store must publish it before it binds.
#: Recertified from C8 (projection ``e4f8f4fb-…``), itself from C7
#: (``8446ab6b-…``) and the native C5 successor (``44f212d5-…``), by reviewing
#: every governing component. C9 typed only the 336 creature profiles' Skills
#: entries, which no shared governing set contains (creature templates are
#: certified per subject by :func:`certify_template`), so no fingerprint and
#: no adapter code moved; the versions stay, and a certificate's projection
#: distinguishes C8 from C9
#: (``.claude/review-notes/issue-15b-c9-recording/recert/``).
CERTIFIED_RELEASE: tuple[UUID, str, UUID] = (
    UUID("1299484e-c72d-509b-bd8d-d0169ee1f8d2"),
    "5.2.1-corpus.8781d4e0-a3b",
    UUID("3703faf5-8b51-5c3f-b28c-b378b005f7bf"),
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
        fingerprint="cf5cceb71bccab4669486638edaf556e192693413b39357539af1794ffa2c234",  # noqa: E501  # pragma: allowlist secret
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
            "a tool component and one of its typed activity identities, with "
            "the typed kind for a Gaming Set or Musical Instrument; that tool "
            "(and kind) held; validated tool proficiency, per kind for a "
            "Gaming Set or Musical Instrument"
        ),
        effects="success or failure against the activity's printed DC",
        fingerprint="929069d89f6eb1e3c7aac49cede11b5fdd2b7d6ab502f9eb92c1e21e4df1e088",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.INITIATIVE: Capability(
        Operation.INITIATIVE,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "the typed Initiative roll (a Dexterity check); Advantage/"
            "Disadvantage from typed condition facts, including Initiative's own"
        ),
        effects="an Initiative total with outcome `undetermined`; no order",
        fingerprint="2128e4ed48b6cd8c78ead7fd34db1dcad5b8195442fb31706ffed5c69436f9be",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.WEAPON_ATTACK: Capability(
        Operation.WEAPON_ATTACK,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "a wielded weapon instance of an accepted weapon record; a target "
            "character or creature of the story; the GameMaster's approved "
            "contextual facts (range band, cover, light, named enemies within 5 "
            "feet for a ranged attack, hand facts); validated proficiency and "
            "ability; for an Ammunition weapon, a held ammunition item whose typed "
            "supply serves it"
        ),
        effects=(
            "hit, miss or Critical Hit against the target's AC; damage with its "
            "responses, temporary HP and zero-HP consequences on the target; "
            "masteries; the Light and Nick extra attacks; one ammunition expended "
            "per attack, hit or miss, by CAS on the holding (none left removes "
            "it). Not yet: sight that needs a sense's range"
        ),
        fingerprint="c300a9ca00877390339759decf9884f5029aa7d6ea3100d33432f3ef4e21a6aa",  # noqa: E501  # pragma: allowlist secret
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
        fingerprint="a50a0bee9828fedc5f8e6c84c9f130d7e0abdc5743d7bc1dfff6420ea4750d61",  # noqa: E501  # pragma: allowlist secret
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
        fingerprint="883d7298958b7f109afff97c78ac567e4e1d862e234a038bd2c2bbd2e707d8b4",  # noqa: E501  # pragma: allowlist secret
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
        fingerprint="9a74de52d3437d0207127f21872ef0efa21aa734acb20f89e2463356a2a5f43f",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.KNOCKOUT_RECOVERY: Capability(
        Operation.KNOCKOUT_RECOVERY,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "the GameMaster's attestation that the Short Rest a named knockout "
            "began was completed (OD-15c-2)"
        ),
        effects="the knockout's Unconscious ends, leaving the creature Prone",
        fingerprint="9a74de52d3437d0207127f21872ef0efa21aa734acb20f89e2463356a2a5f43f",  # noqa: E501  # pragma: allowlist secret
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
        fingerprint="87e613c653e85610544f83b5aedc90eb2476480fd833a7ff50a4f1c252544665",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.END_TURN: Capability(
        Operation.END_TURN,
        CapabilityStatus.EXECUTABLE,
        inputs="the subject whose turn is active",
        effects="its turn instance ends (an appended edge)",
        fingerprint="87e613c653e85610544f83b5aedc90eb2476480fd833a7ff50a4f1c252544665",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.CREATURE_ATTACK: Capability(
        Operation.CREATURE_ATTACK,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "a continuing creature of the story and one of its template's printed "
            "attack entries admitted by the code-owned roster (roster.py); a "
            "target character or creature; the GameMaster's approved contextual "
            "facts (range band, cover, light, named enemies or allies within 5 "
            "feet, a charge, a follow-up attack, a Multiattack composition)"
        ),
        effects=(
            "hit, miss or Critical Hit against the target's AC; each damage term "
            "with responses and zero-HP consequences; a typed hit effect "
            "(condition, size limit, escape DC, turn-bounded duration, or a save "
            "against one, a Grappled-linked condition); every typed same-entry "
            "clause (creature_clauses.py); damage under Advantage or Bloodied; "
            "usage limits and Recharge; Multiattack with replacements; a save's "
            "creature-type and Elf exclusions from the target's accepted type "
            "(C8): a spared target takes the damage and makes no save. Not "
            "executed (refused): speed changes, forced movement, legendary "
            "actions, a type or species not established (creature_types.py)"
        ),
        fingerprint="26b90a5a9df851f99cf97b100ce9384a42adefaea83ea01e9e4e3ec75c7a3ecd",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.CREATURE_SAVE_EFFECT: Capability(
        Operation.CREATURE_SAVE_EFFECT,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "a continuing creature and one of its printed save-effect entries; "
            "the targets the GameMaster selects in its area (OD-15c-1); each "
            "target's save under its own binding; the entry's usage (Recharge, "
            "X/Day)"
        ),
        effects=(
            "damage rolled once: full on a failure, halved on a success when "
            "printed; a typed condition on a failure; the use spent; targets "
            "that must have a condition (from the source, or at all) and the "
            "GameMaster's enemies. Not executed (refused): creature-type, "
            "sight, environment or trigger predicates, formula DCs, failure "
            "effects beyond a condition"
        ),
        fingerprint="e09799e62b4e25f16f1c23523c725ba4269c253bf80d48f73741a2b36541e41b",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.CREATURE_SPECIES: Capability(
        Operation.CREATURE_SPECIES,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "a continuing creature whose template is a source-open Humanoid "
            "(monsters.md:55) and one accepted Humanoid species from the "
            "code-generated options (Owner decision 2026-10-13); no dice"
        ),
        effects=(
            "the creature's exact species recorded under its template and "
            "binding, by CAS when the Turn is delivered; read only by target "
            "predicates (the Ghoul's Elf exception). No traits, numbers or type "
            "change"
        ),
        fingerprint="bafd77c6c5edad6892dbce70bdfb34ad5a60636198ef82d64e71fb5b0b360e41",  # noqa: E501  # pragma: allowlist secret
    ),
    Operation.CONTEST: Capability(
        Operation.CONTEST,
        CapabilityStatus.EXECUTABLE,
        inputs=(
            "two distinct participants of the story, each with an ability and an "
            "optional skill it governs; a character's check by the 15c check "
            "procedure; a creature's from its C9 printed Skills entry (a listed "
            "skill with its usual ability is the printed total, nothing added; "
            "an atypical ability refuses; unlisted or no skill: the ability "
            "modifier; no Skills fact: missing authority); whether the acting "
            "character perceives the opposition"
        ),
        effects=(
            "a winner (the higher total) or a tie (equal totals: the prior "
            "situation is unchanged), and nothing else: no sheet, condition, "
            "damage, movement, attitude or resource change. The initiator's one "
            "action in an active turn; none outside one"
        ),
        fingerprint="20afc845fd4bd53808301cf05675159fcd39b9e8963a3ad872b9ab5ca799e2c4",  # noqa: E501  # pragma: allowlist secret
    ),
}

#: Explicit exclusions (unsupported capability, never coverage).
EXCLUSIONS: tuple[str, ...] = (
    # CRD Issue 15c excluded contests; ADR-015b Group 17 admits the generic
    # contest (Operation.CONTEST). Hide/Search recorded totals, passive
    # comparisons and other specific opposed forms keep their own rules.
    "opposed forms other than the generic contest (recorded totals, passive "
    "comparisons)",
    "legendary actions and other usage kinds (legendary uses, form-only, "
    "required entries)",
    "general spell and feature execution",
    "general healing, rests and resurrection",
    "initiative order management and general encounter state",
    "ammunition recovery after a fight (the source rule is kept, not executed)",
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
    if operation is Operation.FIXED_DC_CHECK:
        yield from FIXED_DC_CHECKS
    yield from _CHECK_PROCEDURE
    yield from {
        Operation.DIFFICULTY_CHECK: _DIFFICULTY_TABLE,
        Operation.TOOL_CHECK: _TOOL_PROCEDURE,
        Operation.INITIATIVE: _INITIATIVE_PROCEDURE,
        Operation.WEAPON_ATTACK: (
            *_WEAPON_ATTACK_PROCEDURE,
            *SAVE_PROCEDURE,
            *_ECONOMY_PROCEDURE,
            *_AMMUNITION_SUPPLIES,
            *_BLOODIED_PROCEDURE,
        ),
        Operation.BEGIN_TURN: _TURN_PROCEDURE,
        Operation.END_TURN: _TURN_PROCEDURE,
        Operation.DEATH_SAVING_THROW: _DEATH_SAVE_PROCEDURE,
        Operation.STABILIZE: (*_FIRST_AID_PROCEDURE, *_ECONOMY_PROCEDURE),
        Operation.CREATURE_SAVE_EFFECT: (
            *SAVE_PROCEDURE,
            (_DAMAGE, "half_damage"),
            (_DAMAGE, "damage_rolls"),
            (_DAMAGE, "multiple_targets"),
            *_WEAPON_ATTACK_PROCEDURE,
            *_ECONOMY_PROCEDURE,
            *_BLOODIED_PROCEDURE,
        ),
        Operation.CREATURE_ATTACK: (
            *_CREATURE_ATTACK_PROCEDURE,
            *_WEAPON_ATTACK_PROCEDURE,
            *SAVE_PROCEDURE,
            *_ECONOMY_PROCEDURE,
            *_BLOODIED_PROCEDURE,
            *_CREATURE_TYPES,
        ),
        Operation.CREATURE_SPECIES: _CREATURE_TYPES[:-1],
        Operation.CONTEST: (*_CONTEST_PROCEDURE, *_ECONOMY_PROCEDURE),
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


def certify_template(index: AuthorityIndex, template: str) -> str:
    """The digest of a creature template's exact effective components under
    *index*, for the certificate; refuses a template an override touched.

    A template is subject-specific authority, so it is not in an operation's
    pinned shared-procedure fingerprint: each creature an operation reads is
    certified against its own binding. The adapter was certified against the
    accepted source templates; an override that supplied, replaced or
    suppressed any part of one is not that authority.
    """
    record = index.record(template)
    if record is None:
        raise AdjudicationRefusal(
            RefusalKind.MISSING_AUTHORITY, f"template {template} is absent"
        )
    if template in index.overridden or any(
        c.supplied_by_override_id is not None
        or any(f.supplied_by_override_id is not None for f in c.facts)
        for c in record.components
    ):
        raise AdjudicationRefusal(
            RefusalKind.INCOMPATIBLE_CERTIFICATION,
            f"an override changed {template}; this adapter is certified against "
            "the accepted creature templates only",
        )
    entries = sorted(
        [template, c.semantic_key, component_schema_id(c)] for c in record.components
    )
    encoded = json.dumps(entries, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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
