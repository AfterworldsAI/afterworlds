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
run, and #137 contract 3 names family groups that no observed shape has yet
forced. Each is added explicitly here when accounting surfaces it, or the
affected component is classified honestly as prose-bound. That obligation is met
no later than full-corpus closure; it is never met by widening the union into
something that can hold anything.

**Discharged by the conditions batch** (the 15 SRD conditions and the
``Condition`` glossary rule, accounted against the production SRD 5.2.1
release):

* *critical changes* — :class:`CriticalHitRuleFact`, from Paralyzed's and
  Unconscious's *"Any attack roll that hits you is a Critical Hit"* and the
  Champion's lowered threshold;
* *typed state effects* — :class:`StateEffectFact`, over a closed
  evidence-bound vocabulary.

**Narrowed but still deferred:**

* *targeting restrictions* — the batch forced three instances (Charmed's *"can't
  attack the charmer"*, Frightened's *"can't willingly move closer to the source
  of fear"*, Invisible's *"any effect that requires its target to be seen"*), and
  a corpus sweep of the restriction mechanics found their referents range over
  distances, creature relationships, spell schools, spatial areas, and effect
  properties. A closed vocabulary spanning those is a predicate language, so
  these are classified as affirmatively prose-bound under
  ``contextual_applicability`` rather than typed. The sweep, not the
  convenience, is the justification.

**Untouched:** contests, explicit probability, random-table selection,
eligibility, choices, sequencing.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from enum import StrEnum
from types import UnionType
from typing import Any, ClassVar, Union, cast, get_args, get_origin, get_type_hints

from afterworlds.ingestion.corpus.hashing import canonical_bytes, sha256_hex
from afterworlds.ingestion.mechanical.models import ComponentHandling

__all__ = [
    # Vocabularies
    "AbilityScore",
    "ActionCost",
    "AdvantageState",
    "AttackKind",
    "AutomaticOutcome",
    "ConditionEffectKind",
    "ConditionKind",
    "CriticalHitChange",
    "Currency",
    "DamageResponseKind",
    "DamageScope",
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
    "RollActor",
    "RollContext",
    "ScalingBasis",
    "ScalingDirection",
    "ScalingEffect",
    "SpeedChange",
    "SpellSchool",
    "StateEffectKind",
    "TimeUnit",
    "WeaponProperty",
    # Shared typed value objects
    "DiceExpression",
    "Money",
    "Rational",
    "RollSpec",
    "SpellCastingTime",
    "SpellComponents",
    "SpellDuration",
    "SpellRange",
    # Typed fact families
    "AbilityCheckFact",
    "ActionEconomyFact",
    "ActionRestrictionFact",
    "AdvantageFact",
    "AttackRollFact",
    "AutomaticOutcomeFact",
    "ConditionEffectFact",
    "CriticalHitRuleFact",
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
    "SpeedModificationFact",
    "SpellDescriptorFact",
    "SpellListQualifierFact",
    "SpellSlotProgressionFact",
    "StateEffectFact",
    "WeaponPropertyFact",
    # Keyed drafts
    "Applicability",
    "ApplicabilityKind",
    "Comparison",
    "ComponentOption",
    "ConditionLevelFact",
    "CreatureSize",
    "LevelDirection",
    "MovementAmount",
    "MovementCostFact",
    "MovementCostKind",
    "MovementPermissionFact",
    "Phase",
    "QuantityMultiplierFact",
    "Sense",
    "SensoryCapabilityFact",
    "SizeComparison",
    "SizeRelation",
    "TrackedQuantity",
    "TransformationFact",
    "TransformedForm",
    "applicability_violations",
    "size_comparison_violations",
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
    "UnsupportedRepresentationShapeError",
    "fact_from_payload",
    "fact_invariant_violations",
    "fact_key",
    "fact_payload",
    "REPRESENTATION_SCHEMA_VERSION",
    "representation_schema_hash",
    "representation_schema_payload",
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
    #: Playing the Game > Movement and Position prints the mode list — "Your
    #: movement can include climbing, crawling, jumping, and swimming" — and
    #: Rules Glossary > Speed cross-references the same set, so this is a
    #: printed-vocabulary member rather than an inferred one.
    CRAWL = "crawl"
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
    """Which roll a fact applies to.

    ``D20_TEST`` is the source's own umbrella term for all three of attack roll,
    ability check, and saving throw — *"When you make a D20 Test, the roll is
    reduced by 2 times your Exhaustion level"* (Exhaustion, p181), and
    *"the target has Advantage on D20 Tests"* (Spells). A rule stated about D20
    Tests is not three rules, and splitting it into three would invent a claim
    per context that the source states once.
    """

    ATTACK_ROLL = "attack_roll"
    ABILITY_CHECK = "ability_check"
    SAVING_THROW = "saving_throw"
    INITIATIVE = "initiative"
    D20_TEST = "d20_test"


class RollActor(StrEnum):
    """Whose roll a fact is about — the axis the source states constantly.

    The Rules Glossary prints both polarities in one sentence: *"Attack rolls
    against you have Advantage, and your attack rolls have Disadvantage"*
    (Blinded, p177) versus *"Attack rolls against you have Disadvantage, and
    your attack rolls have Advantage"* (Invisible, p184). Those are opposite
    rules. Without this member they reduce to the same two facts, and a
    deterministic consumer reading the typed surface could not tell the two
    conditions apart.

    Measured corpus-wide, not inferred from the conditions: 60 occurrences of
    *"attack rolls against …"* across ten sections.

    Two members, deliberately. A third-party actor — *"the charmer has
    Advantage on any ability check to interact with you socially"* — is a roll
    directed at the subject whose *actor restriction* is applicability prose on
    a ``MIXED`` component, which is the representation this module already
    defines for a stated qualifier. Adding a member no corpus evidence forces
    would widen the union on speculation.
    """

    #: The subject of the rule makes the roll. "your attack rolls"
    SUBJECT = "subject"
    #: Someone else makes the roll against the subject. "attack rolls against you"
    AGAINST_SUBJECT = "against_subject"


class AutomaticOutcome(StrEnum):
    """A D20 Test resolved without rolling.

    *"You automatically fail Strength and Dexterity saving throws"* (Paralyzed,
    Petrified, Stunned, Unconscious) and *"a chosen creature automatically
    succeeds on its saving throw"* (Classes). This is not advantage taken to an
    extreme; it is the absence of a roll, and 25 occurrences across five
    sections state it.
    """

    SUCCESS = "success"
    FAILURE = "failure"


class DamageScope(StrEnum):
    """Whether a damage response names a type or covers all of them.

    *"You have Resistance to all damage"* (Petrified, p186) is one claim about
    every damage type, not thirteen claims. Enumerating the thirteen would also
    be structurally invalid: each fact would need a ``PRIMARY`` provenance claim
    on the same span, which :mod:`validation` rejects as conflicting primary
    claims.
    """

    #: The source names one damage type.
    SPECIFIC = "specific"
    #: The source says "all damage", optionally with named exceptions.
    ALL = "all"


class SpeedChange(StrEnum):
    """How a rule alters the subject's Speed.

    *"Your Speed is 0 and can't increase"* appears in five conditions and 15
    times corpus-wide; *"Speed is reduced by 15 feet"* / *"Speed is halved"*
    another 19 times across six sections.
    """

    SET_TO = "set_to"
    REDUCED_BY = "reduced_by"
    HALVED = "halved"


class CriticalHitChange(StrEnum):
    """How a rule changes when an attack roll is a Critical Hit.

    The *critical changes* family #137 contract 3 names.
    ``AUTOMATIC_ON_HIT``: *"Any attack roll that hits you is a Critical Hit"*
    (Paralyzed and Unconscious). ``THRESHOLD_LOWERED``: *"Your attack rolls …
    can score a Critical Hit on a roll of 19 or 20"* (Champion, Classes).
    """

    AUTOMATIC_ON_HIT = "automatic_on_hit"
    THRESHOLD_LOWERED = "threshold_lowered"


class StateEffectKind(StrEnum):
    """The closed set of typed state effects observed as stated rules.

    Closed and evidence-bound, exactly like every other vocabulary here: a
    member is admitted only with siblings in more than one section, so this
    cannot become a key/value bucket for whatever a batch could not otherwise
    type. Counts are corpus-wide occurrences of the stated rule, not of the
    words.
    """

    #: "Your Concentration is broken." — 7 across Spells, Glossary, Magic Items.
    CONCENTRATION_BROKEN = "concentration_broken"
    #: "You can't speak." — Glossary and Spells (the Monsters A-Z matches are a
    #: *Languages* descriptor, "understands Draconic but can't speak", and are
    #: deliberately not counted here).
    CANNOT_SPEAK = "cannot_speak"
    #: "you drop whatever you're holding" — Glossary and Spells (×3).
    DROPS_HELD_OBJECTS = "drops_held_objects"
    #: "You're unaware of your surroundings." — Glossary and Spells. The
    #: thinnest member admitted: two instances in two sections.
    UNAWARE_OF_SURROUNDINGS = "unaware_of_surroundings"
    #: "You die if your Exhaustion level is 6." — the death transition itself,
    #: separate from whatever threshold triggers it. 86 occurrences across 8
    #: sections, including Playing the Game's Instant Death rules.
    DIES = "dies"
    #: "you cease aging" — Petrified, and Imprisonment's "it doesn't age".
    #: Two instances in two sections: as thin as UNAWARE_OF_SURROUNDINGS, and
    #: admitted on the same bar rather than on a lower one.
    AGING_SUSPENDED = "aging_suspended"


class Sense(StrEnum):
    """A perceptual capability a rule grants or removes.

    SIGHT and HEARING are what Blinded and Deafened remove. The vocabulary is
    printed rather than inferred: Blindsight, Darkvision, Tremorsense and
    Truesight are Rules Glossary entries, and Blindsight's own text ties
    sight-capability to the condition — "you can see ... even if you have the
    Blinded condition". Only the two members conditions-1 instantiates are
    declared; the printed senses are the extension seam, not decoration, and a
    batch that grants one adds it with its own evidence.
    """

    SIGHT = "sight"
    HEARING = "hearing"


class LevelDirection(StrEnum):
    """Whether a condition-level change adds or removes levels."""

    GAIN = "gain"
    REMOVE = "remove"


class MovementCostKind(StrEnum):
    """What a stated movement cost is charged against."""

    #: "each foot of movement costs 1 extra foot" — a rate change.
    PER_FOOT_SURCHARGE = "per_foot_surcharge"
    #: "spend an amount of movement equal to half your Speed" — a lump cost.
    EXPENDITURE = "expenditure"


class MovementAmount(StrEnum):
    """How the source states a movement amount."""

    FEET = "feet"
    HALF_SPEED = "half_speed"


class TransformedForm(StrEnum):
    """What a transformation turns its subject into."""

    #: Petrified; True Polymorph's "If you turn a creature into an object".
    OBJECT = "object"
    #: Wild Shape, Animal Shapes, and the Monsters A-Z shape-shift traits.
    CREATURE_FORM = "creature_form"


class TrackedQuantity(StrEnum):
    """A quantity the source tests against a threshold or multiplies.

    Closed, and deliberately not a general variable namespace: each member is a
    quantity the corpus states a rule about directly.
    """

    #: "if your Speed is 0" — Prone, and Playing the Game > Dropping Prone.
    SPEED = "speed"
    #: "if your Exhaustion level is 6" / "reaches 0".
    CONDITION_LEVEL = "condition_level"
    #: "Your weight increases by a factor of ten."
    WEIGHT = "weight"


class Comparison(StrEnum):
    """How a quantity is tested against a stated value."""

    #: "if your Exhaustion level is 6", "if your Speed is 0".
    EQUALS = "equals"
    #: "When your Exhaustion level reaches 0".
    REACHES = "reaches"


class Phase(StrEnum):
    """When, relative to the owning effect's life, a component applies."""

    WHILE_ACTIVE = "while_active"
    #: "When this condition ends, you remain Prone." 34 occurrences across 4
    #: sections in the "when the spell/effect/condition ends" form.
    ON_END = "on_end"


class CreatureSize(StrEnum):
    """The printed size categories — Rules Glossary > Size."""

    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"
    GARGANTUAN = "gargantuan"


class SizeRelation(StrEnum):
    """The direction of a relative size comparison."""

    SMALLER = "smaller"
    LARGER = "larger"


class ApplicabilityKind(StrEnum):
    """The closed set of conditions under which a component applies.

    Each member ranges over a vocabulary that is already closed. A condition
    the source states over anything else is not admitted here and its span
    stays UNRESOLVED — that refusal is what keeps this from becoming a
    predicate language.
    """

    QUANTITY_THRESHOLD = "quantity_threshold"
    SIZE_COMPARISON = "size_comparison"
    TRIGGER = "trigger"
    PHASE = "phase"


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
    """What a stated change scales with."""

    HIGHER_LEVEL_SPELL_SLOT = "higher_level_spell_slot"
    CHARACTER_LEVEL = "character_level"
    CLASS_LEVEL = "class_level"
    #: A condition that accumulates levels — the Exhaustion level the source
    #: multiplies by: "the roll is reduced by 2 times your Exhaustion level".
    CONDITION_LEVEL = "condition_level"


class ScalingEffect(StrEnum):
    """Which part of an effect a stated change applies to."""

    DAMAGE = "damage"
    HEALING = "healing"
    TARGETS = "targets"
    DURATION = "duration"
    AREA = "area"
    #: "Use the spell slot's level for the spell's level in the stat block."
    EFFECTIVE_SPELL_LEVEL = "effective_spell_level"
    #: "When you make a D20 Test, the roll is reduced by …"
    D20_TEST = "d20_test"
    #: "Your Speed is reduced by a number of feet equal to …"
    SPEED = "speed"


class ScalingDirection(StrEnum):
    """Whether the stated change adds or subtracts.

    ``ScalingFact`` previously recorded only increases, because every observed
    instance was an increase. Exhaustion states two decreases, so the direction
    becomes explicit rather than implied by the family's name. Encoding a
    decrease as a negative ``amount`` would make the sign carry meaning
    the schema never declared.
    """

    INCREASE = "increase"
    DECREASE = "decrease"


class FactFamily(StrEnum):
    """The closed typed-fact union's discriminator."""

    ABILITY_CHECK = "ability_check"
    ACTION_ECONOMY = "action_economy"
    ACTION_RESTRICTION = "action_restriction"
    ADVANTAGE = "advantage"
    ATTACK_ROLL = "attack_roll"
    AUTOMATIC_OUTCOME = "automatic_outcome"
    CONDITION_EFFECT = "condition_effect"
    CONDITION_LEVEL = "condition_level"
    CRITICAL_HIT_RULE = "critical_hit_rule"
    CREATURE_ABILITY_SCORE = "creature_ability_score"
    CREATURE_CHALLENGE = "creature_challenge"
    CREATURE_DEFENSE = "creature_defense"
    CREATURE_SPEED = "creature_speed"
    DAMAGE = "damage"
    DAMAGE_RESPONSE = "damage_response"
    EQUIPMENT_DESCRIPTOR = "equipment_descriptor"
    HEALING = "healing"
    MOVEMENT_COST = "movement_cost"
    MOVEMENT_PERMISSION = "movement_permission"
    PROGRESSION_ENTRY = "progression_entry"
    QUANTITY_MULTIPLIER = "quantity_multiplier"
    RESOURCE_RECOVERY = "resource_recovery"
    SCALING = "scaling"
    SENSORY_CAPABILITY = "sensory_capability"
    SPEED_MODIFICATION = "speed_modification"
    SPELL_DESCRIPTOR = "spell_descriptor"
    SPELL_LIST_QUALIFIER = "spell_list_qualifier"
    SPELL_SLOT_PROGRESSION = "spell_slot_progression"
    STATE_EFFECT = "state_effect"
    TRANSFORMATION = "transformation"
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
class SizeComparison:
    """One size test: an absolute category, or a distance in categories.

    *"unless you are Tiny or two or more sizes smaller than it"* is two of
    these, both over the printed size vocabulary. Absolute and relative are
    distinct forms and never combine: a comparison carrying both would be two
    claims wearing one shape.
    """

    category: CreatureSize | None = None
    relation: SizeRelation | None = None
    at_least: int | None = None


@dataclass(frozen=True)
class RollSpec:
    """Exactly which roll a fact is about: whose, what kind, and of what ability.

    One shared definition rather than three fields repeated per family, for the
    same reason :class:`DiceExpression` is shared: *"Disadvantage on Dexterity
    saving throws"* and *"you automatically fail … Dexterity saving throws"*
    name the same roll, and two spellings of it would drift.

    Both axes are load-bearing and both were missing:

    * ``actor`` — without it *"Attack rolls against you have Advantage, and your
      attack rolls have Disadvantage"* (Blinded) and its exact inverse
      (Invisible) produce identical typed authority.
    * ``ability`` — without it *"Disadvantage on Dexterity saving throws"*
      (Restrained) can only be stated as disadvantage on *every* saving throw,
      which is not a lossy representation but a false one.

    ``ability`` is ``None`` when the source does not name one, and is never
    guessed: an attack roll has no ability qualifier in the source's own
    phrasing, so the field stays absent rather than being filled from the
    weapon's or spell's ability.
    """

    actor: RollActor
    context: RollContext
    #: Set exactly when the source names an ability, which it does only for
    #: ability checks and saving throws.
    ability: AbilityScore | None = None


@dataclass(frozen=True)
class AbilityCheckFact:
    """A check or save with a typed DC source.

    Deliberately **not** migrated onto :class:`RollSpec`. This family states
    *that a roll is called for and where its DC comes from*; ``RollSpec`` says
    *which roll a stated modification applies to*. A DC source has no actor
    polarity — the DC is the same value whoever rolls against it — so folding
    the two together would give this family a field it can never populate.
    """

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
    """One resistance, immunity, or vulnerability, to a type or to all damage.

    The Mummy prints ``Vulnerabilities Fire`` and ``Immunities Necrotic,
    Poison`` — three facts, not one list, so each carries its own provenance.

    ``scope`` exists because the source also states the whole-set form:
    *"You have Resistance to all damage"* (Petrified) and *"Immunity to all
    damage"* (Damage Threshold), 12 times across seven sections. That is one
    claim, and it must stay one claim — thirteen enumerated facts would each
    need a ``PRIMARY`` provenance claim on the same span, which validation
    rejects.

    ``except_types`` carries the stated exceptions of the ``ALL`` form —
    *"Resistance to all damage except Force damage"* (Barbarian),
    *"except Psychic and Radiant"* (Boon of Truesight), *"Immunity to all
    damage except Fire"* (the mummy lord's heart). It is held sorted and
    duplicate-free so one claim has one canonical payload and therefore one
    fact key.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.DAMAGE_RESPONSE

    response: DamageResponseKind
    scope: DamageScope = DamageScope.SPECIFIC
    #: Set exactly for ``SPECIFIC``.
    damage_type: DamageType | None = None
    #: Permitted only for ``ALL``; sorted, non-empty when present.
    except_types: tuple[DamageType, ...] = ()


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
    """A stated advantage or disadvantage on an exactly identified roll.

    ``You have Disadvantage on attack rolls with a Heavy weapon if …`` — the
    *condition* under which it applies is governing prose; that it is
    disadvantage on the subject's own attack rolls is this fact.

    ``roll`` replaces the former bare ``context``. Which roll a rule modifies is
    not only its kind: Prone states three distinct modifications of attack rolls
    in one clause, and under a bare context two of them collapsed into the same
    payload and were rejected as a duplicate fact.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.ADVANTAGE

    state: AdvantageState
    roll: RollSpec


@dataclass(frozen=True)
class AutomaticOutcomeFact:
    """A D20 Test the source resolves without a roll.

    *"You automatically fail Strength and Dexterity saving throws"* is two
    facts, one per named ability, because the source names two rolls. Distinct
    from :class:`AdvantageFact`: an automatic outcome is not an extreme
    advantage, it is the absence of the roll.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.AUTOMATIC_OUTCOME

    roll: RollSpec
    outcome: AutomaticOutcome


@dataclass(frozen=True)
class SpeedModificationFact:
    """A stated change to the subject's own Speed.

    Distinct from :class:`CreatureSpeedFact`, which states what a creature's
    stat block prints. This states what a rule *does* to whatever Speed the
    subject has — *"Your Speed is 0 and can't increase"* (five conditions),
    *"the target's Speed is reduced by 15 feet"* (Classes), *"Speed is halved"*
    (Spells). Using the stat-block family for that would claim the subject's
    printed Speed is 0.

    ``mode`` is ``None`` when the source modifies Speed unqualified, and names a
    mode only where the source does (*"your Fly Speed is reduced to 0"*).
    ``feet`` is set exactly for ``SET_TO`` and ``REDUCED_BY``; ``HALVED`` states
    no number.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.SPEED_MODIFICATION

    change: SpeedChange
    feet: int | None = None
    mode: MovementMode | None = None
    #: "and can't increase" — stated by every condition that zeroes Speed.
    can_increase: bool = True


@dataclass(frozen=True)
class ActionRestrictionFact:
    """An action-economy slot the subject cannot use.

    *"You can't take any action, Bonus Action, or Reaction"* (Incapacitated) is
    three facts, one per named slot. The inverse of
    :class:`ActionEconomyFact`, which states what an effect *consumes*; a cost
    cannot express a prohibition.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.ACTION_RESTRICTION

    cost: ActionCost


@dataclass(frozen=True)
class CriticalHitRuleFact:
    """A stated change to when an attack roll is a Critical Hit.

    ``threshold`` is the lowest d20 face that scores a Critical Hit, set exactly
    for ``THRESHOLD_LOWERED`` (*"on a roll of 19 or 20"* → 19).
    ``AUTOMATIC_ON_HIT`` states no threshold: any hit is a Critical Hit, and the
    circumstance under which the rule applies (*"if the attacker is within 5
    feet of you"*) is governing prose.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.CRITICAL_HIT_RULE

    change: CriticalHitChange
    threshold: int | None = None


@dataclass(frozen=True)
class StateEffectFact:
    """One typed state effect from the closed observed vocabulary.

    The *typed state effects* group #137 contract 3 names. Closed and
    evidence-bound: see :class:`StateEffectKind` for the per-member sibling
    evidence that admitted it. A state a batch cannot type is honestly
    unresolved, never a new member added to make a batch pass.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.STATE_EFFECT

    effect: StateEffectKind


@dataclass(frozen=True)
class SensoryCapabilityFact:
    """A perceptual capability a rule grants or removes.

    *"You can't see"* (Blinded) and *"You can't hear"* (Deafened) state
    deterministic capability states. That some downstream consequences are
    contextual is a fact about narration, not about the rule, so these are
    typed rather than prose-bound. ``range_feet`` is set only for a grant that
    states one; a removal has no range.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.SENSORY_CAPABILITY

    sense: Sense
    can_perceive: bool
    range_feet: int | None = None


@dataclass(frozen=True)
class ConditionLevelFact:
    """A stated change to how many levels of a condition the subject has.

    :class:`ConditionEffectFact` says a condition applies or is removed;
    it cannot say *how many levels*, and for Exhaustion the level is the
    mechanic — level 1 and level 6 differ by death. Exactly one of ``amount``
    and ``all_levels`` is set: *"removes 1 of your Exhaustion levels"* against
    Suffocation's *"removes all levels of Exhaustion"*.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.CONDITION_LEVEL

    condition: ConditionKind
    direction: LevelDirection
    amount: int | None = None
    all_levels: bool = False
    #: "This condition is cumulative." Stated only where the source states it.
    cumulative: bool = False


@dataclass(frozen=True)
class MovementCostFact:
    """What movement costs — a per-foot surcharge, or a lump expenditure.

    The movement-economy counterpart of :class:`ActionEconomyFact`: it states
    the cost, never what the cost buys. ``feet`` is set exactly for
    :attr:`MovementAmount.FEET`; ``HALF_SPEED`` states no number, the same way
    :attr:`SpeedChange.HALVED` does.

    Distinct from :class:`SpeedModificationFact`, and the distinction is not
    cosmetic: Prone charges a one-off expenditure derived from Speed, it does
    not halve Speed, so ``SpeedModificationFact(HALVED)`` here would be false
    rather than lossy.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.MOVEMENT_COST

    kind: MovementCostKind
    amount: MovementAmount
    feet: int | None = None


@dataclass(frozen=True)
class MovementPermissionFact:
    """A movement mode the subject may use.

    Prone's *"to crawl"*, and Tsunami's *"A creature caught in the wall can
    move by swimming."* Two instances in two sections: the thinnest family
    admitted here, and stated as such. Its vocabulary is stronger than its
    sibling count — the mode list is printed at Playing the Game > Movement and
    Position.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.MOVEMENT_PERMISSION

    mode: MovementMode


@dataclass(frozen=True)
class TransformationFact:
    """The subject's form changes, and whether carried gear changes with it.

    Petrified transforms a creature into an object *"along with any nonmagical
    objects you are wearing and carrying"*; True Polymorph states the identical
    structure, and the Monsters A-Z shape-shift traits state its inverse —
    *"Any equipment it is wearing or carrying isn't transformed."* Both
    ``becomes`` members and both inclusion values are instantiated by the
    corpus.

    What the subject becomes in the fiction — Petrified's *"(usually stone)"* —
    is not here: the source hedges it, so it is governing prose.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.TRANSFORMATION

    becomes: TransformedForm
    carried_nonmagical_included: bool


@dataclass(frozen=True)
class QuantityMultiplierFact:
    """A stated quantity multiplied by a factor.

    *"Your weight increases by a factor of ten."* Distinct from
    :class:`ScalingFact`, which states an increase driven by a *basis* such as
    a spell slot level; this states a flat multiplication with no basis, and
    representing it as scaling would invent a basis the source does not state.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.QUANTITY_MULTIPLIER

    quantity: TrackedQuantity
    factor: int


@dataclass(frozen=True)
class ScalingFact:
    """What the source says increases, and with what.

    ``The damage increases by 1d10 for each spell slot level above 4`` is
    ``ScalingFact(HIGHER_LEVEL_SPELL_SLOT, 4, DAMAGE, dice_amount=1d10)``.

    **Declarative only.** This records a stated increase; it is not evaluated,
    and it defines no adjudication parameter. Choosing a slot level at play time
    — the ``chosen_slot_level`` shape — is the recorded Known Unknown owned by
    an ADR-015b amendment, and nothing in this family supplies it.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.SCALING

    basis: ScalingBasis
    #: The level above which the change begins to apply.
    threshold: int
    effect: ScalingEffect
    #: Whether the stated change adds or subtracts. Exhaustion states the only
    #: observed decreases; a negative ``amount`` would hide the
    #: direction in a sign the schema never declared.
    direction: ScalingDirection = ScalingDirection.INCREASE
    dice_amount: DiceExpression | None = None
    amount: int | None = None


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
    | ActionRestrictionFact
    | AdvantageFact
    | AttackRollFact
    | AutomaticOutcomeFact
    | ConditionEffectFact
    | ConditionLevelFact
    | CriticalHitRuleFact
    | MovementCostFact
    | MovementPermissionFact
    | QuantityMultiplierFact
    | SensoryCapabilityFact
    | TransformationFact
    | SpeedModificationFact
    | StateEffectFact
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
    FactFamily.ACTION_RESTRICTION: ActionRestrictionFact,
    FactFamily.ADVANTAGE: AdvantageFact,
    FactFamily.ATTACK_ROLL: AttackRollFact,
    FactFamily.AUTOMATIC_OUTCOME: AutomaticOutcomeFact,
    FactFamily.CONDITION_EFFECT: ConditionEffectFact,
    FactFamily.CRITICAL_HIT_RULE: CriticalHitRuleFact,
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
    FactFamily.CONDITION_LEVEL: ConditionLevelFact,
    FactFamily.MOVEMENT_COST: MovementCostFact,
    FactFamily.MOVEMENT_PERMISSION: MovementPermissionFact,
    FactFamily.QUANTITY_MULTIPLIER: QuantityMultiplierFact,
    FactFamily.SENSORY_CAPABILITY: SensoryCapabilityFact,
    FactFamily.TRANSFORMATION: TransformationFact,
    FactFamily.SPEED_MODIFICATION: SpeedModificationFact,
    FactFamily.SPELL_DESCRIPTOR: SpellDescriptorFact,
    FactFamily.SPELL_LIST_QUALIFIER: SpellListQualifierFact,
    FactFamily.SPELL_SLOT_PROGRESSION: SpellSlotProgressionFact,
    FactFamily.STATE_EFFECT: StateEffectFact,
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


def exact_type_violations(value: object, cls: type, field: str) -> list[str]:
    """The field must hold that exact closed type, or nothing.

    A subclass is refused, not accepted as a narrower case. Every closed
    structure here is identified by the payload its declared fields produce, so
    a subclass carrying an undeclared meaning-bearing field would canonicalize —
    and persist, and hash — identically to one asserting something else. A
    subclass may also redefine ``__eq__``, which would let it slip past the
    duplicate checks that use set membership.
    """
    if type(value) is not cls:
        return [f"{field} must be {cls.__name__}, got {type(value).__name__} {value!r}"]
    return []


#: The name this rule has had since the fact-family validators; kept so the
#: many internal call sites read unchanged.
_vo_field = exact_type_violations


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


def _check_rollspec(value: object, field: str) -> list[str]:
    """Invariants of the shared roll specification.

    Held to the same strictness as the families that contain it, exactly like
    :func:`_check_dice`: a value object is as closed as a family.

    The type test goes through :func:`_vo_field`, the same exact-type seam every
    sibling value object uses, rather than ``isinstance``. A subclass passes an
    ``isinstance`` test and then carries its extra fields straight into
    :func:`fact_payload`, so validation would approve authority that
    :func:`fact_from_payload` refuses to rebuild — a candidate that persists and
    then cannot be reconstructed. "Closed" has to mean the declared type, not a
    type compatible with it.
    """
    if findings := _vo_field(value, RollSpec, field):
        return findings
    value = cast(RollSpec, value)
    findings = [
        *_enum_field(value.actor, RollActor, f"{field}.actor"),
        *_enum_field(value.context, RollContext, f"{field}.context"),
        *_optional_enum_field(value.ability, AbilityScore, f"{field}.ability"),
    ]
    if findings:
        return findings
    # The source names an ability only for the two roll kinds that have one. An
    # ability-qualified attack roll or Initiative would be a qualifier the
    # source never states.
    if value.ability is not None and value.context not in (
        RollContext.ABILITY_CHECK,
        RollContext.SAVING_THROW,
    ):
        findings.append(
            f"{field} qualifies a {value.context.value} by ability; the source "
            "names an ability only for ability checks and saving throws"
        )
    # Initiative is always rolled by the creature whose turn order it sets;
    # "Initiative against you" is not a thing the source can say.
    if value.context is RollContext.INITIATIVE and value.actor is not RollActor.SUBJECT:
        findings.append(f"{field} states Initiative rolled against the subject")
    return findings


def _check_damage_response(fact: DamageResponseFact) -> list[str]:
    findings = [
        *_enum_field(fact.response, DamageResponseKind, "response"),
        *_enum_field(fact.scope, DamageScope, "scope"),
        *_optional_enum_field(fact.damage_type, DamageType, "damage_type"),
    ]
    if not isinstance(fact.except_types, tuple):
        findings.append("except_types is not a tuple")
    else:
        for i, t in enumerate(fact.except_types):
            findings.extend(_enum_field(t, DamageType, f"except_types[{i}]"))
    if findings:
        return findings

    if fact.scope is DamageScope.SPECIFIC:
        if fact.damage_type is None:
            findings.append("specific damage response names no damage type")
        if fact.except_types:
            findings.append(
                "specific damage response carries exceptions; exceptions "
                "qualify the all-damage form"
            )
    else:
        if fact.damage_type is not None:
            findings.append(
                "all-damage response also names a damage type; the value comes "
                "from the scope, not from both"
            )
        # One claim, one canonical payload: tuple order reaches the fact key, so
        # two orderings of the same exceptions would be two facts.
        codes = [t.value for t in fact.except_types]
        if codes != sorted(codes):
            findings.append("except_types is not sorted")
        if len(set(codes)) != len(codes):
            findings.append("except_types repeats a damage type")
        elif len(set(codes)) == len(DamageType):
            # "Resistance to all damage except <every damage type>" responds to
            # nothing. Derived from the closed vocabulary rather than a written
            # count, so a damage type added later cannot leave this stale.
            findings.append(
                "all-damage response excepts every damage type and therefore "
                "responds to none"
            )
    return findings


def _check_automatic_outcome(fact: AutomaticOutcomeFact) -> list[str]:
    return [
        *_check_rollspec(fact.roll, "roll"),
        *_enum_field(fact.outcome, AutomaticOutcome, "outcome"),
    ]


def _check_action_restriction(fact: ActionRestrictionFact) -> list[str]:
    findings = _enum_field(fact.cost, ActionCost, "cost")
    if findings:
        return findings
    # NONE and SPECIAL describe what an effect costs, not a slot that can be
    # forbidden; "you can't take any none" states nothing.
    if fact.cost in (ActionCost.NONE, ActionCost.SPECIAL):
        findings.append(f"{fact.cost.value} is not an action-economy slot to restrict")
    return findings


def _check_critical_hit_rule(fact: CriticalHitRuleFact) -> list[str]:
    findings = [
        *_enum_field(fact.change, CriticalHitChange, "change"),
        *_optional_int_field(fact.threshold, "threshold"),
    ]
    if findings:
        return findings
    if fact.change is CriticalHitChange.THRESHOLD_LOWERED:
        if fact.threshold is None:
            findings.append("threshold_lowered states no threshold")
        elif not 2 <= fact.threshold <= 19:
            # 20 is the ordinary threshold, so a "lowered" threshold of 20
            # lowers nothing: the variant would claim a change it does not make
            # and still satisfy a typed-family obligation. The upper bound is
            # therefore 19, not the die's top face.
            findings.append(
                f"critical-hit threshold {fact.threshold} is not a lowered d20 "
                "threshold; 20 is the ordinary one and 1 is not a face a rule "
                "can lower to"
            )
    elif fact.threshold is not None:
        findings.append(
            "automatic_on_hit carries a threshold; any hit is a Critical Hit"
        )
    return findings


def _check_state_effect(fact: StateEffectFact) -> list[str]:
    return _enum_field(fact.effect, StateEffectKind, "effect")


def _check_speed_modification(fact: SpeedModificationFact) -> list[str]:
    findings = [
        *_enum_field(fact.change, SpeedChange, "change"),
        *_optional_int_field(fact.feet, "feet"),
        *_optional_enum_field(fact.mode, MovementMode, "mode"),
        *_bool_field(fact.can_increase, "can_increase"),
    ]
    if findings:
        return findings
    if fact.change is SpeedChange.HALVED:
        if fact.feet is not None:
            findings.append("halved speed carries a distance; the source states none")
    elif fact.feet is None:
        findings.append(f"{fact.change.value} speed states no distance")
    elif fact.feet < 0:
        findings.append(f"negative speed distance {fact.feet}")
    elif fact.change is SpeedChange.REDUCED_BY and fact.feet == 0:
        # The same rule ``ScalingFact`` already applies to a zero amount: a
        # stated reduction of nothing is not a weaker reduction, it is no rule.
        # ``SET_TO`` is deliberately exempt — "your Speed is 0" is exactly the
        # form five conditions state.
        findings.append("speed reduced by 0 feet changes nothing")
    return findings


def _check_sensory_capability(fact: SensoryCapabilityFact) -> list[str]:
    findings = [
        *_enum_field(fact.sense, Sense, "sense"),
        *_bool_field(fact.can_perceive, "can_perceive"),
        *_optional_int_field(fact.range_feet, "range_feet"),
    ]
    if findings:
        return findings
    if not fact.can_perceive and fact.range_feet is not None:
        findings.append("a removed capability carries a range; the source states none")
    elif fact.range_feet is not None and fact.range_feet <= 0:
        findings.append(f"sense range {fact.range_feet} is not a distance")
    return findings


def _check_condition_level(fact: ConditionLevelFact) -> list[str]:
    findings = [
        *_enum_field(fact.condition, ConditionKind, "condition"),
        *_enum_field(fact.direction, LevelDirection, "direction"),
        *_optional_int_field(fact.amount, "amount"),
        *_bool_field(fact.all_levels, "all_levels"),
        *_bool_field(fact.cumulative, "cumulative"),
    ]
    if findings:
        return findings
    if fact.all_levels:
        if fact.amount is not None:
            findings.append("all_levels carries an amount; the two are alternatives")
    elif fact.amount is None:
        findings.append("a level change states neither an amount nor all_levels")
    elif fact.amount <= 0:
        findings.append(f"level change of {fact.amount} changes nothing")
    if fact.cumulative and fact.direction is not LevelDirection.GAIN:
        findings.append("only an accrual can be cumulative")
    if fact.all_levels and fact.direction is not LevelDirection.REMOVE:
        findings.append("all_levels states a removal, not an accrual")
    return findings


#: The legal ``(kind, amount)`` matrix. Stated as the allowed set rather than as
#: two prohibitions, because both prohibitions the review names —
#: ``PER_FOOT_SURCHARGE`` requires ``FEET``, and ``HALF_SPEED`` requires
#: ``EXPENDITURE`` — forbid the *same single cell*, and reporting one malformed
#: fact twice would describe two defects where there is one. An allowed set also
#: stays correct if either vocabulary gains a member: a new pairing is refused
#: until it is deliberately admitted, rather than silently legal.
_MOVEMENT_COST_MATRIX: frozenset[tuple[MovementCostKind, MovementAmount]] = frozenset(
    {
        # "each foot of movement costs 1 extra foot" — a rate, stated in feet.
        (MovementCostKind.PER_FOOT_SURCHARGE, MovementAmount.FEET),
        # "spend 10 feet of movement" — a lump cost stated as a fixed distance.
        (MovementCostKind.EXPENDITURE, MovementAmount.FEET),
        # "spend movement equal to half your Speed" — a lump cost, no number.
        (MovementCostKind.EXPENDITURE, MovementAmount.HALF_SPEED),
    }
)


def _check_movement_cost(fact: MovementCostFact) -> list[str]:
    findings = [
        *_enum_field(fact.kind, MovementCostKind, "kind"),
        *_enum_field(fact.amount, MovementAmount, "amount"),
        *_optional_int_field(fact.feet, "feet"),
    ]
    if findings:
        return findings
    if (fact.kind, fact.amount) not in _MOVEMENT_COST_MATRIX:
        # A per-foot *rate* cannot be stated as half a Speed: the declared kind
        # charges per foot of movement, while HALF_SPEED is the lump form. The
        # combination reads as a rule but names no computable cost.
        return [f"{fact.kind.value} cannot state a {fact.amount.value} amount"]
    if fact.amount is MovementAmount.FEET:
        if fact.feet is None:
            findings.append("a stated distance carries no feet")
        elif fact.feet <= 0:
            findings.append(f"movement cost of {fact.feet} feet costs nothing")
    elif fact.feet is not None:
        findings.append(
            f"{fact.amount.value} carries a distance; the source states none"
        )
    return findings


def _check_movement_permission(fact: MovementPermissionFact) -> list[str]:
    return [*_enum_field(fact.mode, MovementMode, "mode")]


def _check_transformation(fact: TransformationFact) -> list[str]:
    return [
        *_enum_field(fact.becomes, TransformedForm, "becomes"),
        *_bool_field(fact.carried_nonmagical_included, "carried_nonmagical_included"),
    ]


def _check_quantity_multiplier(fact: QuantityMultiplierFact) -> list[str]:
    findings = [
        *_enum_field(fact.quantity, TrackedQuantity, "quantity"),
        *_int_field(fact.factor, "factor"),
    ]
    if findings:
        return findings
    if fact.factor < 2:
        # A factor of 1 multiplies nothing and 0 is not a multiplication the
        # corpus states; both would be a rule that changes no value.
        findings.append(f"multiplier of {fact.factor} states no change")
    return findings


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
        *_check_rollspec(fact.roll, "roll"),
    ]


def _check_scaling(fact: ScalingFact) -> list[str]:
    findings = [
        *_enum_field(fact.basis, ScalingBasis, "basis"),
        *_int_field(fact.threshold, "threshold"),
        *_enum_field(fact.effect, ScalingEffect, "effect"),
        *_enum_field(fact.direction, ScalingDirection, "direction"),
        *_check_optional_dice(fact.dice_amount, "dice_amount"),
        *_optional_int_field(fact.amount, "amount"),
    ]
    if findings:
        return findings
    if fact.threshold < 0:
        findings.append(f"negative scaling threshold {fact.threshold}")
    stated = (fact.dice_amount is not None) + (fact.amount is not None)
    if fact.effect is ScalingEffect.EFFECTIVE_SPELL_LEVEL:
        # "Use the spell slot's level for the spell's level in the stat block"
        # states no increment of its own — the slot level *is* the value.
        if stated:
            findings.append(
                "effective_spell_level scaling carries an increment; the value "
                "comes from the slot level itself"
            )
        if fact.direction is not ScalingDirection.INCREASE:
            findings.append(
                "effective_spell_level scaling states a direction; a higher slot "
                "level is the value, not a change to one"
            )
    elif stated != 1:
        findings.append("scaling states exactly one of a dice amount or an amount")
    # Magnitude only. Which way it goes is ``direction``, so a value below one
    # changes nothing whichever direction it claims.
    if fact.amount is not None and fact.amount < 1:
        findings.append(f"amount {fact.amount} changes nothing")
    # The observed decreases scale a roll or a Speed. A decreasing damage or
    # healing die is not something the source states, and admitting it would let
    # an upcasting fact silently invert.
    if fact.direction is ScalingDirection.DECREASE and fact.effect not in (
        ScalingEffect.D20_TEST,
        ScalingEffect.SPEED,
    ):
        findings.append(
            f"decreasing {fact.effect.value} scaling is not a form the source states"
        )
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
    FactFamily.ACTION_RESTRICTION: _check_action_restriction,
    FactFamily.ADVANTAGE: _check_advantage,
    FactFamily.ATTACK_ROLL: _check_attack_roll,
    FactFamily.AUTOMATIC_OUTCOME: _check_automatic_outcome,
    FactFamily.CONDITION_EFFECT: _check_condition_effect,
    FactFamily.CONDITION_LEVEL: _check_condition_level,
    FactFamily.MOVEMENT_COST: _check_movement_cost,
    FactFamily.MOVEMENT_PERMISSION: _check_movement_permission,
    FactFamily.QUANTITY_MULTIPLIER: _check_quantity_multiplier,
    FactFamily.SENSORY_CAPABILITY: _check_sensory_capability,
    FactFamily.TRANSFORMATION: _check_transformation,
    FactFamily.CRITICAL_HIT_RULE: _check_critical_hit_rule,
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
    FactFamily.SPEED_MODIFICATION: _check_speed_modification,
    FactFamily.SPELL_DESCRIPTOR: _check_spell_descriptor,
    FactFamily.SPELL_LIST_QUALIFIER: _check_spell_list_qualifier,
    FactFamily.SPELL_SLOT_PROGRESSION: _check_spell_slot_progression,
    FactFamily.STATE_EFFECT: _check_state_effect,
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


def _build_rollspec(value: object, where: str) -> RollSpec:
    """Rebuild the shared roll specification from its persisted payload."""
    p = _json_object(value, ("actor", "context", "ability"), where)
    _reject_at(
        where,
        [
            *_json_enum(p["actor"], RollActor, f"{where}.actor"),
            *_json_enum(p["context"], RollContext, f"{where}.context"),
            *_optional_json_enum(p["ability"], AbilityScore, f"{where}.ability"),
        ],
    )
    return RollSpec(
        actor=RollActor(p["actor"]),
        context=RollContext(p["context"]),
        ability=None if p["ability"] is None else AbilityScore(p["ability"]),
    )


def _build_damage_response(p: Mapping[str, Any]) -> DamageResponseFact:
    raw_except = p["except_types"]
    if not isinstance(raw_except, list):
        raise MalformedFactPayloadError("except_types is not a list")
    findings = [
        *_json_enum(p["response"], DamageResponseKind, "response"),
        *_json_enum(p["scope"], DamageScope, "scope"),
        *_optional_json_enum(p["damage_type"], DamageType, "damage_type"),
    ]
    for i, t in enumerate(raw_except):
        findings.extend(_json_enum(t, DamageType, f"except_types[{i}]"))
    _reject(FactFamily.DAMAGE_RESPONSE, findings)
    return DamageResponseFact(
        response=DamageResponseKind(p["response"]),
        scope=DamageScope(p["scope"]),
        damage_type=None if p["damage_type"] is None else DamageType(p["damage_type"]),
        except_types=tuple(DamageType(t) for t in raw_except),
    )


def _build_automatic_outcome(p: Mapping[str, Any]) -> AutomaticOutcomeFact:
    _reject(
        FactFamily.AUTOMATIC_OUTCOME,
        _json_enum(p["outcome"], AutomaticOutcome, "outcome"),
    )
    return AutomaticOutcomeFact(
        roll=_build_rollspec(p["roll"], "roll"),
        outcome=AutomaticOutcome(p["outcome"]),
    )


def _build_action_restriction(p: Mapping[str, Any]) -> ActionRestrictionFact:
    _reject(FactFamily.ACTION_RESTRICTION, _json_enum(p["cost"], ActionCost, "cost"))
    return ActionRestrictionFact(cost=ActionCost(p["cost"]))


def _build_critical_hit_rule(p: Mapping[str, Any]) -> CriticalHitRuleFact:
    _reject(
        FactFamily.CRITICAL_HIT_RULE,
        [
            *_json_enum(p["change"], CriticalHitChange, "change"),
            *_optional_int_field(p["threshold"], "threshold"),
        ],
    )
    return CriticalHitRuleFact(
        change=CriticalHitChange(p["change"]), threshold=p["threshold"]
    )


def _build_state_effect(p: Mapping[str, Any]) -> StateEffectFact:
    _reject(FactFamily.STATE_EFFECT, _json_enum(p["effect"], StateEffectKind, "effect"))
    return StateEffectFact(effect=StateEffectKind(p["effect"]))


def _build_speed_modification(p: Mapping[str, Any]) -> SpeedModificationFact:
    _reject(
        FactFamily.SPEED_MODIFICATION,
        [
            *_json_enum(p["change"], SpeedChange, "change"),
            *_optional_int_field(p["feet"], "feet"),
            *_optional_json_enum(p["mode"], MovementMode, "mode"),
            *_bool_field(p["can_increase"], "can_increase"),
        ],
    )
    return SpeedModificationFact(
        change=SpeedChange(p["change"]),
        feet=p["feet"],
        mode=None if p["mode"] is None else MovementMode(p["mode"]),
        can_increase=p["can_increase"],
    )


def _build_sensory_capability(p: Mapping[str, Any]) -> SensoryCapabilityFact:
    _reject(
        FactFamily.SENSORY_CAPABILITY,
        [
            *_json_enum(p["sense"], Sense, "sense"),
            *_bool_field(p["can_perceive"], "can_perceive"),
            *_optional_int_field(p["range_feet"], "range_feet"),
        ],
    )
    return SensoryCapabilityFact(
        sense=Sense(p["sense"]),
        can_perceive=p["can_perceive"],
        range_feet=p["range_feet"],
    )


def _build_condition_level(p: Mapping[str, Any]) -> ConditionLevelFact:
    _reject(
        FactFamily.CONDITION_LEVEL,
        [
            *_json_enum(p["condition"], ConditionKind, "condition"),
            *_json_enum(p["direction"], LevelDirection, "direction"),
            *_optional_int_field(p["amount"], "amount"),
            *_bool_field(p["all_levels"], "all_levels"),
            *_bool_field(p["cumulative"], "cumulative"),
        ],
    )
    return ConditionLevelFact(
        condition=ConditionKind(p["condition"]),
        direction=LevelDirection(p["direction"]),
        amount=p["amount"],
        all_levels=p["all_levels"],
        cumulative=p["cumulative"],
    )


def _build_movement_cost(p: Mapping[str, Any]) -> MovementCostFact:
    _reject(
        FactFamily.MOVEMENT_COST,
        [
            *_json_enum(p["kind"], MovementCostKind, "kind"),
            *_json_enum(p["amount"], MovementAmount, "amount"),
            *_optional_int_field(p["feet"], "feet"),
        ],
    )
    return MovementCostFact(
        kind=MovementCostKind(p["kind"]),
        amount=MovementAmount(p["amount"]),
        feet=p["feet"],
    )


def _build_movement_permission(p: Mapping[str, Any]) -> MovementPermissionFact:
    _reject(
        FactFamily.MOVEMENT_PERMISSION,
        [*_json_enum(p["mode"], MovementMode, "mode")],
    )
    return MovementPermissionFact(mode=MovementMode(p["mode"]))


def _build_transformation(p: Mapping[str, Any]) -> TransformationFact:
    _reject(
        FactFamily.TRANSFORMATION,
        [
            *_json_enum(p["becomes"], TransformedForm, "becomes"),
            *_bool_field(
                p["carried_nonmagical_included"], "carried_nonmagical_included"
            ),
        ],
    )
    return TransformationFact(
        becomes=TransformedForm(p["becomes"]),
        carried_nonmagical_included=p["carried_nonmagical_included"],
    )


def _build_quantity_multiplier(p: Mapping[str, Any]) -> QuantityMultiplierFact:
    _reject(
        FactFamily.QUANTITY_MULTIPLIER,
        [
            *_json_enum(p["quantity"], TrackedQuantity, "quantity"),
            *_int_field(p["factor"], "factor"),
        ],
    )
    return QuantityMultiplierFact(
        quantity=TrackedQuantity(p["quantity"]), factor=p["factor"]
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
    _reject(FactFamily.ADVANTAGE, _json_enum(p["state"], AdvantageState, "state"))
    return AdvantageFact(
        state=AdvantageState(p["state"]), roll=_build_rollspec(p["roll"], "roll")
    )


def _build_scaling(p: Mapping[str, Any]) -> ScalingFact:
    _reject(
        FactFamily.SCALING,
        [
            *_json_enum(p["basis"], ScalingBasis, "basis"),
            *_int_field(p["threshold"], "threshold"),
            *_json_enum(p["effect"], ScalingEffect, "effect"),
            *_json_enum(p["direction"], ScalingDirection, "direction"),
            *_optional_int_field(p["amount"], "amount"),
        ],
    )
    return ScalingFact(
        basis=ScalingBasis(p["basis"]),
        threshold=p["threshold"],
        effect=ScalingEffect(p["effect"]),
        direction=ScalingDirection(p["direction"]),
        dice_amount=(
            None
            if p["dice_amount"] is None
            else _build_dice(p["dice_amount"], "dice_amount")
        ),
        amount=p["amount"],
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
    FactFamily.ACTION_RESTRICTION: _build_action_restriction,
    FactFamily.ADVANTAGE: _build_advantage,
    FactFamily.ATTACK_ROLL: _build_attack_roll,
    FactFamily.AUTOMATIC_OUTCOME: _build_automatic_outcome,
    FactFamily.CONDITION_EFFECT: _build_condition_effect,
    FactFamily.CONDITION_LEVEL: _build_condition_level,
    FactFamily.MOVEMENT_COST: _build_movement_cost,
    FactFamily.MOVEMENT_PERMISSION: _build_movement_permission,
    FactFamily.QUANTITY_MULTIPLIER: _build_quantity_multiplier,
    FactFamily.SENSORY_CAPABILITY: _build_sensory_capability,
    FactFamily.TRANSFORMATION: _build_transformation,
    FactFamily.CRITICAL_HIT_RULE: _build_critical_hit_rule,
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
    FactFamily.SPEED_MODIFICATION: _build_speed_modification,
    FactFamily.SPELL_DESCRIPTOR: _build_spell_descriptor,
    FactFamily.SPELL_LIST_QUALIFIER: _build_spell_list_qualifier,
    FactFamily.SPELL_SLOT_PROGRESSION: _build_spell_slot_progression,
    FactFamily.STATE_EFFECT: _build_state_effect,
    FactFamily.WEAPON_PROPERTY: _build_weapon_property,
}

#: Every family must declare a builder and an invariant checker. A family added
#: to the union with neither is a family nothing validates and nothing can
#: reconstruct — a silent hole rather than a visible omission, which is exactly
#: what this module's per-family structure exists to prevent.
assert (
    set(_FACT_TYPES) == set(_FACT_BUILDERS) == set(_FACT_INVARIANTS) == set(FactFamily)
), "every FactFamily needs a type, a builder, and an invariant checker"


# ---------------------------------------------------------------------------
# Representation-schema identity (ADR-005d Decisions 4 and 6)
# ---------------------------------------------------------------------------
#
# The closed union is versioned and identity-bound, for the same reason the
# semantic policy is: authority is only meaningful under the contract it was
# built against. Without this, a projection whose facts all belong to families
# this release did not touch keeps its old UUID across a union that now means
# something different, and a stored binding cannot say which contract governs
# it.
#
# **Distinct from the semantic policy, deliberately.** ``5d-semantic-policy-1``
# identifies the closed *classification* catalogs and the canonicalization rule —
# what makes a span's disposition checkable. This identifies the closed
# *representation* contract — what a fact may say. They change for different
# reasons and on different schedules, and overloading one to carry the other
# would remint every accepted classification whenever a fact family was added.

#: Bumped whenever the closed representation contract changes meaning. Two
#: distinct triggers, and the second is easy to miss:
#:
#: * **structural** — a family added or removed, a field added, removed, or
#:   retyped, a closed vocabulary gaining or losing a member. These also move
#:   :func:`representation_schema_hash`, because it is derived from the declared
#:   types.
#: * **invariant** — a per-family invariant that changes which values the union
#:   admits, with the declared structure untouched. Rejecting a
#:   ``THRESHOLD_LOWERED`` critical-hit threshold of 20, or a Speed reduction of
#:   zero feet, narrows what a fact may say without altering a single field or
#:   enum member, so the structural hash does **not** move. The version must be
#:   bumped by hand in that case: two projections admitting different value sets
#:   are not built under the same contract, and only the version can say so.
#:
#: The hash deliberately does not cover checker implementations — hashing code
#: would remint authority for a refactor, which is the failure the structural
#: derivation exists to avoid. The cost of that choice is exactly this manual
#: obligation, and it is stated here rather than left to be inferred.
#:
#: What the identity **owns**, settled during review and enforced by tests: the
#: canonical *serialized* contract, never the Python implementation expressing
#: it. Renaming a fact class, a value-object class, an enum class, a module, or
#: a local symbol changes nothing any payload can observe, and must therefore
#: move nothing here. Renaming a family discriminator or a serialized field,
#: adding or removing an admitted vocabulary value, or changing a primitive,
#: nullability, array, or nested-object shape still must.
#: :func:`representation_schema_payload` renders that contract in a closed
#: shape grammar which has nowhere to put a Python name.
#:
#: **When a version must be succeeded rather than corrected in place.** Version
#: ``1`` was corrected in place during its own review because it was unmerged:
#: nothing outside that change could have been built against it. That rationale
#: expired at merge and must not be reused. Once a version is **merged**, it is
#: the contract other work builds against, and any meaning-changing addition
#: succeeds it — whether or not a projection has yet been accepted, persisted,
#: or published under it. Acceptance is not the test; reachability is. A schema
#: addition that changes what the union admits therefore always bumps this
#: constant, and the absence of an accepted release never licenses retaining
#: the previous number.
#:
#: Version ``2`` adds the conditions-1 zero-path bundle: six fact families, the
#: component-level applicability qualifier, and the exhaustive actor-choice
#: option set, together with their closed vocabularies.
REPRESENTATION_SCHEMA_VERSION = "5d-representation-schema-2"


class UnsupportedRepresentationShapeError(TypeError):
    """Raised when a declared annotation has no canonical wire shape.

    Fail closed, deliberately. The alternative — rendering an undescribed
    annotation as its Python name or its ``str()`` — is precisely the leak this
    grammar exists to remove, and it would return silently the first time the
    union grew a shape nobody described. A family whose contract cannot be
    stated at the wire is a family whose identity cannot be honestly computed.
    """


#: Closed vocabularies the drafts use directly rather than through a fact
#: field, keyed by the **serialized path** they appear at. They are part of the
#: representation contract — #137 contract 3 names the record and relationship
#: vocabularies as closed — but nothing reaches them by walking fact fields, so
#: they are named here explicitly.
#:
#: Keyed by path rather than by class because the path is what a payload
#: exposes: ``records[].kind`` is where a reader finds these values, and
#: ``RecordKind`` is a name no payload carries. The enum classes appear here
#: only as the source of their admitted values.
#:
#: These paths are written in the module that owns the schema, while the
#: payload emitting them is built in :mod:`projection`. That duplication is
#: real, and it is held honest rather than trusted: a test serializes a
#: representative draft through ``representation_payload`` and resolves every
#: path below against it, so a serializer change that moved one of these keys
#: fails loudly instead of leaving this table describing a path nothing emits.
_DRAFT_VOCABULARIES: Mapping[str, type[StrEnum]] = {
    "components[].handling": ComponentHandling,
    "provenance[].role": ProvenanceRole,
    "provenance[].target_kind": ProvenanceTargetKind,
    "records[].kind": RecordKind,
    "relationships[].kind": RelationshipKind,
}

#: JSON primitive shapes, matched by **exact type identity**. Both hazards this
#: avoids are silent ones: ``bool`` is a subclass of ``int``, and every
#: :class:`StrEnum` is a subclass of ``str``, so a subclass test would render
#: all 33 closed vocabularies as one unconstrained string — collapsing distinct
#: contracts into a single shape with no error raised anywhere. An identity
#: lookup cannot do that.
_PRIMITIVE_SHAPES: Mapping[type, str] = {
    bool: "boolean",
    int: "integer",
    str: "string",
}


def _shape(annotation: object) -> dict[str, object]:
    """Render one declared annotation as its canonical wire shape.

    The grammar is closed: ``integer``, ``string``, ``boolean``,
    ``enum(values)``, ``object(fields)``, ``array(items)``, and a ``nullable``
    flag. Every member describes something a JSON payload can exhibit, which is
    the entire rule — a Python class name describes the implementation, so this
    grammar has nowhere to put one, and an annotation it cannot describe raises
    instead of falling back to a name.
    """
    if annotation == MechanicalFact:
        # The closed typed-fact union, described once under ``facts`` and
        # referenced here. A component and an option both carry a list of
        # them, so the reference must be nameable without repeating 31 family
        # descriptions at every site that holds facts.
        return {"kind": "fact"}

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin in (Union, UnionType):
        # ``X | None`` admits null under the same key. Nothing else in the
        # closed union is a union, and a genuine sum type would need a wire
        # discriminator this grammar does not define — so it is refused rather
        # than flattened into something that reads as settled.
        inner = tuple(a for a in args if a is not type(None))
        if len(inner) != 1 or len(inner) == len(args):
            raise UnsupportedRepresentationShapeError(
                f"{annotation!r} is not an optional of a single shape; the "
                "closed representation admits no other union at the wire"
            )
        return {**_shape(inner[0]), "nullable": True}

    if origin in (tuple, list):
        # ``tuple[X, ...]`` and ``list[X]`` are the same JSON array — the
        # canonical serializer maps both to one — so the container's Python
        # spelling is not part of the contract and must not reach identity.
        items = tuple(a for a in args if a is not Ellipsis)
        if len(items) != 1:
            raise UnsupportedRepresentationShapeError(
                f"{annotation!r} is not a homogeneous sequence of one shape"
            )
        return {"kind": "array", "items": _shape(items[0])}

    if origin is None and isinstance(annotation, type):
        primitive = _PRIMITIVE_SHAPES.get(annotation)
        if primitive is not None:
            return {"kind": primitive}
        if issubclass(annotation, StrEnum):
            # A closed vocabulary *is* its admitted value set at the wire.
            return {"kind": "enum", "values": sorted(m.value for m in annotation)}
        if is_dataclass(annotation):
            # Inlined, not referenced by name: a nested value object serializes
            # as a bare object carrying no type tag, so there is no name to
            # record and no reference that could dangle or alias. Reshaping one
            # is a contract change, and it shows up here directly.
            return {"kind": "object", "fields": _wire_fields(annotation)}

    raise UnsupportedRepresentationShapeError(
        f"{annotation!r} has no canonical wire shape in the closed "
        "representation; describe it in the grammar rather than letting "
        "identity fall back to a Python name"
    )


def _wire_fields(cls: type) -> list[dict[str, object]]:
    """Serialized fields of *cls* — one ``{name, shape}`` entry each, by name.

    **Sorted by field name, not by declaration order.** The contract this
    describes is a named-field set: a payload names its fields, and
    ``fact_from_payload`` matches them by name and rejects on the name set
    rather than on position. Declaration order is Python layout, so letting it
    reach the hash would remint every projection for moving a field up two
    lines — and, since the version must be bumped whenever the hash moves,
    would remint stored authority for an edit that changed no meaning.

    Iterates :func:`dataclasses.fields` rather than the resolved hints:
    ``family`` is a ``ClassVar`` that ``fact_payload`` emits as the
    discriminator, so it is described once per family instead of appearing as a
    field of every one.
    """
    hints = get_type_hints(cls)
    return sorted(
        ({"name": f.name, "shape": _shape(hints[f.name])} for f in fields(cls)),
        key=lambda entry: cast(str, entry["name"]),
    )


def representation_schema_payload() -> dict[str, object]:
    """Canonical, identity-bearing description of the closed representation.

    Describes the **serialized contract**: derived from the declared types, and
    never from the source file's bytes or the names written in it. A comment, a
    docstring, a reordered definition, a renamed class, or a moved module
    leaves this identical; adding a family, adding, removing, renaming, or
    retyping a field, reshaping a nested value object, changing nullability or
    a container shape, or altering an admitted vocabulary value changes it.
    That is the whole point: authority must be reminted when the contract moves
    and left alone when only the implementation does.

    **What is emitted, and what deliberately is not.** Families are keyed by
    their discriminator — the string ``fact_payload`` writes and
    ``fact_from_payload`` dispatches on; fields by their serialized name;
    vocabularies by their sorted admitted values; nested value objects by their
    inlined structure. No class name appears anywhere, because no payload
    carries one, and identity may not depend on what a payload cannot show.

    **Canonicalization.** Every collection here is named or set-like in
    meaning, so each is ordered by its own semantic key: families by
    discriminator, fields by name, vocabulary values by value, draft
    vocabularies by path. Reordering declarations therefore leaves this payload
    — and the hash over it — untouched.

    **Structurally identical shapes render identically, and that is correct.**
    Two vocabularies admitting the same values, or two value objects with the
    same fields, are indistinguishable to anything reading a payload, because
    neither carries a type tag. Context comes from the enclosing family
    discriminator, the field name, or the draft path; there is no global
    uniqueness invariant to enforce, and inventing one would assert a
    distinction the wire does not make.
    """
    return {
        "representation_schema_version": REPRESENTATION_SCHEMA_VERSION,
        "facts": [
            {"family": family.value, "fields": _wire_fields(_FACT_TYPES[family])}
            for family in sorted(FactFamily, key=lambda f: f.value)
        ],
        "components": _wire_fields(ComponentDraft),
        "draft_vocabularies": [
            {"path": path, "shape": _shape(_DRAFT_VOCABULARIES[path])}
            for path in sorted(_DRAFT_VOCABULARIES)
        ],
    }


def representation_schema_hash() -> str:
    """SHA-256 of the closed representation contract."""
    return sha256_hex(canonical_bytes(representation_schema_payload()))


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
class Applicability:
    """One closed condition under which a component or option applies.

    Deliberately **not** a predicate language. ``kind`` selects exactly one
    closed vocabulary, ``negated`` negates the whole predicate and never a
    sub-term, and there are no sub-terms to negate: no operator, no nesting,
    and no way to combine two of these into a third. A condition the source
    states over anything outside these vocabularies is not admitted, and its
    span stays UNRESOLVED rather than being coerced into an approximation.

    *"unless you are Tiny or two or more sizes smaller than it"* is one
    ``SIZE_COMPARISON`` with ``negated=True`` and two entries in ``any_of`` —
    a homogeneous set of size tests, not a Boolean expression.
    """

    kind: ApplicabilityKind
    negated: bool = False
    #: QUANTITY_THRESHOLD
    quantity: TrackedQuantity | None = None
    comparison: Comparison | None = None
    value: int | None = None
    #: SIZE_COMPARISON — satisfied when *any* member matches.
    any_of: tuple[SizeComparison, ...] = ()
    #: TRIGGER — reuses the recovery-cadence vocabulary rather than a second
    #: spelling of "finishing a Long Rest".
    trigger: RecoveryTrigger | None = None
    #: PHASE
    phase: Phase | None = None


@dataclass(frozen=True)
class ComponentOption:
    """One complete typed option of an exhaustive actor choice.

    Holds no options of its own, so the structure is exactly one level deep by
    construction rather than by a check that could be forgotten. Each option is
    mutually exclusive with its siblings per exercise of the choice; selecting
    one does not permanently remove the others.

    ``semantic_key`` is what makes an option's facts addressable — for
    provenance, for override targeting, and for the duplicate check — without
    depending on position, which canonical ordering would make unstable.
    """

    semantic_key: str
    facts: tuple[MechanicalFact, ...] = ()
    applies_when: Applicability | None = None


@dataclass(frozen=True)
class ComponentDraft:
    """One publishable component of a record.

    A component is either a **conjunction** — everything in ``facts`` holds
    together — or an exhaustive **actor choice** — exactly one member of
    ``options`` is taken per exercise. Never both: the two fields are mutually
    exclusive, so nothing can be authored that reads as either.

    ``options`` is exhaustive by definition in this schema version. Prone's
    *"your **only** movement options are"* is the evidence, and no corpus
    instance of a non-exhaustive option set has been found; a future version
    may add one when evidence requires it.
    """

    record_key: str
    semantic_key: str
    handling: ComponentHandling
    #: Required for PROSE_BOUND and MIXED; must name a closed catalog reason.
    irreducibility_reason_code: str | None = None
    facts: tuple[MechanicalFact, ...] = ()
    #: When this component applies at all. ``None`` means unconditionally.
    applies_when: Applicability | None = None
    #: An exhaustive actor choice. Empty, or at least two uniquely keyed
    #: options; never non-empty alongside ``facts``.
    options: tuple[ComponentOption, ...] = ()

    def all_facts(self) -> tuple[MechanicalFact, ...]:
        """Every typed fact this component publishes, direct and per-option.

        For counting, family recognition, and obligation satisfaction, an
        option's facts are authority exactly as direct facts are. This
        deliberately **loses** the option boundary, so it must never be used
        where mutual exclusivity matters — the runtime views build from
        ``facts`` and ``options`` separately for exactly that reason.
        """
        return (*self.facts, *(f for o in self.options for f in o.facts))


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
    record_key: str, component_key: str, fact: object, option_key: str = ""
) -> tuple[str, ...]:
    """Provenance key of one typed fact, keyed by content rather than position.

    ``option_key`` names the owning :class:`ComponentOption`. A fact held
    directly on the component keeps the **three**-element key it has always
    had, so every existing claim, override target, and stored id is unchanged;
    only an option fact carries the fourth element. Without it, the same fact
    appearing in two options of one component would collapse to a single key
    and one option's provenance would silently address the other's.
    """
    base = (record_key, component_key, fact_key(fact))
    return base if not option_key else (*base, option_key)


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


#: Which ``Applicability`` fields each kind populates. A kind carrying a field
#: outside its set is not a weaker claim — it is a claim about a vocabulary it
#: does not range over, and accepting it would let identity depend on fields
#: that mean nothing for that kind.
_APPLICABILITY_FIELDS: Mapping[ApplicabilityKind, frozenset[str]] = {
    ApplicabilityKind.QUANTITY_THRESHOLD: frozenset(
        {"quantity", "comparison", "value"}
    ),
    ApplicabilityKind.SIZE_COMPARISON: frozenset({"any_of"}),
    ApplicabilityKind.TRIGGER: frozenset({"trigger"}),
    ApplicabilityKind.PHASE: frozenset({"phase"}),
}

_APPLICABILITY_ALL_FIELDS = frozenset(
    {"quantity", "comparison", "value", "any_of", "trigger", "phase"}
)


def _is_set(applicability: Applicability, field: str) -> bool:
    value = getattr(applicability, field)
    return bool(value) if field == "any_of" else value is not None


def _exact_optional_int(value: object, where: str) -> str | None:
    """Reject anything that is not exactly a JSON integer or ``None``.

    ``bool`` is an ``int`` subclass, so ``True`` would otherwise satisfy every
    downstream range test as the quantity ``1``; a string would raise an
    incidental ``TypeError`` from the comparison rather than a stated finding.
    Both are malformed authority and both must be refused here, before any
    range comparison reads them.
    """
    if value is None or type(value) is int:
        return None
    return f"{where} is {type(value).__name__} {value!r}, not an integer"


def size_comparison_violations(comparison: SizeComparison) -> list[str]:
    """Violations of one size test's own contract."""
    # Exactly this closed type, before any field is read. A subclass is not a
    # narrower size test: it can carry a meaning-bearing field that
    # ``applicability_payload`` does not emit, so two comparisons asserting
    # different conditions would share one canonical payload and one identity.
    # It can also redefine equality, which would let a duplicate slip past the
    # ``seen`` check in :func:`applicability_violations`.
    if drift := _vo_field(comparison, SizeComparison, "size comparison"):
        return drift
    findings: list[str] = []
    if comparison.category is not None and not isinstance(
        comparison.category, CreatureSize
    ):
        findings.append(f"{comparison.category!r} is not a declared CreatureSize")
    if comparison.relation is not None and not isinstance(
        comparison.relation, SizeRelation
    ):
        findings.append(f"{comparison.relation!r} is not a declared SizeRelation")
    if finding := _exact_optional_int(comparison.at_least, "size distance"):
        findings.append(finding)
    if findings:
        # The type domain first, with its own early return: the relative and
        # absolute checks below read these fields, and reporting a range
        # opinion about a value that is not of the declared type at all would
        # be a second, misleading finding about the same defect.
        return findings
    absolute = comparison.category is not None
    relative = comparison.relation is not None or comparison.at_least is not None
    if absolute and relative:
        findings.append(
            "size comparison states both an absolute category and a relative "
            "distance; they are alternatives"
        )
    elif not absolute and not relative:
        findings.append("size comparison states neither a category nor a distance")
    if relative:
        if comparison.relation is None:
            findings.append("relative size comparison states no direction")
        if comparison.at_least is None:
            findings.append("relative size comparison states no distance")
        elif comparison.at_least < 1:
            findings.append(
                f"relative size distance {comparison.at_least} compares nothing"
            )
    return findings


#: Every direct element type of :class:`RepresentationDraft`, keyed by the field
#: that holds it. An **explicit map guarded by a dataclass-derived change
#: detector**: this literal is maintained by hand, and a test reads
#: ``dataclasses.fields(RepresentationDraft)`` and fails if the two disagree —
#: so a seventh collection added later must appear here or the suite breaks,
#: and a new sibling cannot enter the authority boundary ungated.
#:
#: Stated precisely because an earlier revision of this comment claimed the map
#: was *derived* from the dataclass. It is not; the guarantee comes from the
#: detector, not from derivation.
_DRAFT_ELEMENT_TYPES: Mapping[str, type] = {
    "records": RecordDraft,
    "components": ComponentDraft,
    "prose_bindings": ProseBindingDraft,
    "relationships": RelationshipDraft,
    "references": ReferenceDraft,
    "provenance": ProvenanceClaim,
}


def representation_draft_violations(draft: object) -> list[str]:
    """Exact runtime type of the draft and of every element it holds.

    The closed-structure identity leak, closed at the top-level boundary. A
    subclass of any of these may carry an undeclared meaning-bearing field,
    shadow a declared one, or redefine ``__eq__``/``__hash__``. Validation reads
    them as their base classes and ``representation_payload`` emits only the
    declared base fields, so two drafts asserting *different* authority would
    validate identically, canonicalize to the same bytes, and share one
    projection identity.

    ``isinstance`` is not enough and is deliberately not used: a subclass *is*
    an instance of its base, which is exactly the case being refused. The rule
    is :func:`exact_type_violations`, the same one the fact families,
    applicability structures, and options already use.

    Called **before** any field access, key construction, comprehension, or
    equality/hash-based deduplication downstream — a hostile ``__eq__`` only
    has to be consulted once to collapse two distinct elements into one, and by
    then the finding it should have produced is gone.
    """
    if findings := exact_type_violations(draft, RepresentationDraft, "representation"):
        return findings
    assert isinstance(draft, RepresentationDraft)
    violations: list[str] = []
    for field_name, expected in _DRAFT_ELEMENT_TYPES.items():
        held = getattr(draft, field_name)
        # Exactly ``tuple``, and checked **before** the collection is iterated.
        # ``isinstance`` was the original spelling here and was wrong for the
        # same reason it is wrong everywhere else in this family: a tuple
        # subclass *is* a tuple. It can carry undeclared metadata that
        # ``representation_payload`` never emits — so two drafts asserting
        # different authority canonicalize to identical bytes — and it can
        # override ``__iter__``, so validation and serialization would observe
        # different elements from the same object. Iterating first to find out
        # is exactly the observation being refused.
        if drift := exact_type_violations(held, tuple, f"representation.{field_name}"):
            violations.extend(drift)
            continue
        for index, element in enumerate(held):
            violations.extend(
                exact_type_violations(
                    element, expected, f"representation.{field_name}[{index}]"
                )
            )
    return violations


def option_set_violations(
    facts: tuple[MechanicalFact, ...],
    options: tuple[ComponentOption, ...],
    tag: str,
) -> list[str]:
    """Violations of one component's exhaustive actor-choice contract.

    Stated over ``(facts, options)`` rather than over a whole
    :class:`ComponentDraft` so the *same* rule governs both places a component's
    content can be authored: the build-time representation, and an
    override-supplied complete component patch. A runtime patch layer restating
    these rules would be a looser second copy of the schema, and the two would
    drift.

    Everything rejected here is a shape that would read as something else: a
    conjunction wearing a choice's clothes, a choice with nothing to choose
    between, or two options a consumer could not tell apart.
    """
    findings: list[str] = []
    if not options:
        return findings

    if facts:
        # A component is a conjunction or a choice. Both at once has no single
        # reading: are the direct facts always true, or only alongside the
        # chosen option? The source never states that shape, so it is refused
        # rather than given an invented meaning.
        findings.append(
            f"{tag}: states both direct facts and an actor choice; a component "
            "is a conjunction or a choice, never both"
        )
    if len(options) < 2:
        findings.append(
            f"{tag}: actor choice with {len(options)} option; a choice "
            "of one is a plain component misdescribed"
        )

    seen_keys: set[str] = set()
    seen_facts: set[tuple[str, ...]] = set()
    for option in options:
        otag = f"{tag} option {option.semantic_key}"
        # Exactly this closed type. Same family as the applicability
        # structures: an option subclass could carry a meaning-bearing field
        # that no payload emits, so two options asserting different authority
        # would persist and canonicalize identically — and a redefined
        # ``__eq__`` could evade the duplicate checks immediately below.
        if drift := exact_type_violations(option, ComponentOption, otag):
            findings.extend(drift)
            continue
        if not option.semantic_key.strip():
            findings.append(f"{tag}: option with a blank semantic key")
        elif option.semantic_key in seen_keys:
            # Keys address an option's facts for provenance and for override
            # targeting; two options sharing one would make both unaddressable.
            findings.append(f"{tag}: duplicate option key {option.semantic_key!r}")
        seen_keys.add(option.semantic_key)

        if not option.facts:
            findings.append(f"{otag}: option states no typed facts")
        try:
            signature = tuple(sorted(fact_key(f) for f in option.facts))
        except UnknownFactFamilyError:
            signature = ()
        if signature and signature in seen_facts:
            findings.append(f"{tag}: two options state the same typed facts")
        seen_facts.add(signature)

        if option.applies_when is not None:
            findings.extend(
                f"{otag}: {v}" for v in applicability_violations(option.applies_when)
            )
    return findings


def applicability_violations(applicability: Applicability) -> list[str]:
    """Violations of one applicability's own contract.

    The kind determines the populated field set exactly. This is what keeps the
    shape from drifting into a general predicate: a payload cannot carry a
    threshold *and* a size set and mean their conjunction, because carrying
    both is rejected rather than interpreted.
    """
    # The exact closed type first — before ``kind`` is even read, since a
    # subclass could shadow it. Same reasoning as
    # :func:`size_comparison_violations`: undeclared state that
    # ``applicability_payload`` omits would give distinct authority one
    # canonical representation.
    if drift := _vo_field(applicability, Applicability, "applicability"):
        return drift
    if not isinstance(applicability.kind, ApplicabilityKind):
        return [f"{applicability.kind!r} is not a declared ApplicabilityKind"]
    # The type domain, before ``_is_set`` and before any range comparison.
    # ``_is_set`` reports ``value=True`` as populated and ``True < 0`` is
    # ``False``, so a malformed boolean would otherwise pass every later check
    # silently; ``value="3"`` would raise an incidental ``TypeError`` instead
    # of a stated finding. Neither is an acceptable answer for malformed
    # authority, and both loaders inherit this guard through their existing
    # post-construction call.
    typed: list[str] = []
    if type(applicability.negated) is not bool:
        typed.append(
            f"negated is {type(applicability.negated).__name__} "
            f"{applicability.negated!r}, not a boolean"
        )
    if finding := _exact_optional_int(applicability.value, "threshold value"):
        typed.append(finding)
    for name, member in (
        ("quantity", TrackedQuantity),
        ("comparison", Comparison),
        ("trigger", RecoveryTrigger),
        ("phase", Phase),
    ):
        held = getattr(applicability, name)
        if held is not None and not isinstance(held, member):
            typed.append(f"{held!r} is not a declared {member.__name__}")
    if not isinstance(applicability.any_of, tuple) or any(
        type(c) is not SizeComparison for c in applicability.any_of
    ):
        typed.append("any_of is not a tuple of size comparisons")
    if typed:
        return typed
    allowed = _APPLICABILITY_FIELDS[applicability.kind]
    findings: list[str] = []
    for field in sorted(_APPLICABILITY_ALL_FIELDS - allowed):
        if _is_set(applicability, field):
            findings.append(
                f"{applicability.kind.value} applicability carries {field}, "
                "which it does not range over"
            )
    for field in sorted(allowed):
        if not _is_set(applicability, field):
            findings.append(
                f"{applicability.kind.value} applicability states no {field}"
            )
    if findings:
        return findings
    if applicability.kind is ApplicabilityKind.QUANTITY_THRESHOLD:
        if applicability.value is not None and applicability.value < 0:
            findings.append(f"threshold value {applicability.value} is not a quantity")
    elif applicability.kind is ApplicabilityKind.SIZE_COMPARISON:
        seen: set[SizeComparison] = set()
        for comparison in applicability.any_of:
            findings.extend(size_comparison_violations(comparison))
            if comparison in seen:
                findings.append("duplicate size comparison in one applicability")
            seen.add(comparison)
    return findings


def declared_provenance_targets(
    draft: RepresentationDraft,
) -> dict[ProvenanceTargetKind, set[tuple[str, ...]]]:
    """Every element a provenance claim may legitimately name.

    Facts whose family is unknown are omitted: they have no content-derived key,
    and they are reported separately as facts outside the closed union.
    """
    facts: set[tuple[str, ...]] = set()
    for component in draft.components:
        # Direct facts and option facts alike: an option's fact is authority
        # that must carry its own provenance, and omitting it here would make
        # every such claim read as naming an undeclared element.
        scopes: list[tuple[str, tuple[MechanicalFact, ...]]] = [("", component.facts)]
        scopes.extend((o.semantic_key, o.facts) for o in component.options)
        for option_key, scoped in scopes:
            for fact in scoped:
                try:
                    facts.add(
                        fact_target_key(
                            component.record_key,
                            component.semantic_key,
                            fact,
                            option_key,
                        )
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
