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

import copy
import json
import pathlib
from dataclasses import replace

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.hashing import canonical_bytes
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
    accepted_inputs_payload,
    load_accepted_inputs,
    load_oracle,
)
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.projection import (
    SCHEMA_3_VERSION,
    LegacySchemaPayloadError,
    identify_projection,
    representation_payload,
    validate_schema_binding,
)
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, ProposedSpan
from afterworlds.ingestion.mechanical.representation import (
    RECORD_OWNED_REFERENCE,
    REPRESENTATION_SCHEMA_VERSION,
    AbilityCheckFact,
    AbilityScore,
    Applicability,
    ApplicabilityKind,
    AutomaticOutcome,
    Comparison,
    ComponentDraft,
    ConditionKind,
    ConditionLevelFact,
    ConditionRemovalRestrictionFact,
    ConsumptionBand,
    CreatureSize,
    DamageFact,
    DamageInterval,
    DamageModDirection,
    DamageModificationFact,
    DamageOutcome,
    DamageType,
    DcKind,
    DerivedQuantityFact,
    DiceExpression,
    DieSize,
    DistanceUnit,
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
    SCHEMA_5_HASH,
    SCHEMA_5_VERSION,
    SchemaLiftError,
    accepted_schema_contracts,
    lift_accepted_inputs,
    lift_for,
    schema_binding_violations,
    verify_lift,
)
from afterworlds.persistence.orm.mechanical import MechanicalProjectionORM
from tests.ingestion.mechanical.conftest import (
    NOW,
    RELEASE_BINDING,
    build_ledger,
    build_representation,
    candidate_of,
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
    # Schema 5 refuses this basis on ``ScalingFact`` through the *invariant*
    # contract, which is a different question from *version legality* and is
    # asked by a different function. The exemplar stays as it is because what it
    # has to exercise is the schema-4 vocabulary member, and this is the shape
    # schema 4 admitted it in.
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
#: Everything schema 5 introduced, one exemplar per axis of the delta. Two of
#: the three are *fields* rather than vocabulary members, so they are seen by the
#: field registries rather than by the manifest; ``DistanceUnit`` is the one new
#: closed vocabulary and is the manifest row this list has to cover.
SCHEMA_5_ONLY = [
    pytest.param(
        AbilityCheckFact(
            ability=AbilityScore.CONSTITUTION,
            dc_kind=DcKind.FIXED,
            dc_value=10,
            context=RollContext.SAVING_THROW,
        ),
        id="required-AbilityCheckFact.context",
    ),
    pytest.param(
        DamageFact(
            damage_type=DamageType.BLUDGEONING,
            dice=DiceExpression(1, DieSize.D6, 0),
            per=DamageInterval(
                basis=ScalingBasis.DISTANCE_FALLEN, amount=10, unit=DistanceUnit.FOOT
            ),
        ),
        id="field-DamageFact.per+member-DistanceUnit",
    ),
    pytest.param(
        Applicability(
            kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
            negated=False,
            band=ConsumptionBand(
                quantity=RequiredQuantity.FOOD,
                period=TimePeriod.DAY,
                upper=Rational(1, 2),
            ),
        ),
        id="field-Applicability.band",
    ),
]

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
    for param in (*SCHEMA_4_ONLY, *SCHEMA_5_ONLY):
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


@pytest.mark.parametrize("obj", SCHEMA_5_ONLY)
def test_schema_4_refuses_every_schema_5_only_type_or_value(obj: object) -> None:
    """The same delta one succession later: schema 4 cannot state schema 5."""
    assert post_schema_3_violations(obj, SCHEMA_4_VERSION), obj


@pytest.mark.parametrize("obj", SCHEMA_5_ONLY)
def test_schema_5_admits_what_it_introduced(obj: object) -> None:
    """And the other direction, so the rule is not "refuse everything newer"."""
    assert post_schema_3_violations(obj, SCHEMA_5_VERSION) == []


@pytest.mark.parametrize("obj", SCHEMA_4_ONLY)
def test_schema_5_still_admits_every_schema_4_introduction(obj: object) -> None:
    """A later contract states its predecessor's admissions as well as its own."""
    assert post_schema_3_violations(obj, SCHEMA_5_VERSION) == []


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
    assert representation_schema_hash() == SCHEMA_5_HASH


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


# ---------------------------------------------------------------------------
# Round 4 — the invariant at every ingress, not only where the schema changes
# ---------------------------------------------------------------------------
#
# ``load_accepted_inputs`` reconstructed accepted authority from committed bytes
# and never asked whether that content was legal under the schema the file
# declares. With no lift evidence ``lift_chain_violations`` had nothing to
# object to, so a schema-3 artifact carrying an ``EffectTerminationFact`` — with
# its obligations reconciled, because obligations are derived from the same
# content — became committed accepted authority.
#
# Every case below runs through the real loader on the real committed artifact,
# tampered one field at a time. Each of them loaded clean before this round.


def _tampered(mutate) -> dict:  # type: ignore[no-untyped-def, type-arg]
    """The committed artifact payload with exactly one thing changed."""
    raw = copy.deepcopy(json.loads(ARTIFACT_PATH.read_text(encoding="utf-8")))
    mutate(raw)
    return raw


def _smuggle_a_schema_4_family(raw: dict) -> None:  # type: ignore[type-arg]
    """A family schema 3 never had, *and* the obligation that reconciles it.

    The obligation edit is the point: obligations are derived from the accepted
    representation, so an artifact that adds a family and updates its record
    obligation to match is internally consistent everywhere except in what its
    declared schema is allowed to state.
    """
    component = next(
        c
        for c in raw["representation"]["components"]
        if c["semantic_key"] == "exhaustion_levels"
    )
    component["facts"].append(
        {
            "family": FactFamily.EFFECT_TERMINATION.value,
            "scope": TerminationScope.OWNING_EFFECT.value,
        }
    )
    obligation = next(
        o for o in raw["obligations"] if o["record_key"] == "condition.exhaustion"
    )
    obligation["structured_fact_families"] = sorted(
        set(obligation["structured_fact_families"])
        | {FactFamily.EFFECT_TERMINATION.value}
    )


def _smuggle_a_schema_4_vocabulary_member(raw: dict) -> None:  # type: ignore[type-arg]
    """A value schema 3 Comparison does not admit, on a field schema 3 had."""
    component = next(
        c for c in raw["representation"]["components"] if c["applies_when"]
    )
    component["applies_when"]["comparison"] = Comparison.LESS_THAN.value


def _smuggle_a_schema_4_field(raw: dict) -> None:  # type: ignore[type-arg]
    """A post-schema-3 field holding meaning on a family schema 3 did have."""
    for component in raw["representation"]["components"]:
        for fact in component["facts"]:
            if fact["family"] == FactFamily.CONDITION_LEVEL.value:
                fact["cause_scoped"] = True
                return
    raise AssertionError("no condition_level fact to carry the field")


def _smuggle_a_record_owned_reference(raw: dict) -> None:  # type: ignore[type-arg]
    """H-8 ownership, which the schema-3 reference contract cannot express."""
    raw["representation"]["references"][0][
        "from_component_key"
    ] = RECORD_OWNED_REFERENCE


def _declare_an_unknown_version(raw: dict) -> None:  # type: ignore[type-arg]
    raw["representation_schema"]["version"] = "5d-representation-schema-99"


def _declare_an_invented_hash(raw: dict) -> None:  # type: ignore[type-arg]
    raw["representation_schema"]["hash"] = "f" * 64


def _declare_a_mismatched_known_pair(raw: dict) -> None:  # type: ignore[type-arg]
    """Schema 3 version with the schema 4 hash: two real halves, no contract."""
    raw["representation_schema"]["hash"] = SCHEMA_4_HASH


_ILLEGAL_ARTIFACTS = [
    pytest.param(_smuggle_a_schema_4_family, "effect_termination", id="family"),
    pytest.param(_smuggle_a_schema_4_vocabulary_member, "less_than", id="vocabulary"),
    pytest.param(_smuggle_a_schema_4_field, "cause_scoped", id="meaning-bearing-field"),
    pytest.param(
        _smuggle_a_record_owned_reference, "owned", id="record-owned-reference"
    ),
    pytest.param(_declare_an_unknown_version, "not a contract", id="unknown-version"),
    pytest.param(_declare_an_invented_hash, "not a contract", id="invented-hash"),
    pytest.param(
        _declare_a_mismatched_known_pair, "not a contract", id="mismatched-known-pair"
    ),
]


@pytest.mark.parametrize(("mutate", "expected"), _ILLEGAL_ARTIFACTS)
def test_committed_bytes_are_refused_when_they_are_not_admissible(  # type: ignore[no-untyped-def]
    tmp_path, mutate, expected: str
) -> None:
    """Every axis of the delta, and every way the declaration can be wrong."""
    path = pathlib.Path(tmp_path) / "tampered.json"
    path.write_text(json.dumps(_tampered(mutate)), encoding="utf-8")

    with pytest.raises(OracleLoadError) as raised:
        load_accepted_inputs(path)
    message = str(raised.value)
    assert "is not admissible under it" in message
    assert expected in message


def test_the_committed_artifact_still_loads_and_is_byte_identical() -> None:
    """The over-refusal control, and the one that cannot be allowed to move.

    Written back out through the same writer and compared against the committed
    bytes: this guard sits on the ingress path the committed file itself takes,
    so "still loads" is not enough — it has to still be the same artifact.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    committed = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    assert (inputs.oracle.schema_version, inputs.oracle.schema_hash) == (
        SCHEMA_3_VERSION,
        SCHEMA_3_HASH,
    )
    assert inputs.lifts == ()
    assert accepted_inputs_payload(inputs) == committed


def test_lifted_schema_4_authority_loads(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The other half of the recognition set: a destination pair, really reached."""
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    # Stopping at schema 4 deliberately: this is about a *destination* pair
    # being recognized on the ingress path, and schema 4 is one this build no
    # longer implements — which is exactly the case worth proving.
    lifted, records = lift_accepted_inputs(inputs, (SCHEMA_4_VERSION, SCHEMA_4_HASH))
    path = pathlib.Path(tmp_path) / "lifted.json"
    path.write_text(
        json.dumps(accepted_inputs_payload(replace(lifted, lifts=records))),
        encoding="utf-8",
    )

    loaded = load_accepted_inputs(path)
    assert (loaded.oracle.schema_version, loaded.oracle.schema_hash) == (
        SCHEMA_4_VERSION,
        SCHEMA_4_HASH,
    )
    assert (
        schema_binding_violations(
            loaded.oracle.representation, (SCHEMA_4_VERSION, SCHEMA_4_HASH)
        )
        == []
    )


def test_the_recognized_contracts_are_exactly_the_live_pair_and_the_registry() -> None:
    """Stated once, so the seams cannot disagree about what supported means.

    Serializable is deliberately not the same as admissible: schema 1 and
    schema 2 payloads are still reproducible for historical reconstruction, and
    reproducing an identity is not admitting new accepted authority under it.
    """
    assert accepted_schema_contracts() == {
        (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash()),
        (SCHEMA_3_VERSION, SCHEMA_3_HASH),
        (SCHEMA_4_VERSION, SCHEMA_4_HASH),
    }


_UNRECOGNIZED_PAIRS = [
    pytest.param("5d-representation-schema-99", SCHEMA_3_HASH, id="unknown-version"),
    pytest.param(SCHEMA_3_VERSION, "f" * 64, id="invented-hash"),
    pytest.param(SCHEMA_3_VERSION, SCHEMA_4_HASH, id="mismatched-known-pair"),
]


@pytest.mark.parametrize(("version", "schema_hash"), _UNRECOGNIZED_PAIRS)
@pytest.mark.parametrize("with_prior", [False, True], ids=["no-prior", "equal-schema"])
def test_acceptance_refuses_a_pair_that_names_no_contract(
    version: str, schema_hash: str, with_prior: bool
) -> None:
    """The sibling of the legality defect, on the paths that have no lift.

    The content here is clean schema-3 content — only the declared pair is
    wrong. Without the recognition half a proposal could be accepted, and its
    artifact committed, under a union nothing in this build implements.
    """
    with pytest.raises(AcceptanceError) as raised:
        _accept(_CLEAN, version, schema_hash, with_prior=with_prior)
    assert "not admissible under it" in str(raised.value)


def test_the_publication_gate_returns_a_typed_schema_refusal(  # type: ignore[no-untyped-def]
    session: Session, committed_oracle
) -> None:
    """A reconstructed candidate whose rows outrun its declaration.

    Persisted legally under the live contract, then downgraded in place — the
    shape a hand-edited row or a rolled-back deployment produces. Canonicalizing
    it raises, and the gate contract is that a caller receives a verdict, so the
    assertion is on the *category* rather than on a validator called directly.
    """
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()
    session.execute(
        update(MechanicalProjectionORM)
        .where(MechanicalProjectionORM.projection_uuid == identified.projection_uuid)
        .values(representation_schema_version="5d-representation-schema-99")
    )
    session.flush()

    result = run_publication_gate(
        session, identified.projection_uuid, oracle=committed_oracle
    )
    assert not result.passed
    assert GateFailureCategory.SCHEMA_MISMATCH in {f.category for f in result.failures}


def test_publication_reports_a_structure_outside_the_closed_declaration() -> None:
    """The half of the invariant no version check can see.

    A subclassed nested value object canonicalizes to its declared base payload,
    so it is legal under *every* version and still misrepresents what the
    candidate carries. A candidate can be constructed directly, so neither the
    loader nor ``accept_proposal`` stands between it and publication.
    """
    from tests.ingestion.mechanical.test_subclass_refusal_at_authority_seams import (
        _with_nested_subclass,
    )

    candidate = candidate_of(RELEASE_BINDING, build_ledger(), _with_nested_subclass())
    findings = validate_schema_binding(candidate)
    assert any("must be DiceExpression" in f for f in findings), findings
