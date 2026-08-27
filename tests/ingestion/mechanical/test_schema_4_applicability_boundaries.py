"""Schema-4 applicability operands survive every production boundary — CRD Issue 5d.

A component, option, fact qualifier, or override using any schema-4 applicability
kind carries its required operand in the canonical payload — `outcome`,
`damage_outcome`, `required_quantity`, `fraction`, `unit`. Three production
builders reconstructed only the fields through ``phase`` and dropped the rest, so
the rebuilt value failed its own invariants: accepted artifacts could not load,
persisted candidates could not reconstruct, and equivalent overrides were refused.

The operands are **post-schema-3 keys**, so the canonical payload omits one that
carries no meaning and a legal schema-3 payload has no such key at all. Reading
them with ``[...]`` would fail on entirely honest content; the builders read them
with ``.get`` and the schema-3 control case below is what holds that distinction.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.oracle import OracleLoadError
from afterworlds.ingestion.mechanical.oracle import _applicability as load_accepted
from afterworlds.ingestion.mechanical.persistence import (
    PersistedStateReconstructionError,
)
from afterworlds.ingestion.mechanical.persistence import (
    _applicability_from_row as load_persisted,
)
from afterworlds.ingestion.mechanical.projection import applicability_payload
from afterworlds.ingestion.mechanical.representation import (
    Applicability,
    ApplicabilityKind,
    AutomaticOutcome,
    Comparison,
    ConditionKind,
    ConditionRemovalRestrictionFact,
    DamageOutcome,
    Phase,
    Rational,
    RequiredQuantity,
    TimeUnit,
    fact_from_payload,
    fact_payload,
)
from afterworlds.services.rules_authority.patches import InvalidPatchError
from afterworlds.services.rules_authority.patches import (
    _build_applicability as load_patch,
)

# ---------------------------------------------------------------------------
# One exemplar per schema-4 applicability kind, plus a schema-3 control
# ---------------------------------------------------------------------------

ROLL_OUTCOME = Applicability(
    kind=ApplicabilityKind.ROLL_OUTCOME,
    negated=False,
    outcome=AutomaticOutcome.SUCCESS,
)
DAMAGE_OUTCOME = Applicability(
    kind=ApplicabilityKind.DAMAGE_OUTCOME,
    negated=False,
    damage_outcome=DamageOutcome.ANY_DAMAGE,
)
CONSUMPTION = Applicability(
    kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
    negated=False,
    comparison=Comparison.REACHES,
    required_quantity=RequiredQuantity.WATER,
    fraction=Rational(1, 1),
)
ELAPSED = Applicability(
    kind=ApplicabilityKind.ELAPSED_DURATION,
    negated=False,
    value=6,
    unit=TimeUnit.MINUTE,
)
#: The control. Its payload carries none of the five keys at all, so a builder
#: that read them positionally would fail here on content schema 3 states.
PHASE = Applicability(kind=ApplicabilityKind.PHASE, negated=False, phase=Phase.ON_END)

SCHEMA_4_KINDS = [
    pytest.param(ROLL_OUTCOME, id="roll_outcome"),
    pytest.param(DAMAGE_OUTCOME, id="damage_outcome"),
    pytest.param(CONSUMPTION, id="consumption_threshold"),
    pytest.param(ELAPSED, id="elapsed_duration"),
]
ALL_KINDS = [*SCHEMA_4_KINDS, pytest.param(PHASE, id="phase-schema-3-control")]

#: The three production boundaries that dropped the operands, each with the
#: typed failure it owes its own callers.
BOUNDARIES = [
    pytest.param(
        lambda raw: load_accepted(raw, "where"),
        OracleLoadError,
        id="accepted-input-loader",
    ),
    pytest.param(
        lambda raw: load_persisted(raw, "table", "where"),
        PersistedStateReconstructionError,
        id="persisted-state-loader",
    ),
    pytest.param(
        lambda raw: load_patch(raw, "what"),
        InvalidPatchError,
        id="override-patch-builder",
    ),
]


# ---------------------------------------------------------------------------
# Round trips
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("applicability", ALL_KINDS)
@pytest.mark.parametrize(("build", "error"), BOUNDARIES)
def test_an_applicability_round_trips_through_every_boundary(
    applicability: Applicability, build, error: type[Exception]
) -> None:  # type: ignore[no-untyped-def]
    """Equality on the whole value, so a dropped operand fails rather than degrades."""
    assert build(applicability_payload(applicability)) == applicability


@pytest.mark.parametrize("applicability", ALL_KINDS)
def test_the_nested_fact_builder_was_already_safe(
    applicability: Applicability,
) -> None:
    """The fourth builder, audited and unchanged.

    ``fact_from_payload`` rebuilds ``ConditionRemovalRestrictionFact.until``
    through the representation's own applicability path, which already read all
    five operands. Pinned so the audit's "already safe" disposition stays true.
    """
    fact = ConditionRemovalRestrictionFact(
        condition=ConditionKind.EXHAUSTION, until=applicability
    )
    assert fact_from_payload(fact_payload(fact)) == fact


@pytest.mark.parametrize("applicability", SCHEMA_4_KINDS)
def test_the_operand_is_what_survives_not_merely_the_kind(
    applicability: Applicability,
) -> None:
    """The defect was silent in exactly this way: kind preserved, operand dropped.

    Asserting on the payload's own operand keys rather than on equality alone,
    so a future builder that reconstructs a *different* honest value still fails.
    """
    payload = applicability_payload(applicability)
    operands = {
        k: v
        for k, v in payload.items()
        if k in {"outcome", "damage_outcome", "required_quantity", "fraction", "unit"}
    }
    assert operands, "exemplar carries no schema-4 operand"
    for build, _ in (p.values for p in BOUNDARIES):  # type: ignore[misc]
        rebuilt = build(payload)
        assert applicability_payload(rebuilt) == payload


# ---------------------------------------------------------------------------
# Malformed input fails at its proper typed boundary
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("build", "error"), BOUNDARIES)
@pytest.mark.parametrize(
    ("mutate", "why"),
    [
        pytest.param(
            lambda p: {**p, "outcome": "triumph"},
            "a value outside the declared vocabulary",
            id="wrong-enum",
        ),
        pytest.param(
            lambda p: {k: v for k, v in p.items() if k != "outcome"},
            "the required operand missing entirely",
            id="missing-required-operand",
        ),
        pytest.param(
            lambda p: {**p, "smuggled": 1},
            "a key the closed payload does not declare",
            id="extra-key",
        ),
        pytest.param(
            lambda p: {**p, "outcome": 7},
            "an operand of the wrong primitive type",
            id="malformed-primitive",
        ),
    ],
)
def test_a_malformed_operand_fails_at_its_own_boundary(
    build, error: type[Exception], mutate, why: str
) -> None:  # type: ignore[no-untyped-def]
    """Each boundary reports in its own words rather than raising something raw."""
    with pytest.raises(error):
        build(mutate(applicability_payload(ROLL_OUTCOME)))


@pytest.mark.parametrize(("build", "error"), BOUNDARIES)
@pytest.mark.parametrize(
    ("fraction", "why"),
    [
        pytest.param("1/2", "a bare string where a structure is declared", id="string"),
        pytest.param({"numerator": 1}, "a structure missing a half", id="half"),
        pytest.param(
            {"numerator": 1, "denominator": 2, "extra": 3},
            "a structure carrying an undeclared key",
            id="extra",
        ),
    ],
)
def test_a_malformed_fraction_fails_rather_than_reconstructing_differently(
    build, error: type[Exception], fraction: object, why: str
) -> None:  # type: ignore[no-untyped-def]
    """Nothing is coerced.

    A fraction that reconstructs as a different fraction is worse than one that
    refuses to reconstruct — it publishes an amount the source never stated.
    """
    with pytest.raises(error):
        build({**applicability_payload(CONSUMPTION), "fraction": fraction})


def test_a_schema_3_payload_needs_none_of_the_new_keys() -> None:
    """The control, stated directly.

    The five operands are post-schema-3, so the canonical payload omits them
    when they carry no meaning. A builder reading them positionally would fail
    on content that is entirely honest — this is what makes ``.get`` load-bearing
    rather than defensive.
    """
    payload = applicability_payload(PHASE)
    assert not {
        "outcome",
        "damage_outcome",
        "required_quantity",
        "fraction",
        "unit",
    } & set(payload)
    for build, _ in (p.values for p in BOUNDARIES):  # type: ignore[misc]
        assert build(payload) == PHASE
