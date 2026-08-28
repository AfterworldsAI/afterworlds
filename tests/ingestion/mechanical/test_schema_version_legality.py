"""Version legality covers the whole schema-3 to schema-4 delta — CRD Issue 5d.

``post_schema_3_violations`` originally gated only *fields* registered in
``_POST_SCHEMA_3_FIELDS``. That left two thirds of the delta unguarded:

* a fact **family** schema 3 never had declared no post-schema-3 field, so it
  produced no violation, serialized identically under both requested versions,
  and would let ``verify_lift`` authorize restamped authority no schema-3
  reviewer could have reviewed; and
* an enum **member** added to a field schema 3 already had is invisible to any
  field-keyed rule, because the field is old and only the value is new.

The fix is an explicit auditable manifest — ``introduction_manifest()`` — carried
*inside* the schema payload, so the schema hash covers it. Removing a row to let
something through moves the hash, the destination pin in ``schema_lift`` no
longer matches, and ``lift_for`` refuses the transition. The legality contract
cannot be loosened while the registered lift keeps working.

Nothing here special-cases a family. Every assertion below is driven from the
manifest or from the live declarations, so a schema-5 addition that forgets its
row fails these tests rather than passing them silently.
"""

from __future__ import annotations

import pathlib
from dataclasses import replace

import pytest

from afterworlds.ingestion.corpus.hashing import canonical_bytes
from afterworlds.ingestion.mechanical.acceptance import AcceptanceError, accept_proposal
from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    load_accepted_inputs,
    load_oracle,
)
from afterworlds.ingestion.mechanical.projection import (
    SCHEMA_3_VERSION,
    LegacySchemaPayloadError,
    representation_payload,
)
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, ProposedSpan
from afterworlds.ingestion.mechanical.representation import (
    RECORD_OWNED_REFERENCE,
    AbilityScore,
    Applicability,
    ApplicabilityKind,
    AutomaticOutcome,
    Comparison,
    ComponentDraft,
    ConditionKind,
    ConditionLevelFact,
    ConditionRemovalRestrictionFact,
    CreatureSize,
    DamageModDirection,
    DamageModificationFact,
    DamageOutcome,
    DerivedQuantityFact,
    DiceExpression,
    DieSize,
    EffectTerminationFact,
    FactFamily,
    LevelDirection,
    MeasureUnit,
    Phase,
    Rational,
    RecordDraft,
    RecordKind,
    Recurrence,
    RecurrenceBoundary,
    ReferenceDraft,
    RepresentationDraft,
    RequiredQuantity,
    RollActor,
    RollContext,
    RollSpec,
    ScalingBasis,
    ScalingEffect,
    ScalingFact,
    SizeKeyedQuantityFact,
    SizeQuantity,
    Skill,
    TerminationScope,
    TimePeriod,
    TimeUnit,
    TrackedQuantity,
    introduction_manifest,
    post_schema_3_violations,
    representation_schema_hash,
    representation_schema_payload,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_3_HASH,
    SCHEMA_4_HASH,
    SCHEMA_4_VERSION,
    SchemaLiftError,
    lift_for,
    verify_lift,
)

COMMITTED_ORACLE = pathlib.Path(
    "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-36b786d8-fa2.json"
)
ARTIFACT_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"

# ---------------------------------------------------------------------------
# One live exemplar per axis of the delta
# ---------------------------------------------------------------------------

SCHEMA_4_ONLY = [
    pytest.param(EffectTerminationFact(), id="family-effect_termination"),
    pytest.param(
        SizeKeyedQuantityFact(
            quantity=RequiredQuantity.WATER,
            period=TimePeriod.DAY,
            values=(
                SizeQuantity(CreatureSize.TINY, Rational(1, 4), MeasureUnit.GALLON),
            ),
        ),
        id="family-size_keyed_quantity",
    ),
    pytest.param(
        ConditionRemovalRestrictionFact(
            condition=ConditionKind.EXHAUSTION,
            until=Applicability(
                kind=ApplicabilityKind.PHASE, negated=False, phase=Phase.ON_END
            ),
        ),
        id="family-condition_removal_restriction",
    ),
    pytest.param(
        DamageModificationFact(
            direction=DamageModDirection.REDUCE, factor=Rational(1, 2)
        ),
        id="family-damage_modification",
    ),
    pytest.param(
        DerivedQuantityFact(
            base=1, modifier=AbilityScore.CONSTITUTION, unit=TimeUnit.MINUTE
        ),
        id="family-derived_quantity",
    ),
    # Members added to vocabularies schema 3 already had, on fields schema 3
    # already had. No field-keyed rule can see any of these.
    pytest.param(
        Applicability(
            kind=ApplicabilityKind.QUANTITY_THRESHOLD,
            negated=False,
            quantity=TrackedQuantity.CONDITION_LEVEL,
            comparison=Comparison.LESS_THAN,
            value=3,
        ),
        id="member-Comparison.LESS_THAN",
    ),
    pytest.param(
        Applicability(
            kind=ApplicabilityKind.ROLL_OUTCOME,
            negated=False,
            outcome=AutomaticOutcome.SUCCESS,
        ),
        id="member-ApplicabilityKind.ROLL_OUTCOME",
    ),
    pytest.param(
        Applicability(
            kind=ApplicabilityKind.DAMAGE_OUTCOME,
            negated=False,
            damage_outcome=DamageOutcome.ANY_DAMAGE,
        ),
        id="member-DamageOutcome",
    ),
    pytest.param(
        ScalingFact(
            basis=ScalingBasis.DISTANCE_FALLEN,
            threshold=10,
            effect=ScalingEffect.DAMAGE,
            dice_amount=DiceExpression(1, DieSize.D6, 0),
        ),
        id="member-ScalingBasis.DISTANCE_FALLEN",
    ),
    pytest.param(
        DerivedQuantityFact(
            base=1, modifier=AbilityScore.CONSTITUTION, unit=TimeUnit.SECOND
        ),
        id="member-TimeUnit.SECOND",
    ),
    # Vocabularies schema 4 introduced whole.
    pytest.param(
        RollSpec(
            actor=RollActor.SUBJECT,
            context=RollContext.ABILITY_CHECK,
            ability=AbilityScore.DEXTERITY,
            skill=Skill.ACROBATICS,
        ),
        id="member-Skill",
    ),
    pytest.param(
        Recurrence(boundary=RecurrenceBoundary.END_OF_DAY),
        id="member-RecurrenceBoundary",
    ),
    pytest.param(
        EffectTerminationFact(scope=TerminationScope.OWNING_EFFECT),
        id="member-TerminationScope",
    ),
    # The H-8 ownership form.
    pytest.param(
        ReferenceDraft("r", RECORD_OWNED_REFERENCE, "text", "scope", "r2"),
        id="reference_ownership-record_owned",
    ),
]

#: Content schema 3 states perfectly well. The over-refusal control: a manifest
#: that classified a pre-existing member as schema-4-only would fail here.
SCHEMA_3_LEGAL = [
    pytest.param(
        Applicability(kind=ApplicabilityKind.PHASE, negated=False, phase=Phase.ON_END),
        id="phase-applicability",
    ),
    pytest.param(
        Applicability(
            kind=ApplicabilityKind.QUANTITY_THRESHOLD,
            negated=False,
            quantity=TrackedQuantity.CONDITION_LEVEL,
            comparison=Comparison.REACHES,
            value=3,
        ),
        id="pre-existing-Comparison-member",
    ),
    pytest.param(
        DiceExpression(2, DieSize.D6, 3),
        id="pre-existing-value-object",
    ),
    pytest.param(
        ReferenceDraft("r", "component", "text", "scope", "r2"),
        id="component-owned-reference",
    ),
]


# ---------------------------------------------------------------------------
# The contract, driven from the manifest rather than from a hand-written list
# ---------------------------------------------------------------------------


def test_every_manifest_row_has_an_exemplar_here() -> None:
    """Coverage guard: the manifest may not name something nothing exercises.

    Non-circular on purpose. It does not re-derive the delta — it asserts that
    each row a human put in the manifest is *demonstrated* by a live object in
    this module, so a schema-5 addition that lands a row without coverage fails
    here instead of being trusted.
    """
    exercised: set[str] = set()
    for param in SCHEMA_4_ONLY:
        (obj,) = param.values
        exercised |= _groups_exercised_by(obj)
    assert _MANIFEST_GROUPS - exercised == set(), sorted(_MANIFEST_GROUPS - exercised)


def _group_of(row: dict[str, object]) -> str:
    """The vocabulary or axis a manifest row belongs to.

    Keyed by the row's own rendered vocabulary — the sorted admitted values —
    because that is how the payload identifies one. No class name appears in the
    manifest, deliberately: the schema payload may not depend on anything the
    wire cannot show, and this test reads the payload rather than going around it.
    """
    vocabulary = row["vocabulary"]
    return str(row["kind"]) if vocabulary is None else repr(vocabulary)


_MANIFEST_GROUPS = {_group_of(row) for row in introduction_manifest()}


def _groups_exercised_by(obj: object) -> set[str]:
    """Which manifest groups *obj* actually trips, read from its own findings.

    Grouped rather than per row. A vocabulary is registered whole — all eighteen
    skills, both damage outcomes — and demanding an exemplar per member would be
    eighteen objects proving one rule. What must not happen silently is a
    *vocabulary or axis* landing with no exemplar at all, which is what this
    catches.
    """
    findings = post_schema_3_violations(obj, SCHEMA_3_VERSION)
    return {
        _group_of(row)
        for row in introduction_manifest()
        if any(repr(row["name"]) in f for f in findings)
    }


@pytest.mark.parametrize("obj", SCHEMA_4_ONLY)
def test_schema_3_refuses_every_schema_4_only_type_or_value(obj: object) -> None:
    """Every axis of the delta: families, widened vocabularies, ownership."""
    assert post_schema_3_violations(obj, SCHEMA_3_VERSION), obj


@pytest.mark.parametrize("obj", SCHEMA_4_ONLY)
def test_schema_4_admits_what_it_introduced(obj: object) -> None:
    """The other direction, so the rule is not simply "refuse everything"."""
    assert post_schema_3_violations(obj, SCHEMA_4_VERSION) == []


@pytest.mark.parametrize("obj", SCHEMA_3_LEGAL)
def test_legal_schema_3_content_is_not_over_refused(obj: object) -> None:
    """The over-refusal control.

    A member of a pre-existing vocabulary misclassified as schema-4-only would
    refuse content the earlier reviewer genuinely accepted.
    """
    assert post_schema_3_violations(obj, SCHEMA_3_VERSION) == []


def test_the_committed_oracle_is_legal_under_the_schema_it_declares() -> None:
    """The discriminating test.

    The committed artifact *is* accepted schema-3 content. Any finding here
    means the manifest over-classifies something, and the artifact — which no
    longer moves and cannot be edited — would be the thing it accused.
    """
    oracle = load_oracle(COMMITTED_ORACLE)
    assert post_schema_3_violations(oracle.representation, SCHEMA_3_VERSION) == []


# ---------------------------------------------------------------------------
# The seams
# ---------------------------------------------------------------------------


def test_verify_lift_refuses_a_restamped_prior(bounded_prior=None) -> None:  # type: ignore[no-untyped-def]
    """The seam the defect actually reached.

    A schema-3 prior carrying a schema-4-only family serializes identically
    under both requested versions, so byte-identity would "prove" it survived
    unchanged. The legality step runs first and refuses it as the restamp it is.
    """
    oracle = load_oracle(COMMITTED_ORACLE)
    tampered = replace(
        oracle.representation,
        components=(
            replace(
                oracle.representation.components[0],
                facts=(EffectTerminationFact(),),
            ),
            *oracle.representation.components[1:],
        ),
    )
    lift = lift_for(
        (SCHEMA_3_VERSION, SCHEMA_3_HASH), (SCHEMA_4_VERSION, SCHEMA_4_HASH)
    )
    with pytest.raises(SchemaLiftError) as raised:
        verify_lift(lift, tampered)
    assert "not accepted under the schema it names" in str(raised.value)


#: A leaf the committed artifact never touched, so every probe scope is disjoint.
_PROBE_LEAF = "leaf-acceptance-legality"
_PROBE_SPAN = derive_span_id(_PROBE_LEAF, 0, 28)
_PROBE_RECORD = "hazard.acceptance-legality"

#: Content schema 3 states, and content only schema 4 can state.
_CLEAN = ConditionLevelFact(
    condition=ConditionKind.EXHAUSTION, direction=LevelDirection.GAIN, amount=1
)
_SCHEMA_4_ONLY = EffectTerminationFact()


def _probe_proposal(fact: object, version: str, schema_hash: str, prior):  # type: ignore[no-untyped-def]
    """A minimal well-formed proposal over a span the prior never saw."""
    span = SemanticSpan(
        span_id=_PROBE_SPAN,
        leaf_id=_PROBE_LEAF,
        char_start=0,
        char_end=28,
        disposition=SemanticDisposition.SUBSTANTIVE,
        review_state=ReviewState.PROPOSED,
    )
    representation = RepresentationDraft(
        records=(
            RecordDraft(semantic_key=_PROBE_RECORD, kind=RecordKind.GLOSSARY_RULE),
        ),
        components=(
            ComponentDraft(
                record_key=_PROBE_RECORD,
                semantic_key="accrual",
                handling=ComponentHandling.STRUCTURED,
                facts=(fact,),  # type: ignore[arg-type]
            ),
        ),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )
    return MechanicalProposal(
        binding=prior.oracle.binding,
        policy_version=prior.oracle.policy_version,
        policy_hash=prior.oracle.policy_hash,
        schema_version=version,
        schema_hash=schema_hash,
        proposed_spans=(
            ProposedSpan(span=span, origin="legality-probe", rationale="probe"),
        ),
        proposed_representation=representation,
        proposal_origin="test_schema_version_legality",
    )


def _accept(fact: object, version: str, schema_hash: str, *, with_prior: bool):  # type: ignore[no-untyped-def]
    prior = load_accepted_inputs(ARTIFACT_PATH)
    return accept_proposal(
        _probe_proposal(fact, version, schema_hash, prior),
        batch_id="legality-probe-1",
        rule="the probe span",
        resolved_scope=(_PROBE_SPAN,),
        reviewer="Test",
        accepted_at="2026-08-28T00:00:00Z",
        prior=prior if with_prior else None,
    )


#: The three acceptance branches, named by which path through ``accept_proposal``
#: they take. Legality was previously checked only inside ``verify_lift`` — on
#: the *prior* — so the first two had no check at all and the third checked the
#: wrong half.
_BRANCHES = [
    pytest.param(SCHEMA_3_VERSION, SCHEMA_3_HASH, False, id="no-prior"),
    pytest.param(SCHEMA_3_VERSION, SCHEMA_3_HASH, True, id="equal-schema-prior"),
    pytest.param(SCHEMA_4_VERSION, SCHEMA_4_HASH, True, id="registered-lift-prior"),
]


@pytest.mark.parametrize(("version", "schema_hash", "with_prior"), _BRANCHES)
def test_every_acceptance_branch_accepts_content_its_schema_can_state(
    version: str, schema_hash: str, with_prior: bool
) -> None:
    """The over-refusal control, and the one the new guard could plausibly break.

    A guard that refused here would block honest acceptance outright, which is a
    worse failure than the one it was added to fix.
    """
    fact = _CLEAN if version == SCHEMA_3_VERSION else _SCHEMA_4_ONLY
    result = _accept(fact, version, schema_hash, with_prior=with_prior)
    assert any(b.batch_id == "legality-probe-1" for b in result.batches)


@pytest.mark.parametrize(("version", "schema_hash", "with_prior"), _BRANCHES)
def test_no_acceptance_branch_admits_meaning_its_schema_cannot_state(
    version: str, schema_hash: str, with_prior: bool
) -> None:
    """The defect, closed on every branch rather than only where a lift runs.

    A schema-3 proposal carrying a schema-4-only family was previously accepted
    with ``lifts == ()`` on two of these three paths, producing accepted
    authority its own declaration cannot state — and that a later lift would
    then refuse, stranding it.

    The schema-4 branch is included deliberately even though it cannot fail this
    way today: it is the branch a future succession would extend, and a guard
    that ran only on the older paths would rot the moment schema 5 exists.
    """
    if version == SCHEMA_4_VERSION:
        # Nothing is schema-5-only yet, so this branch's negative case is that
        # the *prior* half is checked too — the half ``verify_lift`` owns.
        assert _accept(
            _SCHEMA_4_ONLY, version, schema_hash, with_prior=with_prior
        ).lifts
        return
    with pytest.raises(AcceptanceError) as raised:
        _accept(_SCHEMA_4_ONLY, version, schema_hash, with_prior=with_prior)
    assert "was not built under the schema it names" in str(raised.value)


def test_the_refusal_names_the_family_rather_than_the_field() -> None:
    """The message has to say what is wrong, not merely that something is."""
    with pytest.raises(AcceptanceError) as raised:
        _accept(_SCHEMA_4_ONLY, SCHEMA_3_VERSION, SCHEMA_3_HASH, with_prior=True)
    message = str(raised.value)
    assert FactFamily.EFFECT_TERMINATION.value in message
    assert SCHEMA_4_VERSION in message


def test_serialization_refuses_the_h8_ownership_under_schema_3() -> None:
    """The serialization seam, for the one axis that has one of its own."""
    from tests.ingestion.mechanical.conftest import build_representation

    base = build_representation()
    draft = replace(
        base,
        references=(
            ReferenceDraft(
                "spell:wish", RECORD_OWNED_REFERENCE, "t", "s", "spell:wish"
            ),
        ),
    )
    with pytest.raises(LegacySchemaPayloadError):
        representation_payload(draft, schema_version=SCHEMA_3_VERSION)


# ---------------------------------------------------------------------------
# Identity binding
# ---------------------------------------------------------------------------


def test_the_manifest_is_carried_inside_the_schema_identity() -> None:
    """What makes the contract unloosenable without invalidating the lift."""
    payload = representation_schema_payload()
    assert payload["introductions"] == introduction_manifest()
    assert representation_schema_hash() == SCHEMA_4_HASH


def test_dropping_a_manifest_row_moves_the_hash_and_breaks_the_pin() -> None:
    """Loosening the contract invalidates the registered lift, by construction.

    Simulated on the payload rather than by mutating module state: the property
    under test is that the hash *covers* the manifest, and a payload missing a
    row hashes differently — so the destination pin no longer matches and
    ``lift_for`` refuses the transition.
    """
    from afterworlds.ingestion.corpus.hashing import sha256_hex

    full = representation_schema_payload()
    loosened = {
        **full,
        "introductions": [
            row
            for row in introduction_manifest()
            if row["name"] != FactFamily.EFFECT_TERMINATION.value
        ],
    }
    assert canonical_bytes(full) != canonical_bytes(loosened)
    assert sha256_hex(canonical_bytes(loosened)) != SCHEMA_4_HASH


def test_the_schema_3_source_pin_is_unmoved() -> None:
    """Re-pinning the destination may never touch the source.

    The source pin names the contract a reviewer actually accepted. Rewriting it
    would silently re-authorize a transition nobody reviewed, which is the exact
    restamp this module exists to refuse.
    """
    assert (
        SCHEMA_3_HASH
        == "43ed330d3b3630d37ed92122fd87cc2c170863bab4465e53c727f1b8c6b86e05"  # noqa: E501  # pragma: allowlist secret
    )
