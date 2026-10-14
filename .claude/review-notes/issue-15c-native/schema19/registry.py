# ---------------------------------------------------------------------------
# Schema 19 -- builders, checks and declared invariants
# ---------------------------------------------------------------------------
#
# The schema-19 families are built and checked from their declared fields:
# every field is a typed dataclass field, a payload's key set must equal the
# field set exactly, nothing is coerced, and a field typed with an accepted fact
# class is built by that family's accepted builder (``fact_from_payload``) and
# checked by its accepted check. Reflection over declared fields is safe here
# for the reason ``_shape`` is: the grammar it walks is closed, and anything it
# cannot describe raises instead of passing through.

_SCHEMA_19_FACT_CLASSES: tuple[type[Any], ...] = (
    CreatureAttackFact,
    CreatureSaveEffectFact,
    CreatureMultiattackFact,
    CreatureEntryUsageFact,
    CreatureEntryReferenceFact,
    CreatureObserverCheckFact,
    CreatureConditionGrantFact,
    CreatureSaveOverrideFact,
    CreatureSaveDamageOverrideFact,
    CreatureRollModifierFact,
    CreatureHitPointRegainProhibitionFact,
    CheckRequirementRemovalFact,
    ZeroHitPointSaveFact,
    CreatureSizeFact,
    CreatureConditionalDefenseFact,
    CreatureDefenseParameterizedFact,
    ClauseBranchFact,
    ClausePredicateFact,
    ClauseGrappleFact,
    ClauseConditionFact,
    ClauseTimedConditionFact,
    ClauseLinkedConditionFact,
    ClauseConditionUntilRepeatFact,
    ClauseConditionEndsFact,
    ClauseConditionEndsEarlyFact,
    ClauseEffectEndsFact,
    ClauseEffectLastsFact,
    ClauseRepeatSaveFact,
    ClauseRepeatSaveLimitFact,
    ClauseTemporaryImmunityFact,
    ClauseNestedSaveFact,
    ClauseNestedSaveTriggerFact,
    ClauseTimedSpeedChangeFact,
    ClauseTimedAcModifierFact,
    ClauseNextRollModifierFact,
    ClauseD20TestPenaltyDieFact,
    ClausePenaltyDieApplicationFact,
    ClauseRollModifierFact,
    ClauseDamageRollPenaltyFact,
    ClauseDamageBranchFact,
    ClauseChoiceTypedDamageFact,
    ClauseConditionalDamageFact,
    ClausePeriodicDamageFact,
    ClausePeriodicHitPointLossFact,
    ClauseHitPointRegainProhibitionFact,
    ClauseHitPointsSetFact,
    ClauseZeroHitPointOutcomeFact,
    ClauseNamedEffectFact,
    ClauseForcedMovementFact,
    ClauseFollowUpAttackFact,
    ClauseTargetingRestrictionFact,
    ClauseDamageQualificationFact,
    ClauseReturningWeaponFact,
    ClauseSaveSuccessFact,
    ClauseSaveTimingFact,
    ClauseSelfSavePredicateFact,
    ClauseSourceMovementFact,
    ClauseTriggerFact,
    ClauseRescueCheckFact,
    ClauseAreaOriginPointFact,
    ClauseAuraFact,
    WeaponRangeClassFact,
    AttackRollAbilityFact,
    NaturalRollOutcomeFact,
    InitiativeRollFact,
    DamageRollRuleFact,
    CriticalDamageFact,
    TemporaryHitPointAbsorptionFact,
    HitPointBoundFact,
    ZeroHitPointOutcomeFact,
    MassiveDamageFact,
    DeathSavingThrowFact,
    DeathSaveNaturalRollFact,
    DamageAtZeroHitPointsFact,
    StabilizationFact,
    StableStateFact,
    KnockoutAlternativeFact,
    RestDurationFact,
    AttackAbilityOptionFact,
    AbilityScoreRequirementFact,
    LightExtraAttackFact,
    AmmunitionPerActivationFact,
    RangeBandRuleFact,
    ReachExtensionFact,
    ThrownAttackFact,
    HandsRequiredFact,
    VersatileDamageFact,
    AmmunitionExpenditureFact,
    MasteryEffectFact,
    ToolEntryFact,
    ToolVariantsFact,
    ToolActivityFact,
    CreatureAttackNotationFact,
    CreatureSaveNotationFact,
    DamageNotationOptionFact,
    MultiattackRuleFact,
    UsageLimitRuleFact,
    LegendaryActionRuleFact,
    SpellAttackModifierFormulaFact,
    SpellSaveDcFormulaFact,
    SpellcastingAbilityFact,
    DifficultyBandFact,
    SkillProficiencyChoiceFact,
    MulticlassSkillProficiencyChoiceFact,
    SkillProficiencyGrantFact,
    SavingThrowProficiencyGrantFact,
    WeaponProficiencyGrantFact,
    ArmorTrainingGrantFact,
    ToolProficiencyGrantFact,
    ToolProficiencyChoiceFact,
    MulticlassProficiencyGrantFact,
    WeaponAndArmorGrantFact,
    WeaponMasteryChoiceFact,
    FeatPrerequisiteFact,
    FeatChoiceFact,
    FeatGrantFact,
    AbilityIncreaseChoiceFact,
    AbilityIncreaseRuleFact,
    ExpertiseRuleFact,
    ExpertiseChoiceFact,
    ArmorClassFormulaFact,
    ShieldBonusFact,
    BaseArmorClassFact,
    BaseArmorClassExclusivityFact,
    ArmorTrainingPenaltyFact,
    ShieldTrainingRequirementFact,
)


def _declared_from_json(annotation: object, value: object, where: str) -> object:
    """Build one declared field from its stored JSON value, exactly."""
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (Union, UnionType):
        inner = next(a for a in args if a is not type(None))
        return None if value is None else _declared_from_json(inner, value, where)
    if origin in (tuple, list):
        (item,) = (a for a in args if a is not Ellipsis)
        if type(value) is not list:
            raise MalformedFactPayloadError(
                f"{where} must be an array, got {type(value).__name__}"
            )
        return tuple(
            _declared_from_json(item, v, f"{where}[{i}]") for i, v in enumerate(value)
        )
    if annotation in (bool, int, str):
        if type(value) is not annotation:
            raise MalformedFactPayloadError(
                f"{where} must be {_PRIMITIVE_SHAPES[cast(type, annotation)]}, got "
                f"{type(value).__name__}"
            )
        return value
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        _reject_at(where, _json_enum(value, annotation, where))
        return annotation(cast(str, value))
    if isinstance(annotation, type) and is_dataclass(annotation):
        family = getattr(annotation, "FAMILY", None)
        if isinstance(family, FactFamily):
            # A nested accepted shape: its own accepted builder, under its own
            # declared family, so it is never a second spelling of it.
            if type(value) is not dict or "family" in value:
                raise MalformedFactPayloadError(
                    f"{where} must be an untagged {family.value} object"
                )
            return fact_from_payload({**value, "family": family.value})
        p = _json_object(value, tuple(f.name for f in fields(annotation)), where)
        hints = get_type_hints(annotation)
        return annotation(
            **{
                f.name: _declared_from_json(hints[f.name], p[f.name], f"{where}.{f.name}")
                for f in fields(annotation)
            }
        )
    raise UnsupportedRepresentationShapeError(
        f"{where}: {annotation!r} has no schema-19 builder"
    )


def _build_declared(cls: type[Any]) -> Callable[[Mapping[str, Any]], MechanicalFact]:
    def build(p: Mapping[str, Any]) -> MechanicalFact:
        hints = get_type_hints(cls)
        family = cast(FactFamily, cls.FAMILY)
        return cast(
            MechanicalFact,
            cls(
                **{
                    f.name: _declared_from_json(
                        hints[f.name], p[f.name], f"{family.value}.{f.name}"
                    )
                    for f in fields(cls)
                }
            ),
        )

    return build


#: The source-valid domain of every integer field schema 19 declares, by
#: owner then field: the least value the field can state, or ``SIGNED`` for a
#: printed bonus, modifier or delta. A sequence of integers takes its element
#: domain from the same row. Completeness is asserted at import, so an integer
#: field nobody gave a domain fails the build rather than admitting anything.
SIGNED = "signed"
_SCHEMA_19_INT_DOMAINS: dict[type, dict[str, int | str]] = {
    ElapsedSpan: {"amount": 1},
    EndingEvent: {"by_creature_within_ft": 1},
    DamageTerm: {"average": 0, "constant": 0},
    DamageWhen: {"source_moved_straight_toward_target_ft_min": 1},
    ConditionalDamage: {"replaces_hit_damage_index": 0},
    ForcedMove: {"distance_ft": 1, "distance_ft_up_to": 1},
    RiderSave: {"dc": 1},
    Rider: {"escape_dc": 1},
    SaveArea: {"size_ft": 1, "width_ft": 1, "height_ft": 1},
    SaveTargets: {"count": 1, "origin_point_within_ft": 1, "within_ft": 1,
                  "swallow_capacity": 1, "at_hit_points": 0},
    EntryOption: {"spell_level": 1},
    MultiattackPart: {"count": 1},
    MultiattackReplacement: {"replaces": 1},
    CheckSpec: {"dc": 1},
    ContributorPredicate: {"ally_within_ft_of_target": 1},
    DamagePlusDc: {"base": 0},
    ZeroHitPointOnSuccess: {"set_hit_points": 0},
    LeveledArmorClass: {"base": 0, "per_spell_level": 0},
    PerLevelAbove: {"amount": 1, "level": 1},
    SizeKeyedHitPoints: {"medium_or_smaller": 1, "large": 1, "huge": 1},
    ParameterizedHitPoints: {"base": 1, "per_spell_level": 1},
    ToolChoice: {"count": 1},
    SubclassEligibility: {"minimum_class_level": 1},
    AbilityMinimum: {"score": 1},
    LevelCount: {"level": 1, "count": 1},
    DeathSaveTiming: {"at_hit_points": 0},
    StableRecovery: {"regain_hit_points": 1},
    AmmunitionRecovery: {"minutes": 1},
    MasteryDc: {"base": 0},
    GrappleAppendages: {"of": 1},
    CreatureAttackFact: {"attack_bonus": SIGNED, "reach_ft": 1, "normal_range_ft": 1,
                         "long_range_ft": 1},
    CreatureSaveEffectFact: {"dc": 1},
    CreatureEntryUsageFact: {"uses": 1, "in_lair": 1, "minimum_d6": 1},
    CreatureDefenseParameterizedFact: {"armor_class": 0},
    _ClauseLocus: {"piece": 0, "under_predicates": 0},
    ClausePredicateFact: {"source_moved_straight_toward_target_ft_min": 1,
                          "target_hit_points_at_most": 0},
    ClauseGrappleFact: {"escape_dc": 1},
    ClauseRepeatSaveLimitFact: {"automatic_success_after_minutes": 1},
    ClauseTemporaryImmunityFact: {"hours": 1},
    ClauseNestedSaveFact: {"dc": 1},
    ClauseTimedSpeedChangeFact: {"feet": 0},
    ClauseTimedAcModifierFact: {"modifier": SIGNED},
    ClauseNextRollModifierFact: {"uses": 1},
    ClauseD20TestPenaltyDieFact: {"count": 1},
    ClauseDamageRollPenaltyFact: {"average": 0},
    ClauseChoiceTypedDamageFact: {"average": 0},
    ClauseConditionalDamageFact: {"replaces_hit_damage_index": 0,
                                  "unconditional_hit_damage_indices": 0},
    ClausePeriodicHitPointLossFact: {"average": 0},
    ClauseHitPointsSetFact: {"to": 0},
    ClauseFollowUpAttackFact: {"count": 1},
    ClauseForcedMovementFact: {"distance_ft": 1, "distance_ft_up_to": 1},
    ClauseReturningWeaponFact: {"or_hovers_within_ft": 1},
    ClauseRescueCheckFact: {"actor_within_ft": 1},
    ClauseAreaOriginPointFact: {"within_ft": 1},
    ClauseAuraFact: {"emanation_ft": 1},
    NaturalRollOutcomeFact: {"face": 1},
    DamageRollRuleFact: {"minimum_damage": 0},
    CriticalDamageFact: {"damage_dice_multiplier": 1},
    HitPointBoundFact: {"minimum_current": 0},
    DeathSavingThrowFact: {"failures_to_die": 1, "success_minimum": 1,
                           "successes_to_stable": 1},
    DeathSaveNaturalRollFact: {"face": 1, "failures": 1, "regain_hit_points": 1},
    DamageAtZeroHitPointsFact: {"failures": 1, "critical_hit_failures": 1},
    StabilizationFact: {"target_at_hit_points": 0},
    KnockoutAlternativeFact: {"set_hit_points": 0},
    RestDurationFact: {"hours": 1},
    AbilityScoreRequirementFact: {"minimum": 1},
    AmmunitionPerActivationFact: {"maximum": 1},
    ReachExtensionFact: {"feet": 1},
    HandsRequiredFact: {"hands": 1},
    VersatileDamageFact: {"hands": 1},
    AmmunitionExpenditureFact: {"per_attack": 1},
    MasteryEffectFact: {"second_target_within_ft": 1, "distance_ft_up_to": 1,
                        "speed_reduction_ft": 1, "maximum_reduction_ft": 1},
    CreatureAttackNotationFact: {"targets": 1},
    SpellSaveDcFormulaFact: {"base": 0},
    DifficultyBandFact: {"dc": 1},
    SkillProficiencyChoiceFact: {"count": 1},
    MulticlassSkillProficiencyChoiceFact: {"count": 0},
    ToolProficiencyChoiceFact: {"count": 1},
    WeaponMasteryChoiceFact: {"kinds_of_weapons": 1},
    FeatPrerequisiteFact: {"minimum_character_level": 1},
    FeatChoiceFact: {"count": 1, "count_per_gain": 1},
    AbilityIncreaseChoiceFact: {"patterns": 1, "maximum_score": 1},
    AbilityIncreaseRuleFact: {"patterns": 1, "maximum_score": 1},
    ExpertiseRuleFact: {"proficiency_bonus_multiplier": 1},
    ExpertiseChoiceFact: {"count_per_gain": 1},
    ArmorClassFormulaFact: {"base": 0, "dexterity_maximum": 0, "strength_minimum": 1},
    ShieldBonusFact: {"bonus": 0},
    BaseArmorClassFact: {"base": 0},
    BaseArmorClassExclusivityFact: {"maximum": 1},
}


def _int_leaves(annotation: object) -> bool:
    """Whether *annotation* is an integer, optionally, or a sequence of them."""
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (Union, UnionType, tuple, list):
        return any(_int_leaves(a) for a in args if a not in (type(None), Ellipsis))
    return annotation is int


def _domain_of(cls: type, field_name: str) -> int | str:
    for owner in cls.__mro__:
        domain = _SCHEMA_19_INT_DOMAINS.get(owner, {}).get(field_name)
        if domain is not None:
            return domain
    raise AssertionError(f"{cls.__name__}.{field_name} has no declared integer domain")


def _schema_19_declared_classes() -> list[type]:
    seen: list[type] = []

    def walk(cls: type) -> None:
        if cls in seen or cls in (DiceExpression, Rational) or isinstance(
            getattr(cls, "FAMILY", None), FactFamily
        ) and cls not in _SCHEMA_19_FACT_CLASSES:
            return
        seen.append(cls)
        hints = get_type_hints(cls)
        for f in fields(cls):
            for a in (hints[f.name], *get_args(hints[f.name])):
                for b in (a, *get_args(a)):
                    if isinstance(b, type) and is_dataclass(b):
                        walk(b)

    for cls in _SCHEMA_19_FACT_CLASSES:
        walk(cls)
    return seen


def _domain_findings(value: object, domain: int | str, where: str) -> list[str]:
    if domain == SIGNED or not _is_int(value):
        return []
    if cast(int, value) < cast(int, domain):
        return [f"{where} {value} is below its least source-valid value {domain}"]
    return []


def _declared_typed_findings(
    annotation: object, value: object, where: str, domain: int | str = SIGNED
) -> list[str]:
    """Check one declared field of a built object, exactly, then its rules.

    An integer is checked against its declared source-valid ``domain``; a
    nested accepted value object (``DiceExpression``, ``Rational``) is checked
    by its accepted validator, so neither is admitted on type alone.
    """
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (Union, UnionType):
        inner = next(a for a in args if a is not type(None))
        return [] if value is None else _declared_typed_findings(inner, value, where, domain)
    if origin in (tuple, list):
        (item,) = (a for a in args if a is not Ellipsis)
        if type(value) is not tuple:
            return [f"{where} must be a tuple, got {type(value).__name__}"]
        return [
            finding
            for i, v in enumerate(value)
            for finding in _declared_typed_findings(item, v, f"{where}[{i}]", domain)
        ]
    if annotation is bool:
        return _bool_field(value, where)
    if annotation is int:
        return _int_field(value, where) or _domain_findings(value, domain, where)
    if annotation is DiceExpression:
        return _check_dice(value, where)
    if annotation is Rational:
        return _check_rational(value, where)
    if annotation is str:
        return _str_field(value, where)
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        return _enum_field(value, annotation, where)
    if isinstance(annotation, type) and is_dataclass(annotation):
        if type(value) is not annotation:
            return [f"{where} must be {annotation.__name__}, got {type(value).__name__}"]
        family = getattr(annotation, "FAMILY", None)
        if isinstance(family, FactFamily):
            return [f"{where}: {x}" for x in _FACT_INVARIANTS[family](value)]
        hints = get_type_hints(annotation)
        findings = [
            finding
            for f in fields(annotation)
            for finding in _declared_typed_findings(
                hints[f.name],
                getattr(value, f.name),
                f"{where}.{f.name}",
                _domain_of(annotation, f.name) if _int_leaves(hints[f.name]) else SIGNED,
            )
        ]
        rule = _SCHEMA_19_SHAPE_RULES.get(annotation)
        return findings or ([f"{where}: {x}" for x in rule(value)] if rule else [])
    return [f"{where}: {annotation!r} has no schema-19 check"]


def _check_declared(fact: Any) -> list[str]:
    cls = type(fact)
    hints = get_type_hints(cls)
    findings = [
        finding
        for f in fields(cls)
        for finding in _declared_typed_findings(
            hints[f.name],
            getattr(fact, f.name),
            f.name,
            _domain_of(cls, f.name) if _int_leaves(hints[f.name]) else SIGNED,
        )
    ]
    if findings:
        return findings
    rule = _SCHEMA_19_FAMILY_RULES.get(cast(FactFamily, cls.FAMILY))
    return rule(fact) if rule else []


def _stated(value: object) -> bool:
    """Stated means not None, not an empty tuple and not ``False`` -- by
    identity, so an integer 0 is a stated value."""
    return not (value is None or value is False or value == ())


def _exactly_one(names: tuple[str, ...], values: tuple[object, ...], what: str) -> list[str]:
    stated = [n for n, v in zip(names, values, strict=True) if _stated(v)]
    if len(stated) != 1:
        return [f"{what} states exactly one of {list(names)}, got {stated}"]
    return []


def _at_most_one(names: tuple[str, ...], values: tuple[object, ...], what: str) -> list[str]:
    stated = [n for n, v in zip(names, values, strict=True) if _stated(v)]
    if len(stated) > 1:
        return [f"{what} states at most one of {list(names)}, got {stated}"]
    return []


def _rule_attack_bonus(fact: CreatureAttackFact) -> list[str]:
    names = ("attack_bonus", "attack_bonus_formula")
    values = (fact.attack_bonus, fact.attack_bonus_formula)
    if fact.automatic_hit:
        return _at_most_one(names, values, "an automatic-hit attack")
    return _exactly_one(names, values, "an attack")


def _rule_save_dc(fact: CreatureSaveEffectFact) -> list[str]:
    return _exactly_one(("dc", "dc_formula"), (fact.dc, fact.dc_formula), "a save effect")


def _rule_defense_parameterized(fact: CreatureDefenseParameterizedFact) -> list[str]:
    return _exactly_one(
        ("armor_class", "armor_class_formula"),
        (fact.armor_class, fact.armor_class_formula),
        "a parameterized defense",
    )


def _rule_timed_condition(fact: ClauseTimedConditionFact) -> list[str]:
    return _exactly_one(
        ("duration_turn", "duration_span"),
        (fact.duration_turn, fact.duration_span),
        "a timed condition",
    )


def _rule_clause_roll_modifier(fact: ClauseRollModifierFact) -> list[str]:
    return _exactly_one(
        ("effects", "ability_based"), (fact.effects, fact.ability_based),
        "a clause roll modifier",
    )


def _rule_skill_choice(
    fact: SkillProficiencyChoiceFact | MulticlassSkillProficiencyChoiceFact,
) -> list[str]:
    return _at_most_one(
        ("from_skills", "from_reference"),
        (fact.from_skills, fact.from_reference),
        "a skill choice",
    )


def _rule_damage_term(term: DamageTerm) -> list[str]:
    return _exactly_one(
        ("damage_type", "damage_type_by_choice"),
        (term.damage_type, term.damage_type_by_choice),
        "a damage term",
    )


def _rule_multiattack_part(part: MultiattackPart) -> list[str]:
    return [
        *_exactly_one(("count", "count_formula"), (part.count, part.count_formula),
                      "a Multiattack part"),
        *_exactly_one(
            ("attack", "any_of", "uses_one_of"),
            (part.attack, part.any_of, part.uses_one_of),
            "a Multiattack part",
        ),
    ]


def _rule_multiattack_replacement(r: MultiattackReplacement) -> list[str]:
    return _exactly_one(
        ("replaces", "replaces_attack", "replaces_any"),
        (r.replaces, r.replaces_attack, r.replaces_any),
        "a Multiattack replacement",
    )


def _rule_save_targets(t: SaveTargets) -> list[str]:
    return _at_most_one(
        ("origin", "origin_point_within_ft"),
        (t.origin, t.origin_point_within_ft),
        "a save's targets",
    )


def _rule_tool_selector(s: ToolSelector) -> list[str]:
    return _exactly_one(
        ("tool_variants_of", "tool_category", "any_tool_entry"),
        (s.tool_variants_of, s.tool_category, s.any_tool_entry),
        "a tool selector",
    )


def _rule_forced_move(m: ForcedMove) -> list[str]:
    return _exactly_one(
        ("distance_ft", "distance_ft_up_to"), (m.distance_ft, m.distance_ft_up_to),
        "a forced movement",
    )


def _rule_parameterized_hit_points(h: ParameterizedHitPoints) -> list[str]:
    findings = _exactly_one(
        ("per_spell_level", "per_spell_level_above", "by_size", "half_of"),
        (h.per_spell_level, h.per_spell_level_above, h.by_size, h.half_of),
        "parameterized Hit Points",
    )
    scaled = h.per_spell_level is not None or h.per_spell_level_above is not None
    if not findings and scaled != (h.base is not None):
        findings.append("parameterized Hit Points state a base exactly when they scale")
    return findings


_SCHEMA_19_FAMILY_RULES: dict[FactFamily, Callable[[Any], list[str]]] = {
    FactFamily.CREATURE_ATTACK: _rule_attack_bonus,
    FactFamily.CREATURE_SAVE_EFFECT: _rule_save_dc,
    FactFamily.CREATURE_DEFENSE_PARAMETERIZED: _rule_defense_parameterized,
    FactFamily.CLAUSE_TIMED_CONDITION: _rule_timed_condition,
    FactFamily.CLAUSE_ROLL_MODIFIER: _rule_clause_roll_modifier,
    FactFamily.SKILL_PROFICIENCY_CHOICE: _rule_skill_choice,
    FactFamily.MULTICLASS_SKILL_PROFICIENCY_CHOICE: _rule_skill_choice,
}

_SCHEMA_19_SHAPE_RULES: dict[type, Callable[[Any], list[str]]] = {
    DamageTerm: _rule_damage_term,
    MultiattackPart: _rule_multiattack_part,
    MultiattackReplacement: _rule_multiattack_replacement,
    SaveTargets: _rule_save_targets,
    ToolSelector: _rule_tool_selector,
    ForcedMove: _rule_forced_move,
    ParameterizedHitPoints: _rule_parameterized_hit_points,
}

def _int_domain_rows() -> tuple[_Invariant, ...]:
    """The integer domains as manifest rows, one per bound, in wire loci only."""
    by_bound: dict[str, list[str]] = {}
    for cls in _schema_19_declared_classes():
        family = getattr(cls, "FAMILY", None)
        locus = f"fact:{family.value}" if isinstance(family, FactFamily) else _shape_locus(cls)
        hints = get_type_hints(cls)
        for f in fields(cls):
            if _int_leaves(hints[f.name]):
                by_bound.setdefault(str(_domain_of(cls, f.name)), []).append(
                    f"{locus}.{f.name}"
                )
    rules = {SIGNED: "a printed signed bonus, modifier or delta; any integer",
             "0": "an integer, never below zero", "1": "an integer of at least one"}
    return tuple(
        _Invariant(
            id=f"integer-field.domain.{bound}",
            locus="fields:integer",
            field="|".join(sorted(names)),
            rule=rules[bound],
        )
        for bound, names in sorted(by_bound.items())
    )


#: The schema-19 invariant manifest rows: exactly the rules the two tables
#: above enforce, plus the weapon-property additions, each demonstrated in both
#: directions by ``test_schema_4_invariant_closure``.
_SCHEMA_19_INVARIANTS: tuple[_Invariant, ...] = (
    _Invariant(
        id="creature_attack.bonus.exactly-one-unless-automatic-hit",
        locus="fact:creature_attack",
        field="attack_bonus+attack_bonus_formula",
        rule="exactly one of a printed bonus and a bonus formula; at most one for an "
        "automatic hit",
    ),
    _Invariant(
        id="creature_save_effect.dc.exactly-one",
        locus="fact:creature_save_effect",
        field="dc+dc_formula",
        rule="exactly one of a printed DC and a DC formula",
    ),
    _Invariant(
        id="creature_defense_parameterized.armor-class.exactly-one",
        locus="fact:creature_defense_parameterized",
        field="armor_class+armor_class_formula",
        rule="exactly one of a fixed Armor Class and an Armor Class formula",
    ),
    _Invariant(
        id="clause_timed_condition.duration.exactly-one",
        locus="fact:clause_timed_condition",
        field="duration_turn+duration_span",
        rule="exactly one of a turn-edge duration and an elapsed duration",
    ),
    _Invariant(
        id="clause_roll_modifier.effects-or-ability-based.exactly-one",
        locus="fact:clause_roll_modifier",
        field="effects+ability_based",
        rule="exactly one of accepted roll modifiers and an ability-based D20 Test "
        "modifier",
    ),
    _Invariant(
        id="skill_proficiency_choice.from.at-most-one",
        locus="fact:skill_proficiency_choice",
        field="from_skills+from_reference",
        rule="a printed skill list or a referenced list, never both",
    ),
    _Invariant(
        id="multiclass_skill_proficiency_choice.from.at-most-one",
        locus="fact:multiclass_skill_proficiency_choice",
        field="from_skills+from_reference",
        rule="a printed skill list or a referenced list, never both",
    ),
    _Invariant(
        id="damage_term.type.exactly-one",
        locus=_shape_locus(DamageTerm),
        field="damage_type+damage_type_by_choice",
        rule="exactly one of a printed damage type and a damage-type choice",
    ),
    _Invariant(
        id="multiattack_part.count.exactly-one",
        locus=_shape_locus(MultiattackPart),
        field="count+count_formula",
        rule="exactly one of a printed count and a count formula",
    ),
    _Invariant(
        id="multiattack_part.selection.exactly-one",
        locus=_shape_locus(MultiattackPart),
        field="attack+any_of+uses_one_of",
        rule="exactly one of a named attack, a choice of attacks and a choice of uses",
    ),
    _Invariant(
        id="multiattack_replacement.replaces.exactly-one",
        locus=_shape_locus(MultiattackReplacement),
        field="replaces+replaces_attack+replaces_any",
        rule="exactly one of a count, a named attack and any attack",
    ),
    _Invariant(
        id="save_targets.origin.at-most-one",
        locus=_shape_locus(SaveTargets),
        field="origin+origin_point_within_ft",
        rule="an area anchored on the source or at a chosen point, never both",
    ),
    _Invariant(
        id="tool_selector.exactly-one",
        locus=_shape_locus(ToolSelector),
        field="tool_variants_of+tool_category+any_tool_entry",
        rule="exactly one of a tool's variants, a tool category and any tool",
    ),
    _Invariant(
        id="forced_move.distance.exactly-one",
        locus=_shape_locus(ForcedMove),
        field="distance_ft+distance_ft_up_to",
        rule="exactly one of an exact distance and an up-to distance",
    ),
    _Invariant(
        id="parameterized_hit_points.basis.exactly-one",
        locus=_shape_locus(ParameterizedHitPoints),
        field="per_spell_level+per_spell_level_above+by_size+half_of+base",
        rule="exactly one basis, with a base exactly when the basis scales by level",
    ),
    _Invariant(
        id="weapon_property.ammunition.ammunition-only",
        locus="fact:weapon_property",
        field="ammunition+ammunition_range_normal_feet+ammunition_range_long_feet",
        rule="stated together, exactly for the ammunition property",
    ),
    _Invariant(
        id="weapon_property.unless.two-handed-only",
        locus="fact:weapon_property",
        field="unless",
        rule="stated only for the two-handed property",
    ),
    _Invariant(
        id="nested-value-object.accepted-rules",
        locus="fields:nested-value-objects",
        field="dice|fraction",
        rule="a nested dice expression or rational number is held to its accepted "
        "rules (at least one die; a positive denominator, a non-negative numerator)",
    ),
    *_int_domain_rows(),
)
