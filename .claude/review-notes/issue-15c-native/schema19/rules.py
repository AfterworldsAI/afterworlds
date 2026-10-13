# ---------------------------------------------------------------------------
# Schema 19 families -- rules, weapons, tools and conventions (C5-A, C5-C)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class WeaponRangeClassFact:
    """A weapon's printed Melee or Ranged group."""

    FAMILY: ClassVar[FactFamily] = FactFamily.WEAPON_RANGE_CLASS

    range_class: RangeClass


@dataclass(frozen=True, kw_only=True)
class AttackRollAbilityFact:
    """*"Strength for a melee attack, Dexterity for a ranged attack"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.ATTACK_ROLL_ABILITY

    ability: AbilityScore
    range_class: RangeClass


@dataclass(frozen=True, kw_only=True)
class NaturalRollOutcomeFact:
    """A natural 1 or 20 on an attack roll."""

    FAMILY: ClassVar[FactFamily] = FactFamily.NATURAL_ROLL_OUTCOME

    context: RollContext
    face: int
    outcome: NaturalOutcome
    critical_hit: bool


@dataclass(frozen=True, kw_only=True)
class InitiativeRollFact:
    """*"Initiative ... a Dexterity check"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.INITIATIVE_ROLL

    ability: AbilityScore
    context: RollContext


@dataclass(frozen=True, kw_only=True)
class DamageRollRuleFact:
    """How a damage roll adds the attack's ability modifier, and its floor."""

    FAMILY: ClassVar[FactFamily] = FactFamily.DAMAGE_ROLL_RULE

    adds_attack_ability_modifier: bool
    fixed_amount_adds_modifier: bool
    minimum_damage: int


@dataclass(frozen=True, kw_only=True)
class CriticalDamageFact:
    """*"Roll all of the attack's damage dice twice ... add any relevant
    modifiers as normal"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CRITICAL_DAMAGE

    applies_to: CriticalDamageScope
    damage_dice_multiplier: int
    modifiers: ModifierApplication


@dataclass(frozen=True, kw_only=True)
class TemporaryHitPointAbsorptionFact:
    """Temporary Hit Points are lost first; leftover damage carries over."""

    FAMILY: ClassVar[FactFamily] = FactFamily.TEMPORARY_HIT_POINT_ABSORPTION

    absorbed_first: bool
    overflow_to_hit_points: bool


@dataclass(frozen=True, kw_only=True)
class HitPointBoundFact:
    """*"Hit Points can't go below 0"* -- a bound on current Hit Points."""

    FAMILY: ClassVar[FactFamily] = FactFamily.HIT_POINT_BOUND

    minimum_current: int


@dataclass(frozen=True, kw_only=True)
class ZeroHitPointOutcomeFact:
    """A zero-HP rule: who, what happens, and the GameMaster's exception."""

    FAMILY: ClassVar[FactFamily] = FactFamily.ZERO_HIT_POINT_OUTCOME

    subject: ZeroHitPointSubject
    outcome: ZeroHitPointResult
    gamemaster_exception: GamemasterException | None
    exception_scope: ExceptionScope | None
    trigger: ZeroHitPointRuleTrigger | None
    until: LifecycleEvent | None


@dataclass(frozen=True, kw_only=True)
class MassiveDamageFact:
    """Instant death when remaining damage equals or exceeds the maximum."""

    FAMILY: ClassVar[FactFamily] = FactFamily.MASSIVE_DAMAGE

    subject: ZeroHitPointSubject
    dies_when_remainder_at_least: DeathThreshold


@dataclass(frozen=True, kw_only=True)
class DeathSavingThrowFact:
    """The Death Saving Throw: its die, thresholds, resets and timing."""

    FAMILY: ClassVar[FactFamily] = FactFamily.DEATH_SAVING_THROW

    ability: AbilityScore | None
    die: DieSize
    failures_to_die: int
    success_minimum: int
    successes_to_stable: int
    reset_on: tuple[LifecycleEvent, ...]
    timing: DeathSaveTiming


@dataclass(frozen=True, kw_only=True)
class DeathSaveNaturalRollFact:
    """A natural 1 (two failures) or 20 (regain 1 Hit Point)."""

    FAMILY: ClassVar[FactFamily] = FactFamily.DEATH_SAVE_NATURAL_ROLL

    face: int
    failures: int | None
    regain_hit_points: int | None


@dataclass(frozen=True, kw_only=True)
class DamageAtZeroHitPointsFact:
    """Damage at 0 Hit Points: failures, critical failures, death threshold."""

    FAMILY: ClassVar[FactFamily] = FactFamily.DAMAGE_AT_ZERO_HIT_POINTS

    failures: int
    critical_hit_failures: int
    dies_when_damage_at_least: DeathThreshold


@dataclass(frozen=True, kw_only=True)
class StabilizationFact:
    """Stabilizing with the Help action."""

    FAMILY: ClassVar[FactFamily] = FactFamily.STABILIZATION

    action: StabilizeAction
    on_success: StabilizeOutcome
    target_at_hit_points: int


@dataclass(frozen=True, kw_only=True)
class StableStateFact:
    """What being Stable means, and its prescribed recovery."""

    FAMILY: ClassVar[FactFamily] = FactFamily.STABLE_STATE

    makes_death_saves: bool
    remains_unconscious: bool
    damage_ends_stable: bool
    recovery: StableRecovery


@dataclass(frozen=True, kw_only=True)
class KnockoutAlternativeFact:
    """Knocking a creature out instead of reducing it to 0 Hit Points."""

    FAMILY: ClassVar[FactFamily] = FactFamily.KNOCKOUT_ALTERNATIVE

    attack: RangeClass
    trigger: KnockoutTrigger
    optional: bool
    set_hit_points: int
    condition: ConditionKind
    starts: RestKind
    ends_after: RestKind
    ends_early_on: tuple[LifecycleEvent, ...]


@dataclass(frozen=True, kw_only=True)
class RestDurationFact:
    """How long a rest lasts."""

    FAMILY: ClassVar[FactFamily] = FactFamily.REST_DURATION

    rest: RestKind
    hours: int


@dataclass(frozen=True, kw_only=True)
class AttackAbilityOptionFact:
    """Finesse: Strength or Dexterity, the same for damage."""

    FAMILY: ClassVar[FactFamily] = FactFamily.ATTACK_ABILITY_OPTION

    abilities: tuple[AbilityScore, ...]
    same_for_damage: bool


@dataclass(frozen=True, kw_only=True)
class AbilityScoreRequirementFact:
    """Heavy: a minimum score, and what being below it imposes."""

    FAMILY: ClassVar[FactFamily] = FactFamily.ABILITY_SCORE_REQUIREMENT

    ability: AbilityScore
    minimum: int
    range_class: RangeClass
    unmet: UnmetEffect


@dataclass(frozen=True, kw_only=True)
class LightExtraAttackFact:
    """Light: the extra attack with a different Light weapon."""

    FAMILY: ClassVar[FactFamily] = FactFamily.LIGHT_EXTRA_ATTACK

    trigger: LightTrigger
    first_attack: LightFirstAttack
    requires: LightRequirement
    cost: ActionCost
    when: LightTiming
    ability_modifier_damage: ModifierDamage
    limit: UseFrequency
    optional: bool


@dataclass(frozen=True, kw_only=True)
class AmmunitionPerActivationFact:
    """Loading: one piece per action, Bonus Action or Reaction."""

    FAMILY: ClassVar[FactFamily] = FactFamily.AMMUNITION_PER_ACTIVATION

    maximum: int
    per: tuple[ActionCost, ...]


@dataclass(frozen=True, kw_only=True)
class RangeBandRuleFact:
    """Range: Disadvantage beyond normal, no attack beyond long."""

    FAMILY: ClassVar[FactFamily] = FactFamily.RANGE_BAND_RULE

    beyond_normal: RangeOutcome
    beyond_long: RangeOutcome


@dataclass(frozen=True, kw_only=True)
class ReachExtensionFact:
    """Reach: 5 more feet for attacks with it and Opportunity Attacks."""

    FAMILY: ClassVar[FactFamily] = FactFamily.REACH_EXTENSION

    feet: int
    applies_to: tuple[ReachScope, ...]


@dataclass(frozen=True, kw_only=True)
class ThrownAttackFact:
    """Thrown: a ranged attack, drawn as part of it, with the melee ability."""

    FAMILY: ClassVar[FactFamily] = FactFamily.THROWN_ATTACK

    attack: RangeClass
    draw_as_part_of_attack: bool
    melee_weapon_ability: ThrownAbility


@dataclass(frozen=True, kw_only=True)
class HandsRequiredFact:
    """Two-Handed: two hands when attacking."""

    FAMILY: ClassVar[FactFamily] = FactFamily.HANDS_REQUIRED

    hands: int
    when: HandsWhen


@dataclass(frozen=True, kw_only=True)
class VersatileDamageFact:
    """Versatile: the two-handed melee damage."""

    FAMILY: ClassVar[FactFamily] = FactFamily.VERSATILE_DAMAGE

    attack: RangeClass
    hands: int


@dataclass(frozen=True, kw_only=True)
class AmmunitionExpenditureFact:
    """Ammunition: one piece per attack, drawing, loading and recovery."""

    FAMILY: ClassVar[FactFamily] = FactFamily.AMMUNITION_EXPENDITURE

    per_attack: int
    requires: AmmunitionRequirement
    drawing_is_part_of_the_attack: bool
    loading_requires_free_hand: FreeHandRule
    recovery: AmmunitionRecovery


@dataclass(frozen=True, kw_only=True)
class MasteryEffectFact:
    """One mastery property's effect, as its Mastery Properties entry prints
    it. Only the fields its property states are set."""

    FAMILY: ClassVar[FactFamily] = FactFamily.MASTERY_EFFECT

    mastery: WeaponMastery
    trigger: MasteryTrigger
    optional: bool
    applies_to: MasteryAppliesTo | None
    against: MasteryAgainst | None
    cost: MasteryCost | None
    damage: MasteryDamage | None
    damage_type: MasteryDamageType | None
    increase: MasteryIncrease | None
    ability_modifier_damage: ModifierDamage | None
    limit: UseFrequency | None
    second_target_within_ft: int | None
    second_target_within_reach: bool | None
    direction: ForcedDirection | None
    distance_ft_up_to: int | None
    maximum_size: CreatureSize | None
    speed_reduction_ft: int | None
    maximum_reduction_ft: int | None
    duration: TurnBoundary | None
    effect: AdvantageFact | None
    save: AbilityScore | None
    dc: MasteryDc | None
    on_failure: tuple[ConditionEffectFact, ...]


@dataclass(frozen=True, kw_only=True)
class ToolEntryFact:
    """A tool's printed ability and Tools-section group."""

    FAMILY: ClassVar[FactFamily] = FactFamily.TOOL_ENTRY

    ability: AbilityScore
    category: ToolCategory


@dataclass(frozen=True, kw_only=True)
class ToolVariantsFact:
    """Gaming Set / Musical Instrument: its kinds, each a separate
    proficiency."""

    FAMILY: ClassVar[FactFamily] = FactFamily.TOOL_VARIANTS

    variants: tuple[ToolVariant, ...]
    separate_proficiency: bool


@dataclass(frozen=True, kw_only=True)
class ToolActivityFact:
    """Which printed activity of a tool a component, or one option of its
    choice, is: the source activity's selectable identity."""

    FAMILY: ClassVar[FactFamily] = FactFamily.TOOL_ACTIVITY

    activity: ToolActivity


@dataclass(frozen=True, kw_only=True)
class CreatureAttackNotationFact:
    """How a stat-block attack is read: one target, its outcome sections."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_ATTACK_NOTATION

    targets: int
    sections: tuple[AttackSection, ...]


@dataclass(frozen=True, kw_only=True)
class CreatureSaveNotationFact:
    """How a stat-block save effect is read."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_SAVE_NOTATION

    half_damage_rounding: RoundingRule
    half_damage_only_ignores_other_effects: bool


@dataclass(frozen=True, kw_only=True)
class DamageNotationOptionFact:
    """Average or dice, the GameMaster's choice."""

    FAMILY: ClassVar[FactFamily] = FactFamily.DAMAGE_NOTATION_OPTION

    options: tuple[DamageNotation, ...]
    exclusive: bool
    selected_by: Chooser


@dataclass(frozen=True, kw_only=True)
class MultiattackRuleFact:
    """Multiattack is taken as the Attack action, composed per entry."""

    FAMILY: ClassVar[FactFamily] = FactFamily.MULTIATTACK_RULE

    action: MultiattackAction
    composition: MultiattackComposition


@dataclass(frozen=True, kw_only=True)
class UsageLimitRuleFact:
    """One limited-usage notation and how uses come back."""

    FAMILY: ClassVar[FactFamily] = FactFamily.USAGE_LIMIT_RULE

    kind: UsageRuleKind
    regain: tuple[RestKind, ...]
    also_regain: tuple[RestKind, ...]
    die: DieSize | None
    roll_at: RecurrenceBoundary | None
    turn_of: TurnOwner | None


@dataclass(frozen=True, kw_only=True)
class LegendaryActionRuleFact:
    """Legendary actions: timing, one at a time, regain, conditions."""

    FAMILY: ClassVar[FactFamily] = FactFamily.LEGENDARY_ACTION_RULE

    timing: LegendaryTiming
    one_at_a_time: bool
    regain: LegendaryRegain
    not_while_has_conditions: tuple[ConditionKind, ...]


@dataclass(frozen=True, kw_only=True)
class SpellAttackModifierFormulaFact:
    """*"spellcasting ability modifier + Proficiency Bonus"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.SPELL_ATTACK_MODIFIER_FORMULA

    sum: tuple[FormulaTerm, ...]


@dataclass(frozen=True, kw_only=True)
class SpellSaveDcFormulaFact:
    """*"8 + spellcasting ability modifier + Proficiency Bonus"*."""

    FAMILY: ClassVar[FactFamily] = FactFamily.SPELL_SAVE_DC_FORMULA

    base: int
    plus: tuple[FormulaTerm, ...]


@dataclass(frozen=True, kw_only=True)
class SpellcastingAbilityFact:
    """A class's spellcasting ability."""

    FAMILY: ClassVar[FactFamily] = FactFamily.SPELLCASTING_ABILITY

    ability: AbilityScore


@dataclass(frozen=True, kw_only=True)
class DifficultyBandFact:
    """One Typical Difficulty Class row."""

    FAMILY: ClassVar[FactFamily] = FactFamily.DIFFICULTY_BAND

    applies_to: RollContext
    difficulty: Difficulty
    dc: int


# Grants ---------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class SkillProficiencyChoiceFact:
    """A choice of skill proficiencies: from a list, or from another
    component's list (``from_reference``)."""

    FAMILY: ClassVar[FactFamily] = FactFamily.SKILL_PROFICIENCY_CHOICE

    count: int
    from_skills: tuple[Skill, ...]
    from_reference: ComponentReference | None
    context: GrantContext | None
    eligibility: SubclassEligibility | None
    gain_levels: ProgressionReference | None
    or_tools: ToolSelector | None
    repeatable: bool | None


@dataclass(frozen=True, kw_only=True)
class MulticlassSkillProficiencyChoiceFact:
    """The skill a multiclass entry grants, if any."""

    FAMILY: ClassVar[FactFamily] = FactFamily.MULTICLASS_SKILL_PROFICIENCY_CHOICE

    count: int
    from_skills: tuple[Skill, ...]
    from_reference: ComponentReference | None


@dataclass(frozen=True, kw_only=True)
class SkillProficiencyGrantFact:
    """A background's fixed skills."""

    FAMILY: ClassVar[FactFamily] = FactFamily.SKILL_PROFICIENCY_GRANT

    skills: tuple[Skill, ...]


@dataclass(frozen=True, kw_only=True)
class SavingThrowProficiencyGrantFact:
    """Saving-throw proficiencies a class or feature grants."""

    FAMILY: ClassVar[FactFamily] = FactFamily.SAVING_THROW_PROFICIENCY_GRANT

    abilities: tuple[AbilityScore, ...]
    context: GrantContext | None
    gain_levels: ProgressionReference | None


@dataclass(frozen=True, kw_only=True)
class WeaponProficiencyGrantFact:
    """A class's weapon proficiencies, by category or qualified category."""

    FAMILY: ClassVar[FactFamily] = FactFamily.WEAPON_PROFICIENCY_GRANT

    categories: tuple[WeaponCategory, ...]
    qualified: tuple[QualifiedWeaponCategory, ...]
    context: GrantContext | None


@dataclass(frozen=True, kw_only=True)
class ArmorTrainingGrantFact:
    """A class's armor training."""

    FAMILY: ClassVar[FactFamily] = FactFamily.ARMOR_TRAINING_GRANT

    armor: tuple[ArmorCategory, ...]
    shields: bool
    context: GrantContext | None


@dataclass(frozen=True, kw_only=True)
class ToolProficiencyGrantFact:
    """Fixed tool proficiencies."""

    FAMILY: ClassVar[FactFamily] = FactFamily.TOOL_PROFICIENCY_GRANT

    tools: tuple[ComponentReference, ...]
    context: GrantContext | None


@dataclass(frozen=True, kw_only=True)
class ToolProficiencyChoiceFact:
    """A choice of tool proficiencies."""

    FAMILY: ClassVar[FactFamily] = FactFamily.TOOL_PROFICIENCY_CHOICE

    count: int
    options: tuple[ToolSelector, ...]
    context: GrantContext | None


@dataclass(frozen=True, kw_only=True)
class MulticlassProficiencyGrantFact:
    """What a multiclass entry grants besides a skill -- and that it grants
    no saving throws."""

    FAMILY: ClassVar[FactFamily] = FactFamily.MULTICLASS_PROFICIENCY_GRANT

    saving_throws: tuple[AbilityScore, ...]
    weapons: WeaponCategories
    armor_training: ArmorTraining
    tool_choice: ToolChoice | None
    tool_grant: tuple[ComponentReference, ...]


@dataclass(frozen=True, kw_only=True)
class WeaponAndArmorGrantFact:
    """A chosen class option's weapon proficiency and armor training."""

    FAMILY: ClassVar[FactFamily] = FactFamily.WEAPON_AND_ARMOR_GRANT

    weapons: WeaponCategories
    armor_training: ArmorTraining
    chosen_option_of: str
    gain_levels: ProgressionReference


@dataclass(frozen=True, kw_only=True)
class WeaponMasteryChoiceFact:
    """Weapon Mastery: how many kinds, which are eligible, counts by level and
    the Long Rest swap."""

    FAMILY: ClassVar[FactFamily] = FactFamily.WEAPON_MASTERY_CHOICE

    kinds_of_weapons: int
    categories: tuple[WeaponCategory, ...]
    melee_only: bool | None
    requires_weapon_proficiency: bool | None
    count_by_level: tuple[LevelCount, ...]
    rest_swap: RestSwap
    gain_levels: ProgressionReference


@dataclass(frozen=True, kw_only=True)
class FeatPrerequisiteFact:
    """A feat's category and prerequisites."""

    FAMILY: ClassVar[FactFamily] = FactFamily.FEAT_PREREQUISITE

    category: FeatCategory
    minimum_character_level: int | None
    minimum_ability_score: AbilityMinimum | None
    requires_feature: RequiredFeature | None


@dataclass(frozen=True, kw_only=True)
class FeatChoiceFact:
    """A feat a feature or species entitles: a named feat or any qualifying
    one, of a category."""

    FAMILY: ClassVar[FactFamily] = FactFamily.FEAT_CHOICE

    count: int | None
    count_per_gain: int | None
    category: FeatCategory | None
    named_feat: str | None
    or_any_feat_whose_prerequisites_are_met: bool | None
    gain_levels: ProgressionReference | None


@dataclass(frozen=True, kw_only=True)
class FeatGrantFact:
    """A background's fixed feat (``feat`` a ``feats.*`` record key)."""

    FAMILY: ClassVar[FactFamily] = FactFamily.FEAT_GRANT

    feat: str
    qualifier: FeatQualifier | None


@dataclass(frozen=True, kw_only=True)
class AbilityIncreaseChoiceFact:
    """An ability-score increase: which abilities, which patterns, the cap."""

    FAMILY: ClassVar[FactFamily] = FactFamily.ABILITY_INCREASE_CHOICE

    abilities: tuple[AbilityScore, ...]
    any_ability: bool | None
    patterns: tuple[tuple[int, ...], ...]
    distinct_abilities: bool | None
    maximum_score: int | None
    repeatable: bool | None
    rule: ComponentReference | None


@dataclass(frozen=True, kw_only=True)
class AbilityIncreaseRuleFact:
    """The background ability-score rule."""

    FAMILY: ClassVar[FactFamily] = FactFamily.ABILITY_INCREASE_RULE

    patterns: tuple[tuple[int, ...], ...]
    distinct_abilities: bool
    maximum_score: int


@dataclass(frozen=True, kw_only=True)
class ExpertiseRuleFact:
    """Expertise: requires proficiency, no duplicates, doubled bonus."""

    FAMILY: ClassVar[FactFamily] = FactFamily.EXPERTISE_RULE

    requires_skill_proficiency: bool
    no_duplicate: bool
    proficiency_bonus_multiplier: int


@dataclass(frozen=True, kw_only=True)
class ExpertiseChoiceFact:
    """Expertise a feature grants per gain."""

    FAMILY: ClassVar[FactFamily] = FactFamily.EXPERTISE_CHOICE

    count_per_gain: int
    from_proficient_skills: bool
    from_skills: tuple[Skill, ...]
    gain_levels: ProgressionReference


# Armor and AC (C5-C) ----------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class ArmorClassFormulaFact:
    """An armor row's AC formula, Strength requirement and Stealth effect."""

    FAMILY: ClassVar[FactFamily] = FactFamily.ARMOR_CLASS_FORMULA

    category: ArmorCategory
    base: int
    adds_dexterity_modifier: bool
    dexterity_maximum: int | None
    strength_minimum: int | None
    stealth_disadvantage: bool


@dataclass(frozen=True, kw_only=True)
class ShieldBonusFact:
    """A Shield's AC bonus."""

    FAMILY: ClassVar[FactFamily] = FactFamily.SHIELD_BONUS

    bonus: int


@dataclass(frozen=True, kw_only=True)
class BaseArmorClassFact:
    """Base AC without armor."""

    FAMILY: ClassVar[FactFamily] = FactFamily.BASE_ARMOR_CLASS

    base: int
    adds_dexterity_modifier: bool


@dataclass(frozen=True, kw_only=True)
class BaseArmorClassExclusivityFact:
    """Only one base AC calculation at a time."""

    FAMILY: ClassVar[FactFamily] = FactFamily.BASE_ARMOR_CLASS_EXCLUSIVITY

    maximum: int


@dataclass(frozen=True, kw_only=True)
class ArmorTrainingPenaltyFact:
    """Wearing armor without training."""

    FAMILY: ClassVar[FactFamily] = FactFamily.ARMOR_TRAINING_PENALTY

    applies_to: tuple[ArmorCategory, ...]
    applies_when: TrainingCondition
    d20_tests: AdvantageState
    abilities: tuple[AbilityScore, ...]
    cannot_cast_spells: bool


@dataclass(frozen=True, kw_only=True)
class ShieldTrainingRequirementFact:
    """A Shield gives no AC benefit without training."""

    FAMILY: ClassVar[FactFamily] = FactFamily.SHIELD_TRAINING_REQUIREMENT

    untrained: UntrainedShield
