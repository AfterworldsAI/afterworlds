"""Source-fixed-DC ability checks — the CRD Issue 15c executable check path.

:func:`prepare` validates a proposal completely and derives every number from
exact typed authority and recorded state, before any die is rolled; it raises
:class:`~afterworlds.pipeline.rpg.capability.AdjudicationRefusal` otherwise.
:func:`roll` then rolls the prepared check. Nothing here writes state.

Numbers and their sources:

* the DC, ability and skill: the admitted check identity's typed
  ``ability_check`` fact (``dc_kind`` fixed);
* the ability modifier: the base score plus the recorded adjustments, each
  validated against its source's typed increase (pattern, abilities, cap) by
  :mod:`.grants`, then ``(score - 10) // 2`` (``play.six_abilities``);
* the Proficiency Bonus: the typed ``proficiency_bonus_band`` for the
  character's total level, added under the typed skill
  ``proficiency_application`` when a validated grant gives the skill, and
  multiplied by the typed Expertise rule for a validated Expertise grant;
* Advantage/Disadvantage: typed ``advantage`` facts on the subject's recorded
  conditions; both present cancel (``play.d20_tests``).

Natural 1 and 20 have no special effect on an ability check. Anything that
could contribute to the roll but is not executed here — an active effect, a
contributing class feature, species trait or feat, an equipped or attuned
magic item, worn armor (its rules are held on candidate C1-C), Exhaustion, a
magical contagion, or a condition fact whose applicability needs judgement —
refuses the check rather than being ignored.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    SKILL_ABILITY,
    AbilityCheckFact,
    AbilityScore,
    AdvantageFact,
    AdvantageState,
    AutomaticOutcomeFact,
    ConditionKind,
    DcKind,
    Difficulty,
    DifficultyBandFact,
    InitiativeRollFact,
    ProficiencyApplicationFact,
    ProficiencyBonusBandFact,
    ProficiencyKind,
    RecordKind,
    RollActor,
    RollContext,
    Skill,
    ToolActivity,
    ToolActivityFact,
    ToolEntryFact,
    ToolVariantsFact,
)
from afterworlds.models.dnd5e_state import Dnd5eCharacterState
from afterworlds.models.rpg import RollProposal
from afterworlds.pipeline.rpg.capability import (
    FIXED_DC_CHECKS,
    TOOL_COMPONENTS,
    AdjudicationRefusal,
    Certificate,
    Operation,
    RefusalKind,
    certify,
)
from afterworlds.pipeline.rpg.dice import DiceService
from afterworlds.pipeline.rpg.grants import (
    ability_score,
    skill_proficiency,
    tool_proficiency,
)
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from afterworlds.services.dnd5e_state.turn import TurnCharacter

__all__ = ["CHECK_OPERATIONS", "PreparedCheck", "RolledCheck", "prepare", "roll"]


_PB_COMPONENT = ("play.proficiency.proficiency_bonus", "proficiency_bonus_bands")
_SKILL_PROFICIENCY = ("play.proficiency.skill_proficiencies", "skill_proficiency")
_TOOL_PROFICIENCY = ("play.proficiency", "tool_proficiency")

#: Class features, species traits and feats that can change the owner's own
#: ability check. Compiled from the pinned source: a phrase scan of
#: ``classes.md`` "Level N" features, species traits and ``feats.md`` for
#: ability-check, saving-throw, D20 Test, Initiative and reroll language gave a
#: superset (recorded in the 15c review notes); this is its ability-check
#: subset, read entry by entry. Contributors to saves, Initiative or other
#: creatures' rolls are compiled with the operations that roll them. A
#: character holding one of these has its checks refused until the contributor
#: is executable.
CHECK_CONTRIBUTING_FEATURES: frozenset[str] = frozenset(
    {
        "classes.barbarian.rage",
        "classes.barbarian.primal_knowledge",
        "classes.barbarian.indomitable_might",
        "classes.bard.jack_of_all_trades",
        "classes.bard.college_of_lore.peerless_skill",
        "classes.druid.wild_shape",
        "classes.fighter.tactical_mind",
        "classes.fighter.champion.remarkable_athlete",
        "classes.rogue.reliable_talent",
        "classes.rogue.stroke_of_luck",
        "classes.warlock.fiend_patron.dark_ones_own_luck",
    }
)
CHECK_CONTRIBUTING_TRAITS: frozenset[tuple[str, str]] = frozenset(
    {
        ("character_origins.goliath", "large_form"),
        ("character_origins.goliath", "powerful_build"),
        ("character_origins.halfling", "luck"),
    }
)


#: Features and feats that change the owner's Initiative roll beyond what an
#: ability-check contributor does (``classes.md`` Feral Instinct, Remarkable
#: Athlete; ``feats.md`` Alert's Initiative Proficiency). Triggered side
#: effects of rolling Initiative (Rage, Bardic Inspiration, Focus or Wild Shape
#: regains) change no number of the roll and are not executed here.
INITIATIVE_CONTRIBUTORS: frozenset[str] = frozenset(
    {
        "classes.barbarian.feral_instinct",
        "classes.fighter.champion.remarkable_athlete",
        "feats.alert",
    }
)


@dataclass(frozen=True)
class PreparedCheck:
    """A fully validated check: every input fixed, no die rolled yet.

    ``dc`` is ``None`` only for Initiative, whose admitted outcome is
    ``undetermined`` (#191 AC5).
    """

    operation: Operation
    identity: str
    ability: AbilityScore
    skill: Skill | None
    dc: int | None
    dc_source: str | None
    ability_modifier: int
    proficiency: int
    advantage_sources: tuple[str, ...]
    disadvantage_sources: tuple[str, ...]
    certificate: Certificate
    breakdown: dict[str, int] = field(default_factory=dict)

    @property
    def expression(self) -> str:
        adv, dis = bool(self.advantage_sources), bool(self.disadvantage_sources)
        if adv and not dis:
            return "2d20kh1"
        if dis and not adv:
            return "2d20kl1"
        return "1d20"

    @property
    def modifier(self) -> int:
        return self.ability_modifier + self.proficiency


@dataclass(frozen=True)
class RolledCheck:
    prepared: PreparedCheck
    raw_rolls: tuple[int, ...]
    chosen: int

    @property
    def total(self) -> int:
        return self.chosen + self.prepared.modifier

    @property
    def outcome(self) -> str:
        if self.prepared.dc is None:
            return "undetermined"
        return "success" if self.total >= self.prepared.dc else "failure"

    def provenance_json(self) -> str:
        p = self.prepared
        return json.dumps(
            {
                "visible_total": p.modifier,
                "breakdown": p.breakdown,
                "operation": p.operation.value,
                "check_identity": p.identity,
                "ability": p.ability.value,
                "skill": p.skill.value if p.skill else None,
                "dc_source": p.dc_source,
                "advantage_sources": list(p.advantage_sources),
                "disadvantage_sources": list(p.disadvantage_sources),
                "certificate": p.certificate.as_json(),
            },
            sort_keys=True,
        )


@dataclass(frozen=True)
class _Spec:
    """What the selected source fixes, before character inputs."""

    identity: str
    ability: AbilityScore
    skill: Skill | None
    dc: int | None
    dc_source: str | None
    #: The proficiency that applies, with its typed application component.
    proficiency: str  # "skill" | "tool" | "none"
    contexts: frozenset[RollContext]
    tool: tuple[str, str] | None = None


_CHECK_CONTEXTS = frozenset({RollContext.ABILITY_CHECK, RollContext.D20_TEST})


def _refuse(kind: RefusalKind, detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(kind, detail)


def _operation(proposal: RollProposal) -> Operation:
    if proposal.operation is None:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{proposal.check_label!r} names no roster operation; labels and "
            "tags are never mechanical authority",
        )
    try:
        return Operation(proposal.operation)
    except ValueError:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{proposal.operation!r} is not a roster operation",
        ) from None


def _member[E: StrEnum](vocabulary: type[E], value: str | None, what: str) -> E:
    try:
        return vocabulary(value or "")
    except ValueError:
        raise _refuse(
            RefusalKind.INVALID_SELECTION, f"{value!r} is not a {what}"
        ) from None


def _fixed_check(fact: object, where: str) -> AbilityCheckFact:
    if (
        not isinstance(fact, AbilityCheckFact)
        or fact.dc_kind is not DcKind.FIXED
        or fact.dc_value is None
        or fact.ability is None
        or fact.context is not RollContext.ABILITY_CHECK
    ):
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            f"{where} states no single source-fixed ability check under this "
            "binding",
        )
    return fact


def _fixed_dc_spec(proposal: RollProposal, index: AuthorityIndex) -> _Spec:
    record, _, component = (proposal.check_identity or "").partition("/")
    if (record, component) not in FIXED_DC_CHECKS:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{proposal.check_identity!r} is not an admitted source-fixed check "
            f"identity ({', '.join('/'.join(i) for i in FIXED_DC_CHECKS)})",
        )
    where = f"{record}/{component}"
    found = index.component(record, component)
    facts = [] if found is None else [f.fact for f in found.facts]
    if len(facts) != 1:
        _fixed_check(None, where)
    fact = _fixed_check(facts[0], where)
    assert fact.ability is not None
    return _Spec(
        identity=where,
        ability=AbilityScore(fact.ability),
        skill=Skill(fact.skill) if fact.skill is not None else None,
        dc=fact.dc_value,
        dc_source=where,
        proficiency="skill",
        contexts=_CHECK_CONTEXTS,
    )


def _difficulty_spec(proposal: RollProposal, index: AuthorityIndex) -> _Spec:
    ability = _member(AbilityScore, proposal.ability, "ability")
    skill = (
        _member(Skill, proposal.skill, "skill") if proposal.skill is not None else None
    )
    if skill is not None and SKILL_ABILITY[skill] is not ability:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{skill.value} is governed by {SKILL_ABILITY[skill].value}, not "
            f"{ability.value}",
        )
    difficulty = _member(Difficulty, proposal.difficulty, "difficulty identity")
    table = index.component("play.d20_tests", "typical_dcs")
    bands = [
        f.fact
        for f in (table.facts if table else ())
        if isinstance(f.fact, DifficultyBandFact)
        and f.fact.difficulty is difficulty
        and f.fact.applies_to is RollContext.ABILITY_CHECK
    ]
    if len(bands) != 1:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            f"the Typical DCs state no {difficulty.value} band for ability checks",
        )
    source = f"play.d20_tests/typical_dcs#{difficulty.value}"
    return _Spec(
        identity=source,
        ability=ability,
        skill=skill,
        dc=bands[0].dc,
        dc_source=source,
        proficiency="skill",
        contexts=_CHECK_CONTEXTS,
    )


def _tool_spec(
    proposal: RollProposal, index: AuthorityIndex, character: TurnCharacter
) -> _Spec:
    record, _, component = (proposal.check_identity or "").partition("/")
    if (record, component) not in TOOL_COMPONENTS:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{proposal.check_identity!r} is not a tool of the Tools catalogue",
        )
    activity = _member(ToolActivity, proposal.tool_activity, "tool activity")
    found = index.component(record, component)
    if found is None:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, f"{record}/{component} is absent")
    groups = [("", [f.fact for f in found.facts])] + [
        (o.semantic_key, [f.fact for f in o.facts]) for o in found.options
    ]
    chosen = [
        (key, facts)
        for key, facts in groups
        if any(
            isinstance(f, ToolActivityFact) and f.activity is activity for f in facts
        )
    ]
    if len(chosen) != 1:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{activity.value} is not an activity of {record}/{component}",
        )
    key, facts = chosen[0]
    if any(isinstance(f, ToolVariantsFact) for f in facts):
        raise _refuse(
            RefusalKind.MISSING_STATE,
            f"{record}/{component} is a separate proficiency per kind, and CRD "
            "Issue 2b records no kind for a tool grant or item",
        )
    checks = [f for f in facts if isinstance(f, AbilityCheckFact)]
    where = f"{record}/{component}" + (f"#{key}" if key else "")
    if len(checks) != 1 or not any(isinstance(f, ToolEntryFact) for f in facts):
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, f"{where} states no single tool check"
        )
    fact = _fixed_check(checks[0], where)
    assert fact.ability is not None
    if not any(
        (i.record_key, i.component_key) == (record, component) for i in character.items
    ):
        raise _refuse(
            RefusalKind.MISSING_STATE,
            f"the character holds no {record}/{component} to use",
        )
    return _Spec(
        identity=f"{where}:{activity.value}",
        ability=AbilityScore(fact.ability),
        skill=None,
        dc=fact.dc_value,
        dc_source=where,
        proficiency="tool",
        contexts=_CHECK_CONTEXTS,
        tool=(record, component),
    )


def _initiative_spec(index: AuthorityIndex) -> _Spec:
    found = index.component("play.combat", "initiative_roll")
    rolls = [
        f.fact
        for f in (found.facts if found else ())
        if isinstance(f.fact, InitiativeRollFact)
    ]
    if len(rolls) != 1 or rolls[0].context is not RollContext.ABILITY_CHECK:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            "play.combat/initiative_roll states no typed Initiative roll",
        )
    return _Spec(
        identity="play.combat/initiative_roll",
        ability=AbilityScore(rolls[0].ability),
        skill=None,
        dc=None,
        dc_source=None,
        proficiency="none",
        contexts=_CHECK_CONTEXTS | {RollContext.INITIATIVE},
    )


def _state(character: TurnCharacter) -> Dnd5eCharacterState:
    state = character.stored.state
    missing = [
        name
        for name, value in (
            ("ability_scores", state.ability_scores),
            ("ability_adjustments", state.ability_adjustments),
            ("classes", state.classes),
            ("skill_proficiencies", state.skill_proficiencies),
            ("conditions", state.conditions),
            ("active_effects", state.active_effects),
            ("feats", state.feats),
            ("species", state.species),
        )
        if value is None
    ]
    if missing:
        raise _refuse(
            RefusalKind.MISSING_STATE,
            f"the character records no {', '.join(missing)}",
        )
    return state


def _proficiency_bonus(index: AuthorityIndex, level: int) -> int:
    component = index.component(*_PB_COMPONENT)
    bands = [
        f.fact
        for f in (component.facts if component else ())
        if isinstance(f.fact, ProficiencyBonusBandFact)
    ]
    for band in bands:
        if (band.minimum is None or band.minimum <= level) and level <= band.maximum:
            return band.bonus
    raise _refuse(
        RefusalKind.MISSING_AUTHORITY,
        f"no proficiency-bonus band covers level {level} under this binding",
    )


def _skill_applies(index: AuthorityIndex) -> bool:
    component = index.component(*_SKILL_PROFICIENCY)
    return any(
        isinstance(f.fact, ProficiencyApplicationFact)
        and f.fact.proficiency is ProficiencyKind.SKILL
        and f.fact.roll.context is RollContext.ABILITY_CHECK
        for f in (component.facts if component else ())
    )


def _features(
    state: Dnd5eCharacterState, index: AuthorityIndex, contributors: frozenset[str]
) -> set[str]:
    """Class features the character has gained, by typed progression level.

    A subclass feature has no typed gain level; holding the subclass counts as
    holding it (conservative).
    """
    held: set[str] = set()
    for cl in state.classes or ():
        for entry in index.progression(cl.class_record_key):
            if entry.level <= cl.level:
                held.add(entry.entitlement_key)
        if cl.subclass_record_key:
            prefix = cl.subclass_record_key + "."
            held |= {k for k in contributors if k.startswith(prefix)}
    return held


def _refuse_contributors(
    character: TurnCharacter,
    state: Dnd5eCharacterState,
    index: AuthorityIndex,
    ability: AbilityScore,
    extra: frozenset[str] = frozenset(),
) -> None:
    def unsupported(what: str) -> AdjudicationRefusal:
        return _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{what} can contribute to this check and is not executable here",
        )

    if state.active_effects:
        raise unsupported(f"active effect {state.active_effects[0].source.record_key}")
    contributors = CHECK_CONTRIBUTING_FEATURES | extra
    found = sorted(_features(state, index, contributors) & contributors)
    found += sorted(
        f.feat_record_key
        for f in state.feats or ()
        if f.feat_record_key in contributors
    )
    if found:
        raise unsupported(f"feature or feat {found[0]}")
    assert state.species is not None
    for record, trait in sorted(CHECK_CONTRIBUTING_TRAITS):
        if record == state.species.record_key:
            raise unsupported(f"species trait {record}/{trait}")
    if any(h.kind == "contagion" for h in state.hazards or ()):
        raise unsupported("a magical contagion")
    for item in character.items:
        kind = index.kind(item.record_key)
        if kind is RecordKind.MAGIC_ITEM and (item.equipped or item.attuned_subject_id):
            raise unsupported(f"magic item {item.record_key}")
        worn_armor = (
            item.equipped
            and item.record_key.startswith("equipment.armor.")
            and item.record_key != "equipment.armor.shield"
        )
        if worn_armor and ability in (AbilityScore.STRENGTH, AbilityScore.DEXTERITY):
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY,
                f"worn armor {item.record_key} can impose Disadvantage on this "
                "check; armor rules await candidate C1-C",
            )


def _advantage(
    state: Dnd5eCharacterState,
    index: AuthorityIndex,
    ability: AbilityScore,
    skill: Skill | None,
    contexts: frozenset[RollContext] = _CHECK_CONTEXTS,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    advantage: list[str] = []
    disadvantage: list[str] = []
    for instance in state.conditions or ():
        if instance.condition is ConditionKind.EXHAUSTION:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                "Exhaustion's D20 Test reduction is not executable here",
            )
        record = index.record(f"glossary.{instance.condition.value}")
        if record is None:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY,
                f"condition {instance.condition.value} has no governing record",
            )
        for component in record.components:
            for ef in component.facts:
                fact = ef.fact
                if not isinstance(fact, (AdvantageFact, AutomaticOutcomeFact)):
                    continue
                roll = fact.roll
                if (
                    roll.actor is not RollActor.SUBJECT
                    or roll.context not in contexts
                    or roll.ability not in (None, ability)
                    or roll.skill not in (None, skill)
                ):
                    continue
                where = f"{record.semantic_key}/{component.semantic_key}"
                contextual = (
                    component.handling is not ComponentHandling.STRUCTURED
                    or component.applies_when is not None
                    or ef.qualifier is not None
                )
                if contextual or isinstance(fact, AutomaticOutcomeFact):
                    raise _refuse(
                        RefusalKind.UNSUPPORTED_CAPABILITY,
                        f"{where} can affect this check under circumstances "
                        "that need judgement and is not executable here",
                    )
                if fact.state is AdvantageState.ADVANTAGE:
                    advantage.append(where)
                else:
                    disadvantage.append(where)
    return tuple(advantage), tuple(disadvantage)


def _tool_applies(index: AuthorityIndex) -> bool:
    component = index.component(*_TOOL_PROFICIENCY)
    return any(
        isinstance(f.fact, ProficiencyApplicationFact)
        and f.fact.proficiency is ProficiencyKind.TOOL
        and f.fact.roll.context is RollContext.ABILITY_CHECK
        for f in (component.facts if component else ())
    )


def _spec(
    operation: Operation,
    proposal: RollProposal,
    index: AuthorityIndex,
    character: TurnCharacter,
) -> _Spec:
    if operation is Operation.FIXED_DC_CHECK:
        return _fixed_dc_spec(proposal, index)
    if operation is Operation.DIFFICULTY_CHECK:
        return _difficulty_spec(proposal, index)
    if operation is Operation.TOOL_CHECK:
        return _tool_spec(proposal, index, character)
    if operation is Operation.INITIATIVE:
        return _initiative_spec(index)
    raise _refuse(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        f"{operation.value} is not a check operation",
    )


#: The operations this module executes.
CHECK_OPERATIONS: frozenset[Operation] = frozenset(
    {
        Operation.FIXED_DC_CHECK,
        Operation.DIFFICULTY_CHECK,
        Operation.TOOL_CHECK,
        Operation.INITIATIVE,
    }
)


def prepare(proposal: RollProposal, character: TurnCharacter) -> PreparedCheck:
    """Validate *proposal* and derive every input, or refuse (typed)."""
    operation = _operation(proposal)
    index = character.index
    if index is None:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            "the character's exact binding authority was not resolved",
        )
    certificate = certify(operation, index)
    spec = _spec(operation, proposal, index, character)
    ability, skill = spec.ability, spec.skill
    state = _state(character)
    extra = (
        INITIATIVE_CONTRIBUTORS if operation is Operation.INITIATIVE else frozenset()
    )
    _refuse_contributors(character, state, index, ability, extra)
    advantage, disadvantage = _advantage(state, index, ability, skill, spec.contexts)

    score, _ = ability_score(index, state, ability)
    ability_modifier = (score - 10) // 2
    level = sum(c.level for c in state.classes or ())
    if level < 1:
        raise _refuse(RefusalKind.MISSING_STATE, "the character records no level")
    multiplier, expertise = 0, None
    if spec.proficiency == "skill" and skill is not None:
        multiplier, expertise = skill_proficiency(index, state, skill)
        applies = _skill_applies(index)
    elif spec.proficiency == "tool" and spec.tool is not None:
        multiplier = int(tool_proficiency(index, state, *spec.tool))
        applies = _tool_applies(index)
    proficiency = 0
    if multiplier:
        if not applies:
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY,
                f"{spec.proficiency} proficiency's application to ability checks "
                "is absent",
            )
        proficiency = _proficiency_bonus(index, level) * multiplier
    breakdown = {f"{ability.value}_modifier": ability_modifier}
    if proficiency:
        key = "expertise" if expertise else "proficiency_bonus"
        breakdown[key] = proficiency
    return PreparedCheck(
        operation=operation,
        identity=spec.identity,
        ability=ability,
        skill=skill,
        dc=spec.dc,
        dc_source=spec.dc_source,
        ability_modifier=ability_modifier,
        proficiency=proficiency,
        advantage_sources=advantage,
        disadvantage_sources=disadvantage,
        certificate=certificate,
        breakdown=breakdown,
    )


def roll(prepared: PreparedCheck, dice: DiceService) -> RolledCheck:
    result = dice.roll(prepared.expression)
    return RolledCheck(prepared, result.raw_rolls, result.chosen)
