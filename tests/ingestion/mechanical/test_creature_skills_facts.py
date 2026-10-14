"""Schema 22 ``creature_skills`` (CRD Issue 15b C9).

The intrinsic invariant (manifested, inside the schema hash), the payload
boundary, and the relational rule: the fact sits only on a creature profile,
at most once. Shaped on raw candidate C9's Goblin Warrior Skills entry.
"""

from __future__ import annotations

from typing import Any

import pytest

from afterworlds.ingestion.mechanical.representation import (
    SKILL_ABILITY,
    AbilityScore,
    ComponentDraft,
    ComponentHandling,
    CreatureSize,
    CreatureSizeFact,
    CreatureSkillBonus,
    CreatureSkillsFact,
    MalformedFactPayloadError,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    Skill,
    fact_from_payload,
    fact_invariant_violations,
    fact_payload,
    post_schema_3_violations,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_21_VERSION,
    SCHEMA_22_VERSION,
)
from afterworlds.ingestion.mechanical.validation import (
    _validate_creature_skills,
    validate_representation,
)
from tests.ingestion.mechanical.conftest import bound_corpus, build_ledger

GOBLIN = {
    "family": "creature_skills",
    "skills": [{"skill": "stealth", "ability": "dexterity", "bonus": 6}],
}

_USUAL = {s.value: a.value for s, a in SKILL_ABILITY.items()}


def _skills(*items: tuple[str, object]) -> dict[str, Any]:
    return {
        "family": "creature_skills",
        "skills": [
            {"skill": s, "ability": _USUAL.get(s, "dexterity"), "bonus": b}
            for s, b in items
        ],
    }


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(GOBLIN, id="goblin-warrior"),
        pytest.param(_skills(), id="empty"),
        pytest.param(_skills(("perception", 2), ("stealth", -1)), id="two-signed"),
    ],
)
def test_round_trip(payload: dict[str, Any]) -> None:
    fact = fact_from_payload(payload)
    assert type(fact) is CreatureSkillsFact
    assert fact_invariant_violations(fact) == ()
    assert fact_payload(fact) == payload


def test_empty_is_a_positive_statement() -> None:
    """No printed Skills entry is a legal fact, distinct from a missing one."""
    fact = fact_from_payload(_skills())
    assert fact == CreatureSkillsFact(skills=())
    assert fact_invariant_violations(fact) == ()


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(_skills(("stealth", 6), ("perception", 2)), id="unsorted"),
        pytest.param(_skills(("stealth", 6), ("stealth", 4)), id="duplicate"),
    ],
)
def test_an_illegal_skills_entry_is_refused(payload: dict[str, Any]) -> None:
    assert fact_invariant_violations(fact_from_payload(payload)), payload


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(_skills(("sneaking", 6)), id="unknown-skill"),
        pytest.param(_skills(("Stealth", 6)), id="case"),
        pytest.param(_skills(("stealth", "6")), id="string-bonus"),
        pytest.param(_skills(("stealth", True)), id="bool-bonus"),
        pytest.param(_skills(("stealth", 6.0)), id="float-bonus"),
        pytest.param(
            {
                "family": "creature_skills",
                "skills": [
                    {
                        "skill": "stealth",
                        "ability": "dexterity",
                        "bonus": 6,
                        "expertise": True,
                    }
                ],
            },
            id="extra-item-key",
        ),
        pytest.param({**GOBLIN, "proficiency_bonus": 2}, id="extra-fact-key"),
        pytest.param({"family": "creature_skills"}, id="missing-field"),
    ],
)
def test_a_malformed_payload_does_not_build(payload: dict[str, Any]) -> None:
    with pytest.raises(MalformedFactPayloadError):
        fact_from_payload(payload)


def test_a_hand_built_non_vocabulary_value_is_refused() -> None:
    fact = CreatureSkillsFact(
        skills=(
            CreatureSkillBonus(
                skill="stealth",  # type: ignore[arg-type]
                ability=AbilityScore.DEXTERITY,
                bonus=6,
            ),
        )
    )
    assert fact_invariant_violations(fact)


def test_schema_21_cannot_state_the_family() -> None:
    """The introduction manifest refuses it under 21 and admits it under 22."""
    fact = fact_from_payload(GOBLIN)
    (finding,) = post_schema_3_violations(fact, SCHEMA_21_VERSION)
    assert "creature_skills" in finding
    assert post_schema_3_violations(fact, SCHEMA_22_VERSION) == []


def test_the_bonus_is_for_the_usual_pairing_only() -> None:
    """Assassin: Acrobatics +7 is printed for Dexterity (Acrobatics)
    (monsters-A-Z.md:532); the fact cannot carry it as Strength (Acrobatics),
    a pairing the rules permit (playing-the-game.md:239) but the stat block
    does not print."""
    usual = {
        "family": "creature_skills",
        "skills": [{"skill": "acrobatics", "ability": "dexterity", "bonus": 7}],
    }
    assert fact_invariant_violations(fact_from_payload(usual)) == ()
    atypical = {
        "family": "creature_skills",
        "skills": [{"skill": "acrobatics", "ability": "strength", "bonus": 7}],
    }
    (finding,) = fact_invariant_violations(fact_from_payload(atypical))
    assert "usual ability" in finding


def test_the_ability_is_required() -> None:
    with pytest.raises(MalformedFactPayloadError):
        fact_from_payload(
            {"family": "creature_skills", "skills": [{"skill": "stealth", "bonus": 6}]}
        )


# --- the relational rule ---------------------------------------------------

DEX = AbilityScore.DEXTERITY
STEALTH = CreatureSkillsFact(
    skills=(CreatureSkillBonus(skill=Skill.STEALTH, ability=DEX, bonus=6),)
)
NONE_PRINTED = CreatureSkillsFact(skills=())
UNSORTED = CreatureSkillsFact(
    skills=(
        CreatureSkillBonus(skill=Skill.STEALTH, ability=DEX, bonus=6),
        CreatureSkillBonus(
            skill=Skill.PERCEPTION, ability=AbilityScore.WISDOM, bonus=2
        ),
    )
)
SMALL = CreatureSizeFact(sizes=(CreatureSize.SMALL,))


def _draft(*facts: object, kind: RecordKind = RecordKind.CREATURE) -> Any:
    component = ComponentDraft(
        record_key="monsters.goblin.goblin_warrior",
        semantic_key="goblin_warrior",
        handling=ComponentHandling.STRUCTURED,
        facts=facts,  # type: ignore[arg-type]
    )
    return RepresentationDraft(
        records=(RecordDraft(semantic_key=component.record_key, kind=kind),),
        components=(component,),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )


@pytest.mark.parametrize("skills", [STEALTH, NONE_PRINTED], ids=["listed", "empty"])
def test_a_creature_profile_validates(skills: CreatureSkillsFact) -> None:
    assert _validate_creature_skills(_draft(SMALL, skills)) == []


def test_a_non_creature_record_is_refused() -> None:
    (finding,) = _validate_creature_skills(
        _draft(SMALL, STEALTH, kind=RecordKind.SPELL)
    )
    assert "only on a creature profile" in finding


def test_a_creature_component_without_a_size_is_refused() -> None:
    (finding,) = _validate_creature_skills(_draft(STEALTH))
    assert "only on a creature profile" in finding


def test_two_facts_on_one_profile_are_refused() -> None:
    (finding,) = _validate_creature_skills(_draft(SMALL, STEALTH, NONE_PRINTED))
    assert "at most one" in finding


def test_refused_structure_is_never_read_relationally() -> None:
    """A refused fact is not counted; a refused size leaves the profile unjudged."""
    assert _validate_creature_skills(_draft(SMALL, STEALTH, UNSORTED)) == []
    assert _validate_creature_skills(_draft(UNSORTED)) == []
    bad_size = CreatureSizeFact(sizes=())
    assert _validate_creature_skills(_draft(bad_size, STEALTH)) == []


def test_the_rule_runs_inside_validate_representation() -> None:
    """Wired into the candidate validation path, not only callable."""

    def findings(draft: RepresentationDraft) -> list[str]:
        found = validate_representation(draft, build_ledger(), bound_corpus())
        return [f for f in found if "creature_skills" in f]

    assert findings(_draft(SMALL, STEALTH)) == []
    assert findings(_draft(STEALTH))
    assert findings(_draft(SMALL, STEALTH, NONE_PRINTED))
