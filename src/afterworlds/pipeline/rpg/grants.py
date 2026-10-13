"""Contributing-grant entitlement — CRD Issue 15c.

CRD Issue 2b records grants with their source; it validates identity, not
entitlement. Storage provenance is not entitlement (Codex grant-trust review).
Before an operation uses a recorded grant's number, this module checks the
grant against the exact typed grant authority its source states under the
character's binding (native C5, schema 19):

* the source is one the character holds: its initial class's level-1 traits,
  a later class's multiclass traits, its background or species, a feat it
  holds by an entitled selection, or a class/subclass feature it has gained;
* the source's typed grant or choice admits the granted value, and the number
  of grants taken from one choice stays within its stated count (per gain);
* an ability adjustment's amounts form one of its rule's patterns, over
  admitted (and, where stated, distinct) abilities, and its cap is the typed
  ``maximum_score`` — never a recorded value or a default;
* Expertise comes from an expertise source, on a skill the character is
  proficient in by a separate valid grant, never twice for one skill
  (``glossary.expertise``).

A grant whose source states no typed grant is ``MISSING_AUTHORITY``; one its
source does not entitle is ``INVALID_SELECTION``; state the check needs and the
character lacks is ``MISSING_STATE``. Full character-build legality is out of
scope (#191): only grants an operation consumes are validated.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import permutations

from afterworlds.ingestion.mechanical.representation import (
    AbilityIncreaseChoiceFact,
    AbilityIncreaseRuleFact,
    AbilityScore,
    ComponentReference,
    ExpertiseChoiceFact,
    ExpertiseRuleFact,
    FeatChoiceFact,
    FeatGrantFact,
    FeatPrerequisiteFact,
    GrantContext,
    MulticlassProficiencyGrantFact,
    MulticlassSkillProficiencyChoiceFact,
    SavingThrowProficiencyGrantFact,
    Skill,
    SkillProficiencyChoiceFact,
    SkillProficiencyGrantFact,
    ToolEntryFact,
    ToolProficiencyChoiceFact,
    ToolProficiencyGrantFact,
    ToolSelector,
)
from afterworlds.models.dnd5e_state import (
    AbilityAdjustment,
    ChoiceRecord,
    Dnd5eCharacterState,
    FeatSelection,
    GrantSource,
    OptionChoice,
    RecordChoice,
    SkillGrant,
    ToolGrant,
    VocabularyChoice,
)
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.services.dnd5e_state.authority import AuthorityIndex

__all__ = [
    "EXPERTISE_RULE",
    "ability_score",
    "save_proficiency",
    "skill_proficiency",
    "tool_proficiency",
]

#: The rule component every Expertise grant is checked against.
EXPERTISE_RULE = ("glossary.expertise", "gaining_expertise")


def _invalid(detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(RefusalKind.INVALID_SELECTION, detail)


def _missing(detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(RefusalKind.MISSING_AUTHORITY, detail)


def _where(source: GrantSource) -> str:
    return f"{source.record_key}/{source.component_key or '-'}"


def _facts(
    index: AuthorityIndex, source: GrantSource, state: Dnd5eCharacterState
) -> list[object]:
    """The typed facts *source* states for this character: its direct facts,
    plus the facts of the option the character's linked choice selected."""
    if source.component_key is None:
        raise _invalid(f"{source.record_key} names no granting component")
    component = index.component(source.record_key, source.component_key)
    if component is None:
        raise _missing(f"{_where(source)} is absent from the binding")
    facts: list[object] = [f.fact for f in component.facts]
    if component.options:
        chosen = _chosen_options(state, source)
        facts += [
            f.fact
            for o in component.options
            if o.semantic_key in chosen
            for f in o.facts
        ]
    return facts


def _linked(state: Dnd5eCharacterState, source: GrantSource) -> ChoiceRecord | None:
    """The choice a grant cites, which must be a choice made under the same
    source: a ``choice_id`` never authorizes another source's grant."""
    if source.choice_id is None:
        return None
    linked = {c.choice_id: c for c in state.choices or ()}.get(source.choice_id)
    if linked is None:
        raise _invalid(f"{_where(source)} cites unrecorded choice {source.choice_id!r}")
    if (linked.source.record_key, linked.source.component_key) != (
        source.record_key,
        source.component_key,
    ):
        raise _invalid(
            f"{_where(source)} cites choice {source.choice_id!r}, which was made "
            f"under {_where(linked.source)}"
        )
    return linked


def _chosen_options(state: Dnd5eCharacterState, source: GrantSource) -> set[str]:
    linked = _linked(state, source)
    if linked is None:
        return set()
    return {s.option_key for s in linked.selected if isinstance(s, OptionChoice)}


def _selected(
    state: Dnd5eCharacterState, source: GrantSource, vocabulary: str
) -> set[str] | None:
    """The values of *vocabulary* the linked choice selected; ``None`` when the
    grant cites no choice."""
    linked = _linked(state, source)
    if linked is None:
        return None
    return {
        s.value
        for s in linked.selected
        if isinstance(s, VocabularyChoice) and s.vocabulary == vocabulary
    }


def _require_selected(
    state: Dnd5eCharacterState, source: GrantSource, vocabulary: str, value: str
) -> None:
    """A grant citing a choice must grant what that choice selected."""
    selected = _selected(state, source, vocabulary)
    if selected is not None and value not in selected:
        raise _invalid(
            f"{_where(source)} grants {value}, but its choice "
            f"{source.choice_id!r} selected {sorted(selected) or 'no ' + vocabulary}"
        )


# ---------------------------------------------------------------------------
# Held sources
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Classes:
    levels: dict[str, int]
    initial: str
    subclasses: dict[str, str]
    total: int


def _classes(state: Dnd5eCharacterState) -> _Classes:
    classes = state.classes
    if not classes:
        raise AdjudicationRefusal(
            RefusalKind.MISSING_STATE, "the character records no class"
        )
    if state.level_history:
        initial = state.level_history[0]
    elif len(classes) == 1:
        initial = classes[0].class_record_key
    else:
        raise AdjudicationRefusal(
            RefusalKind.MISSING_STATE,
            "a multiclass character's level history is not recorded, so its "
            "initial class (and level-1 grants) cannot be established",
        )
    return _Classes(
        levels={c.class_record_key: c.level for c in classes},
        initial=initial,
        subclasses={
            c.subclass_record_key: c.class_record_key
            for c in classes
            if c.subclass_record_key
        },
        total=sum(c.level for c in classes),
    )


def _gains(index: AuthorityIndex, classes: _Classes, entitlement_key: str) -> int:
    """How many times the character has gained *entitlement_key* by level."""
    return sum(
        1
        for class_key, level in classes.levels.items()
        for entry in index.progression(class_key)
        if entry.entitlement_key == entitlement_key and entry.level <= level
    )


def _feat_prerequisite(
    index: AuthorityIndex, feat_key: str
) -> FeatPrerequisiteFact | None:
    record = index.record(feat_key)
    if record is None:
        raise _missing(f"{feat_key} is absent from the binding")
    found = [
        f.fact
        for c in record.components
        for f in c.facts
        if isinstance(f.fact, FeatPrerequisiteFact)
    ]
    return found[0] if found else None


def _feat_entitled(
    index: AuthorityIndex,
    state: Dnd5eCharacterState,
    classes: _Classes,
    feat_key: str,
) -> list[FeatSelection]:
    """The character's selections of *feat_key*, each checked against the
    source that granted it and the feat's typed prerequisites."""
    selections = [f for f in state.feats or () if f.feat_record_key == feat_key]
    if not selections:
        raise _invalid(f"the character holds no selection of {feat_key}")
    prerequisite = _feat_prerequisite(index, feat_key)
    for selection in selections:
        _check_feat_source(index, state, classes, selection, prerequisite)
        if prerequisite is None:
            continue
        if (
            prerequisite.minimum_character_level is not None
            and classes.total < prerequisite.minimum_character_level
        ):
            raise _invalid(
                f"{feat_key} requires character level "
                f"{prerequisite.minimum_character_level}; the character is level "
                f"{classes.total}"
            )
        minimum = prerequisite.minimum_ability_score
        # ponytail: base scores only; a score met only after increases refuses
        # rather than reconstructing when each was gained.
        if (
            minimum is not None
            and state.ability_scores is not None
            and not any(
                getattr(state.ability_scores, a.value) >= minimum.score
                for a in minimum.any_of
            )
        ):
            raise AdjudicationRefusal(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{feat_key} requires "
                f"{' or '.join(a.value for a in minimum.any_of)} "
                f"{minimum.score}+, which the base scores do not meet; when "
                "increases were gained is not recorded",
            )
        if prerequisite.requires_feature is not None:
            raise AdjudicationRefusal(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{feat_key}'s {prerequisite.requires_feature.value} prerequisite "
                "is not validated here",
            )
    return selections


def _check_feat_source(
    index: AuthorityIndex,
    state: Dnd5eCharacterState,
    classes: _Classes,
    selection: FeatSelection,
    prerequisite: FeatPrerequisiteFact | None,
) -> None:
    source = selection.source
    feat = selection.feat_record_key
    facts = _facts(index, source, state)
    if any(isinstance(f, FeatGrantFact) and f.feat == feat for f in facts):
        _require_held(index, state, classes, source)
        return
    for choice in (f for f in facts if isinstance(f, FeatChoiceFact)):
        in_category = prerequisite is None or (
            choice.category is None or choice.category is prerequisite.category
        )
        admits = (
            choice.named_feat == feat
            or (
                choice.named_feat is None
                and choice.category is not None
                and in_category
            )
            # "or another feat of your choice for which you qualify": the
            # feat's own typed prerequisite is then checked by the caller.
            or (bool(choice.or_any_feat_whose_prerequisites_are_met) and in_category)
        )
        if not admits:
            continue
        if choice.named_feat != feat and prerequisite is None:
            # Origin and Fighting Style feats state their category in prose
            # only, so eligibility under a category or "any feat you qualify
            # for" choice cannot be certified from typed authority.
            raise _missing(
                f"{feat} states no typed category or prerequisite, so its "
                f"eligibility under {_where(source)} cannot be certified"
            )
        _require_held(index, state, classes, source)
        allowed = choice.count
        if choice.gain_levels is not None:
            gains = _gains(index, classes, choice.gain_levels.entitlement_key)
            allowed = gains * (choice.count_per_gain or 1)
        taken = sum(
            1
            for f in state.feats or ()
            if (f.source.record_key, f.source.component_key)
            == (source.record_key, source.component_key)
        )
        if allowed is not None and taken > allowed:
            raise _invalid(
                f"{_where(source)} entitles {allowed} feat selection(s); the "
                f"character records {taken}"
            )
        return
    if not any(isinstance(f, (FeatGrantFact, FeatChoiceFact)) for f in facts):
        raise _missing(f"{_where(source)} states no typed feat grant or choice")
    raise _invalid(f"{_where(source)} does not grant {feat}")


def _require_held(
    index: AuthorityIndex,
    state: Dnd5eCharacterState,
    classes: _Classes,
    source: GrantSource,
    *,
    context: GrantContext | None = None,
    multiclass: bool = False,
) -> None:
    """Refuse unless the character holds the record *source* names."""
    key = source.record_key
    if multiclass:
        class_key = key.removesuffix(".as_a_multiclass_character")
        if class_key not in classes.levels or class_key == classes.initial:
            raise _invalid(
                f"{key} applies only to a class taken after the first; "
                f"{class_key} is not one"
            )
        return
    if context is GrantContext.LEVEL_1_CHARACTER:
        if key != classes.initial:
            raise _invalid(
                f"{_where(source)} is granted to a level-1 {key} only; the "
                f"character's initial class is {classes.initial}"
            )
        return
    if key in classes.levels or key in classes.subclasses:
        return
    origins = {o.record_key for o in (state.species, state.background) if o}
    if key in origins:
        return
    if any(f.feat_record_key == key for f in state.feats or ()):
        _feat_entitled(index, state, classes, key)
        return
    if _gains(index, classes, key) > 0:
        return
    raise _invalid(f"the character does not hold {key}, the source of this grant")


def _instances(
    index: AuthorityIndex,
    state: Dnd5eCharacterState,
    classes: _Classes,
    source: GrantSource,
) -> int:
    """How many times the character earned *source*'s grant: once per valid
    selection of a feat, once for any other held source."""
    if any(f.feat_record_key == source.record_key for f in state.feats or ()):
        return len(_feat_entitled(index, state, classes, source.record_key))
    return 1


# ---------------------------------------------------------------------------
# Ability scores
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _IncreaseRule:
    abilities: frozenset[AbilityScore]
    any_ability: bool
    patterns: frozenset[tuple[int, ...]]
    distinct: bool
    maximum: int


def ability_score(
    index: AuthorityIndex, state: Dnd5eCharacterState, ability: AbilityScore
) -> tuple[int, tuple[str, ...]]:
    """The validated adjusted score and the sources applied to it.

    Every adjustment the character records is validated, not only those for
    *ability*: a pattern spans abilities (+2/+1), so one invalid half voids
    the whole increase.
    """
    if state.ability_scores is None:
        raise AdjudicationRefusal(RefusalKind.MISSING_STATE, "no ability scores")
    classes = _classes(state)
    score: int = getattr(state.ability_scores, ability.value)
    applied: list[tuple[int, str, int]] = []  # (cap, source, amount)
    groups = _adjustment_groups(state.ability_adjustments or ())
    _bind_to_earned(index, state, classes, groups)
    for adjustments in groups.values():
        source = adjustments[0].source
        _linked(state, source)
        rule = _increase_rule(index, state, classes, source)
        amounts = tuple(sorted((a.amount for a in adjustments), reverse=True))
        if amounts not in rule.patterns:
            raise _invalid(
                f"{_where(source)}: increases {list(amounts)} are not one of its "
                f"patterns {sorted(list(p) for p in rule.patterns)}"
            )
        abilities = [a.ability for a in adjustments]
        selected = _selected(state, source, "ability")
        if selected is not None and selected != {a.value for a in abilities}:
            raise _invalid(
                f"{_where(source)}: increases to "
                f"{sorted(a.value for a in abilities)} disagree with choice "
                f"{source.choice_id!r}, which selected {sorted(selected)}"
            )
        if rule.distinct and len(set(abilities)) != len(abilities):
            raise _invalid(
                f"{_where(source)}: the increases must be to different abilities"
            )
        for a in adjustments:
            if not rule.any_ability and a.ability not in rule.abilities:
                raise _invalid(f"{_where(source)} cannot increase {a.ability.value}")
            if a.maximum is not None and a.maximum != rule.maximum:
                raise _invalid(
                    f"{_where(source)}: recorded maximum {a.maximum} differs from "
                    f"the source's {rule.maximum}"
                )
            if a.ability is ability:
                applied.append((rule.maximum, _where(source), a.amount))
    return _order_independent(score, applied, ability), tuple(w for _, w, _ in applied)


def _order_independent(
    base: int, applied: list[tuple[int, str, int]], ability: AbilityScore
) -> int:
    """The score after *applied* increases, when it does not depend on the
    order they were gained in; a refusal when it does.

    Each increase raises the score but not past its own cap. Within one cap the
    order cannot matter; across caps it can (a +1 to 30 before or after a +2
    to 20, from 19). CRD Issue 2b records no acquisition order, so the result
    is taken only if every order of the cap groups agrees.
    """
    by_cap: dict[int, int] = defaultdict(int)
    for cap, _, amount in applied:
        by_cap[cap] += amount
    results = set()
    for order in permutations(sorted(by_cap)):
        score = base
        for cap in order:
            score = max(score, min(score + by_cap[cap], cap))
        results.add(score)
    if len(results) != 1:
        raise AdjudicationRefusal(
            RefusalKind.MISSING_STATE,
            f"{ability.value}: the increases' caps make the score depend on the "
            f"order they were gained ({sorted(results)}), which is not recorded",
        )
    return results.pop()


def _adjustment_groups(
    adjustments: Iterable[AbilityAdjustment],
) -> dict[tuple[str, str | None, str | None], list[AbilityAdjustment]]:
    """One group per increase taken: a source, and its linked choice."""
    groups: dict[tuple[str, str | None, str | None], list[AbilityAdjustment]] = (
        defaultdict(list)
    )
    for a in adjustments:
        if a.amount <= 0:
            raise AdjudicationRefusal(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{_where(a.source)}: an ability decrease is not executable here",
            )
        s = a.source
        groups[(s.record_key, s.component_key, s.choice_id)].append(a)
    return groups


def _bind_to_earned(
    index: AuthorityIndex,
    state: Dnd5eCharacterState,
    classes: _Classes,
    groups: dict[tuple[str, str | None, str | None], list[AbilityAdjustment]],
) -> None:
    """Each increase group is one earned increase. A source earns one per
    valid selection of a feat (and the group must cite that selection's
    choice), and one for any other held source; no earned increase is taken
    twice under different choice ids."""
    by_source: dict[tuple[str, str | None], list[str | None]] = defaultdict(list)
    for record, component, choice_id in groups:
        by_source[(record, component)].append(choice_id)
    for (record, component), choice_ids in by_source.items():
        source = GrantSource(record_key=record, component_key=component)
        earned = _instances(index, state, classes, source)
        if len(choice_ids) > earned:
            raise _invalid(
                f"{_where(source)} was earned {earned} time(s); the character "
                f"records {len(choice_ids)} increases from it"
            )
        selections = [f for f in state.feats or () if f.feat_record_key == record]
        if not selections:
            continue
        used: set[int] = set()
        for choice_id in choice_ids:
            owner = next(
                (
                    i
                    for i, sel in enumerate(selections)
                    if i not in used
                    and (
                        choice_id in sel.choice_ids
                        or (choice_id is None and len(selections) == 1)
                    )
                ),
                None,
            )
            if owner is None:
                raise _invalid(
                    f"{_where(source)}: increase {choice_id!r} cites no selection "
                    f"of {record} it was earned by"
                )
            used.add(owner)


def _increase_rule(
    index: AuthorityIndex,
    state: Dnd5eCharacterState,
    classes: _Classes,
    source: GrantSource,
) -> _IncreaseRule:
    facts = _facts(index, source, state)
    choices = [f for f in facts if isinstance(f, AbilityIncreaseChoiceFact)]
    if len(choices) != 1:
        raise _missing(f"{_where(source)} states no single typed ability increase")
    choice = choices[0]
    _require_held(index, state, classes, source)
    patterns = choice.patterns
    distinct = bool(choice.distinct_abilities)
    maximum = choice.maximum_score
    if choice.rule is not None:
        ref = index.component(choice.rule.record_key, choice.rule.component_key)
        rules = [
            f.fact
            for f in (ref.facts if ref else ())
            if isinstance(f.fact, AbilityIncreaseRuleFact)
        ]
        if len(rules) != 1:
            raise _missing(f"{_where(source)}'s increase rule is absent")
        patterns = rules[0].patterns
        distinct = rules[0].distinct_abilities
        maximum = rules[0].maximum_score
    if not patterns or maximum is None:
        raise _missing(f"{_where(source)} states no increase pattern or maximum")
    return _IncreaseRule(
        abilities=frozenset(choice.abilities),
        any_ability=bool(choice.any_ability),
        patterns=frozenset(tuple(sorted(p, reverse=True)) for p in patterns),
        distinct=distinct,
        maximum=maximum,
    )


# ---------------------------------------------------------------------------
# Skills and Expertise
# ---------------------------------------------------------------------------


def _skill_options(
    index: AuthorityIndex,
    from_skills: tuple[Skill, ...],
    reference: ComponentReference | None,
) -> set[Skill]:
    options = set(from_skills)
    if reference is not None:
        ref = index.component(reference.record_key, reference.component_key)
        for f in ref.facts if ref else ():
            if isinstance(f.fact, SkillProficiencyChoiceFact):
                options |= set(f.fact.from_skills)
    return options


#: One pick a grant spends from a choice: the choice's key and its allowance
#: (count per earned instance, times the instances); ``None`` for a fixed grant.
_Pick = tuple[tuple[str, str | None, str], int] | None


def _pick(
    index: AuthorityIndex,
    state: Dnd5eCharacterState,
    classes: _Classes,
    source: GrantSource,
    kind: str,
    count: int,
) -> _Pick:
    allowance = count * _instances(index, state, classes, source)
    return (source.record_key, source.component_key, kind), allowance


def _skill_grant_count(
    index: AuthorityIndex,
    state: Dnd5eCharacterState,
    classes: _Classes,
    grant: SkillGrant,
) -> _Pick:
    """Validate a proficiency grant; return the pick it spends."""
    source = grant.source
    _require_selected(state, source, "skill", grant.skill.value)
    facts = _facts(index, source, state)
    for fact in facts:
        if isinstance(fact, SkillProficiencyGrantFact) and grant.skill in fact.skills:
            _require_held(index, state, classes, source)
            return None
    for fact in facts:
        if isinstance(fact, SkillProficiencyChoiceFact) and grant.skill in (
            _skill_options(index, fact.from_skills, fact.from_reference)
        ):
            _require_held(index, state, classes, source, context=fact.context)
            e = fact.eligibility
            if e is not None and (
                classes.subclasses.get(e.subclass_key) != e.class_key
                or classes.levels.get(e.class_key, 0) < e.minimum_class_level
            ):
                raise _invalid(
                    f"{_where(source)} requires {e.subclass_key} at "
                    f"{e.class_key} level {e.minimum_class_level}"
                )
            return _pick(index, state, classes, source, "skill", fact.count)
        if isinstance(fact, MulticlassSkillProficiencyChoiceFact) and grant.skill in (
            _skill_options(index, fact.from_skills, fact.from_reference)
        ):
            _require_held(index, state, classes, source, multiclass=True)
            return (source.record_key, source.component_key, "multiclass"), fact.count
    granting = (
        SkillProficiencyGrantFact,
        SkillProficiencyChoiceFact,
        MulticlassSkillProficiencyChoiceFact,
    )
    if not any(isinstance(f, granting) for f in facts):
        raise _missing(f"{_where(source)} states no typed skill grant")
    raise _invalid(f"{_where(source)} does not grant {grant.skill.value}")


def _within_counts(picks: Iterable[_Pick]) -> None:
    taken: Counter[tuple[str, str | None, str]] = Counter()
    limits: dict[tuple[str, str | None, str], int] = {}
    for pick in picks:
        if pick is None:
            continue
        key, allowance = pick
        taken[key] += 1
        limits[key] = allowance
    for key, n in taken.items():
        if n > limits[key]:
            raise _invalid(
                f"{key[0]}/{key[1]} entitles {limits[key]} choice(s); the "
                f"character records {n}"
            )


def _expertise_rule(index: AuthorityIndex) -> ExpertiseRuleFact:
    component = index.component(*EXPERTISE_RULE)
    rules = [
        f.fact
        for f in (component.facts if component else ())
        if isinstance(f.fact, ExpertiseRuleFact)
    ]
    if len(rules) != 1:
        raise _missing("glossary.expertise states no typed Expertise rule")
    return rules[0]


def _check_expertise_source(
    index: AuthorityIndex,
    state: Dnd5eCharacterState,
    classes: _Classes,
    grant: SkillGrant,
    all_expert: list[SkillGrant],
) -> None:
    source = grant.source
    facts = [
        f for f in _facts(index, source, state) if isinstance(f, ExpertiseChoiceFact)
    ]
    if len(facts) != 1:
        raise _invalid(f"{_where(source)} grants no Expertise")
    fact = facts[0]
    if fact.from_skills and grant.skill not in fact.from_skills:
        raise _invalid(f"{_where(source)} cannot give Expertise in {grant.skill.value}")
    gains = _gains(index, classes, fact.gain_levels.entitlement_key)
    if gains == 0:
        raise _invalid(
            f"the character has not gained {fact.gain_levels.entitlement_key}"
        )
    taken = sum(
        1
        for g in all_expert
        if (g.source.record_key, g.source.component_key)
        == (source.record_key, source.component_key)
    )
    if taken > gains * fact.count_per_gain:
        raise _invalid(
            f"{_where(source)} entitles {gains * fact.count_per_gain} Expertise "
            f"choice(s); the character records {taken}"
        )


def skill_proficiency(
    index: AuthorityIndex, state: Dnd5eCharacterState, skill: Skill
) -> tuple[int, str | None]:
    """The proficiency-bonus multiplier for *skill* (0, 1, or Expertise's) and
    the Expertise source, after validating the grants it depends on.

    Count limits are checked across every recorded proficiency grant, since a
    choice's other picks consume the same allowance.
    """
    grants = state.skill_proficiencies or ()
    classes = _classes(state)
    plain = [g for g in grants if not g.expertise]
    expert = [g for g in grants if g.expertise]
    _proficiency_picks(index, state, classes)
    proficient = any(g.skill is skill for g in plain)
    mine = [g for g in expert if g.skill is skill]
    if not mine:
        return (1 if proficient else 0), None
    rule = _expertise_rule(index)
    if len(mine) > 1 and rule.no_duplicate:
        raise _invalid(f"{skill.value} records Expertise more than once")
    if rule.requires_skill_proficiency and not proficient:
        raise _invalid(
            f"Expertise in {skill.value} requires proficiency in it by a "
            "separate grant"
        )
    _check_expertise_source(index, state, classes, mine[0], expert)
    return rule.proficiency_bonus_multiplier, _where(mine[0].source)


# ---------------------------------------------------------------------------
# Saving throws and tools
# ---------------------------------------------------------------------------


def save_proficiency(
    index: AuthorityIndex, state: Dnd5eCharacterState, ability: AbilityScore
) -> bool:
    """Whether the character is validly proficient in *ability*'s saves."""
    classes = _classes(state)
    proficient = False
    for grant in state.saving_throw_proficiencies or ():
        facts = _facts(index, grant.source, state)
        admitted = False
        for fact in facts:
            if (
                isinstance(fact, SavingThrowProficiencyGrantFact)
                and grant.ability in fact.abilities
            ):
                _require_held(index, state, classes, grant.source, context=fact.context)
                if fact.gain_levels is not None and not _gains(
                    index, classes, fact.gain_levels.entitlement_key
                ):
                    raise _invalid(
                        "the character has not gained "
                        f"{fact.gain_levels.entitlement_key}"
                    )
                admitted = True
            if (
                isinstance(fact, MulticlassProficiencyGrantFact)
                and grant.ability in fact.saving_throws
            ):
                _require_held(index, state, classes, grant.source, multiclass=True)
                admitted = True
        if not admitted:
            granting = (SavingThrowProficiencyGrantFact, MulticlassProficiencyGrantFact)
            if not any(isinstance(f, granting) for f in facts):
                raise _missing(
                    f"{_where(grant.source)} states no typed saving-throw grant"
                )
            raise _invalid(
                f"{_where(grant.source)} does not grant {grant.ability.value} saves"
            )
        proficient |= grant.ability is ability
    return proficient


def _tool_matches(
    index: AuthorityIndex, selector: ToolSelector, record: str, component: str | None
) -> bool:
    if selector.any_tool_entry:
        return True
    if selector.tool_variants_of is not None:
        ref = selector.tool_variants_of
        return (record, component) == (ref.record_key, ref.component_key)
    if selector.tool_category is not None and component is not None:
        c = index.component(record, component)
        facts = [
            *(c.facts if c else ()),
            *(f for o in (c.options if c else ()) for f in o.facts),
        ]
        return any(
            isinstance(f.fact, ToolEntryFact)
            and f.fact.category is selector.tool_category
            for f in facts
        )
    return False


def _tool_grant_count(
    index: AuthorityIndex,
    state: Dnd5eCharacterState,
    classes: _Classes,
    grant: ToolGrant,
) -> _Pick:
    """Validate a tool grant; return the pick it spends. A skill choice that
    may be spent on tools instead (Skilled's ``or_tools``) shares one
    allowance with its skill picks."""
    source = grant.source
    target = (grant.record_key, grant.component_key)
    linked = _linked(state, source)
    if linked is not None and not any(
        (isinstance(s, RecordChoice) and s.record_key == grant.record_key)
        or (isinstance(s, OptionChoice) and s.option_key == grant.component_key)
        for s in linked.selected
    ):
        raise _invalid(
            f"{_where(source)} grants {target[0]}/{target[1]}, but its choice "
            f"{source.choice_id!r} did not select it"
        )
    facts = _facts(index, source, state)
    for fact in facts:
        if isinstance(fact, ToolProficiencyGrantFact) and any(
            (t.record_key, t.component_key) == target for t in fact.tools
        ):
            _require_held(index, state, classes, source, context=fact.context)
            return None
        if isinstance(fact, ToolProficiencyChoiceFact) and any(
            _tool_matches(index, s, *target) for s in fact.options
        ):
            _require_held(index, state, classes, source, context=fact.context)
            return _pick(index, state, classes, source, "tool", fact.count)
        if (
            isinstance(fact, SkillProficiencyChoiceFact)
            and fact.or_tools is not None
            and _tool_matches(index, fact.or_tools, *target)
        ):
            _require_held(index, state, classes, source, context=fact.context)
            return _pick(index, state, classes, source, "skill", fact.count)
        if isinstance(fact, MulticlassProficiencyGrantFact):
            if any((t.record_key, t.component_key) == target for t in fact.tool_grant):
                _require_held(index, state, classes, source, multiclass=True)
                return None
            if fact.tool_choice is not None and any(
                _tool_matches(index, s, *target) for s in fact.tool_choice.options
            ):
                _require_held(index, state, classes, source, multiclass=True)
                key = (source.record_key, source.component_key, "multiclass-tool")
                return key, fact.tool_choice.count
    granting = (
        ToolProficiencyGrantFact,
        ToolProficiencyChoiceFact,
        MulticlassProficiencyGrantFact,
        SkillProficiencyChoiceFact,
    )
    if not any(isinstance(f, granting) for f in facts):
        raise _missing(f"{_where(source)} states no typed tool grant")
    raise _invalid(f"{_where(source)} does not grant {target[0]}/{target[1]}")


def _proficiency_picks(
    index: AuthorityIndex, state: Dnd5eCharacterState, classes: _Classes
) -> None:
    """Validate every skill-proficiency and tool grant and their shared choice
    allowances: a choice's picks are counted across both collections."""
    _within_counts(
        [
            *(
                _skill_grant_count(index, state, classes, g)
                for g in state.skill_proficiencies or ()
                if not g.expertise
            ),
            *(
                _tool_grant_count(index, state, classes, g)
                for g in state.tool_proficiencies or ()
            ),
        ]
    )


def tool_proficiency(
    index: AuthorityIndex, state: Dnd5eCharacterState, record: str, component: str
) -> bool:
    """Whether the character is validly proficient with the tool at
    (*record*, *component*). Tool Expertise has no typed source and refuses."""
    classes = _classes(state)
    for grant in state.tool_proficiencies or ():
        if grant.expertise:
            raise AdjudicationRefusal(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"tool Expertise ({_where(grant.source)}) has no typed source "
                "authority",
            )
    _proficiency_picks(index, state, classes)
    return any(
        (g.record_key, g.component_key) == (record, component)
        for g in state.tool_proficiencies or ()
    )
