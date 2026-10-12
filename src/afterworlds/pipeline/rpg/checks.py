"""Source-fixed-DC ability checks — the CRD Issue 15c executable check path.

:func:`prepare` validates a proposal completely and derives every number from
exact typed authority and recorded state, before any die is rolled; it raises
:class:`~afterworlds.pipeline.rpg.capability.AdjudicationRefusal` otherwise.
:func:`roll` then rolls the prepared check. Nothing here writes state.

Numbers and their sources:

* the DC, ability and skill: the admitted check identity's typed
  ``ability_check`` fact (``dc_kind`` fixed);
* the ability modifier: the base score plus recorded sourced adjustments, each
  capped at its stated maximum (20 when none is stated), then
  ``(score - 10) // 2`` (``play.six_abilities``);
* the Proficiency Bonus: the typed ``proficiency_bonus_band`` for the
  character's total level, added under the typed skill
  ``proficiency_application`` when the skill is recorded, doubled for
  Expertise;
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

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    AdvantageFact,
    AdvantageState,
    AutomaticOutcomeFact,
    ConditionKind,
    DcKind,
    ProficiencyApplicationFact,
    ProficiencyBonusBandFact,
    ProficiencyKind,
    RecordKind,
    RollActor,
    RollContext,
    Skill,
)
from afterworlds.models.dnd5e_state import Dnd5eCharacterState
from afterworlds.models.rpg import RollProposal
from afterworlds.pipeline.rpg.capability import (
    FIXED_DC_CHECKS,
    AdjudicationRefusal,
    Certificate,
    Operation,
    RefusalKind,
    certify,
)
from afterworlds.pipeline.rpg.dice import DiceService
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from afterworlds.services.dnd5e_state.turn import TurnCharacter

__all__ = ["PreparedCheck", "RolledCheck", "prepare", "roll"]

_PB_COMPONENT = ("play.proficiency.proficiency_bonus", "proficiency_bonus_bands")
_SKILL_PROFICIENCY = ("play.proficiency.skill_proficiencies", "skill_proficiency")
_DEFAULT_ABILITY_CAP = 20

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


@dataclass(frozen=True)
class PreparedCheck:
    """A fully validated check: every input fixed, no die rolled yet."""

    identity: tuple[str, str]
    ability: AbilityScore
    skill: Skill | None
    dc: int
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
        return "success" if self.total >= self.prepared.dc else "failure"

    def provenance_json(self) -> str:
        p = self.prepared
        return json.dumps(
            {
                "visible_total": p.modifier,
                "breakdown": p.breakdown,
                "operation": Operation.FIXED_DC_CHECK.value,
                "check_identity": "/".join(p.identity),
                "ability": p.ability.value,
                "skill": p.skill.value if p.skill else None,
                "dc_source": "/".join(p.identity),
                "advantage_sources": list(p.advantage_sources),
                "disadvantage_sources": list(p.disadvantage_sources),
                "certificate": p.certificate.as_json(),
            },
            sort_keys=True,
        )


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


def _identity(proposal: RollProposal) -> tuple[str, str]:
    record, _, component = (proposal.check_identity or "").partition("/")
    if (record, component) not in FIXED_DC_CHECKS:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{proposal.check_identity!r} is not an admitted source-fixed check "
            f"identity ({', '.join('/'.join(i) for i in FIXED_DC_CHECKS)})",
        )
    return record, component


def _check_fact(index: AuthorityIndex, identity: tuple[str, str]) -> AbilityCheckFact:
    component = index.component(*identity)
    facts = [] if component is None else [f.fact for f in component.facts]
    checks = [f for f in facts if isinstance(f, AbilityCheckFact)]
    if (
        len(facts) != 1
        or len(checks) != 1
        or checks[0].dc_kind is not DcKind.FIXED
        or checks[0].dc_value is None
        or checks[0].ability is None
        or checks[0].context is not RollContext.ABILITY_CHECK
    ):
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            f"{'/'.join(identity)} states no single source-fixed ability check "
            "under this binding",
        )
    return checks[0]


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


def _ability_score(state: Dnd5eCharacterState, ability: AbilityScore) -> int:
    assert state.ability_scores is not None
    score: int = getattr(state.ability_scores, ability.value)
    for adj in state.ability_adjustments or ():
        if adj.ability is not ability:
            continue
        cap = adj.maximum if adj.maximum is not None else _DEFAULT_ABILITY_CAP
        raised = min(score + adj.amount, cap)
        score = max(score, raised) if adj.amount > 0 else score + adj.amount
    return score


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


def _features(state: Dnd5eCharacterState, index: AuthorityIndex) -> set[str]:
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
            held |= {k for k in CHECK_CONTRIBUTING_FEATURES if k.startswith(prefix)}
    return held


def _refuse_contributors(
    character: TurnCharacter,
    state: Dnd5eCharacterState,
    index: AuthorityIndex,
    ability: AbilityScore,
) -> None:
    def unsupported(what: str) -> AdjudicationRefusal:
        return _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{what} can contribute to this check and is not executable here",
        )

    if state.active_effects:
        raise unsupported(f"active effect {state.active_effects[0].source.record_key}")
    found = sorted(_features(state, index) & CHECK_CONTRIBUTING_FEATURES)
    found += sorted(
        f.feat_record_key
        for f in state.feats or ()
        if f.feat_record_key in CHECK_CONTRIBUTING_FEATURES
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
                    or roll.context
                    not in (RollContext.ABILITY_CHECK, RollContext.D20_TEST)
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
    identity = _identity(proposal)
    fact = _check_fact(index, identity)
    assert fact.ability is not None and fact.dc_value is not None
    ability = AbilityScore(fact.ability)
    skill = Skill(fact.skill) if fact.skill is not None else None
    state = _state(character)
    _refuse_contributors(character, state, index, ability)
    advantage, disadvantage = _advantage(state, index, ability, skill)

    score = _ability_score(state, ability)
    ability_modifier = (score - 10) // 2
    level = sum(c.level for c in state.classes or ())
    if level < 1:
        raise _refuse(RefusalKind.MISSING_STATE, "the character records no level")
    proficiency = 0
    grant = next(
        (g for g in state.skill_proficiencies or () if g.skill is skill),
        None,
    )
    if grant is not None:
        if not _skill_applies(index):
            raise _refuse(
                RefusalKind.MISSING_AUTHORITY,
                "skill proficiency's application to ability checks is absent",
            )
        bonus = _proficiency_bonus(index, level)
        proficiency = bonus * 2 if grant.expertise else bonus
    breakdown = {f"{ability.value}_modifier": ability_modifier}
    if proficiency:
        key = "expertise" if grant and grant.expertise else "proficiency_bonus"
        breakdown[key] = proficiency
    return PreparedCheck(
        identity=identity,
        ability=ability,
        skill=skill,
        dc=fact.dc_value,
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
