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
from sqlalchemy import update
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.acceptance import AcceptanceError, accept_proposal
from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.gate import (
    GateFailureCategory,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    OracleLoadError,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.oracle import _applicability as load_accepted
from afterworlds.ingestion.mechanical.persistence import (
    PersistedStateReconstructionError,
    persist_draft,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.persistence import (
    _applicability_from_row as load_persisted,
)
from afterworlds.ingestion.mechanical.projection import (
    applicability_payload,
    identify_projection,
)
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, ProposedSpan
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    Applicability,
    ApplicabilityKind,
    AutomaticOutcome,
    Comparison,
    ComponentDraft,
    ConditionKind,
    ConditionLevelFact,
    ConditionRemovalRestrictionFact,
    CreatureChallengeFact,
    CreatureSize,
    DamageModDirection,
    DamageModificationFact,
    DamageOutcome,
    EquipmentDescriptorFact,
    LevelDirection,
    MalformedFactPayloadError,
    MeasureUnit,
    Phase,
    Rational,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    RequiredQuantity,
    SizeKeyedQuantityFact,
    SizeQuantity,
    TimePeriod,
    TimeUnit,
    applicability_violations,
    fact_from_payload,
    fact_invariant_violations,
    fact_payload,
    representation_schema_hash,
)
from afterworlds.persistence.orm.mechanical import MechanicalComponentORM
from afterworlds.services.rules_authority.patches import InvalidPatchError
from afterworlds.services.rules_authority.patches import (
    _build_applicability as load_patch,
)
from tests.ingestion.mechanical.conftest import (
    NOW,
    RELEASE_BINDING,
    build_ledger,
    build_representation,
    candidate_of,
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


# ---------------------------------------------------------------------------
# The acceptance probe: a directly constructed proposal carrying one threshold
# ---------------------------------------------------------------------------

_ARTIFACT_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"
_PROBE_LEAF = "leaf-fraction-probe"
_PROBE_SPAN = derive_span_id(_PROBE_LEAF, 0, 28)
_PROBE_RECORD = "hazard.fraction-probe"


def _accept_with_applicability(applicability: Applicability):  # type: ignore[no-untyped-def]
    """Accept a proposal whose one component applies under *applicability*.

    Declared under the live contract, because a consumption threshold is
    schema-4 meaning; no prior, because this asks what acceptance does with the
    proposal's own nested value object rather than what a succession does.
    """
    span = SemanticSpan(
        span_id=_PROBE_SPAN,
        leaf_id=_PROBE_LEAF,
        char_start=0,
        char_end=28,
        disposition=SemanticDisposition.SUBSTANTIVE,
        review_state=ReviewState.PROPOSED,
    )
    prior = load_accepted_inputs(_ARTIFACT_PATH)
    proposal = MechanicalProposal(
        binding=prior.oracle.binding,
        policy_version=prior.oracle.policy_version,
        policy_hash=prior.oracle.policy_hash,
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
        proposed_spans=(
            ProposedSpan(span=span, origin="fraction-probe", rationale="probe"),
        ),
        proposed_representation=RepresentationDraft(
            records=(
                RecordDraft(semantic_key=_PROBE_RECORD, kind=RecordKind.GLOSSARY_RULE),
            ),
            components=(
                ComponentDraft(
                    record_key=_PROBE_RECORD,
                    semantic_key="accrual",
                    handling=ComponentHandling.STRUCTURED,
                    facts=(
                        ConditionLevelFact(
                            condition=ConditionKind.EXHAUSTION,
                            direction=LevelDirection.GAIN,
                            amount=1,
                        ),
                    ),
                    applies_when=applicability,
                ),
            ),
            prose_bindings=(),
            relationships=(),
            references=(),
            provenance=(),
        ),
        proposal_origin="test_schema_4_applicability_boundaries",
    )
    return accept_proposal(
        proposal,
        batch_id="fraction-probe-1",
        rule="the probe span",
        resolved_scope=(_PROBE_SPAN,),
        reviewer="Test",
        accepted_at="2026-08-28T00:00:00Z",
        prior=None,
    )


# ---------------------------------------------------------------------------
# Round 5 — the fraction is a Rational, and a Rational has invariants
# ---------------------------------------------------------------------------
#
# ``applicability_violations`` checked that ``fraction`` held the exact type and
# stopped there, so ``Rational(1, 0)``, ``Rational(1, -2)`` and ``Rational(-1, 2)``
# satisfied it. Every boundary above delegates to that function, so the invalid
# value survived acceptance, committed loading, persistence, overrides and
# publication validation — a zero denominator is not a number, and a negative
# numerator is not a *share* of a requirement.
#
# The fix delegates to ``_check_rational``, the rule the other four Rational
# owners already use. These tests pin that there is one definition of validity
# and that it did not silently get stronger.

#: Every way a ``Rational`` can be malformed, at the value-object level.
INVALID_FRACTIONS = [
    pytest.param(Rational(1, 0), "denominator", id="zero-denominator"),
    pytest.param(Rational(1, -2), "denominator", id="negative-denominator"),
    pytest.param(Rational(-1, 2), "numerator", id="negative-numerator"),
    pytest.param(Rational(True, 2), "numerator", id="boolean-numerator"),  # type: ignore[arg-type]
    pytest.param(Rational(1, False), "denominator", id="boolean-denominator"),  # type: ignore[arg-type]
    pytest.param(Rational("1", 2), "numerator", id="string-numerator"),  # type: ignore[arg-type]
    pytest.param(Rational(1, 2.0), "denominator", id="float-denominator"),  # type: ignore[arg-type]
]

#: What ``_check_rational`` admits, stated so the shared contract cannot be
#: quietly narrowed. Unreduced and improper fractions are legal: reduction is a
#: normalization this build deliberately does not perform, and a consumption
#: bound above one is a semantic question no numeric rule here answers.
VALID_FRACTIONS = [
    pytest.param(Rational(0, 1), id="zero"),
    pytest.param(Rational(1, 1), id="whole"),
    pytest.param(Rational(1, 2), id="one-half"),
    pytest.param(Rational(2, 4), id="unreduced"),
    pytest.param(Rational(3, 2), id="improper"),
]


def _consumption(fraction: Rational) -> Applicability:
    return Applicability(
        kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
        negated=False,
        comparison=Comparison.REACHES,
        required_quantity=RequiredQuantity.WATER,
        fraction=fraction,
    )


@pytest.mark.parametrize(("fraction", "member"), INVALID_FRACTIONS)
def test_direct_validation_refuses_an_invalid_fraction(
    fraction: Rational, member: str
) -> None:
    """The seam every other boundary delegates to."""
    findings = applicability_violations(_consumption(fraction))
    assert findings, fraction
    named = [
        f for f in findings if f"fraction.{member}" in f or "fraction must be" in f
    ]
    assert named, findings


@pytest.mark.parametrize("fraction", VALID_FRACTIONS)
def test_a_valid_fraction_is_not_refused(fraction: Rational) -> None:
    """The over-refusal control, and the guard on the shared contract.

    ``_check_rational`` admits any non-negative numerator over a positive
    denominator. Delegating to it must not import a stricter rule by accident —
    an unreduced or improper fraction is still a fraction.
    """
    assert applicability_violations(_consumption(fraction)) == []


@pytest.mark.parametrize(("fraction", "member"), INVALID_FRACTIONS)
def test_the_nested_fact_builder_refuses_an_invalid_fraction(
    fraction: Rational, member: str
) -> None:
    """``ConditionRemovalRestrictionFact.until``, through the fact validator."""
    fact = ConditionRemovalRestrictionFact(
        condition=ConditionKind.EXHAUSTION,
        cause_scoped=True,
        until=_consumption(fraction),
    )
    assert fact_invariant_violations(fact)


#: The same values on the wire, where each builder rebuilds a ``Rational`` from
#: its two stored members. ``True``/``"1"`` are what a hand-edited JSON column or
#: a patch body actually holds; ``0``/``-2`` are what a correct-looking one does.
INVALID_FRACTION_PAYLOADS = [
    pytest.param({"numerator": 1, "denominator": 0}, id="zero-denominator"),
    pytest.param({"numerator": 1, "denominator": -2}, id="negative-denominator"),
    pytest.param({"numerator": -1, "denominator": 2}, id="negative-numerator"),
    pytest.param({"numerator": True, "denominator": 2}, id="boolean-numerator"),
    pytest.param({"numerator": "1", "denominator": 2}, id="string-numerator"),
]


@pytest.mark.parametrize(("build", "error"), BOUNDARIES)
@pytest.mark.parametrize("fraction", INVALID_FRACTION_PAYLOADS)
def test_every_builder_refuses_an_invalid_fraction_in_its_own_words(
    build, error: type[Exception], fraction: dict[str, object]
) -> None:  # type: ignore[no-untyped-def]
    """Accepted-input loader, persisted-state loader, override patch builder.

    None of them needed a numeric rule of its own — each already validates the
    rebuilt value through ``applicability_violations``, so correcting the shared
    validator corrected all three. That is the property being pinned.
    """
    with pytest.raises(error):
        build({**applicability_payload(CONSUMPTION), "fraction": fraction})


@pytest.mark.parametrize("fraction", INVALID_FRACTION_PAYLOADS)
def test_the_nested_fact_builder_refuses_it_on_the_wire_too(
    fraction: dict[str, object],
) -> None:
    """The fourth builder, for the same reason and through the same validator."""
    payload = fact_payload(
        ConditionRemovalRestrictionFact(
            condition=ConditionKind.EXHAUSTION, cause_scoped=True, until=CONSUMPTION
        )
    )
    payload["until"] = {**payload["until"], "fraction": fraction}  # type: ignore[dict-item,index]
    with pytest.raises((MalformedFactPayloadError, ValueError)):
        fact_from_payload(payload)


@pytest.mark.parametrize(("fraction", "member"), INVALID_FRACTIONS)
def test_acceptance_refuses_a_proposal_carrying_an_invalid_threshold(
    fraction: Rational, member: str
) -> None:
    """A directly constructed proposal, through the real ``accept_proposal``.

    Nothing between a proposal object and accepted authority re-validates a
    nested value object except the draft validators — which is why the invariant
    has to live in the one they all call.
    """
    with pytest.raises(AcceptanceError):
        _accept_with_applicability(_consumption(fraction))


def test_acceptance_still_admits_a_valid_threshold() -> None:
    """The over-refusal control on the acceptance path."""
    result = _accept_with_applicability(_consumption(Rational(1, 2)))
    assert any(b.batch_id == "fraction-probe-1" for b in result.batches)


def test_publication_over_a_malformed_persisted_fraction_is_categorized(
    session: Session, committed_oracle
) -> None:  # type: ignore[no-untyped-def]
    """The gate returns a verdict rather than raising, as in round 2.

    A stored applicability whose fraction cannot pass its invariants is exactly
    the shape ``PersistedStateReconstructionError`` exists for, and
    ``PERSISTED_STATE`` is the category the gate owes that failure.
    """
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()
    session.execute(
        update(MechanicalComponentORM)
        .where(MechanicalComponentORM.projection_uuid == identified.projection_uuid)
        .values(
            applies_when={
                **applicability_payload(CONSUMPTION),
                "fraction": {"numerator": 1, "denominator": 0},
            }
        )
    )
    session.flush()

    result = run_publication_gate(
        session, identified.projection_uuid, oracle=committed_oracle
    )
    assert not result.passed
    assert GateFailureCategory.PERSISTED_STATE in {f.category for f in result.failures}


# ---------------------------------------------------------------------------
# The bounded Rational-owner audit, pinned
# ---------------------------------------------------------------------------

_BAD = Rational(1, 0)

RATIONAL_OWNERS = [
    pytest.param(
        SizeKeyedQuantityFact(
            quantity=RequiredQuantity.FOOD,
            period=TimePeriod.DAY,
            values=(
                SizeQuantity(
                    size=CreatureSize.MEDIUM, amount=_BAD, unit=MeasureUnit.POUND
                ),
            ),
        ),
        id="SizeQuantity.amount",
    ),
    pytest.param(
        CreatureChallengeFact(challenge_rating=_BAD, proficiency_bonus=2),
        id="CreatureChallengeFact.challenge_rating",
    ),
    pytest.param(
        EquipmentDescriptorFact(cost=None, weight_pounds=_BAD),
        id="EquipmentDescriptorFact.weight_pounds",
    ),
    pytest.param(
        DamageModificationFact(direction=DamageModDirection.REDUCE, factor=_BAD),
        id="DamageModificationFact.factor",
    ),
    pytest.param(
        ConditionRemovalRestrictionFact(
            condition=ConditionKind.EXHAUSTION,
            cause_scoped=True,
            until=_consumption(_BAD),
        ),
        id="Applicability.fraction",
    ),
]


@pytest.mark.parametrize("fact", RATIONAL_OWNERS)
def test_every_rational_owner_refuses_the_same_invalid_value(fact: object) -> None:
    """One definition of validity, exercised through each owner in turn.

    Four of these already delegated to ``_check_rational``; the fifth is what
    this round corrected. Kept as one table so a sixth owner added later has an
    obvious place to be, and no place to restate the rule instead.
    """
    assert fact_invariant_violations(fact), fact
