"""Runtime field types inside the closed union — CRD Issue 5d, review round 2.

Field-set validation stopped missing and extra keys; it did not stop a key
holding the wrong kind of value. That gap matters most for Booleans: JSON
``"false"`` is a truthy string, and Python's ``bool`` is a subclass of ``int``,
so ``True`` slips through a bare integer check. Either one silently inverts a
mechanical rule downstream.

Both paths are covered here — a dataclass constructed directly in memory, and a
payload rebuilt from a persisted row — because a fact reaching authority
through either path is equally authoritative.
"""

from __future__ import annotations

from typing import Any

import pytest

from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    CreatureAbilityScoreFact,
    DcKind,
    MalformedFactPayloadError,
    ProgressionEntryFact,
    RollContext,
    SpellDescriptorFact,
    SpellSchool,
    fact_from_payload,
    fact_invariant_violations,
    fact_key,
    fact_payload,
)

HONEST = (
    AbilityCheckFact(
        AbilityScore.WISDOM, DcKind.FIXED, 15, context=RollContext.ABILITY_CHECK
    ),
    AbilityCheckFact(
        AbilityScore.DEXTERITY, DcKind.SPELL_SAVE_DC, context=RollContext.ABILITY_CHECK
    ),
    CreatureAbilityScoreFact(AbilityScore.CONSTITUTION, 14),
    SpellDescriptorFact(
        level=0, school=SpellSchool.EVOCATION, ritual=False, concentration=False
    ),
    SpellDescriptorFact(
        level=3, school=SpellSchool.ILLUSION, ritual=True, concentration=True
    ),
    ProgressionEntryFact(level=5, entitlement_key="feature:extra"),
    ProgressionEntryFact(level=5, entitlement_key="feature:extra", quantity=2),
)


def _payload(family: str, **fields: Any) -> dict[str, Any]:
    return {"family": family, **fields}


def _check_payload(family: str, **fields: Any) -> dict[str, Any]:
    """A complete payload for *family*, with *fields* overriding the honest ones."""
    base = {
        "ability_check": {
            "ability": "wisdom",
            "dc_kind": "fixed",
            # Schema 5: required, so an honest payload always carries it.
            "context": "ability_check",
            "dc_value": 15,
        },
        "creature_ability_score": {
            "ability": "strength",
            "score": 12,
            "modifier": None,
            "save_modifier": None,
        },
        "spell_descriptor": {
            "level": 3,
            "school": "illusion",
            "ritual": False,
            "concentration": False,
            "casting_time": None,
            "spell_range": None,
            "components": None,
            "duration": None,
        },
        "progression_entry": {
            "level": 5,
            "entitlement_key": "feature:extra",
            "quantity": 2,
        },
    }[family]
    return _payload(family, **{**base, **fields})


# -- honest facts are unchanged ----------------------------------------------


@pytest.mark.parametrize("fact", HONEST)
def test_honest_facts_round_trip_with_identical_payload_and_key(fact: object) -> None:
    payload = fact_payload(fact)
    rebuilt = fact_from_payload(payload)
    assert rebuilt == fact
    assert fact_payload(rebuilt) == payload
    assert fact_key(rebuilt) == fact_key(fact)
    assert fact_invariant_violations(rebuilt) == ()


# -- in-memory: a well-formed dataclass with mistyped fields -----------------
#
# Every case below constructs the declared dataclass, so class membership is
# satisfied and only the field types are wrong.


@pytest.mark.parametrize(
    ("fact", "expected"),
    [
        (
            AbilityCheckFact(  # type: ignore[arg-type]
                AbilityScore.WISDOM,
                DcKind.FIXED,
                "15",
                context=RollContext.ABILITY_CHECK,
            ),
            "dc_value must be an integer",
        ),
        (
            AbilityCheckFact(  # type: ignore[arg-type]
                AbilityScore.WISDOM,
                DcKind.FIXED,
                True,
                context=RollContext.ABILITY_CHECK,
            ),
            "dc_value must be an integer",
        ),
        (
            AbilityCheckFact(  # type: ignore[arg-type]
                "wisdom", DcKind.FIXED, 15, context=RollContext.ABILITY_CHECK
            ),
            "ability must be AbilityScore",
        ),
        (
            AbilityCheckFact(  # type: ignore[arg-type]
                AbilityScore.WISDOM, "fixed", 15, context=RollContext.ABILITY_CHECK
            ),
            "dc_kind must be DcKind",
        ),
        (
            CreatureAbilityScoreFact(AbilityScore.STRENGTH, True),  # type: ignore[arg-type]
            "score must be an integer",
        ),
        (
            CreatureAbilityScoreFact(AbilityScore.STRENGTH, "12"),  # type: ignore[arg-type]
            "score must be an integer",
        ),
        (
            CreatureAbilityScoreFact("strength", 12),  # type: ignore[arg-type]
            "ability must be AbilityScore",
        ),
        (
            SpellDescriptorFact("3", SpellSchool.ILLUSION, False, False),  # type: ignore[arg-type]
            "level must be an integer",
        ),
        (
            SpellDescriptorFact(True, SpellSchool.ILLUSION, False, False),  # type: ignore[arg-type]
            "level must be an integer",
        ),
        (
            SpellDescriptorFact(3, "illusion", False, False),  # type: ignore[arg-type]
            "school must be SpellSchool",
        ),
        (
            SpellDescriptorFact(3, SpellSchool.ILLUSION, "false", False),  # type: ignore[arg-type]
            "ritual must be a boolean",
        ),
        (
            SpellDescriptorFact(3, SpellSchool.ILLUSION, 1, False),  # type: ignore[arg-type]
            "ritual must be a boolean",
        ),
        (
            SpellDescriptorFact(3, SpellSchool.ILLUSION, False, "false"),  # type: ignore[arg-type]
            "concentration must be a boolean",
        ),
        (
            SpellDescriptorFact(3, SpellSchool.ILLUSION, False, 0),  # type: ignore[arg-type]
            "concentration must be a boolean",
        ),
        (
            ProgressionEntryFact(True, "feature:x"),  # type: ignore[arg-type]
            "level must be an integer",
        ),
        (
            ProgressionEntryFact(5, 42),  # type: ignore[arg-type]
            "entitlement_key must be a string",
        ),
        (
            ProgressionEntryFact(5, "feature:x", "2"),  # type: ignore[arg-type]
            "quantity must be an integer",
        ),
        (
            ProgressionEntryFact(5, "feature:x", True),  # type: ignore[arg-type]
            "quantity must be an integer",
        ),
    ],
)
def test_mistyped_in_memory_field_is_reported(fact: object, expected: str) -> None:
    violations = fact_invariant_violations(fact)
    assert any(expected in v for v in violations), violations


def test_mistyped_field_suppresses_the_misleading_semantic_finding() -> None:
    # dc_value is a string, so the fixed/non-fixed relationship cannot be
    # judged; reporting "fixed DC without a dc_value" would be noise.
    violations = fact_invariant_violations(
        AbilityCheckFact(  # type: ignore[arg-type]
            AbilityScore.WISDOM,
            DcKind.SPELL_SAVE_DC,
            "15",
            context=RollContext.ABILITY_CHECK,
        )
    )
    assert any("dc_value must be an integer" in v for v in violations)
    assert not any("carries dc_value" in v for v in violations)


# -- persisted payloads: nothing is coerced ----------------------------------


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (_check_payload("ability_check", dc_value="15"), "dc_value must be an integer"),
        (_check_payload("ability_check", dc_value=True), "dc_value must be an integer"),
        (
            _check_payload("ability_check", ability="luck"),
            "not a declared AbilityScore",
        ),
        (_check_payload("ability_check", ability=12), "must be a string AbilityScore"),
        (_check_payload("ability_check", dc_kind=False), "must be a string DcKind"),
        (
            _check_payload("creature_ability_score", score=True),
            "score must be an integer",
        ),
        (
            _check_payload("creature_ability_score", score="12"),
            "score must be an integer",
        ),
        (
            _check_payload("creature_ability_score", ability="fortitude"),
            "not a declared AbilityScore",
        ),
        (_check_payload("spell_descriptor", level="3"), "level must be an integer"),
        (_check_payload("spell_descriptor", level=True), "level must be an integer"),
        (
            _check_payload("spell_descriptor", school="chronomancy"),
            "not a declared SpellSchool",
        ),
        (
            _check_payload("spell_descriptor", ritual="false"),
            "ritual must be a boolean",
        ),
        (_check_payload("spell_descriptor", ritual=1), "ritual must be a boolean"),
        (_check_payload("spell_descriptor", ritual=0), "ritual must be a boolean"),
        (
            _check_payload("spell_descriptor", concentration="false"),
            "concentration must be a boolean",
        ),
        (_check_payload("progression_entry", level=True), "level must be an integer"),
        (
            _check_payload("progression_entry", entitlement_key=42),
            "entitlement_key must be a string",
        ),
        (
            _check_payload("progression_entry", quantity="2"),
            "quantity must be an integer",
        ),
        (
            _check_payload("progression_entry", quantity=True),
            "quantity must be an integer",
        ),
    ],
)
def test_mistyped_persisted_field_is_rejected(
    payload: dict[str, Any], expected: str
) -> None:
    with pytest.raises(MalformedFactPayloadError, match="mistyped fields"):
        fact_from_payload(payload)
    with pytest.raises(MalformedFactPayloadError) as exc:
        fact_from_payload(payload)
    assert expected in str(exc.value)


def test_string_number_is_not_coerced_to_an_integer() -> None:
    with pytest.raises(MalformedFactPayloadError):
        fact_from_payload(_check_payload("spell_descriptor", level="3"))


def test_integer_is_not_coerced_to_a_boolean() -> None:
    with pytest.raises(MalformedFactPayloadError):
        fact_from_payload(_check_payload("spell_descriptor", concentration=1))


def test_null_is_not_accepted_for_a_required_field() -> None:
    with pytest.raises(MalformedFactPayloadError):
        fact_from_payload(_check_payload("creature_ability_score", score=None))


def test_optional_fields_still_accept_null() -> None:
    fact = fact_from_payload(
        _check_payload("ability_check", dc_kind="contested", dc_value=None)
    )
    assert isinstance(fact, AbilityCheckFact)
    assert fact.dc_value is None
    assert fact_invariant_violations(fact) == ()
