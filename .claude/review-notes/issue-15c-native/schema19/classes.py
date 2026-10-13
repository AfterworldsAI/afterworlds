# ---------------------------------------------------------------------------
# Schema 19 value objects -- CRD Issue 15c
# ---------------------------------------------------------------------------
#
# Each is a closed, typed object: every field is declared, nothing is a free
# mapping, and a payload's key set must equal the field set exactly. A field
# typed with an accepted fact class (``ConditionEffectFact``,
# ``AdvantageFact``, ``SpeedModificationFact``) nests that accepted shape and
# is built by its accepted builder, so a nested condition or roll modifier is
# never a second spelling of an accepted family.


@dataclass(frozen=True, kw_only=True)
class TurnBoundary:
    """*"until the start of the <creature>'s next turn"*: an edge of a named
    participant's turn."""

    until: RecurrenceBoundary
    turn: TurnWhich
    turn_of: TurnOwner


@dataclass(frozen=True, kw_only=True)
class ElapsedSpan:
    """*"for 1 hour"*, *"for 24 hours or until the <creature> dies"*."""

    amount: int
    unit: TimeUnit
    or_until: SpanEnd | None


@dataclass(frozen=True, kw_only=True)
class EndingEvent:
    """An event that ends an effect early; a waking action names how near the
    creature taking it must be."""

    event: EndingEventKind
    by_creature_within_ft: int | None


@dataclass(frozen=True, kw_only=True)
class FormulaRef:
    """A value printed as a formula another component states, computed for a
    named participant: *"Bonus equals your spell attack modifier"*.
    ``formula_ref`` addresses that component as ``record_key/component_key``."""

    formula_ref: str
    of: FormulaSubject


@dataclass(frozen=True, kw_only=True)
class FormulaAddend:
    """A runtime value a parameterized damage term adds."""

    input: FormulaInput


@dataclass(frozen=True, kw_only=True)
class DamageTypeChoice:
    """A damage type the source leaves to a choice, keyed by a form
    (celestial/fey/fiend) or stated as a choice rule."""

    chosen_for: ChoiceAnchor | None
    chosen_by: Chooser | None
    chosen_from: ChoiceSource | None
    when: ChoiceTime | None
    celestial: DamageType | None
    fey: DamageType | None
    fiend: DamageType | None


@dataclass(frozen=True, kw_only=True)
class DamageTerm:
    """One printed damage term: an average and dice, or a formula's dice,
    constant and runtime addends, of a stated or chosen type."""

    average: int | None
    dice: DiceExpression | None
    constant: int | None
    addends: tuple[FormulaAddend, ...]
    damage_type: DamageType | None
    damage_type_by_choice: DamageTypeChoice | None


@dataclass(frozen=True, kw_only=True)
class SizedDamage:
    """Hit damage printed per size: *"(Medium or smaller) ... (Large) ...
    (Huge)"*."""

    medium_or_smaller: tuple[DamageTerm, ...]
    large: tuple[DamageTerm, ...]
    huge: tuple[DamageTerm, ...]


@dataclass(frozen=True, kw_only=True)
class DamageWhen:
    """The predicate a conditional damage term is stated under."""

    source_bloodied: bool | None
    target_bloodied: bool | None
    attack_roll_had_advantage: bool | None
    target_grappled_by_source: bool | None
    source_moved_straight_toward_target_ft_min: int | None
    target_maximum_size: CreatureSize | None


@dataclass(frozen=True, kw_only=True)
class ConditionalDamage:
    """Damage added to, or replacing ``hit_damage[replaces_hit_damage_index]``
    of, a hit when ``when`` holds."""

    mode: DamageMode
    term: DamageTerm
    when: DamageWhen
    replaces_hit_damage_index: int | None


@dataclass(frozen=True, kw_only=True)
class ForcedMove:
    """A push or pull: exactly ``distance_ft``, or up to
    ``distance_ft_up_to``."""

    direction: ForcedDirection
    distance_ft: int | None
    distance_ft_up_to: int | None


@dataclass(frozen=True, kw_only=True)
class LinkedCondition:
    """A condition lasting while another effect lasts: *"and it has the
    Restrained condition until the grapple ends"*."""

    condition: ConditionEffectFact
    until: LinkEnd


@dataclass(frozen=True, kw_only=True)
class RiderSave:
    """A save a hit forces, with its failure condition and exclusions."""

    save: AbilityScore
    dc: int
    on_failure: ConditionEffectFact
    duration: TurnBoundary | None
    target_excludes: tuple[TargetTag, ...]


@dataclass(frozen=True, kw_only=True)
class Rider:
    """What a hit or a failed save applies besides damage."""

    applies_to: RiderSubject | None
    condition: ConditionEffectFact | None
    speed: SpeedModificationFact | None
    duration: TurnBoundary | None
    escape_dc: int | None
    maximum_size: CreatureSize | None
    conditional_damage: ConditionalDamage | None
    forced_movement: ForcedMove | None
    linked: LinkedCondition | None
    rider_save: RiderSave | None


@dataclass(frozen=True, kw_only=True)
class SaveArea:
    """An area of effect a save is made in."""

    shape: AreaShape
    size_ft: int
    radius: bool
    width_ft: int | None
    height_ft: int | None


@dataclass(frozen=True, kw_only=True)
class TurnTrigger:
    """*"that starts its turn ..."*."""

    turn_of: TurnOwner
    when: RecurrenceBoundary


@dataclass(frozen=True, kw_only=True)
class SaveTargets:
    """Who must make a save: the printed participant predicates."""

    count: int | None
    each: bool | None
    living: bool | None
    maximum_size: CreatureSize | None
    types: tuple[TargetTag, ...]
    has_conditions: tuple[ConditionKind, ...]
    area: SaveArea | None
    origin: AreaOriginAnchor | None
    origin_point_within_ft: int | None
    within_ft: int | None
    in_source_space: bool | None
    related_to_source: tuple[ConditionKind, ...]
    requires_source_sees_target: bool | None
    requires_source_sees_point: bool | None
    requires_target_sees_source: bool | None
    source_environment: SourceEnvironment | None
    swallow_capacity: int | None
    trigger: TurnTrigger | None
    excludes: TargetExclusion | None
    excludes_types: tuple[TargetTag, ...]
    automatic_failure_types: tuple[TargetTag, ...]
    automatic_success_types: tuple[TargetTag, ...]
    willing_or_conditions: tuple[ConditionKind, ...]
    at_hit_points: int | None
    stated_by: TargetsStatedBy | None


@dataclass(frozen=True, kw_only=True)
class EntryOption:
    """A sibling entry a Multiattack names, optionally used to cast one spell
    (``spell`` a ``spells.*`` record key) at a printed level."""

    entry: str
    spell: str | None
    spell_level: int | None


@dataclass(frozen=True, kw_only=True)
class MultiattackPart:
    """One printed part of a Multiattack alternative."""

    count: int | None
    count_formula: CountFormula | None
    attack: str | None
    any_of: tuple[str, ...]
    uses_one_of: tuple[EntryOption, ...]
    optional: bool | None
    if_available: bool | None


@dataclass(frozen=True, kw_only=True)
class MultiattackAlternative:
    """One selectable composition."""

    condition: MultiattackCondition | None
    parts: tuple[MultiattackPart, ...]


@dataclass(frozen=True, kw_only=True)
class MultiattackReplacement:
    """*"It can replace one/any attack with ..."*."""

    replaces: int | None
    replaces_attack: str | None
    replaces_any: bool | None
    with_one_of: tuple[EntryOption, ...]
    if_available: bool | None


@dataclass(frozen=True, kw_only=True)
class CheckSpec:
    """A fixed-DC ability check with its skill."""

    ability: AbilityScore
    skill: Skill
    dc: int


@dataclass(frozen=True, kw_only=True)
class ObserverCondition:
    """*"if the creature hasn't witnessed the cube move or otherwise act"*."""

    checker_has_not_witnessed_subject_move_or_act: bool


@dataclass(frozen=True, kw_only=True)
class ContributorPredicate:
    """When a standing trait's effects apply."""

    stated: ContributorStated | None
    subject_not: ConditionKind | None
    subject_bloodied: bool | None
    ally_not: ConditionKind | None
    ally_within_ft_of_target: int | None
    target_missing_hit_points: bool | None
    attack: RangeClass | None


@dataclass(frozen=True, kw_only=True)
class SaveOverride:
    """Legendary Resistance: on a failed save, choose to succeed instead."""

    chooser: SaveOverrideChooser
    may_choose: SaveOverrideOutcome
    on: SaveOverrideTrigger
    usage: SaveOverrideUsage


@dataclass(frozen=True, kw_only=True)
class SaveDamageOverride:
    """Evasion: the damage a save takes on success and on failure."""

    save: AbilityScore
    on: SaveDamageScope
    success: SaveDamageResult
    failure: SaveDamageResult


@dataclass(frozen=True, kw_only=True)
class IcyTerrain:
    """Ice Walk: ice and snow aren't Difficult Terrain for the subject."""

    difficult_terrain_of: tuple[TerrainKind, ...]
    extra_movement: bool


@dataclass(frozen=True, kw_only=True)
class SpeedPredicate:
    """*"If the swarm has a Climb Speed"*."""

    subject_has_speed: MovementMode


@dataclass(frozen=True, kw_only=True)
class DamagePlusDc:
    """*"DC 5 plus the damage taken"*."""

    base: int
    plus: DcAddend


@dataclass(frozen=True, kw_only=True)
class ZeroHitPointUnless:
    """*"unless the damage is Radiant or from a Critical Hit"*."""

    damage_type: DamageType
    critical_hit: bool


@dataclass(frozen=True, kw_only=True)
class ZeroHitPointOnSuccess:
    """*"the zombie drops to 1 Hit Point instead"* -- instead of 0."""

    set_hit_points: int
    instead_of_zero_hit_points: bool


@dataclass(frozen=True, kw_only=True)
class RelationQualification:
    """*"its vampire master"*: a relation and the qualification the related
    creature must have. Validating either is runtime state."""

    relation: RelationKind
    qualification: RelationQualifier


@dataclass(frozen=True, kw_only=True)
class DamageTypeSelection:
    """*"the one damage type chosen for Draconic Origin"*."""

    vocabulary: tuple[DamageType, ...]
    chosen_by: Chooser
    chosen_for: ChoiceAnchor


@dataclass(frozen=True, kw_only=True)
class LeveledArmorClass:
    """*"AC 10 + 1 per spell level"*."""

    base: int
    per_spell_level: int


@dataclass(frozen=True, kw_only=True)
class PerLevelAbove:
    """*"10 for each spell level above 4"*."""

    amount: int
    level: int


@dataclass(frozen=True, kw_only=True)
class SizeKeyedHitPoints:
    """*"HP 10 (Medium or smaller), 20 (Large), 40 (Huge)"*."""

    medium_or_smaller: int
    large: int
    huge: int


@dataclass(frozen=True, kw_only=True)
class ParameterizedHitPoints:
    """A summon's printed Hit Points formula."""

    base: int | None
    per_spell_level: int | None
    per_spell_level_above: PerLevelAbove | None
    by_size: SizeKeyedHitPoints | None
    half_of: ParameterizedHitPointsBasis | None


@dataclass(frozen=True, kw_only=True)
class ProgressionReference:
    """The accepted ``progression_entry`` facts that give a grant's levels."""

    entitlement_key: str


@dataclass(frozen=True, kw_only=True)
class ComponentReference:
    """An accepted component, by record and component key."""

    record_key: str
    component_key: str


@dataclass(frozen=True, kw_only=True)
class ToolSelector:
    """A tool choice's option set: one tool's variants, one category, or any
    tool."""

    tool_variants_of: ComponentReference | None
    tool_category: ToolCategory | None
    any_tool_entry: bool | None


@dataclass(frozen=True, kw_only=True)
class ToolChoice:
    """*"proficiency with one Musical Instrument of your choice"*."""

    count: int
    options: tuple[ToolSelector, ...]


@dataclass(frozen=True, kw_only=True)
class SubclassEligibility:
    """The subclass and class level a subclass feature's grant requires."""

    class_key: str
    subclass_key: str
    minimum_class_level: int


@dataclass(frozen=True, kw_only=True)
class QualifiedWeaponCategory:
    """*"Martial weapons that have the Finesse or Light property"*."""

    category: WeaponCategory
    with_any_property: tuple[WeaponProperty, ...]


@dataclass(frozen=True, kw_only=True)
class WeaponCategories:
    """Weapon proficiency by category."""

    categories: tuple[WeaponCategory, ...]


@dataclass(frozen=True, kw_only=True)
class ArmorTraining:
    """Armor training by category, and Shields."""

    armor: tuple[ArmorCategory, ...]
    shields: bool


@dataclass(frozen=True, kw_only=True)
class AbilityMinimum:
    """*"Strength or Dexterity 13+"*."""

    any_of: tuple[AbilityScore, ...]
    score: int


@dataclass(frozen=True, kw_only=True)
class LevelCount:
    """One row of a Features-table count column."""

    level: int
    count: int


@dataclass(frozen=True, kw_only=True)
class RestSwap:
    """*"Whenever you finish a Long Rest, you can change ..."*."""

    after: RestKind
    change: SwapScope


@dataclass(frozen=True, kw_only=True)
class DeathSaveTiming:
    """*"Whenever you start your turn with 0 Hit Points"*."""

    at_hit_points: int
    turn_of: TurnOwner
    when: RecurrenceBoundary


@dataclass(frozen=True, kw_only=True)
class StableRecovery:
    """*"A Stable creature that isn't healed regains 1 Hit Point after 1d4
    hours"*."""

    dice: DiceExpression
    regain_hit_points: int
    unit: TimeUnit
    unless: RecoveryUnless


@dataclass(frozen=True, kw_only=True)
class FreeHandRule:
    """*"you need a free hand to load a one-handed weapon"*."""

    when: FreeHandWhen


@dataclass(frozen=True, kw_only=True)
class AmmunitionRecovery:
    """*"recover half the ammunition (round down) ... after a fight by taking
    a minute"*."""

    after: RecoveryAfter
    minutes: int
    fraction: Rational
    rounding: RoundingRule
    remainder: RecoveryRemainder


@dataclass(frozen=True, kw_only=True)
class MasteryDc:
    """Topple's *"DC 8 plus the ability modifier ... and your Proficiency
    Bonus"*."""

    base: int
    plus: tuple[FormulaTerm, ...]


@dataclass(frozen=True, kw_only=True)
class NextRoll:
    """Whose next attack roll, and against whom."""

    actor: NextRollActor
    context: RollContext
    against: NextRollActor | None


@dataclass(frozen=True, kw_only=True)
class RepeatOnce:
    """*"until the end of its next turn, at which point it repeats the save"*."""

    at: RepeatSaveAt
    turn_of: TurnOwner
    once: bool


@dataclass(frozen=True, kw_only=True)
class RepeatCondition:
    """*"if it is still Restrained"*."""

    has_condition: ConditionKind


@dataclass(frozen=True, kw_only=True)
class ReflectionPredicate:
    """*"If the basilisk sees its reflection in the Cone"*."""

    source_sees_own_reflection_in: AreaShape


@dataclass(frozen=True, kw_only=True)
class AbilityBasedD20Tests:
    """*"Disadvantage on Strength-based D20 Tests"*: every D20 Test made with
    one ability. The accepted roll shape names an ability only for an ability
    check or a saving throw, so the D20 Test umbrella keyed by an ability is
    its own closed value rather than a loosened accepted rule."""

    state: AdvantageState
    ability: AbilityScore


@dataclass(frozen=True, kw_only=True)
class GrappleAppendages:
    """*"from one of two claws"*, *"from both talons"*, *"from all four
    tentacles"*; ``of`` is the printed number, when printed."""

    use: AppendageUse
    of: int | None
    appendage: Appendage


# ---------------------------------------------------------------------------
# Schema 19 families -- creature entries (C5-B)
# ---------------------------------------------------------------------------
#
# Each fact names the stat-block entry it states by its printed name (any
# usage parenthetical removed) and section, which is unique within its
# component; the entry's complete text stays governed prose on the component.


@dataclass(frozen=True, kw_only=True)
class CreatureAttackFact:
    """One printed creature attack: *"Melee Attack Roll: +4, reach 5 ft.
    Hit: 6 (1d8 + 2) Piercing damage ..."*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_ATTACK

    entry: str
    section: EntrySection
    kind: CreatureAttackRange
    attack_bonus: int | None
    attack_bonus_formula: FormulaRef | None
    automatic_hit: bool | None
    reach_ft: int | None
    normal_range_ft: int | None
    long_range_ft: int | None
    advantage_when: AttackAdvantageWhen | None
    hit_damage: tuple[DamageTerm, ...]
    hit_damage_by_size: SizedDamage | None
    size_input: SizeInput | None
    hit_effect: Rider | None


@dataclass(frozen=True, kw_only=True)
class CreatureSaveEffectFact:
    """One printed creature save effect: *"Dexterity Saving Throw: DC 13,
    each creature in a 15-foot Cone. Failure: ... Success: Half damage."*"""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_SAVE_EFFECT

    entry: str
    section: EntrySection
    save: AbilityScore
    dc: int | None
    dc_formula: FormulaRef | None
    targets: SaveTargets
    failure_damage: tuple[DamageTerm, ...]
    failure_effect: Rider | None
    success: SaveSuccess | None
    reuse_limit: ReuseLimitKind | None


@dataclass(frozen=True, kw_only=True)
class CreatureMultiattackFact:
    """A creature's Multiattack: its selectable alternatives and
    replacements."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_MULTIATTACK

    entry: str
    section: EntrySection
    alternatives: tuple[MultiattackAlternative, ...]
    replacements: tuple[MultiattackReplacement, ...]


@dataclass(frozen=True, kw_only=True)
class CreatureEntryUsageFact:
    """An entry's printed usage: Recharge, X/Day, Legendary Action Uses, a
    form restriction or a required entry."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_ENTRY_USAGE

    entry: str
    section: EntrySection
    kind: UsageKind
    uses: int | None
    in_lair: int | None
    minimum_d6: int | None
    forms: tuple[CreatureForm, ...]
    recharge_after_long_rest: bool | None
    requires_entry: str | None


@dataclass(frozen=True, kw_only=True)
class CreatureEntryReferenceFact:
    """An entry that uses another entry of the same stat block by name."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_ENTRY_REFERENCE

    entry: str
    section: EntrySection
    references: str


@dataclass(frozen=True, kw_only=True)
class CreatureObserverCheckFact:
    """A check another creature makes about this one (Mimicry, Transparent)."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_OBSERVER_CHECK

    entry: str
    section: EntrySection
    check: CheckSpec
    made_by: ObserverKind
    purpose: ObserverPurpose
    only_if: ObserverCondition | None


@dataclass(frozen=True, kw_only=True)
class CreatureConditionGrantFact:
    """A trait that gives its subject standing conditions."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_CONDITION_GRANT

    entry: str
    section: EntrySection
    subject: EntrySubject
    conditions: tuple[ConditionKind, ...]


@dataclass(frozen=True, kw_only=True)
class CreatureSaveOverrideFact:
    """Legendary Resistance."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_SAVE_OVERRIDE

    entry: str
    section: EntrySection
    subject: EntrySubject
    save_override: SaveOverride


@dataclass(frozen=True, kw_only=True)
class CreatureSaveDamageOverrideFact:
    """Evasion."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_SAVE_DAMAGE_OVERRIDE

    entry: str
    section: EntrySection
    subject: EntrySubject
    applies_when: ContributorPredicate | None
    save_damage_override: SaveDamageOverride


@dataclass(frozen=True, kw_only=True)
class CreatureRollModifierFact:
    """A standing trait's Advantage or Disadvantage, with its predicate and,
    for a check about the subject, the skill and purpose it is limited to."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_ROLL_MODIFIER

    entry: str
    section: EntrySection
    subject: EntrySubject
    applies_when: ContributorPredicate | None
    effects: tuple[AdvantageFact, ...]
    skill: Skill | None
    purpose: ContributorPurpose | None


@dataclass(frozen=True, kw_only=True)
class CreatureHitPointRegainProhibitionFact:
    """Swarm: *"can't regain Hit Points or gain Temporary Hit Points"* --
    unconditional in the source."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_HIT_POINT_REGAIN_PROHIBITION

    entry: str
    section: EntrySection
    subject: EntrySubject
    hit_points: bool
    temporary_hit_points: bool | None


@dataclass(frozen=True, kw_only=True)
class CheckRequirementRemovalFact:
    """Spider Climb / Ice Walk: no ability check to climb the named surfaces
    (``check`` addresses the requirement's component)."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CHECK_REQUIREMENT_REMOVAL

    entry: str
    section: EntrySection
    subject: EntrySubject
    check: str
    surfaces: SurfaceKind
    also: IcyTerrain | None
    applies_when: SpeedPredicate | None


@dataclass(frozen=True, kw_only=True)
class ZeroHitPointSaveFact:
    """Undead Fortitude: a damage-triggered save that substitutes 1 Hit
    Point."""

    FAMILY: ClassVar[FactFamily] = FactFamily.ZERO_HIT_POINT_SAVE

    entry: str
    section: EntrySection
    subject: EntrySubject
    trigger: ZeroHitPointTrigger
    save: AbilityScore
    dc: DamagePlusDc
    unless: ZeroHitPointUnless
    on_success: ZeroHitPointOnSuccess


@dataclass(frozen=True, kw_only=True)
class CreatureSizeFact:
    """The sizes a stat block's size line prints (*"Medium or Small"*)."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_SIZE

    sizes: tuple[CreatureSize, ...]


@dataclass(frozen=True, kw_only=True)
class CreatureConditionalDefenseFact:
    """A qualified entry in a defensive list: *"Charmed (except from its
    vampire master)"*, *"Piercing from a weapon wielded by a creature under
    Bless"*, *"the damage type chosen for Draconic Origin"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_CONDITIONAL_DEFENSE

    kind: ConditionalDefenseKind
    condition: ConditionKind | None
    damage_type: DamageType | None
    while_active_effect: str | None
    unless_source_is: RelationQualification | None
    attack: DefenseAttack | None
    attacker_active_effect: str | None
    selection: DamageTypeSelection | None


@dataclass(frozen=True, kw_only=True)
class CreatureDefenseParameterizedFact:
    """A summon's AC and Hit Points, fixed or by printed formula."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_DEFENSE_PARAMETERIZED

    armor_class: int | None
    armor_class_formula: LeveledArmorClass | None
    hit_points: ParameterizedHitPoints


# Clause pieces -------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class _ClauseLocus:
    """Where a clause piece sits, and its explicit source-local links.

    ``piece`` is the piece's index in its clause; ``under_predicates`` are the
    indices of the leading predicates that scope it. ``effect_id`` names an
    effect this piece creates (``E1``...), entry-local; ``bound_effect``,
    ``lasts_while_effect``, ``ends_effects`` and ``duration_of_effects`` name
    such effects of the same entry. None is a runtime identifier.
    """

    entry: str
    section: EntrySection
    part: ClausePart
    piece: int
    branch: ClauseBranch
    effect_id: str | None
    bound_effect: str | None
    lasts_while_effect: str | None
    ends_effects: tuple[str, ...]
    duration_of_effects: tuple[str, ...]
    under_predicates: tuple[int, ...]


@dataclass(frozen=True, kw_only=True)
class ClauseBranchFact(_ClauseLocus):
    """A printed branch label (*"_Second Failure:_"*)."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_BRANCH


@dataclass(frozen=True, kw_only=True)
class ClausePredicateFact(_ClauseLocus):
    """A leading predicate scoping the rest of its sentence."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_PREDICATE

    target_maximum_size: CreatureSize | None
    source_moved_straight_toward_target_ft_min: int | None
    attack_roll_had_advantage: bool | None
    target_is_creature: bool | None
    target_type: TargetTag | None
    target_reduced_to_0_hit_points_by_this: bool | None
    target_hit_points_at_most: int | None
    otherwise: bool | None
    while_condition: ConditionKind | None
    while_state: PredicateWhile | None
    refers_to: PredicateRefersTo | None
    duration: TurnBoundary | None
    at: RepeatSaveAt | None


@dataclass(frozen=True, kw_only=True)
class ClauseGrappleFact(_ClauseLocus):
    """*"it has the Grappled condition (escape DC 14) from one of two
    claws"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_GRAPPLE

    condition: ConditionKind
    escape_dc: int
    appendages: GrappleAppendages | None
    instead_of_damage: bool | None


@dataclass(frozen=True, kw_only=True)
class ClauseConditionFact(_ClauseLocus):
    """Conditions a piece applies, without a duration of its own."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_CONDITION

    effects: tuple[ConditionEffectFact, ...]
    replaces_condition: ConditionKind | None


@dataclass(frozen=True, kw_only=True)
class ClauseTimedConditionFact(_ClauseLocus):
    """Conditions with a turn-edge or elapsed duration and ending events."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_TIMED_CONDITION

    effects: tuple[ConditionEffectFact, ...]
    duration_turn: TurnBoundary | None
    duration_span: ElapsedSpan | None
    ends_early_when: tuple[EndingEvent, ...]
    replaces_condition: ConditionKind | None


@dataclass(frozen=True, kw_only=True)
class ClauseLinkedConditionFact(_ClauseLocus):
    """Conditions lasting while a named effect lasts."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_LINKED_CONDITION

    effects: tuple[ConditionEffectFact, ...]
    while_state: PredicateWhile


@dataclass(frozen=True, kw_only=True)
class ClauseConditionUntilRepeatFact(_ClauseLocus):
    """*"until the end of its next turn, at which point it repeats the
    save"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_CONDITION_UNTIL_REPEAT

    effects: tuple[ConditionEffectFact, ...]
    duration: TurnBoundary
    repeat_save: RepeatOnce


@dataclass(frozen=True, kw_only=True)
class ClauseConditionEndsFact(_ClauseLocus):
    """*"The Poisoned condition ends."*"""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_CONDITION_ENDS

    condition: ConditionKind


@dataclass(frozen=True, kw_only=True)
class ClauseConditionEndsEarlyFact(_ClauseLocus):
    """*"which ends early if the target takes any damage"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_CONDITION_ENDS_EARLY

    ends_early_when: tuple[EndingEvent, ...]


@dataclass(frozen=True, kw_only=True)
class ClauseEffectEndsFact(_ClauseLocus):
    """*"This effect ends for the target if ..."*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_EFFECT_ENDS

    ends_early_when: tuple[EndingEvent, ...]


@dataclass(frozen=True, kw_only=True)
class ClauseEffectLastsFact(_ClauseLocus):
    """*"This effect lasts until the end of its next turn."*"""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_EFFECT_LASTS

    duration: TurnBoundary
    scope: EffectLastsScope


@dataclass(frozen=True, kw_only=True)
class ClauseRepeatSaveFact(_ClauseLocus):
    """A repeated save and what its success ends."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_REPEAT_SAVE

    at: RepeatSaveAt | None
    turn_of: TurnOwner | None
    ends_on: SaveEndsOn | None
    only_if: RepeatCondition | None


@dataclass(frozen=True, kw_only=True)
class ClauseRepeatSaveLimitFact(_ClauseLocus):
    """*"After 1 minute, it succeeds automatically."*"""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_REPEAT_SAVE_LIMIT

    automatic_success_after_minutes: int


@dataclass(frozen=True, kw_only=True)
class ClauseTemporaryImmunityFact(_ClauseLocus):
    """*"The target is immune to this <creature>'s <entry> for 24 hours."*"""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_TEMPORARY_IMMUNITY

    to: ImmunityScope
    immune_to_entry: str
    hours: int


@dataclass(frozen=True, kw_only=True)
class ClauseNestedSaveFact(_ClauseLocus):
    """*"_Constitution Saving Throw:_ DC 12."* inside a rider."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_NESTED_SAVE

    ability: AbilityScore
    dc: int


@dataclass(frozen=True, kw_only=True)
class ClauseNestedSaveTriggerFact(_ClauseLocus):
    """*"it is subjected to the following effect"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_NESTED_SAVE_TRIGGER


@dataclass(frozen=True, kw_only=True)
class ClauseTimedSpeedChangeFact(_ClauseLocus):
    """*"its Speed decreases by 10 feet until the end of its next turn"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_TIMED_SPEED_CHANGE

    change: TimedSpeedChange
    feet: int | None
    duration: TurnBoundary | None


@dataclass(frozen=True, kw_only=True)
class ClauseTimedAcModifierFact(_ClauseLocus):
    """*"takes a -2 penalty to AC until the end of its next turn"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_TIMED_AC_MODIFIER

    modifier: int
    duration: TurnBoundary


@dataclass(frozen=True, kw_only=True)
class ClauseNextRollModifierFact(_ClauseLocus):
    """Advantage or Disadvantage on one next attack roll, until it expires."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_NEXT_ROLL_MODIFIER

    roll: NextRoll
    state: AdvantageState
    uses: int
    expires: TurnBoundary


@dataclass(frozen=True, kw_only=True)
class ClauseD20TestPenaltyDieFact(_ClauseLocus):
    """*"rolls 1d6 whenever it makes an ability check or attack roll"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_D20_TEST_PENALTY_DIE

    contexts: tuple[RollContext, ...]
    count: int
    die: DieSize


@dataclass(frozen=True, kw_only=True)
class ClausePenaltyDieApplicationFact(_ClauseLocus):
    """*"and subtracts the number rolled from the D20 Test"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_PENALTY_DIE_APPLICATION

    subtracts_from: PenaltyTarget


@dataclass(frozen=True, kw_only=True)
class ClauseRollModifierFact(_ClauseLocus):
    """Advantage or Disadvantage a clause imposes on its subject's rolls
    (``ability_disadvantage``, ``roll_disadvantage`` and
    ``escape_disadvantage`` pieces)."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_ROLL_MODIFIER

    subject: RiderSubject
    effects: tuple[AdvantageFact, ...]
    ability_based: AbilityBasedD20Tests | None
    purpose: EscapePurpose | None


@dataclass(frozen=True, kw_only=True)
class ClauseDamageRollPenaltyFact(_ClauseLocus):
    """*"subtracts 3 (1d6) from its damage rolls"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_DAMAGE_ROLL_PENALTY

    average: int
    dice: DiceExpression


@dataclass(frozen=True, kw_only=True)
class ClauseDamageBranchFact(_ClauseLocus):
    """Damage a branch deals (*"Otherwise, the target takes ..."*)."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_DAMAGE_BRANCH

    terms: tuple[DamageTerm, ...]


@dataclass(frozen=True, kw_only=True)
class ClauseChoiceTypedDamageFact(_ClauseLocus):
    """Damage of a chosen type."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_CHOICE_TYPED_DAMAGE

    average: int | None
    dice: DiceExpression
    damage_type: DamageTypeChoice


@dataclass(frozen=True, kw_only=True)
class ClauseConditionalDamageFact(_ClauseLocus):
    """Replacement damage under a predicate, beside unconditional terms that
    joined the attack's ``hit_damage``."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_CONDITIONAL_DAMAGE

    mode: DamageMode
    term: DamageTerm
    when: DamageWhen
    replaces_hit_damage_index: int | None
    unconditional_hit_damage_indices: tuple[int, ...]


@dataclass(frozen=True, kw_only=True)
class ClausePeriodicDamageFact(_ClauseLocus):
    """*"takes 7 (2d6) Thunder damage at the start of each of the stalker's
    turns"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_PERIODIC_DAMAGE

    at: RecurrenceBoundary
    term: DamageTerm
    turn_of: TurnOwner


@dataclass(frozen=True, kw_only=True)
class ClausePeriodicHitPointLossFact(_ClauseLocus):
    """*"loses 5 (1d10) Hit Points at the start of each of its turns"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_PERIODIC_HIT_POINT_LOSS

    at: RecurrenceBoundary
    average: int
    dice: DiceExpression
    turn_of: TurnOwner


@dataclass(frozen=True, kw_only=True)
class ClauseHitPointRegainProhibitionFact(_ClauseLocus):
    """*"the target can't regain Hit Points"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_HIT_POINT_REGAIN_PROHIBITION

    hit_points: bool


@dataclass(frozen=True, kw_only=True)
class ClauseHitPointsSetFact(_ClauseLocus):
    """*"it drops to 0 Hit Points"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_HIT_POINTS_SET

    to: int


@dataclass(frozen=True, kw_only=True)
class ClauseZeroHitPointOutcomeFact(_ClauseLocus):
    """*"the target becomes Stable"*, *"dies if reduced to 0 Hit Points by
    this attack"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_ZERO_HIT_POINT_OUTCOME

    becomes: ClauseZeroHitPointResult
    when: ClauseZeroHitPointCause | None


@dataclass(frozen=True, kw_only=True)
class ClauseNamedEffectFact(_ClauseLocus):
    """*"the target is cursed for 1 hour"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_NAMED_EFFECT

    name: NamedEffect
    duration: ElapsedSpan | None


@dataclass(frozen=True, kw_only=True)
class ClauseForcedMovementFact(_ClauseLocus):
    """A push or pull a clause states."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_FORCED_MOVEMENT

    direction: ForcedDirection
    distance_ft: int | None
    distance_ft_up_to: int | None


@dataclass(frozen=True, kw_only=True)
class ClauseFollowUpAttackFact(_ClauseLocus):
    """*"the allosaurus can make one Bite attack against it"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_FOLLOW_UP_ATTACK

    attack: str
    count: int
    optional: bool


@dataclass(frozen=True, kw_only=True)
class ClauseTargetingRestrictionFact(_ClauseLocus):
    """*"can't be targeted by the crocodile's Tail"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_TARGETING_RESTRICTION

    source_attack: str
    excludes: TargetingExclusion


@dataclass(frozen=True, kw_only=True)
class ClauseDamageQualificationFact(_ClauseLocus):
    """*"Being underwater doesn't grant Resistance to this Fire damage."*"""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_DAMAGE_QUALIFICATION

    underwater_fire_resistance_applies: bool


@dataclass(frozen=True, kw_only=True)
class ClauseReturningWeaponFact(_ClauseLocus):
    """*"The spear magically returns to the <creature>'s hand"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_RETURNING_WEAPON

    weapon: ReturningWeaponKind
    or_hovers_within_ft: int | None


@dataclass(frozen=True, kw_only=True)
class ClauseSaveSuccessFact(_ClauseLocus):
    """*"Half damage"* inside a framed save's success branch."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_SAVE_SUCCESS

    half_damage: bool


@dataclass(frozen=True, kw_only=True)
class ClauseSaveTimingFact(_ClauseLocus):
    """*"at the end of the aboleth's turn"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_SAVE_TIMING

    at: RecurrenceBoundary
    turn: TurnWhich
    turn_of: TurnOwner


@dataclass(frozen=True, kw_only=True)
class ClauseSelfSavePredicateFact(_ClauseLocus):
    """*"If the basilisk sees its reflection in the Cone, the basilisk must
    make this save."*"""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_SELF_SAVE_PREDICATE

    when: ReflectionPredicate


@dataclass(frozen=True, kw_only=True)
class ClauseSourceMovementFact(_ClauseLocus):
    """*"The kraken then moves up to its Speed."*"""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_SOURCE_MOVEMENT

    up_to: SourceMovementLimit


@dataclass(frozen=True, kw_only=True)
class ClauseTriggerFact(_ClauseLocus):
    """*"The mephit explodes when it dies."*"""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_TRIGGER

    on: TriggerOn


@dataclass(frozen=True, kw_only=True)
class ClauseRescueCheckFact(_ClauseLocus):
    """*"As an action, a creature within 5 feet ... can pull a creature out of
    it by succeeding on a DC 14 Strength (Athletics) check."*"""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_RESCUE_CHECK

    actor_within_ft: int
    uses: RescueCost
    check: CheckSpec
    ends: RescueEnds


@dataclass(frozen=True, kw_only=True)
class ClauseAreaOriginPointFact(_ClauseLocus):
    """*"at a point it can see within 90 feet"* / *"centered on that
    point"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_AREA_ORIGIN_POINT

    within_ft: int | None
    requires_source_sees_point: bool | None
    centered_on: AreaCenter | None


@dataclass(frozen=True, kw_only=True)
class ClauseAuraFact(_ClauseLocus):
    """*"emanates an aura in a 20-foot Emanation while it doesn't have the
    Incapacitated condition"* / *"in the aura"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CLAUSE_AURA

    emanation_ft: int | None
    suspended_while_source_has: ConditionKind | None
    targets_within: AuraTargets | None
