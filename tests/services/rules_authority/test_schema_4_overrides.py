"""Every schema-4 addition is overridable — CRD Issue 5d, PR A.

Typed patches rebuild facts through the projection's own ``fact_from_payload``,
so a *family* added to the closed union is patchable the moment it exists. That
is a claim about this code rather than a law of nature, and schema 4 added ten
things, only five of which are families:

* five new fact families;
* four new or widened *fields* on families that already existed — a skill axis
  on ``RollSpec`` and ``AbilityCheckFact``, check alternatives, a damage-dice
  maximum, and cause scoping on a condition level — each of which could be
  silently dropped on the way through a payload without the family failing; and
* ``ComponentDraft.recurs``, the one component-level key, which needed the
  override contract widened rather than merely exercised.

``recurs`` is overridable under the *existing* contract, not a new decision.
``ComponentBody`` already carries every component-level meaning-bearing field a
complete replacement must supply — ``applies_when``, ``options``,
``fact_qualifiers`` — each optional on the way in and omitted from the canonical
payload at its default so no authored override-set identity moves. ``recurs``
is the same shape, and a complete component patch that could not carry it would
silently republish a repeating effect as a one-off.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    Applicability,
    ApplicabilityKind,
    ConditionKind,
    ConditionLevelFact,
    ConditionRemovalRestrictionFact,
    ConsumptionBand,
    CreatureSize,
    DamageFact,
    DamageInterval,
    DamageModDirection,
    DamageModificationFact,
    DamageType,
    DcKind,
    DerivedQuantityFact,
    DiceExpression,
    DieSize,
    DistanceUnit,
    EffectTerminationFact,
    LevelDirection,
    MeasureUnit,
    Rational,
    RecurrenceBoundary,
    RequiredQuantity,
    RollActor,
    RollContext,
    RollSpec,
    ScalingBasis,
    SizeKeyedQuantityFact,
    SizeQuantity,
    Skill,
    TerminationScope,
    TimePeriod,
    TimeUnit,
    fact_key,
    fact_payload,
)
from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.services.rules_authority.patches import (
    InvalidPatchError,
    patch_from_payload,
    patch_payload,
)
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)
from tests.services.rules_authority.conftest import (
    CHECK_COMPONENT_TARGET,
    CHECK_KEY,
    CREATURE_KEY,
    DESCRIPTOR_FACT_TARGET,
    DESCRIPTOR_KEY,
    SPELL_KEY,
    RuntimeFixture,
    append_fact_payload,
    author_override,
    replace_fact_payload,
)
from tests.services.rules_authority.test_typed_overrides import component, effective

# ---------------------------------------------------------------------------
# One exemplar per schema-4 addition, each quoting the clause that forced it
# ---------------------------------------------------------------------------

#: Burning — *"the fire also goes out"*.
TERMINATION = EffectTerminationFact(scope=TerminationScope.OWNING_EFFECT)

#: Dehydration — *"A creature requires an amount of water per day based on its
#: size"*, the Water Needs per Day table.
WATER = SizeKeyedQuantityFact(
    quantity=RequiredQuantity.WATER,
    period=TimePeriod.DAY,
    values=(
        SizeQuantity(CreatureSize.TINY, Rational(1, 4), MeasureUnit.GALLON),
        SizeQuantity(CreatureSize.SMALL, Rational(1, 1), MeasureUnit.GALLON),
        SizeQuantity(CreatureSize.MEDIUM, Rational(1, 1), MeasureUnit.GALLON),
    ),
)

#: Dehydration — *"Exhaustion caused by dehydration can't be removed until the
#: creature drinks the full amount of water required for a day."*
REMOVAL_RESTRICTION = ConditionRemovalRestrictionFact(
    condition=ConditionKind.EXHAUSTION,
    until=Applicability(
        kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
        negated=False,
        band=ConsumptionBand(
            quantity=RequiredQuantity.WATER,
            period=TimePeriod.DAY,
            lower=Rational(1, 1),
            lower_inclusive=True,
        ),
    ),
    cause_scoped=True,
)

#: Falling — *"any damage resulting from the fall is halved"*. Rounding is left
#: unset because Falling states none; *Round Down* is its own corpus content.
HALVED = DamageModificationFact(
    direction=DamageModDirection.REDUCE, factor=Rational(1, 2)
)

#: Suffocation — *"a number of minutes equal to 1 plus its Constitution modifier
#: (minimum of 30 seconds)"*.
BREATH = DerivedQuantityFact(
    base=1,
    modifier=AbilityScore.CONSTITUTION,
    unit=TimeUnit.MINUTE,
    floor_amount=30,
    floor_unit=TimeUnit.SECOND,
)

#: Grappling — *"a Strength (Athletics) or Dexterity (Acrobatics) check"*. The
#: skill axis, carried on the fact *and* on each nested roll spec of the choice.
#: Two alternatives because a choice of one is a single roll misdescribed, which
#: the family's own contract refuses — here as everywhere.
ACROBATICS = AbilityCheckFact(
    ability=AbilityScore.DEXTERITY,
    dc_kind=DcKind.FIXED,
    context=RollContext.ABILITY_CHECK,
    dc_value=15,
    skill=Skill.ACROBATICS,
    alternatives=(
        # Canonically ordered, not authoring-ordered: the source states no
        # precedence between the two, so one ordering is the only identity.
        RollSpec(
            actor=RollActor.SUBJECT,
            context=RollContext.ABILITY_CHECK,
            ability=AbilityScore.DEXTERITY,
            skill=Skill.ACROBATICS,
        ),
        RollSpec(
            actor=RollActor.SUBJECT,
            context=RollContext.ABILITY_CHECK,
            ability=AbilityScore.STRENGTH,
            skill=Skill.ATHLETICS,
        ),
    ),
)

#: Falling — *"1d6 ... for every 10 feet it fell, to a maximum of 20d6"*. Schema
#: 5 states the interval on the damage itself, so the amount is per interval and
#: there is no base beside it.
CAPPED = DamageFact(
    damage_type=DamageType.BLUDGEONING,
    dice=DiceExpression(1, DieSize.D6, 0),
    maximum_dice=20,
    per=DamageInterval(
        basis=ScalingBasis.DISTANCE_FALLEN, amount=10, unit=DistanceUnit.FOOT
    ),
)

#: Malnutrition — a level this record itself causes, not an edit to Exhaustion.
CAUSE_SCOPED_LEVEL = ConditionLevelFact(
    condition=ConditionKind.EXHAUSTION,
    direction=LevelDirection.GAIN,
    amount=1,
    cause_scoped=True,
)

SCHEMA_4_FACTS = [
    pytest.param(TERMINATION, id="effect_termination"),
    pytest.param(WATER, id="size_keyed_quantity"),
    pytest.param(REMOVAL_RESTRICTION, id="condition_removal_restriction"),
    pytest.param(HALVED, id="damage_modification"),
    pytest.param(BREATH, id="derived_quantity"),
    pytest.param(ACROBATICS, id="skill_axis_and_alternatives"),
    pytest.param(CAPPED, id="maximum_dice"),
    pytest.param(CAUSE_SCOPED_LEVEL, id="cause_scoped_level"),
]


# ---------------------------------------------------------------------------
# The families and fields, through the real override path
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("fact", SCHEMA_4_FACTS)
def test_a_schema_4_fact_can_be_appended_by_an_override(
    runtime: RuntimeFixture, fact: object
) -> None:
    """Each reaches the effective view as the same typed object it went in as.

    Equality is on the whole fact, so a field the payload dropped on the way
    through — a skill, a maximum, a cause scope — fails here rather than
    surviving as a quietly weaker claim.
    """
    author_override(
        runtime.session,
        override_id=f"ov-append-{fact_key(fact)}",
        target=CHECK_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=append_fact_payload(fact),
    )
    check = component(effective(runtime), CREATURE_KEY, CHECK_KEY)
    assert check is not None
    (added,) = [f for f in check.facts if f.fact_key == fact_key(fact)]
    assert added.fact == fact
    assert added.supplied_by_override_id == f"ov-append-{fact_key(fact)}"
    # Override-supplied authority names its override, never 5c spans.
    assert added.span_ids == ()


@pytest.mark.parametrize("fact", SCHEMA_4_FACTS)
def test_a_schema_4_fact_can_replace_an_existing_fact(
    runtime: RuntimeFixture, fact: object
) -> None:
    """``REPLACE`` supplies a complete replacement, not a merge of two shapes."""
    author_override(
        runtime.session,
        override_id=f"ov-replace-{fact_key(fact)}",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=replace_fact_payload(fact),
    )
    descriptor = component(effective(runtime), SPELL_KEY, DESCRIPTOR_KEY)
    assert descriptor is not None
    assert [f.fact for f in descriptor.facts] == [fact]


@pytest.mark.parametrize("fact", SCHEMA_4_FACTS)
def test_a_schema_4_fact_round_trips_through_the_patch_payload(fact: object) -> None:
    """Rebuild and re-serialize: the patch identity is derived from the whole fact."""
    payload = append_fact_payload(fact)
    patch = patch_from_payload(
        payload,
        operation=OverrideOperationEnum.APPEND,
        target=CHECK_COMPONENT_TARGET,
    )
    assert patch_payload(patch) == payload
    # And the rebuilt fact is the same object, not merely the same bytes.
    assert patch.fact == fact  # type: ignore[union-attr]


def test_a_nested_schema_4_value_object_is_not_flattened() -> None:
    """The per-size rows come back as ``SizeQuantity``, in the table's own order."""
    patch = patch_from_payload(
        append_fact_payload(WATER),
        operation=OverrideOperationEnum.APPEND,
        target=CHECK_COMPONENT_TARGET,
    )
    rebuilt = patch.fact  # type: ignore[union-attr]
    assert rebuilt == WATER
    assert [v.size for v in rebuilt.values] == [
        CreatureSize.TINY,
        CreatureSize.SMALL,
        CreatureSize.MEDIUM,
    ]
    assert all(isinstance(v, SizeQuantity) for v in rebuilt.values)


def test_a_schema_4_family_still_answers_to_its_own_invariants() -> None:
    """No looser runtime door: the family contract is enforced here too.

    A day-scoped requirement whose rows repeat one size states two different
    amounts for that size, and the union refuses it at build time. The patch
    path must refuse it in the same words rather than admitting a fact the
    projection would not.
    """
    broken = {
        **fact_payload(WATER),
        "values": [
            {
                "size": "tiny",
                "amount": {"numerator": 1, "denominator": 4},
                "unit": "gallon",
            },
            {
                "size": "tiny",
                "amount": {"numerator": 1, "denominator": 1},
                "unit": "gallon",
            },
        ],
    }
    with pytest.raises(InvalidPatchError):
        patch_from_payload(
            {"patch": "append_fact", "fact": broken},
            operation=OverrideOperationEnum.APPEND,
            target=CHECK_COMPONENT_TARGET,
        )


# ---------------------------------------------------------------------------
# recurs — the one addition that needed the contract widened
# ---------------------------------------------------------------------------

RECURS = {"boundary": "start_of_turn", "whose": "subject"}

APPEND_COMPONENT_TARGET = MechanicalTarget(
    kind=MechanicalTargetKind.RECORD, record_key=CREATURE_KEY
)


def _component_patch(**extra: object) -> dict[str, object]:
    return {
        "patch": "append_component",
        "component": {
            "semantic_key": "house-burning",
            "handling": "structured",
            "facts": [fact_payload(CAPPED)],
            **extra,
        },
    }


def _build(payload: dict[str, object]):  # type: ignore[no-untyped-def]
    return patch_from_payload(
        payload,
        operation=OverrideOperationEnum.APPEND,
        target=APPEND_COMPONENT_TARGET,
    )


def test_an_override_supplied_component_can_state_a_cadence() -> None:
    """``recurs`` is carried by a complete component patch, like every other key."""
    patch = _build(_component_patch(recurs=RECURS))
    assert patch.body.recurs is not None  # type: ignore[union-attr]
    assert patch.body.recurs.boundary is RecurrenceBoundary.START_OF_TURN  # type: ignore[union-attr]
    assert patch.body.recurs.whose is RollActor.SUBJECT  # type: ignore[union-attr]


def test_a_cadence_reaches_the_effective_view(runtime: RuntimeFixture) -> None:
    """Otherwise the field is decorative: a repeating effect read as a one-off."""
    author_override(
        runtime.session,
        override_id="ov-recurring-component",
        target=APPEND_COMPONENT_TARGET,
        operation=OverrideOperationEnum.APPEND,
        payload=_component_patch(recurs=RECURS),
    )
    added = component(effective(runtime), CREATURE_KEY, "house-burning")
    assert added is not None
    assert added.recurs is not None
    assert added.recurs.boundary is RecurrenceBoundary.START_OF_TURN


def test_an_omitted_cadence_means_none_rather_than_inheriting() -> None:
    """Component replacement is complete: absent states no cadence, not "keep"."""
    assert _build(_component_patch()).body.recurs is None  # type: ignore[union-attr]


def test_a_patch_without_a_cadence_keeps_its_exact_bytes() -> None:
    """The identity of every override authored before schema 4 stays put.

    ``recurs`` is omitted from the canonical payload when absent, for the same
    reason ``fact_qualifiers`` is. Emitting it as ``null`` would remint the
    override-set identity of every component patch already authored — the same
    authority under a new identifier, no longer naming the retained version it
    was recorded against.
    """
    canonical = patch_payload(_build(_component_patch()))
    # A fixed point: re-reading the canonical form reproduces it exactly, so an
    # authored payload's identity does not drift on every republish.
    assert patch_payload(_build(canonical)) == canonical
    assert "recurs" not in canonical["component"]  # type: ignore[operator,index]


def test_a_stated_cadence_is_identity_bearing() -> None:
    """Two cadences are two patches; the payload is not blind to the difference."""
    without = patch_payload(_build(_component_patch()))
    start = patch_payload(_build(_component_patch(recurs=RECURS)))
    end = patch_payload(
        _build(_component_patch(recurs={"boundary": "end_of_turn", "whose": "subject"}))
    )
    assert len({str(without), str(start), str(end)}) == 3


@pytest.mark.parametrize(
    ("recurs", "why"),
    [
        ({"boundary": "start_of_turn"}, "a turn boundary with no whose"),
        ({"boundary": "end_of_day", "whose": "subject"}, "a day boundary with a whose"),
        ({"boundary": "every_other_tuesday"}, "a boundary outside the vocabulary"),
        (
            {"boundary": "end_of_turn", "whose": "the dm"},
            "an actor outside the vocabulary",
        ),
        (
            {"boundary": "end_of_day", "smuggled": 1},
            "a key the structure does not declare",
        ),
        ("start_of_turn", "a bare string where a structure is declared"),
    ],
)
def test_a_dishonest_cadence_is_refused(recurs: object, why: str) -> None:
    """The same invariants the projection enforces, read by a third reader.

    A turn belongs to a creature, so a turn-boundary cadence needs a ``whose``;
    a day does not, so one carrying it ranges over a vocabulary it does not
    have. Neither is a weaker claim — each is a claim about something else.
    """
    with pytest.raises(InvalidPatchError):
        _build(_component_patch(recurs=recurs))
