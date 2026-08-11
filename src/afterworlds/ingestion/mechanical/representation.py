"""Records, components, typed facts, and provenance — CRD Issue 5d, Decisions 3–4.

Everything here is keyed by **committed semantic keys**, never by position and
never by a derived identity. That ordering is deliberate: ADR-005d Decision 6
requires identity derivation to be acyclic, so the projection identity is
computed from this keyed content and the stable record/component/fact IDs are
derived from that identity afterwards (see :mod:`projection`). Nothing in this
module may contain a derived ID.

The typed fact union is closed. A structure that is not one of the declared
families is rejected — there is no generic dictionary, no expression string, no
numeric key-value bag to fall back on. When a component's meaning cannot be
reduced faithfully into a declared family, the honest answer is to bind exact
governing prose under a closed irreducibility reason, not to widen the union
into something that can hold anything.

Each family is justified by authority observed in the production SRD 5.2.1
release. The first four came from the required real-corpus canaries in #137:

* ``ability_check`` — the illusion canary's typed check/DC-source authority;
* ``creature_ability_score`` — the composite-creature canary's ability grid;
* ``spell_descriptor`` — the Wish and spell-scoped-creature canaries; and
* ``progression_entry`` — the class-progression-table canary.

The rest were added by the CRD Issue 5d production-authoring checkpoint, which
measured the full release and found substantive authority those four cannot
carry: creature defence, speed, and challenge; attack and damage lines; healing;
damage responses and conditions; action economy; resource and recharge cadence;
equipment descriptors; advantage/disadvantage; spell-slot progression; class
spell-list qualifiers; and stated scaling. Each family names the corpus shape
that justifies it.

Two rules bound that growth, and neither is negotiable:

* **Closed, always.** No generic dictionary, no expression string, no numeric
  key-value bag. A structure outside the declared families is rejected. When a
  component's meaning cannot be reduced faithfully, the honest answer is exact
  governing prose under a closed irreducibility reason.
* **Declarative, never executable.** :class:`ScalingFact` records *what the
  source says scales*; it is not a formula anything evaluates, and nothing here
  defines an adjudication parameter. The typed parameter contract for spell-slot
  upcasting and variable-resource recovery remains the recorded Known Unknown
  owned by an ADR-015b amendment.

This is still not a claim of corpus completeness. Full-corpus accounting has not
run, and #137 contract 3 names family groups — targeting restrictions, contests,
critical changes, explicit probability, random-table selection, eligibility,
choices, and sequencing — that no observed shape has yet forced. Each is added
explicitly here when accounting surfaces it, or the affected component is
classified honestly as prose-bound. That obligation is met no later than
full-corpus closure; it is never met by widening the union into something that
can hold anything.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, fields
from enum import StrEnum
from typing import Any, ClassVar, cast

from afterworlds.ingestion.corpus.hashing import canonical_bytes, sha256_hex
from afterworlds.ingestion.mechanical.models import ComponentHandling

__all__ = [
    # Vocabularies
    "AbilityScore",
    "ActionCost",
    "AdvantageState",
    "AttackKind",
    "ConditionEffectKind",
    "ConditionKind",
    "Currency",
    "DamageResponseKind",
    "DamageType",
    "DcKind",
    "DieSize",
    "DurationKind",
    "FactFamily",
    "MovementMode",
    "ProvenanceRole",
    "ProvenanceTargetKind",
    "RangeKind",
    "RecordKind",
    "RecoveryTrigger",
    "RelationshipKind",
    "RollContext",
    "ScalingBasis",
    "ScalingEffect",
    "SpellSchool",
    "TimeUnit",
    "WeaponProperty",
    # Shared typed value objects
    "DiceExpression",
    "Money",
    "Rational",
    "SpellCastingTime",
    "SpellComponents",
    "SpellDuration",
    "SpellRange",
    # Typed fact families
    "AbilityCheckFact",
    "ActionEconomyFact",
    "AdvantageFact",
    "AttackRollFact",
    "ConditionEffectFact",
    "CreatureAbilityScoreFact",
    "CreatureChallengeFact",
    "CreatureDefenseFact",
    "CreatureSpeedFact",
    "DamageFact",
    "DamageResponseFact",
    "EquipmentDescriptorFact",
    "HealingFact",
    "MechanicalFact",
    "ProgressionEntryFact",
    "ResourceRecoveryFact",
    "ScalingFact",
    "SpellDescriptorFact",
    "SpellListQualifierFact",
    "SpellSlotProgressionFact",
    "WeaponPropertyFact",
    # Keyed drafts
    "ComponentDraft",
    "ProseBindingDraft",
    "ProvenanceClaim",
    "RecordDraft",
    "ReferenceDraft",
    "RelationshipDraft",
    "RepresentationDraft",
    # Errors and helpers
    "MalformedFactPayloadError",
    "UnknownFactFamilyError",
    "fact_from_payload",
    "fact_invariant_violations",
    "fact_key",
    "fact_payload",
    "prose_bindings_by_target_key",
]


class RecordKind(StrEnum):
    """Closed record vocabulary (#137 contract 3).

    ``CREATURE`` is the record kind for every creature stat block. Source
    ancestry such as *Animals* or *Monsters A–Z* is where a creature was found,
    not what kind of record it is, and rules-defined creature type is a
    descriptor rather than a kind.
    """

    GENERAL_RULE = "general_rule"
    GLOSSARY_RULE = "glossary_rule"
    CHARACTER_CREATION = "character_creation"
    CHARACTER_ADVANCEMENT = "character_advancement"
    CLASS = "class"
    CLASS_FEATURE = "class_feature"
    SPECIES = "species"
    BACKGROUND = "background"
    FEAT = "feat"
    EQUIPMENT = "equipment"
    SPELL = "spell"
    CONDITION = "condition"
    GAMEPLAY_TOOL = "gameplay_tool"
    MAGIC_ITEM = "magic_item"
    CREATURE = "creature"


class RelationshipKind(StrEnum):
    """Closed relationship vocabulary between records."""

    #: A record wholly contained by another, e.g. a spell-scoped stat block.
    SCOPED_WITHIN = "scoped_within"
    #: One record grants another, e.g. a progression level granting a feature.
    GRANTS = "grants"
    #: One record is required before another applies.
    PREREQUISITE = "prerequisite"
    #: A spell belongs to a class's spell list. Distinct from ``GRANTS``: a
    #: class spell list states *eligibility to prepare or know*, which is a
    #: membership classification, while ``GRANTS`` is a level-indexed
    #: entitlement the character actually receives. The production release
    #: carries 73 ``Spell | School | Special`` tables, all inside Classes, and
    #: neither of the other kinds says what they say.
    SPELL_LIST_MEMBER = "spell_list_member"


class ProvenanceTargetKind(StrEnum):
    """What a provenance claim attaches source text to."""

    RECORD = "record"
    COMPONENT = "component"
    FACT = "fact"
    PROSE_BINDING = "prose_binding"
    RELATIONSHIP = "relationship"
    REFERENCE = "reference"


class ProvenanceRole(StrEnum):
    """Whether a span *states* the claim or merely supports it.

    Contextual claims may overlap freely — several components can legitimately
    draw context from one sentence. Two primary claims over the same span
    cannot: that is two structures both asserting they are what the text says.
    """

    PRIMARY = "primary"
    CONTEXTUAL = "contextual"


class AbilityScore(StrEnum):
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    CONSTITUTION = "constitution"
    INTELLIGENCE = "intelligence"
    WISDOM = "wisdom"
    CHARISMA = "charisma"


class SpellSchool(StrEnum):
    ABJURATION = "abjuration"
    CONJURATION = "conjuration"
    DIVINATION = "divination"
    ENCHANTMENT = "enchantment"
    EVOCATION = "evocation"
    ILLUSION = "illusion"
    NECROMANCY = "necromancy"
    TRANSMUTATION = "transmutation"


class DcKind(StrEnum):
    """Where a check's difficulty class comes from.

    A missing source value is never invented: ``FIXED`` is the only kind that
    carries a number, and the others say *where the number comes from* rather
    than guessing one.
    """

    FIXED = "fixed"
    SPELL_SAVE_DC = "spell_save_dc"
    CONTESTED = "contested"
    GAMEMASTER_SET = "gamemaster_set"


class DieSize(StrEnum):
    """The closed set of dice the source rolls.

    A die is named, never a bare integer: ``d100`` and ``d10`` are different
    dice, and an open integer field would admit a ``d7`` the rules do not have.
    """

    D4 = "d4"
    D6 = "d6"
    D8 = "d8"
    D10 = "d10"
    D12 = "d12"
    D20 = "d20"
    D100 = "d100"

    @property
    def faces(self) -> int:
        """The highest number this die can roll.

        Derived from the member's own name rather than kept in a parallel
        table, so a die added to this union cannot arrive without its range.
        """
        return int(self.value[1:])


class DamageType(StrEnum):
    """The closed SRD damage-type vocabulary."""

    ACID = "acid"
    BLUDGEONING = "bludgeoning"
    COLD = "cold"
    FIRE = "fire"
    FORCE = "force"
    LIGHTNING = "lightning"
    NECROTIC = "necrotic"
    PIERCING = "piercing"
    POISON = "poison"
    PSYCHIC = "psychic"
    RADIANT = "radiant"
    SLASHING = "slashing"
    THUNDER = "thunder"


class DamageResponseKind(StrEnum):
    """How a creature or effect responds to a damage type."""

    RESISTANCE = "resistance"
    IMMUNITY = "immunity"
    VULNERABILITY = "vulnerability"


class AttackKind(StrEnum):
    """What kind of attack roll the source declares."""

    MELEE_WEAPON = "melee_weapon"
    RANGED_WEAPON = "ranged_weapon"
    MELEE_SPELL = "melee_spell"
    RANGED_SPELL = "ranged_spell"


class ActionCost(StrEnum):
    """The action-economy slot an effect consumes."""

    ACTION = "action"
    BONUS_ACTION = "bonus_action"
    REACTION = "reaction"
    LEGENDARY_ACTION = "legendary_action"
    #: Costs no part of the actor's economy — e.g. an ongoing trait.
    NONE = "none"
    #: The source states a cost its own vocabulary does not name. Never a
    #: stand-in for "we did not look": a component using this still carries the
    #: exact governing prose that says what actually happens.
    SPECIAL = "special"


class TimeUnit(StrEnum):
    """The closed time vocabulary for durations and casting times."""

    ROUND = "round"
    TURN = "turn"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


class DurationKind(StrEnum):
    """How long an effect lasts, as the source states it."""

    INSTANTANEOUS = "instantaneous"
    TIMED = "timed"
    UNTIL_DISPELLED = "until_dispelled"
    SPECIAL = "special"


class RangeKind(StrEnum):
    """Where an effect can reach, as the source states it."""

    SELF = "self"
    TOUCH = "touch"
    RANGED = "ranged"
    SIGHT = "sight"
    UNLIMITED = "unlimited"
    SPECIAL = "special"


class MovementMode(StrEnum):
    """A creature's movement modes."""

    WALK = "walk"
    BURROW = "burrow"
    CLIMB = "climb"
    FLY = "fly"
    SWIM = "swim"


class ConditionKind(StrEnum):
    """The closed SRD condition vocabulary."""

    BLINDED = "blinded"
    CHARMED = "charmed"
    DEAFENED = "deafened"
    EXHAUSTION = "exhaustion"
    FRIGHTENED = "frightened"
    GRAPPLED = "grappled"
    INCAPACITATED = "incapacitated"
    INVISIBLE = "invisible"
    PARALYZED = "paralyzed"
    PETRIFIED = "petrified"
    POISONED = "poisoned"
    PRONE = "prone"
    RESTRAINED = "restrained"
    STUNNED = "stunned"
    UNCONSCIOUS = "unconscious"


class ConditionEffectKind(StrEnum):
    """What a component does with a condition."""

    #: The effect imposes the condition.
    APPLIES = "applies"
    #: The subject cannot receive the condition.
    IMMUNITY = "immunity"
    #: The effect removes the condition.
    REMOVES = "removes"


class RecoveryTrigger(StrEnum):
    """When a limited resource comes back."""

    SHORT_REST = "short_rest"
    LONG_REST = "long_rest"
    DAWN = "dawn"
    #: Recovered by rolling at least a stated minimum on a stated die.
    RECHARGE_ROLL = "recharge_roll"


class AdvantageState(StrEnum):
    """Whether a stated effect confers advantage or disadvantage."""

    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"


class RollContext(StrEnum):
    """Which roll an advantage state applies to."""

    ATTACK_ROLL = "attack_roll"
    ABILITY_CHECK = "ability_check"
    SAVING_THROW = "saving_throw"
    INITIATIVE = "initiative"


class Currency(StrEnum):
    """The closed SRD coin vocabulary."""

    CP = "cp"
    SP = "sp"
    EP = "ep"
    GP = "gp"
    PP = "pp"


class WeaponProperty(StrEnum):
    """The closed SRD weapon-property vocabulary.

    Each of these is also a rule record in its own right in the production
    release (``Ammunition``, ``Finesse``, ``Heavy``, ``Light``, … on p89). This
    enum is how a *weapon* cites one; the rule text itself lives in that record.
    """

    AMMUNITION = "ammunition"
    FINESSE = "finesse"
    HEAVY = "heavy"
    LIGHT = "light"
    LOADING = "loading"
    REACH = "reach"
    THROWN = "thrown"
    TWO_HANDED = "two_handed"
    VERSATILE = "versatile"


class ScalingBasis(StrEnum):
    """What a stated increase scales with."""

    HIGHER_LEVEL_SPELL_SLOT = "higher_level_spell_slot"
    CHARACTER_LEVEL = "character_level"
    CLASS_LEVEL = "class_level"


class ScalingEffect(StrEnum):
    """Which part of an effect a stated increase applies to."""

    DAMAGE = "damage"
    HEALING = "healing"
    TARGETS = "targets"
    DURATION = "duration"
    AREA = "area"
    #: "Use the spell slot's level for the spell's level in the stat block."
    EFFECTIVE_SPELL_LEVEL = "effective_spell_level"


class FactFamily(StrEnum):
    """The closed typed-fact union's discriminator."""

    ABILITY_CHECK = "ability_check"
    ACTION_ECONOMY = "action_economy"
    ADVANTAGE = "advantage"
    ATTACK_ROLL = "attack_roll"
    CONDITION_EFFECT = "condition_effect"
    CREATURE_ABILITY_SCORE = "creature_ability_score"
    CREATURE_CHALLENGE = "creature_challenge"
    CREATURE_DEFENSE = "creature_defense"
    CREATURE_SPEED = "creature_speed"
    DAMAGE = "damage"
    DAMAGE_RESPONSE = "damage_response"
    EQUIPMENT_DESCRIPTOR = "equipment_descriptor"
    HEALING = "healing"
    PROGRESSION_ENTRY = "progression_entry"
    RESOURCE_RECOVERY = "resource_recovery"
    SCALING = "scaling"
    SPELL_DESCRIPTOR = "spell_descriptor"
    SPELL_LIST_QUALIFIER = "spell_list_qualifier"
    SPELL_SLOT_PROGRESSION = "spell_slot_progression"
    WEAPON_PROPERTY = "weapon_property"


# ---------------------------------------------------------------------------
# Shared typed value objects
# ---------------------------------------------------------------------------
#
# Families compose these rather than each flattening the same shape into its own
# fields. One definition of "a dice expression" means damage, healing, hit
# points, and recharge cannot drift into four incompatible spellings of it.
#
# They are frozen dataclasses, not dicts: a value object is as closed as a
# family, with its own builder and its own invariants.


@dataclass(frozen=True)
class DiceExpression:
    """``count`` dice of one size, plus a signed flat modifier.

    ``2d6 + 3`` is ``DiceExpression(2, DieSize.D6, 3)``. A modifier of 0 is a
    stated absence of one, not a missing value.
    """

    count: int
    die: DieSize
    modifier: int = 0


@dataclass(frozen=True)
class Rational:
    """An exact fraction — never a float.

    Challenge Rating 1/2 and a weight of 1/4 lb are exact source values.
    Rounding them into a float would make identity depend on binary
    representation and would quietly invent precision the source never stated.
    """

    numerator: int
    denominator: int


@dataclass(frozen=True)
class Money:
    """A stated price in one coin denomination."""

    amount: int
    currency: Currency


@dataclass(frozen=True)
class SpellCastingTime:
    """A spell's stated casting time.

    Either an action-economy cost (``Casting Time: Action``) or an elapsed time
    (``Casting Time: 1 Minute``) — the invariant below requires exactly one.
    """

    cost: ActionCost | None = None
    amount: int | None = None
    unit: TimeUnit | None = None


@dataclass(frozen=True)
class SpellRange:
    """A spell's stated range. ``feet`` is set exactly for ``RANGED``."""

    kind: RangeKind
    feet: int | None = None


@dataclass(frozen=True)
class SpellComponents:
    """A spell's stated components.

    The material *description* is governing prose, not a typed field: reducing
    "a diamond worth 300+ GP, which the spell consumes" to a boolean would lose
    the requirement. ``material_consumed`` is recorded because the source states
    it as a distinct mechanical fact.
    """

    verbal: bool
    somatic: bool
    material: bool
    material_consumed: bool = False


@dataclass(frozen=True)
class SpellDuration:
    """A spell's stated duration. ``amount``/``unit`` are set for ``TIMED``."""

    kind: DurationKind
    amount: int | None = None
    unit: TimeUnit | None = None
    concentration: bool = False


@dataclass(frozen=True)
class AbilityCheckFact:
    """A check or save with a typed DC source."""

    FAMILY: ClassVar[FactFamily] = FactFamily.ABILITY_CHECK

    ability: AbilityScore
    dc_kind: DcKind
    dc_value: int | None = None


@dataclass(frozen=True)
class CreatureAbilityScoreFact:
    """One row of a creature's ability grid.

    The production release prints **three** columns per ability, and they do not
    always agree with each other by derivation — the Mummy's Wisdom row is
    ``12 / +1 / +3``, where the save bonus reflects proficiency the score alone
    does not state. All three are recorded, and the two printed bonuses stay
    optional because a stat block that prints only a score has not stated them.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_ABILITY_SCORE

    ability: AbilityScore
    score: int
    #: The printed ability modifier column, when the source prints one.
    modifier: int | None = None
    #: The printed saving-throw column, when the source prints one.
    save_modifier: int | None = None


@dataclass(frozen=True)
class SpellDescriptorFact:
    """The typed descriptor line a spell record carries.

    One fact rather than five, because the source prints one line —
    ``Level 9 Conjuration (Sorcerer, Wizard) Casting Time: Action Range: Self
    Components: V Duration: Instantaneous`` — and a component may claim a span
    primarily only once. Splitting it into five families would force the
    accepted classification to cut that line into five sub-spans purely to
    satisfy the provenance rule, which is a representation artefact rather than
    a distinction the source makes.

    The material *description* remains prose-bound: see :class:`SpellComponents`.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.SPELL_DESCRIPTOR

    level: int
    school: SpellSchool
    ritual: bool
    concentration: bool
    casting_time: SpellCastingTime | None = None
    spell_range: SpellRange | None = None
    components: SpellComponents | None = None
    duration: SpellDuration | None = None


@dataclass(frozen=True)
class ProgressionEntryFact:
    """One level-indexed entitlement from a progression table.

    ``entitlement_key`` names *what* is granted. It is a semantic key, never a
    place to smuggle a second dimension: spell slots are indexed by slot level
    as well as character level, and they get their own family
    (:class:`SpellSlotProgressionFact`) precisely so nobody writes
    ``entitlement_key="slots_level_3"``.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.PROGRESSION_ENTRY

    level: int
    entitlement_key: str
    quantity: int | None = None


@dataclass(frozen=True)
class SpellSlotProgressionFact:
    """One cell of a class table's spell-slot grid.

    Two typed indices, because the source's grid has two: the class table at
    p31 is ``Level | Class Features | Cantrips | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
    9``, where the row is the character level and each numbered column is a slot
    level. Encoding the slot level into a string key would be exactly the
    stringly escape hatch ADR-005d Decision 4 forbids.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.SPELL_SLOT_PROGRESSION

    character_level: int
    slot_level: int
    slots: int


@dataclass(frozen=True)
class SpellListQualifierFact:
    """A stated qualifier on one entry of a class spell list.

    Membership itself is a :attr:`RelationshipKind.SPELL_LIST_MEMBER` edge; this
    carries what the ``Special`` column of the 73 ``Spell | School | Special``
    tables says *about* that membership. A qualifier fact without its
    membership edge is rejected by :mod:`validation` — the two are one claim.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.SPELL_LIST_QUALIFIER

    spell_record_key: str
    always_prepared: bool = False
    minimum_class_level: int | None = None


@dataclass(frozen=True)
class AttackRollFact:
    """One stated attack roll.

    ``Melee Attack Roll: +5, reach 5 ft.`` — the reach and the two range bands
    are separate optional fields because a melee attack states reach, a ranged
    attack states a normal and a long range, and inventing the absent one would
    be inventing authority.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.ATTACK_ROLL

    attack_kind: AttackKind
    to_hit_bonus: int
    reach_feet: int | None = None
    range_normal_feet: int | None = None
    range_long_feet: int | None = None


@dataclass(frozen=True)
class DamageFact:
    """One stated damage amount of one type.

    ``Hit: 10 (2d6 + 3) Bludgeoning damage`` carries both the rolled expression
    and the printed average, and both are retained: the average is what a stat
    block uses when the GameMaster does not roll, so dropping it would lose a
    stated mechanical value.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.DAMAGE

    damage_type: DamageType
    dice: DiceExpression | None = None
    flat_amount: int | None = None
    stated_average: int | None = None


@dataclass(frozen=True)
class HealingFact:
    """One stated restoration of hit points.

    ``restores_all_hit_points`` is Wish's *Instant Health* — "regain all Hit
    Points" is a stated effect with no amount, not an amount nobody recorded.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.HEALING

    dice: DiceExpression | None = None
    flat_amount: int | None = None
    restores_all_hit_points: bool = False


@dataclass(frozen=True)
class DamageResponseFact:
    """One resistance, immunity, or vulnerability to a damage type.

    The Mummy prints ``Vulnerabilities Fire`` and ``Immunities Necrotic,
    Poison`` — three facts, not one list, so each carries its own provenance.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.DAMAGE_RESPONSE

    damage_type: DamageType
    response: DamageResponseKind


@dataclass(frozen=True)
class ConditionEffectFact:
    """One condition a component applies, removes, or is immune to."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CONDITION_EFFECT

    condition: ConditionKind
    effect: ConditionEffectKind


@dataclass(frozen=True)
class CreatureDefenseFact:
    """A creature's stated Armor Class and Hit Points.

    ``AC 11`` … ``HP 58 (9d8 + 18)`` — the average and the expression are both
    printed, and both are recorded for the same reason as :class:`DamageFact`.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_DEFENSE

    armor_class: int
    hit_points: int
    hit_point_dice: DiceExpression | None = None


@dataclass(frozen=True)
class CreatureSpeedFact:
    """One of a creature's movement speeds. ``Speed 20 ft.``"""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_SPEED

    mode: MovementMode
    feet: int


@dataclass(frozen=True)
class CreatureChallengeFact:
    """A creature's stated Challenge Rating and proficiency bonus.

    CR is a :class:`Rational` because ``CR 1/2`` is an exact source value.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_CHALLENGE

    challenge_rating: Rational
    proficiency_bonus: int | None = None


@dataclass(frozen=True)
class ActionEconomyFact:
    """What action-economy slot a component's effect consumes."""

    FAMILY: ClassVar[FactFamily] = FactFamily.ACTION_ECONOMY

    cost: ActionCost


@dataclass(frozen=True)
class ResourceRecoveryFact:
    """A limited resource and when the source says it comes back.

    ``recharge_die``/``recharge_minimum`` carry ``Recharge 5–6``; they are set
    exactly for :attr:`RecoveryTrigger.RECHARGE_ROLL`.

    This records *cadence*, not an adjudication parameter. How a variable
    recovery amount is chosen at play time remains the ADR-015b Known Unknown.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.RESOURCE_RECOVERY

    resource_key: str
    recovers_on: RecoveryTrigger
    uses: int | None = None
    recharge_die: DieSize | None = None
    recharge_minimum: int | None = None


@dataclass(frozen=True)
class AdvantageFact:
    """A stated advantage or disadvantage on a named kind of roll.

    ``You have Disadvantage on attack rolls with a Heavy weapon if …`` — the
    *condition* under which it applies is governing prose; that it is
    disadvantage on attack rolls is this fact.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.ADVANTAGE

    state: AdvantageState
    context: RollContext


@dataclass(frozen=True)
class ScalingFact:
    """What the source says increases, and with what.

    ``The damage increases by 1d10 for each spell slot level above 4`` is
    ``ScalingFact(HIGHER_LEVEL_SPELL_SLOT, 4, DAMAGE, dice_increase=1d10)``.

    **Declarative only.** This records a stated increase; it is not evaluated,
    and it defines no adjudication parameter. Choosing a slot level at play time
    — the ``chosen_slot_level`` shape — is the recorded Known Unknown owned by
    an ADR-015b amendment, and nothing in this family supplies it.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.SCALING

    basis: ScalingBasis
    #: The level above which the increase begins to apply.
    threshold: int
    effect: ScalingEffect
    dice_increase: DiceExpression | None = None
    amount_increase: int | None = None


@dataclass(frozen=True)
class EquipmentDescriptorFact:
    """An item's stated price and weight.

    ``weight_pounds`` is a :class:`Rational` so ``1/4 lb`` stays exact.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.EQUIPMENT_DESCRIPTOR

    cost: Money | None = None
    weight_pounds: Rational | None = None


@dataclass(frozen=True)
class WeaponPropertyFact:
    """One weapon property a weapon carries.

    ``versatile_damage`` is set exactly for :attr:`WeaponProperty.VERSATILE`,
    and ``thrown_range`` exactly for :attr:`WeaponProperty.THROWN`, because
    those are the two properties the source parameterizes.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.WEAPON_PROPERTY

    weapon_property: WeaponProperty
    versatile_damage: DiceExpression | None = None
    thrown_range_normal_feet: int | None = None
    thrown_range_long_feet: int | None = None


MechanicalFact = (
    AbilityCheckFact
    | ActionEconomyFact
    | AdvantageFact
    | AttackRollFact
    | ConditionEffectFact
    | CreatureAbilityScoreFact
    | CreatureChallengeFact
    | CreatureDefenseFact
    | CreatureSpeedFact
    | DamageFact
    | DamageResponseFact
    | EquipmentDescriptorFact
    | HealingFact
    | ProgressionEntryFact
    | ResourceRecoveryFact
    | ScalingFact
    | SpellDescriptorFact
    | SpellListQualifierFact
    | SpellSlotProgressionFact
    | WeaponPropertyFact
)

_FACT_TYPES: dict[FactFamily, type] = {
    FactFamily.ABILITY_CHECK: AbilityCheckFact,
    FactFamily.ACTION_ECONOMY: ActionEconomyFact,
    FactFamily.ADVANTAGE: AdvantageFact,
    FactFamily.ATTACK_ROLL: AttackRollFact,
    FactFamily.CONDITION_EFFECT: ConditionEffectFact,
    FactFamily.CREATURE_ABILITY_SCORE: CreatureAbilityScoreFact,
    FactFamily.CREATURE_CHALLENGE: CreatureChallengeFact,
    FactFamily.CREATURE_DEFENSE: CreatureDefenseFact,
    FactFamily.CREATURE_SPEED: CreatureSpeedFact,
    FactFamily.DAMAGE: DamageFact,
    FactFamily.DAMAGE_RESPONSE: DamageResponseFact,
    FactFamily.EQUIPMENT_DESCRIPTOR: EquipmentDescriptorFact,
    FactFamily.HEALING: HealingFact,
    FactFamily.PROGRESSION_ENTRY: ProgressionEntryFact,
    FactFamily.RESOURCE_RECOVERY: ResourceRecoveryFact,
    FactFamily.SCALING: ScalingFact,
    FactFamily.SPELL_DESCRIPTOR: SpellDescriptorFact,
    FactFamily.SPELL_LIST_QUALIFIER: SpellListQualifierFact,
    FactFamily.SPELL_SLOT_PROGRESSION: SpellSlotProgressionFact,
    FactFamily.WEAPON_PROPERTY: WeaponPropertyFact,
}


class UnknownFactFamilyError(TypeError):
    """Raised when a structure outside the closed union is offered as a fact."""


class MalformedFactPayloadError(ValueError):
    """Raised when a persisted payload cannot rebuild its declared family."""


# ---------------------------------------------------------------------------
# Intrinsic family invariants
# ---------------------------------------------------------------------------
#
# Class membership is not validity. A fact can belong to the closed union and
# still contradict its own declared contract, and such a fact would persist as
# mechanically unusable authority. Each family therefore declares its intrinsic
# invariants here, next to the family itself, so adding a family without
# thinking about its invariants is a visible omission rather than a silent one.
#
# Only constraints intrinsic to the declared fields belong here. Corpus-specific
# limits — the SRD's 0–9 spell levels, its 1–30 ability scores — are policy about
# a particular Rules Package, not properties of the type, and enforcing them here
# would make the union quietly SRD-only. Bounds below are limited to what the
# field's own meaning requires: an ordinal or magnitude cannot be negative, a
# semantic key cannot be blank, and a stated quantity cannot be zero or less.


# Shared primitive checks. Python's ``bool`` is a subclass of ``int``, so a bare
# ``isinstance(value, int)`` accepts ``True`` — and a string like ``"false"`` is
# truthy, so a mistyped Boolean silently inverts a rule downstream. Every
# integer check below therefore excludes ``bool`` explicitly, and no check ever
# coerces: ``"12"`` is not 12, ``1`` is not ``True``, and normalizing either
# would be inventing authority the source never stated.


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _int_field(value: object, field: str) -> list[str]:
    if not _is_int(value):
        return [f"{field} must be an integer, got {type(value).__name__} {value!r}"]
    return []


def _optional_int_field(value: object, field: str) -> list[str]:
    if value is None:
        return []
    return _int_field(value, field)


def _bool_field(value: object, field: str) -> list[str]:
    if not isinstance(value, bool):
        return [f"{field} must be a boolean, got {type(value).__name__} {value!r}"]
    return []


def _str_field(value: object, field: str) -> list[str]:
    if not isinstance(value, str) or isinstance(value, StrEnum):
        return [f"{field} must be a string, got {type(value).__name__} {value!r}"]
    return []


def _enum_field(value: object, enum_cls: type[StrEnum], field: str) -> list[str]:
    """The field must hold the declared enum member, not a look-alike string.

    ``StrEnum`` members *are* strings, so a plain ``"wisdom"`` would satisfy a
    string check while carrying none of the enum's guarantees.
    """
    if not isinstance(value, enum_cls):
        return [
            f"{field} must be {enum_cls.__name__}, got "
            f"{type(value).__name__} {value!r}"
        ]
    return []


def _check_ability_check(fact: AbilityCheckFact) -> list[str]:
    findings = [
        *_enum_field(fact.ability, AbilityScore, "ability"),
        *_enum_field(fact.dc_kind, DcKind, "dc_kind"),
        *_optional_int_field(fact.dc_value, "dc_value"),
    ]
    if findings:
        # The DC relationship below reads dc_kind and dc_value; checking it
        # against mistyped values would report a second, misleading violation.
        return findings
    if fact.dc_kind is DcKind.FIXED:
        if fact.dc_value is None:
            findings.append("fixed DC without a dc_value")
    elif fact.dc_value is not None:
        findings.append(
            f"{fact.dc_kind.value} DC carries dc_value {fact.dc_value}; the "
            "value comes from the named source, not from the fact"
        )
    return findings


def _check_creature_ability_score(fact: CreatureAbilityScoreFact) -> list[str]:
    findings = [
        *_enum_field(fact.ability, AbilityScore, "ability"),
        *_int_field(fact.score, "score"),
        *_optional_int_field(fact.modifier, "modifier"),
        *_optional_int_field(fact.save_modifier, "save_modifier"),
    ]
    if findings:
        return findings
    if fact.score < 0:
        findings.append(f"negative ability score {fact.score}")
    return findings


def _check_spell_descriptor(fact: SpellDescriptorFact) -> list[str]:
    findings = [
        *_int_field(fact.level, "level"),
        *_enum_field(fact.school, SpellSchool, "school"),
        *_bool_field(fact.ritual, "ritual"),
        *_bool_field(fact.concentration, "concentration"),
        *(
            []
            if fact.casting_time is None
            else _check_casting_time(fact.casting_time, "casting_time")
        ),
        *(
            []
            if fact.spell_range is None
            else _check_spell_range(fact.spell_range, "spell_range")
        ),
        *(
            []
            if fact.components is None
            else _check_components(fact.components, "components")
        ),
        *([] if fact.duration is None else _check_duration(fact.duration, "duration")),
    ]
    if findings:
        return findings
    if fact.level < 0:
        findings.append(f"negative spell level {fact.level}")
    # The descriptor's own ``concentration`` flag and the duration's are one
    # claim printed once. Two spellings that disagree is a contradiction, not a
    # value to pick between.
    if fact.duration is not None and fact.duration.concentration != fact.concentration:
        findings.append(
            f"concentration {fact.concentration} disagrees with duration's "
            f"{fact.duration.concentration}"
        )
    return findings


def _check_progression_entry(fact: ProgressionEntryFact) -> list[str]:
    findings = [
        *_int_field(fact.level, "level"),
        *_str_field(fact.entitlement_key, "entitlement_key"),
        *_optional_int_field(fact.quantity, "quantity"),
    ]
    if findings:
        return findings
    if fact.level < 0:
        findings.append(f"negative progression level {fact.level}")
    if not fact.entitlement_key.strip():
        findings.append("progression entry without an entitlement key")
    if fact.quantity is not None and fact.quantity < 1:
        findings.append(f"progression quantity {fact.quantity} grants nothing")
    return findings


# -- Value-object invariants ------------------------------------------------
#
# A value object is as closed as a family and gets the same treatment: the exact
# declared type, then its own contract. Checking them here rather than inside
# each family means damage, healing, and hit points cannot disagree about what
# makes a dice expression valid.


def _optional_enum_field(
    value: object, enum_cls: type[StrEnum], field: str
) -> list[str]:
    if value is None:
        return []
    return _enum_field(value, enum_cls, field)


def _vo_field(value: object, cls: type, field: str) -> list[str]:
    """The field must hold that exact value-object type, or nothing."""
    if type(value) is not cls:
        return [f"{field} must be {cls.__name__}, got {type(value).__name__} {value!r}"]
    return []


def _check_dice(value: object, field: str) -> list[str]:
    if findings := _vo_field(value, DiceExpression, field):
        return findings
    dice = cast(DiceExpression, value)
    findings = [
        *_int_field(dice.count, f"{field}.count"),
        *_enum_field(dice.die, DieSize, f"{field}.die"),
        *_int_field(dice.modifier, f"{field}.modifier"),
    ]
    if findings:
        return findings
    if dice.count < 1:
        findings.append(f"{field}.count {dice.count} rolls no dice")
    return findings


def _check_optional_dice(value: object, field: str) -> list[str]:
    return [] if value is None else _check_dice(value, field)


def _check_rational(value: object, field: str) -> list[str]:
    if findings := _vo_field(value, Rational, field):
        return findings
    r = cast(Rational, value)
    findings = [
        *_int_field(r.numerator, f"{field}.numerator"),
        *_int_field(r.denominator, f"{field}.denominator"),
    ]
    if findings:
        return findings
    if r.denominator <= 0:
        findings.append(f"{field}.denominator {r.denominator} is not positive")
    if r.numerator < 0:
        findings.append(f"{field}.numerator {r.numerator} is negative")
    return findings


def _check_optional_rational(value: object, field: str) -> list[str]:
    return [] if value is None else _check_rational(value, field)


def _check_money(value: object, field: str) -> list[str]:
    if findings := _vo_field(value, Money, field):
        return findings
    money = cast(Money, value)
    findings = [
        *_int_field(money.amount, f"{field}.amount"),
        *_enum_field(money.currency, Currency, f"{field}.currency"),
    ]
    if findings:
        return findings
    if money.amount < 0:
        findings.append(f"{field}.amount {money.amount} is negative")
    return findings


def _check_casting_time(value: object, field: str) -> list[str]:
    if findings := _vo_field(value, SpellCastingTime, field):
        return findings
    ct = cast(SpellCastingTime, value)
    findings = [
        *_optional_enum_field(ct.cost, ActionCost, f"{field}.cost"),
        *_optional_int_field(ct.amount, f"{field}.amount"),
        *_optional_enum_field(ct.unit, TimeUnit, f"{field}.unit"),
    ]
    if findings:
        return findings
    elapsed = ct.amount is not None or ct.unit is not None
    if (ct.cost is None) == (not elapsed):
        findings.append(
            f"{field}: state exactly one of an action cost or an elapsed time"
        )
    if elapsed and (ct.amount is None or ct.unit is None):
        findings.append(f"{field}: an elapsed casting time needs both amount and unit")
    if ct.amount is not None and ct.amount < 1:
        findings.append(f"{field}.amount {ct.amount} is not a duration")
    return findings


def _check_spell_range(value: object, field: str) -> list[str]:
    if findings := _vo_field(value, SpellRange, field):
        return findings
    rng = cast(SpellRange, value)
    findings = [
        *_enum_field(rng.kind, RangeKind, f"{field}.kind"),
        *_optional_int_field(rng.feet, f"{field}.feet"),
    ]
    if findings:
        return findings
    if rng.kind is RangeKind.RANGED:
        if rng.feet is None:
            findings.append(f"{field}: a ranged spell states a distance")
        elif rng.feet < 1:
            findings.append(f"{field}.feet {rng.feet} is not a distance")
    elif rng.feet is not None:
        findings.append(
            f"{field}: {rng.kind.value} range carries feet {rng.feet}; the "
            "distance comes from the named kind, not from the fact"
        )
    return findings


def _check_components(value: object, field: str) -> list[str]:
    if findings := _vo_field(value, SpellComponents, field):
        return findings
    c = cast(SpellComponents, value)
    findings = [
        *_bool_field(c.verbal, f"{field}.verbal"),
        *_bool_field(c.somatic, f"{field}.somatic"),
        *_bool_field(c.material, f"{field}.material"),
        *_bool_field(c.material_consumed, f"{field}.material_consumed"),
    ]
    if findings:
        return findings
    if c.material_consumed and not c.material:
        findings.append(f"{field}: consumes a material component it does not have")
    return findings


def _check_duration(value: object, field: str) -> list[str]:
    if findings := _vo_field(value, SpellDuration, field):
        return findings
    d = cast(SpellDuration, value)
    findings = [
        *_enum_field(d.kind, DurationKind, f"{field}.kind"),
        *_optional_int_field(d.amount, f"{field}.amount"),
        *_optional_enum_field(d.unit, TimeUnit, f"{field}.unit"),
        *_bool_field(d.concentration, f"{field}.concentration"),
    ]
    if findings:
        return findings
    if d.kind is DurationKind.TIMED:
        if d.amount is None or d.unit is None:
            findings.append(f"{field}: a timed duration needs both amount and unit")
        elif d.amount < 1:
            findings.append(f"{field}.amount {d.amount} is not a duration")
    elif d.amount is not None or d.unit is not None:
        findings.append(
            f"{field}: {d.kind.value} duration carries an amount; the length "
            "comes from the named kind, not from the fact"
        )
    return findings


# -- Family invariants ------------------------------------------------------


def _check_spell_slot_progression(fact: SpellSlotProgressionFact) -> list[str]:
    findings = [
        *_int_field(fact.character_level, "character_level"),
        *_int_field(fact.slot_level, "slot_level"),
        *_int_field(fact.slots, "slots"),
    ]
    if findings:
        return findings
    if fact.character_level < 1:
        findings.append(f"character_level {fact.character_level} is not a level")
    if fact.slot_level < 1:
        findings.append(f"slot_level {fact.slot_level} is not a slot level")
    if fact.slots < 1:
        findings.append(f"slots {fact.slots} grants nothing")
    return findings


def _check_spell_list_qualifier(fact: SpellListQualifierFact) -> list[str]:
    findings = [
        *_str_field(fact.spell_record_key, "spell_record_key"),
        *_bool_field(fact.always_prepared, "always_prepared"),
        *_optional_int_field(fact.minimum_class_level, "minimum_class_level"),
    ]
    if findings:
        return findings
    if not fact.spell_record_key.strip():
        findings.append("spell_list qualifier without a spell record key")
    if fact.minimum_class_level is not None and fact.minimum_class_level < 1:
        findings.append(
            f"minimum_class_level {fact.minimum_class_level} is not a level"
        )
    if not fact.always_prepared and fact.minimum_class_level is None:
        findings.append("spell_list qualifier states no qualifier")
    return findings


def _check_attack_roll(fact: AttackRollFact) -> list[str]:
    findings = [
        *_enum_field(fact.attack_kind, AttackKind, "attack_kind"),
        *_int_field(fact.to_hit_bonus, "to_hit_bonus"),
        *_optional_int_field(fact.reach_feet, "reach_feet"),
        *_optional_int_field(fact.range_normal_feet, "range_normal_feet"),
        *_optional_int_field(fact.range_long_feet, "range_long_feet"),
    ]
    if findings:
        return findings
    for name, value in (
        ("reach_feet", fact.reach_feet),
        ("range_normal_feet", fact.range_normal_feet),
        ("range_long_feet", fact.range_long_feet),
    ):
        if value is not None and value < 1:
            findings.append(f"{name} {value} is not a distance")
    if (
        fact.range_long_feet is not None
        and fact.range_normal_feet is not None
        and fact.range_long_feet < fact.range_normal_feet
    ):
        findings.append(
            f"range_long_feet {fact.range_long_feet} is shorter than "
            f"range_normal_feet {fact.range_normal_feet}"
        )
    if fact.range_long_feet is not None and fact.range_normal_feet is None:
        findings.append("range_long_feet without a normal range")
    return findings


def _check_damage(fact: DamageFact) -> list[str]:
    findings = [
        *_enum_field(fact.damage_type, DamageType, "damage_type"),
        *_check_optional_dice(fact.dice, "dice"),
        *_optional_int_field(fact.flat_amount, "flat_amount"),
        *_optional_int_field(fact.stated_average, "stated_average"),
    ]
    if findings:
        return findings
    if (fact.dice is None) == (fact.flat_amount is None):
        findings.append(
            "damage states exactly one of a dice expression or a flat amount"
        )
    if fact.flat_amount is not None and fact.flat_amount < 1:
        findings.append(f"flat_amount {fact.flat_amount} deals no damage")
    if fact.stated_average is not None and fact.stated_average < 1:
        findings.append(f"stated_average {fact.stated_average} deals no damage")
    return findings


def _check_healing(fact: HealingFact) -> list[str]:
    findings = [
        *_check_optional_dice(fact.dice, "dice"),
        *_optional_int_field(fact.flat_amount, "flat_amount"),
        *_bool_field(fact.restores_all_hit_points, "restores_all_hit_points"),
    ]
    if findings:
        return findings
    stated = [
        fact.dice is not None,
        fact.flat_amount is not None,
        fact.restores_all_hit_points,
    ]
    if sum(stated) != 1:
        findings.append(
            "healing states exactly one of a dice expression, a flat amount, or "
            "full restoration"
        )
    if fact.flat_amount is not None and fact.flat_amount < 1:
        findings.append(f"flat_amount {fact.flat_amount} restores nothing")
    return findings


def _check_damage_response(fact: DamageResponseFact) -> list[str]:
    return [
        *_enum_field(fact.damage_type, DamageType, "damage_type"),
        *_enum_field(fact.response, DamageResponseKind, "response"),
    ]


def _check_condition_effect(fact: ConditionEffectFact) -> list[str]:
    return [
        *_enum_field(fact.condition, ConditionKind, "condition"),
        *_enum_field(fact.effect, ConditionEffectKind, "effect"),
    ]


def _check_creature_defense(fact: CreatureDefenseFact) -> list[str]:
    findings = [
        *_int_field(fact.armor_class, "armor_class"),
        *_int_field(fact.hit_points, "hit_points"),
        *_check_optional_dice(fact.hit_point_dice, "hit_point_dice"),
    ]
    if findings:
        return findings
    if fact.armor_class < 0:
        findings.append(f"negative armor_class {fact.armor_class}")
    if fact.hit_points < 1:
        findings.append(f"hit_points {fact.hit_points} is not a living creature")
    return findings


def _check_creature_speed(fact: CreatureSpeedFact) -> list[str]:
    findings = [
        *_enum_field(fact.mode, MovementMode, "mode"),
        *_int_field(fact.feet, "feet"),
    ]
    if findings:
        return findings
    if fact.feet < 0:
        findings.append(f"negative speed {fact.feet}")
    return findings


def _check_creature_challenge(fact: CreatureChallengeFact) -> list[str]:
    return [
        *_check_rational(fact.challenge_rating, "challenge_rating"),
        *_optional_int_field(fact.proficiency_bonus, "proficiency_bonus"),
    ]


def _check_action_economy(fact: ActionEconomyFact) -> list[str]:
    return _enum_field(fact.cost, ActionCost, "cost")


def _check_resource_recovery(fact: ResourceRecoveryFact) -> list[str]:
    findings = [
        *_str_field(fact.resource_key, "resource_key"),
        *_enum_field(fact.recovers_on, RecoveryTrigger, "recovers_on"),
        *_optional_int_field(fact.uses, "uses"),
        *_optional_enum_field(fact.recharge_die, DieSize, "recharge_die"),
        *_optional_int_field(fact.recharge_minimum, "recharge_minimum"),
    ]
    if findings:
        return findings
    if not fact.resource_key.strip():
        findings.append("resource recovery without a resource key")
    if fact.uses is not None and fact.uses < 1:
        findings.append(f"uses {fact.uses} grants nothing")
    recharge = fact.recharge_die is not None or fact.recharge_minimum is not None
    if fact.recovers_on is RecoveryTrigger.RECHARGE_ROLL:
        if fact.recharge_die is None or fact.recharge_minimum is None:
            findings.append(
                "recharge_roll recovery needs both a die and a minimum roll"
            )
        elif fact.recharge_minimum < 1:
            findings.append(f"recharge_minimum {fact.recharge_minimum} always succeeds")
        elif fact.recharge_minimum > fact.recharge_die.faces:
            # The mirror of the check above, and it matters more: a threshold
            # the die cannot reach is a resource that never recharges, which
            # would persist and publish as typed authority for a feature that
            # can never come back. ``Recharge 6`` on a d6 is real and must pass,
            # so the bound is inclusive.
            findings.append(
                f"recharge_minimum {fact.recharge_minimum} is unreachable on "
                f"{fact.recharge_die.value}; the resource could never recharge"
            )
    elif recharge:
        findings.append(
            f"{fact.recovers_on.value} recovery carries recharge terms; the "
            "cadence comes from the named trigger, not from the fact"
        )
    return findings


def _check_advantage(fact: AdvantageFact) -> list[str]:
    return [
        *_enum_field(fact.state, AdvantageState, "state"),
        *_enum_field(fact.context, RollContext, "context"),
    ]


def _check_scaling(fact: ScalingFact) -> list[str]:
    findings = [
        *_enum_field(fact.basis, ScalingBasis, "basis"),
        *_int_field(fact.threshold, "threshold"),
        *_enum_field(fact.effect, ScalingEffect, "effect"),
        *_check_optional_dice(fact.dice_increase, "dice_increase"),
        *_optional_int_field(fact.amount_increase, "amount_increase"),
    ]
    if findings:
        return findings
    if fact.threshold < 0:
        findings.append(f"negative scaling threshold {fact.threshold}")
    stated = (fact.dice_increase is not None) + (fact.amount_increase is not None)
    if fact.effect is ScalingEffect.EFFECTIVE_SPELL_LEVEL:
        # "Use the spell slot's level for the spell's level in the stat block"
        # states no increment of its own — the slot level *is* the value.
        if stated:
            findings.append(
                "effective_spell_level scaling carries an increment; the value "
                "comes from the slot level itself"
            )
    elif stated != 1:
        findings.append(
            "scaling states exactly one of a dice increase or an amount increase"
        )
    if fact.amount_increase is not None and fact.amount_increase < 1:
        findings.append(f"amount_increase {fact.amount_increase} increases nothing")
    return findings


def _check_equipment_descriptor(fact: EquipmentDescriptorFact) -> list[str]:
    findings = [
        *([] if fact.cost is None else _check_money(fact.cost, "cost")),
        *_check_optional_rational(fact.weight_pounds, "weight_pounds"),
    ]
    if findings:
        return findings
    if fact.cost is None and fact.weight_pounds is None:
        findings.append("equipment descriptor states neither a cost nor a weight")
    return findings


def _check_weapon_property(fact: WeaponPropertyFact) -> list[str]:
    findings = [
        *_enum_field(fact.weapon_property, WeaponProperty, "weapon_property"),
        *_check_optional_dice(fact.versatile_damage, "versatile_damage"),
        *_optional_int_field(fact.thrown_range_normal_feet, "thrown_range_normal_feet"),
        *_optional_int_field(fact.thrown_range_long_feet, "thrown_range_long_feet"),
    ]
    if findings:
        return findings
    thrown = (
        fact.thrown_range_normal_feet is not None
        or fact.thrown_range_long_feet is not None
    )
    if fact.weapon_property is not WeaponProperty.VERSATILE:
        if fact.versatile_damage is not None:
            findings.append(
                f"{fact.weapon_property.value} property carries versatile damage"
            )
    elif fact.versatile_damage is None:
        findings.append("versatile property without its two-handed damage")
    if fact.weapon_property is not WeaponProperty.THROWN:
        if thrown:
            findings.append(
                f"{fact.weapon_property.value} property carries a thrown range"
            )
    elif fact.thrown_range_normal_feet is None:
        findings.append("thrown property without a normal range")
    for name, value in (
        ("thrown_range_normal_feet", fact.thrown_range_normal_feet),
        ("thrown_range_long_feet", fact.thrown_range_long_feet),
    ):
        if value is not None and value < 1:
            findings.append(f"{name} {value} is not a distance")
    return findings


_FACT_INVARIANTS: dict[FactFamily, Callable[[Any], list[str]]] = {
    FactFamily.ABILITY_CHECK: _check_ability_check,
    FactFamily.ACTION_ECONOMY: _check_action_economy,
    FactFamily.ADVANTAGE: _check_advantage,
    FactFamily.ATTACK_ROLL: _check_attack_roll,
    FactFamily.CONDITION_EFFECT: _check_condition_effect,
    FactFamily.CREATURE_ABILITY_SCORE: _check_creature_ability_score,
    FactFamily.CREATURE_CHALLENGE: _check_creature_challenge,
    FactFamily.CREATURE_DEFENSE: _check_creature_defense,
    FactFamily.CREATURE_SPEED: _check_creature_speed,
    FactFamily.DAMAGE: _check_damage,
    FactFamily.DAMAGE_RESPONSE: _check_damage_response,
    FactFamily.EQUIPMENT_DESCRIPTOR: _check_equipment_descriptor,
    FactFamily.HEALING: _check_healing,
    FactFamily.PROGRESSION_ENTRY: _check_progression_entry,
    FactFamily.RESOURCE_RECOVERY: _check_resource_recovery,
    FactFamily.SCALING: _check_scaling,
    FactFamily.SPELL_DESCRIPTOR: _check_spell_descriptor,
    FactFamily.SPELL_LIST_QUALIFIER: _check_spell_list_qualifier,
    FactFamily.SPELL_SLOT_PROGRESSION: _check_spell_slot_progression,
    FactFamily.WEAPON_PROPERTY: _check_weapon_property,
}


def fact_invariant_violations(fact: object) -> tuple[str, ...]:
    """Return violations of *fact*'s own family contract.

    Membership of the closed union is checked first: an unknown family has no
    invariants to check because it has no contract.
    """
    family = getattr(fact, "FAMILY", None)
    if not isinstance(family, FactFamily) or _FACT_TYPES.get(family) is not type(fact):
        return (
            f"{type(fact).__name__} is not a member of the closed typed-fact union",
        )
    return tuple(_FACT_INVARIANTS[family](fact))


# JSON-side primitive checks. A persisted payload arrives as plain JSON values,
# so each builder states the exact primitive shape it accepts before it
# constructs anything. Nothing is coerced: ``"12"`` stays a string and fails,
# because turning it into 12 would be this layer inventing a mechanical value
# the persisted row does not contain.


def _json_enum(value: object, enum_cls: type[StrEnum], field: str) -> list[str]:
    """The stored value must be a plain string naming a declared member."""
    if type(value) is not str:
        return [
            f"{field} must be a string {enum_cls.__name__} value, got "
            f"{type(value).__name__} {value!r}"
        ]
    try:
        enum_cls(value)
    except ValueError:
        return [f"{field} {value!r} is not a declared {enum_cls.__name__}"]
    return []


def _optional_json_enum(
    value: object, enum_cls: type[StrEnum], field: str
) -> list[str]:
    """A declared member or ``null``, for a stored ``Enum | None`` field."""
    if value is None:
        return []
    return _json_enum(value, enum_cls, field)


def _reject(family: FactFamily, findings: list[str]) -> None:
    if findings:
        raise MalformedFactPayloadError(
            f"{family.value} payload has mistyped fields: {'; '.join(findings)}"
        )


def _build_ability_check(p: Mapping[str, Any]) -> AbilityCheckFact:
    _reject(
        FactFamily.ABILITY_CHECK,
        [
            *_json_enum(p["ability"], AbilityScore, "ability"),
            *_json_enum(p["dc_kind"], DcKind, "dc_kind"),
            *_optional_int_field(p["dc_value"], "dc_value"),
        ],
    )
    return AbilityCheckFact(
        ability=AbilityScore(p["ability"]),
        dc_kind=DcKind(p["dc_kind"]),
        dc_value=p["dc_value"],
    )


def _build_creature_ability_score(p: Mapping[str, Any]) -> CreatureAbilityScoreFact:
    _reject(
        FactFamily.CREATURE_ABILITY_SCORE,
        [
            *_json_enum(p["ability"], AbilityScore, "ability"),
            *_int_field(p["score"], "score"),
            *_optional_int_field(p["modifier"], "modifier"),
            *_optional_int_field(p["save_modifier"], "save_modifier"),
        ],
    )
    return CreatureAbilityScoreFact(
        ability=AbilityScore(p["ability"]),
        score=p["score"],
        modifier=p["modifier"],
        save_modifier=p["save_modifier"],
    )


# -- Value-object builders --------------------------------------------------
#
# Same strictness as a family: the exact declared key set, no coercion, no
# defaulting. A nested object is not a free-form dict that happens to live
# inside a typed fact.


def _json_object(value: object, keys: tuple[str, ...], where: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        raise MalformedFactPayloadError(
            f"{where} must be an object, got {type(value).__name__} {value!r}"
        )
    supplied = set(value)
    if missing := sorted(set(keys) - supplied):
        raise MalformedFactPayloadError(f"{where} is missing {missing}")
    if extra := sorted(supplied - set(keys)):
        raise MalformedFactPayloadError(f"{where} carries extra {extra}")
    return value


def _reject_at(where: str, findings: list[str]) -> None:
    if findings:
        raise MalformedFactPayloadError(f"{where}: {'; '.join(findings)}")


def _build_dice(value: object, where: str) -> DiceExpression:
    p = _json_object(value, ("count", "die", "modifier"), where)
    _reject_at(
        where,
        [
            *_int_field(p["count"], "count"),
            *_json_enum(p["die"], DieSize, "die"),
            *_int_field(p["modifier"], "modifier"),
        ],
    )
    return DiceExpression(
        count=p["count"], die=DieSize(p["die"]), modifier=p["modifier"]
    )


def _build_rational(value: object, where: str) -> Rational:
    p = _json_object(value, ("numerator", "denominator"), where)
    _reject_at(
        where,
        [
            *_int_field(p["numerator"], "numerator"),
            *_int_field(p["denominator"], "denominator"),
        ],
    )
    return Rational(numerator=p["numerator"], denominator=p["denominator"])


def _build_money(value: object, where: str) -> Money:
    p = _json_object(value, ("amount", "currency"), where)
    _reject_at(
        where,
        [
            *_int_field(p["amount"], "amount"),
            *_json_enum(p["currency"], Currency, "currency"),
        ],
    )
    return Money(amount=p["amount"], currency=Currency(p["currency"]))


def _build_casting_time(value: object, where: str) -> SpellCastingTime:
    p = _json_object(value, ("cost", "amount", "unit"), where)
    _reject_at(
        where,
        [
            *_optional_json_enum(p["cost"], ActionCost, "cost"),
            *_optional_int_field(p["amount"], "amount"),
            *_optional_json_enum(p["unit"], TimeUnit, "unit"),
        ],
    )
    return SpellCastingTime(
        cost=None if p["cost"] is None else ActionCost(p["cost"]),
        amount=p["amount"],
        unit=None if p["unit"] is None else TimeUnit(p["unit"]),
    )


def _build_spell_range(value: object, where: str) -> SpellRange:
    p = _json_object(value, ("kind", "feet"), where)
    _reject_at(
        where,
        [
            *_json_enum(p["kind"], RangeKind, "kind"),
            *_optional_int_field(p["feet"], "feet"),
        ],
    )
    return SpellRange(kind=RangeKind(p["kind"]), feet=p["feet"])


def _build_components(value: object, where: str) -> SpellComponents:
    p = _json_object(
        value, ("verbal", "somatic", "material", "material_consumed"), where
    )
    _reject_at(
        where,
        [
            *_bool_field(p["verbal"], "verbal"),
            *_bool_field(p["somatic"], "somatic"),
            *_bool_field(p["material"], "material"),
            *_bool_field(p["material_consumed"], "material_consumed"),
        ],
    )
    return SpellComponents(
        verbal=p["verbal"],
        somatic=p["somatic"],
        material=p["material"],
        material_consumed=p["material_consumed"],
    )


def _build_duration(value: object, where: str) -> SpellDuration:
    p = _json_object(value, ("kind", "amount", "unit", "concentration"), where)
    _reject_at(
        where,
        [
            *_json_enum(p["kind"], DurationKind, "kind"),
            *_optional_int_field(p["amount"], "amount"),
            *_optional_json_enum(p["unit"], TimeUnit, "unit"),
            *_bool_field(p["concentration"], "concentration"),
        ],
    )
    return SpellDuration(
        kind=DurationKind(p["kind"]),
        amount=p["amount"],
        unit=None if p["unit"] is None else TimeUnit(p["unit"]),
        concentration=p["concentration"],
    )


def _build_spell_descriptor(p: Mapping[str, Any]) -> SpellDescriptorFact:
    _reject(
        FactFamily.SPELL_DESCRIPTOR,
        [
            *_int_field(p["level"], "level"),
            *_json_enum(p["school"], SpellSchool, "school"),
            *_bool_field(p["ritual"], "ritual"),
            *_bool_field(p["concentration"], "concentration"),
        ],
    )
    return SpellDescriptorFact(
        level=p["level"],
        school=SpellSchool(p["school"]),
        ritual=p["ritual"],
        concentration=p["concentration"],
        casting_time=(
            None
            if p["casting_time"] is None
            else _build_casting_time(p["casting_time"], "casting_time")
        ),
        spell_range=(
            None
            if p["spell_range"] is None
            else _build_spell_range(p["spell_range"], "spell_range")
        ),
        components=(
            None
            if p["components"] is None
            else _build_components(p["components"], "components")
        ),
        duration=(
            None
            if p["duration"] is None
            else _build_duration(p["duration"], "duration")
        ),
    )


def _build_spell_slot_progression(p: Mapping[str, Any]) -> SpellSlotProgressionFact:
    _reject(
        FactFamily.SPELL_SLOT_PROGRESSION,
        [
            *_int_field(p["character_level"], "character_level"),
            *_int_field(p["slot_level"], "slot_level"),
            *_int_field(p["slots"], "slots"),
        ],
    )
    return SpellSlotProgressionFact(
        character_level=p["character_level"],
        slot_level=p["slot_level"],
        slots=p["slots"],
    )


def _build_spell_list_qualifier(p: Mapping[str, Any]) -> SpellListQualifierFact:
    _reject(
        FactFamily.SPELL_LIST_QUALIFIER,
        [
            *_str_field(p["spell_record_key"], "spell_record_key"),
            *_bool_field(p["always_prepared"], "always_prepared"),
            *_optional_int_field(p["minimum_class_level"], "minimum_class_level"),
        ],
    )
    return SpellListQualifierFact(
        spell_record_key=p["spell_record_key"],
        always_prepared=p["always_prepared"],
        minimum_class_level=p["minimum_class_level"],
    )


def _build_attack_roll(p: Mapping[str, Any]) -> AttackRollFact:
    _reject(
        FactFamily.ATTACK_ROLL,
        [
            *_json_enum(p["attack_kind"], AttackKind, "attack_kind"),
            *_int_field(p["to_hit_bonus"], "to_hit_bonus"),
            *_optional_int_field(p["reach_feet"], "reach_feet"),
            *_optional_int_field(p["range_normal_feet"], "range_normal_feet"),
            *_optional_int_field(p["range_long_feet"], "range_long_feet"),
        ],
    )
    return AttackRollFact(
        attack_kind=AttackKind(p["attack_kind"]),
        to_hit_bonus=p["to_hit_bonus"],
        reach_feet=p["reach_feet"],
        range_normal_feet=p["range_normal_feet"],
        range_long_feet=p["range_long_feet"],
    )


def _build_damage(p: Mapping[str, Any]) -> DamageFact:
    _reject(
        FactFamily.DAMAGE,
        [
            *_json_enum(p["damage_type"], DamageType, "damage_type"),
            *_optional_int_field(p["flat_amount"], "flat_amount"),
            *_optional_int_field(p["stated_average"], "stated_average"),
        ],
    )
    return DamageFact(
        damage_type=DamageType(p["damage_type"]),
        dice=None if p["dice"] is None else _build_dice(p["dice"], "dice"),
        flat_amount=p["flat_amount"],
        stated_average=p["stated_average"],
    )


def _build_healing(p: Mapping[str, Any]) -> HealingFact:
    _reject(
        FactFamily.HEALING,
        [
            *_optional_int_field(p["flat_amount"], "flat_amount"),
            *_bool_field(p["restores_all_hit_points"], "restores_all_hit_points"),
        ],
    )
    return HealingFact(
        dice=None if p["dice"] is None else _build_dice(p["dice"], "dice"),
        flat_amount=p["flat_amount"],
        restores_all_hit_points=p["restores_all_hit_points"],
    )


def _build_damage_response(p: Mapping[str, Any]) -> DamageResponseFact:
    _reject(
        FactFamily.DAMAGE_RESPONSE,
        [
            *_json_enum(p["damage_type"], DamageType, "damage_type"),
            *_json_enum(p["response"], DamageResponseKind, "response"),
        ],
    )
    return DamageResponseFact(
        damage_type=DamageType(p["damage_type"]),
        response=DamageResponseKind(p["response"]),
    )


def _build_condition_effect(p: Mapping[str, Any]) -> ConditionEffectFact:
    _reject(
        FactFamily.CONDITION_EFFECT,
        [
            *_json_enum(p["condition"], ConditionKind, "condition"),
            *_json_enum(p["effect"], ConditionEffectKind, "effect"),
        ],
    )
    return ConditionEffectFact(
        condition=ConditionKind(p["condition"]),
        effect=ConditionEffectKind(p["effect"]),
    )


def _build_creature_defense(p: Mapping[str, Any]) -> CreatureDefenseFact:
    _reject(
        FactFamily.CREATURE_DEFENSE,
        [
            *_int_field(p["armor_class"], "armor_class"),
            *_int_field(p["hit_points"], "hit_points"),
        ],
    )
    return CreatureDefenseFact(
        armor_class=p["armor_class"],
        hit_points=p["hit_points"],
        hit_point_dice=(
            None
            if p["hit_point_dice"] is None
            else _build_dice(p["hit_point_dice"], "hit_point_dice")
        ),
    )


def _build_creature_speed(p: Mapping[str, Any]) -> CreatureSpeedFact:
    _reject(
        FactFamily.CREATURE_SPEED,
        [
            *_json_enum(p["mode"], MovementMode, "mode"),
            *_int_field(p["feet"], "feet"),
        ],
    )
    return CreatureSpeedFact(mode=MovementMode(p["mode"]), feet=p["feet"])


def _build_creature_challenge(p: Mapping[str, Any]) -> CreatureChallengeFact:
    _reject(
        FactFamily.CREATURE_CHALLENGE,
        _optional_int_field(p["proficiency_bonus"], "proficiency_bonus"),
    )
    return CreatureChallengeFact(
        challenge_rating=_build_rational(p["challenge_rating"], "challenge_rating"),
        proficiency_bonus=p["proficiency_bonus"],
    )


def _build_action_economy(p: Mapping[str, Any]) -> ActionEconomyFact:
    _reject(FactFamily.ACTION_ECONOMY, _json_enum(p["cost"], ActionCost, "cost"))
    return ActionEconomyFact(cost=ActionCost(p["cost"]))


def _build_resource_recovery(p: Mapping[str, Any]) -> ResourceRecoveryFact:
    _reject(
        FactFamily.RESOURCE_RECOVERY,
        [
            *_str_field(p["resource_key"], "resource_key"),
            *_json_enum(p["recovers_on"], RecoveryTrigger, "recovers_on"),
            *_optional_int_field(p["uses"], "uses"),
            *_optional_json_enum(p["recharge_die"], DieSize, "recharge_die"),
            *_optional_int_field(p["recharge_minimum"], "recharge_minimum"),
        ],
    )
    return ResourceRecoveryFact(
        resource_key=p["resource_key"],
        recovers_on=RecoveryTrigger(p["recovers_on"]),
        uses=p["uses"],
        recharge_die=(
            None if p["recharge_die"] is None else DieSize(p["recharge_die"])
        ),
        recharge_minimum=p["recharge_minimum"],
    )


def _build_advantage(p: Mapping[str, Any]) -> AdvantageFact:
    _reject(
        FactFamily.ADVANTAGE,
        [
            *_json_enum(p["state"], AdvantageState, "state"),
            *_json_enum(p["context"], RollContext, "context"),
        ],
    )
    return AdvantageFact(
        state=AdvantageState(p["state"]), context=RollContext(p["context"])
    )


def _build_scaling(p: Mapping[str, Any]) -> ScalingFact:
    _reject(
        FactFamily.SCALING,
        [
            *_json_enum(p["basis"], ScalingBasis, "basis"),
            *_int_field(p["threshold"], "threshold"),
            *_json_enum(p["effect"], ScalingEffect, "effect"),
            *_optional_int_field(p["amount_increase"], "amount_increase"),
        ],
    )
    return ScalingFact(
        basis=ScalingBasis(p["basis"]),
        threshold=p["threshold"],
        effect=ScalingEffect(p["effect"]),
        dice_increase=(
            None
            if p["dice_increase"] is None
            else _build_dice(p["dice_increase"], "dice_increase")
        ),
        amount_increase=p["amount_increase"],
    )


def _build_equipment_descriptor(p: Mapping[str, Any]) -> EquipmentDescriptorFact:
    return EquipmentDescriptorFact(
        cost=None if p["cost"] is None else _build_money(p["cost"], "cost"),
        weight_pounds=(
            None
            if p["weight_pounds"] is None
            else _build_rational(p["weight_pounds"], "weight_pounds")
        ),
    )


def _build_weapon_property(p: Mapping[str, Any]) -> WeaponPropertyFact:
    _reject(
        FactFamily.WEAPON_PROPERTY,
        [
            *_json_enum(p["weapon_property"], WeaponProperty, "weapon_property"),
            *_optional_int_field(
                p["thrown_range_normal_feet"], "thrown_range_normal_feet"
            ),
            *_optional_int_field(p["thrown_range_long_feet"], "thrown_range_long_feet"),
        ],
    )
    return WeaponPropertyFact(
        weapon_property=WeaponProperty(p["weapon_property"]),
        versatile_damage=(
            None
            if p["versatile_damage"] is None
            else _build_dice(p["versatile_damage"], "versatile_damage")
        ),
        thrown_range_normal_feet=p["thrown_range_normal_feet"],
        thrown_range_long_feet=p["thrown_range_long_feet"],
    )


def _build_progression_entry(p: Mapping[str, Any]) -> ProgressionEntryFact:
    _reject(
        FactFamily.PROGRESSION_ENTRY,
        [
            *_int_field(p["level"], "level"),
            *_str_field(p["entitlement_key"], "entitlement_key"),
            *_optional_int_field(p["quantity"], "quantity"),
        ],
    )
    return ProgressionEntryFact(
        level=p["level"],
        entitlement_key=p["entitlement_key"],
        quantity=p["quantity"],
    )


_FACT_BUILDERS: dict[FactFamily, Callable[[Mapping[str, Any]], MechanicalFact]] = {
    FactFamily.ABILITY_CHECK: _build_ability_check,
    FactFamily.ACTION_ECONOMY: _build_action_economy,
    FactFamily.ADVANTAGE: _build_advantage,
    FactFamily.ATTACK_ROLL: _build_attack_roll,
    FactFamily.CONDITION_EFFECT: _build_condition_effect,
    FactFamily.CREATURE_ABILITY_SCORE: _build_creature_ability_score,
    FactFamily.CREATURE_CHALLENGE: _build_creature_challenge,
    FactFamily.CREATURE_DEFENSE: _build_creature_defense,
    FactFamily.CREATURE_SPEED: _build_creature_speed,
    FactFamily.DAMAGE: _build_damage,
    FactFamily.DAMAGE_RESPONSE: _build_damage_response,
    FactFamily.EQUIPMENT_DESCRIPTOR: _build_equipment_descriptor,
    FactFamily.HEALING: _build_healing,
    FactFamily.PROGRESSION_ENTRY: _build_progression_entry,
    FactFamily.RESOURCE_RECOVERY: _build_resource_recovery,
    FactFamily.SCALING: _build_scaling,
    FactFamily.SPELL_DESCRIPTOR: _build_spell_descriptor,
    FactFamily.SPELL_LIST_QUALIFIER: _build_spell_list_qualifier,
    FactFamily.SPELL_SLOT_PROGRESSION: _build_spell_slot_progression,
    FactFamily.WEAPON_PROPERTY: _build_weapon_property,
}

#: Every family must declare a builder and an invariant checker. A family added
#: to the union with neither is a family nothing validates and nothing can
#: reconstruct — a silent hole rather than a visible omission, which is exactly
#: what this module's per-family structure exists to prevent.
assert (
    set(_FACT_TYPES) == set(_FACT_BUILDERS) == set(_FACT_INVARIANTS) == set(FactFamily)
), "every FactFamily needs a type, a builder, and an invariant checker"


def fact_from_payload(
    payload: Mapping[str, Any], *, declared_family: str | None = None
) -> MechanicalFact:
    """Rebuild a typed fact from its persisted payload.

    Strict by design. A persisted payload is only authority if it still says
    exactly what it said when it was written, so this rejects rather than
    repairs:

    * an unknown family — not a forward-compatible unknown, but a fact this
      build cannot honestly represent;
    * a missing field, which would otherwise rebuild into a fact with a
      silently defaulted value;
    * an extra field, which would otherwise be dropped, hiding whatever was
      added to the row; and
    * a payload discriminator that disagrees with the column that stores it
      alongside — one of the two has been rewritten, and guessing which is
      not reconstruction.

    Explicit per-family builders rather than reflection, so each family states
    the exact field set it accepts.
    """
    raw = payload.get("family")
    try:
        family = FactFamily(str(raw))
    except ValueError:
        raise UnknownFactFamilyError(
            f"{raw!r} is not a member of the closed typed-fact union"
        ) from None

    if declared_family is not None and declared_family != family.value:
        raise MalformedFactPayloadError(
            f"persisted family {declared_family!r} disagrees with payload family "
            f"{family.value!r}"
        )

    expected = {f.name for f in fields(_FACT_TYPES[family])} | {"family"}
    supplied = set(payload)
    if missing := sorted(expected - supplied):
        raise MalformedFactPayloadError(f"{family.value} payload is missing {missing}")
    if extra := sorted(supplied - expected):
        raise MalformedFactPayloadError(f"{family.value} payload carries extra {extra}")

    try:
        return _FACT_BUILDERS[family](payload)
    except (TypeError, ValueError) as exc:
        raise MalformedFactPayloadError(
            f"{family.value} payload does not rebuild its declared family: {exc}"
        ) from exc


def fact_key(fact: object) -> str:
    """Stable content-derived key for one fact within its component.

    Derived from the canonical payload, never from a position in the component's
    fact tuple, so reordering or inserting a sibling fact cannot churn it.
    """
    return sha256_hex(canonical_bytes(fact_payload(fact)))[:16]


def fact_payload(fact: object) -> dict[str, object]:
    """Canonical payload for one typed fact.

    Raises rather than returning findings: an unknown family has no canonical
    form, so there is nothing honest to serialize. Callers that want a
    collected report use :func:`validation.validate_representation`.
    """
    family = getattr(fact, "FAMILY", None)
    if not isinstance(family, FactFamily) or _FACT_TYPES.get(family) is not type(fact):
        raise UnknownFactFamilyError(
            f"{type(fact).__name__} is not a member of the closed typed-fact union"
        )
    # Safe now: the family check above proved *fact* is one of the declared
    # frozen dataclasses, which is what asdict needs.
    payload: dict[str, object] = {"family": family.value}
    for key, value in sorted(asdict(cast(Any, fact)).items()):
        payload[key] = _canonical_value(value)
    return payload


def _canonical_value(value: object) -> object:
    """Canonical JSON form of one field value, however deeply nested.

    ``asdict`` already turns a nested value object into a dict, but it leaves
    ``StrEnum`` members as enum instances. They *are* strings, so a serializer
    would accept them — and then a payload rebuilt from storage would hold a
    plain ``str`` where the freshly built one holds an enum, and the two would
    be the same bytes but different objects. Normalizing here means the
    canonical form is the *stored* form, so a round trip is a fixed point
    rather than something that merely happens to hash the same.
    """
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {k: _canonical_value(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_canonical_value(v) for v in value]
    return value


# ---------------------------------------------------------------------------
# Keyed drafts — semantic keys only, no derived identities
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RecordDraft:
    """A semantic record assembled from accepted membership.

    ``parent_key`` is set for a nested record — the complete creature stat block
    embedded in spell authority is a record in its own right, not a copy.
    """

    semantic_key: str
    kind: RecordKind
    parent_key: str | None = None


@dataclass(frozen=True)
class ComponentDraft:
    """One publishable component of a record."""

    record_key: str
    semantic_key: str
    handling: ComponentHandling
    #: Required for PROSE_BOUND and MIXED; must name a closed catalog reason.
    irreducibility_reason_code: str | None = None
    facts: tuple[MechanicalFact, ...] = ()


@dataclass(frozen=True)
class ProseBindingDraft:
    """Exact governing prose for a component: one accepted span of one chunk.

    Two halves, and #137 contract 3 requires both:

    * **the text comes from 5c.** ``chunk_id`` names the authoritative
      ``RuleChunk``, so nothing here copies source text into a second prose
      store; and
    * **the authority is the accepted span, not the whole passage.**
      ``span_id`` names one accepted classification span, and
      ``chunk_char_start``/``chunk_char_end`` are that span's offsets *into the
      chunk's own text*. A component governed by one clause of a paragraph
      resolves to that clause — the rest of the paragraph is other components'
      authority, or none.

    The offsets are redundant with the span, deliberately and checkably: they
    let runtime resolution slice the chunk without re-reading the 5c projection
    relation, and :mod:`validation` recomputes them from the bound release and
    rejects a binding whose declared offsets do not match. Redundancy that is
    verified on every build cannot drift; redundancy that is trusted can.

    A component may bind several passages; each is a separate binding, and the
    provenance key below keeps them distinct.
    """

    component_key: str
    record_key: str
    chunk_id: str
    #: The accepted span this binding governs. Governing prose is accepted
    #: authority, so it resolves through the classification, not around it.
    span_id: str
    #: Half-open offsets into ``chunk_id``'s own text.
    chunk_char_start: int
    chunk_char_end: int
    irreducibility_reason_code: str


@dataclass(frozen=True)
class RelationshipDraft:
    """A typed relationship between two records."""

    source_record_key: str
    target_record_key: str
    kind: RelationshipKind


@dataclass(frozen=True)
class ReferenceDraft:
    """A source-authored mechanical reference resolved at build time.

    ``scope_key`` is the committed source scope the reference was resolved
    within, which is what makes a repeated name resolvable: the same wording in
    two scopes is two references, not one ambiguity.
    """

    from_record_key: str
    from_component_key: str
    source_text: str
    scope_key: str
    target_record_key: str


@dataclass(frozen=True)
class ProvenanceClaim:
    """An exact 5c leaf-subspan claim by one representation element."""

    target_kind: ProvenanceTargetKind
    target_key: tuple[str, ...]
    span_id: str
    role: ProvenanceRole


@dataclass(frozen=True)
class RepresentationDraft:
    """The complete keyed representation for one candidate projection."""

    records: tuple[RecordDraft, ...]
    components: tuple[ComponentDraft, ...]
    prose_bindings: tuple[ProseBindingDraft, ...]
    relationships: tuple[RelationshipDraft, ...]
    references: tuple[ReferenceDraft, ...]
    provenance: tuple[ProvenanceClaim, ...]


# ---------------------------------------------------------------------------
# Canonical provenance target identities
# ---------------------------------------------------------------------------
#
# One definition per target kind, used everywhere a target is enumerated,
# required, claimed, or checked. Building these tuples inline in more than one
# place is how a key drifts: the enumerator and the validator then disagree
# about what "the same element" means, and a claim can match an element it was
# never about.
#
# Each key must identify exactly one declared element. Two elements that differ
# semantically must not share a key — that is why a prose binding carries its
# chunk and reason (one component may bind several passages) and a reference
# carries its owning component (the same wording in one scope may be cited by
# more than one component).


def record_target_key(record: RecordDraft) -> tuple[str, ...]:
    """Provenance key of a record."""
    return (record.semantic_key,)


def component_target_key(component: ComponentDraft) -> tuple[str, ...]:
    """Provenance key of a component."""
    return (component.record_key, component.semantic_key)


def fact_target_key(
    record_key: str, component_key: str, fact: object
) -> tuple[str, ...]:
    """Provenance key of one typed fact, keyed by content rather than position."""
    return (record_key, component_key, fact_key(fact))


def prose_binding_target_key(binding: ProseBindingDraft) -> tuple[str, ...]:
    """Provenance key of one prose binding.

    ``(record_key, component_key)`` alone cannot address a component that binds
    more than one passage, so the bound chunk, the accepted span within it, and
    the reason it is bound are all part of the identity. The span is what keeps
    two clauses of the *same* chunk distinct — without it, a component binding
    two sentences of one paragraph would collapse to one key.
    """
    return (
        binding.record_key,
        binding.component_key,
        binding.chunk_id,
        binding.span_id,
        binding.irreducibility_reason_code,
    )


def relationship_target_key(relationship: RelationshipDraft) -> tuple[str, ...]:
    """Provenance key of one typed relationship."""
    return (
        relationship.source_record_key,
        relationship.target_record_key,
        relationship.kind.value,
    )


def reference_target_key(reference: ReferenceDraft) -> tuple[str, ...]:
    """Provenance key of one resolved reference, including its source ownership."""
    return (
        reference.from_record_key,
        reference.from_component_key,
        reference.source_text,
        reference.scope_key,
        reference.target_record_key,
    )


def prose_bindings_by_target_key(
    draft: RepresentationDraft,
) -> dict[tuple[str, ...], ProseBindingDraft]:
    """Map each prose binding's provenance key back to the binding itself.

    Provenance validation needs the binding, not just its key, to check that a
    claimed span lies inside the chunk that binding names. Recovering it
    through the same key function keeps one definition of "the same element".
    """
    return {prose_binding_target_key(b): b for b in draft.prose_bindings}


def declared_provenance_targets(
    draft: RepresentationDraft,
) -> dict[ProvenanceTargetKind, set[tuple[str, ...]]]:
    """Every element a provenance claim may legitimately name.

    Facts whose family is unknown are omitted: they have no content-derived key,
    and they are reported separately as facts outside the closed union.
    """
    facts: set[tuple[str, ...]] = set()
    for component in draft.components:
        for fact in component.facts:
            try:
                facts.add(
                    fact_target_key(component.record_key, component.semantic_key, fact)
                )
            except UnknownFactFamilyError:
                continue

    return {
        ProvenanceTargetKind.RECORD: {record_target_key(r) for r in draft.records},
        ProvenanceTargetKind.COMPONENT: {
            component_target_key(c) for c in draft.components
        },
        ProvenanceTargetKind.FACT: facts,
        ProvenanceTargetKind.PROSE_BINDING: {
            prose_binding_target_key(b) for b in draft.prose_bindings
        },
        ProvenanceTargetKind.RELATIONSHIP: {
            relationship_target_key(r) for r in draft.relationships
        },
        ProvenanceTargetKind.REFERENCE: {
            reference_target_key(r) for r in draft.references
        },
    }


#: Element kinds that must each carry their own provenance (ADR-005d Decision 3).
#: Records and components are deliberately absent: their obligation is span
#: coverage under the classification contract, not a per-element edge, and
#: conflating the two would let a component claim stand in for the traceability
#: of every fact beneath it.
PROVENANCE_REQUIRED_KINDS: tuple[ProvenanceTargetKind, ...] = (
    ProvenanceTargetKind.FACT,
    ProvenanceTargetKind.PROSE_BINDING,
    ProvenanceTargetKind.RELATIONSHIP,
    ProvenanceTargetKind.REFERENCE,
)
