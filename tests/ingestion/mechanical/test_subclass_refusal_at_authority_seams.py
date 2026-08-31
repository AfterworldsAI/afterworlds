"""No undeclared subclass reaches an authority-bearing operation — CRD Issue 5d.

Schema 4's canonical walker resolves an instance to the closed class it declares
(``_declared_type``), so a subclass's payload is a whitelist of declared fields
rather than whatever the subclass added. That is deliberate and merged — see
``test_review_round_4_closed_structures`` — and it is *only* sound because the
exact-type gates refuse such a value before it can be persisted. The property it
rests on is a strong one and worth stating rather than assuming:

    Two instances of a subclass asserting **different** authority canonicalize
    to byte-identical payloads and share one derived identity.

This module audits every path where that identity is authoritative — hashing,
merging, persistence, gating, publication, and the override door — and pins the
refusal at each. The audit found one open seam and this is where its closure is
proved: ``accept_proposal`` merges two representations and mints an oracle
identity, and it has neither a ledger nor a bound corpus, so it could not call
``validate_representation``. It now runs ``held_structure_violations``, the
nested half of the same rule ``representation_draft_violations`` states for the
top level.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, fields, replace

import pytest

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
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    reconstruct_candidate,
)
from afterworlds.ingestion.mechanical.projection import (
    identify_projection,
    validate_candidate,
)
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, ProposedSpan
from afterworlds.ingestion.mechanical.representation import (
    Applicability,
    ApplicabilityKind,
    ComponentDraft,
    ComponentOption,
    CreatureSize,
    DamageFact,
    DamageType,
    DiceExpression,
    DieSize,
    FactQualifier,
    MeasureUnit,
    Phase,
    Rational,
    RecordDraft,
    RecordKind,
    Recurrence,
    RecurrenceBoundary,
    RepresentationDraft,
    RequiredQuantity,
    RollActor,
    SizeKeyedQuantityFact,
    SizeQuantity,
    TimePeriod,
    UnknownFactFamilyError,
    declared_meaning_violations,
    fact_key,
    fact_payload,
    held_structure_violations,
    representation_draft_violations,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_3_HASH,
    SCHEMA_3_VERSION,
    SCHEMA_4_HASH,
    SCHEMA_4_VERSION,
    SchemaLiftError,
    lift_accepted_inputs,
    lift_for,
    verify_lift,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from tests.ingestion.mechanical.conftest import (
    NOW,
    RELEASE_BINDING,
    SPELL_KEY,
    bound_corpus,
    build_ledger,
    build_representation,
    candidate_of,
)

COMMITTED_ORACLE = pathlib.Path(
    "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-36b786d8-fa2.json"
)
ARTIFACT_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"
SCHEMA_3 = (SCHEMA_3_VERSION, SCHEMA_3_HASH)
SCHEMA_4 = (SCHEMA_4_VERSION, SCHEMA_4_HASH)

#: A leaf the committed artifact never touched, so the probe scope is disjoint.
PROBE_LEAF = "leaf-subclass-probe"
PROBE_SPAN = derive_span_id(PROBE_LEAF, 0, 28)
PROBE_RECORD = "hazard.subclass-probe"


# ---------------------------------------------------------------------------
# The subclasses, one per structure the walker narrows
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiceWithScope(DiceExpression):
    """Extra meaning-bearing state no payload emits."""

    scope: str = ""


@dataclass(frozen=True)
class ApplicabilityWithScope(Applicability):
    scope: str = ""


@dataclass(frozen=True)
class RecurrenceWithScope(Recurrence):
    scope: str = ""


@dataclass(frozen=True)
class OptionWithScope(ComponentOption):
    scope: str = ""


@dataclass(frozen=True)
class QualifierWithScope(FactQualifier):
    scope: str = ""


@dataclass(frozen=True)
class SizeQuantityWithScope(SizeQuantity):
    scope: str = ""


def _damage(dice: DiceExpression) -> DamageFact:
    return DamageFact(damage_type=DamageType.FIRE, dice=dice)


#: A fact with no nested structure of its own, so a qualifier case fails for the
#: qualifier rather than for what it qualifies.
_FLAT = DamageFact(damage_type=DamageType.FIRE, flat_amount=3)


def _with_nested_subclass():
    """The bounded fixture whose first component holds a subclassed dice value."""
    base = build_representation()
    tampered = replace(
        base.components[0], facts=(_damage(DiceWithScope(2, DieSize.D6, 3, "allies")),)
    )
    return replace(base, components=(tampered, *base.components[1:]))


# ---------------------------------------------------------------------------
# The property the whole audit rests on
# ---------------------------------------------------------------------------


def test_two_subclasses_asserting_different_authority_share_one_payload() -> None:
    """The leak, stated rather than assumed. Every refusal below exists for this."""
    near = _damage(DiceWithScope(2, DieSize.D6, 3, "allies"))
    far = _damage(DiceWithScope(2, DieSize.D6, 3, "enemies"))
    assert near != far
    assert fact_payload(near) == fact_payload(far)
    assert fact_key(near) == fact_key(far)


def test_a_fact_subclass_cannot_even_be_serialized() -> None:
    """The *family* union is closed by exact type, so this half never got in."""

    @dataclass(frozen=True)
    class SneakyDamage(DamageFact):
        scope: str = ""

    with pytest.raises(UnknownFactFamilyError):
        fact_payload(SneakyDamage(damage_type=DamageType.FIRE))


# ---------------------------------------------------------------------------
# Each seam, in the order the user's audit names them
# ---------------------------------------------------------------------------


def test_merging_refuses_a_nested_subclass_before_minting_an_identity() -> None:
    """The seam the audit found open.

    ``accept_proposal`` has no ledger and no corpus, so it cannot run
    ``validate_representation``. Without ``held_structure_violations`` two
    proposals asserting different nested authority would merge identically and
    share one accepted oracle identity.
    """
    findings = held_structure_violations(_with_nested_subclass())
    assert any("must be DiceExpression" in f for f in findings), findings
    # ...and the top-level gate genuinely does not see it, which is why the
    # nested half had to exist.
    assert representation_draft_violations(_with_nested_subclass()) == []


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        pytest.param(
            lambda c: replace(
                c, facts=(_damage(DiceWithScope(1, DieSize.D6, 0, "x")),)
            ),
            "must be DiceExpression",
            id="nested-value-object",
        ),
        pytest.param(
            lambda c: replace(
                c,
                applies_when=ApplicabilityWithScope(
                    kind=ApplicabilityKind.PHASE, negated=False, phase=Phase.ON_END
                ),
            ),
            "must be Applicability",
            id="component-applicability",
        ),
        pytest.param(
            lambda c: replace(
                c,
                recurs=RecurrenceWithScope(
                    boundary=RecurrenceBoundary.END_OF_TURN, whose=RollActor.SUBJECT
                ),
            ),
            "must be Recurrence",
            id="component-recurrence",
        ),
        pytest.param(
            lambda c: replace(
                c,
                facts=(),
                options=(
                    OptionWithScope(semantic_key="a", facts=(_damage(None),)),
                    ComponentOption(semantic_key="b", facts=(_damage(None),)),
                ),
            ),
            "must be ComponentOption",
            id="option",
        ),
        pytest.param(
            lambda c: replace(
                c,
                facts=(_FLAT,),
                fact_qualifiers=(
                    QualifierWithScope(
                        fact_key=fact_key(_FLAT),
                        option_key="",
                        applies_when=Applicability(
                            kind=ApplicabilityKind.PHASE,
                            negated=False,
                            phase=Phase.ON_END,
                        ),
                    ),
                ),
            ),
            "must be FactQualifier",
            id="fact-qualifier",
        ),
        pytest.param(
            lambda c: replace(
                c,
                facts=(
                    SizeKeyedQuantityFact(
                        quantity=RequiredQuantity.WATER,
                        period=TimePeriod.DAY,
                        values=(
                            SizeQuantityWithScope(
                                CreatureSize.TINY, Rational(1, 4), MeasureUnit.GALLON
                            ),
                        ),
                    ),
                ),
            ),
            "size quantities",
            id="size-quantity",
        ),
    ],
)
def test_every_narrowed_structure_is_refused_at_the_merge_seam(
    mutate, expected: str
) -> None:  # type: ignore[no-untyped-def]
    """One case per structure ``_declared_type`` narrows. None is exempt."""
    base = build_representation()
    draft = replace(base, components=(mutate(base.components[0]), *base.components[1:]))
    assert any(expected in f for f in held_structure_violations(draft))


def test_the_walker_reports_nothing_against_the_committed_oracle() -> None:
    """The discriminating test: honest accepted authority must produce no finding.

    A walker that fired here would be over-strict, and the committed artifact —
    which no longer moves and cannot be edited — would be the thing it was
    accusing.
    """
    oracle = load_oracle(COMMITTED_ORACLE)
    assert held_structure_violations(oracle.representation) == []


def test_a_verified_lift_refuses_a_nested_subclass() -> None:
    """Byte-identity is the wrong proof to run on a payload that misrepresents.

    A subclassed value object survives the lift's element-by-element comparison
    for exactly the reason it survives everywhere: it canonicalizes to its
    declared base. Proving *that* unchanged proves the wrong thing.
    """
    lift = lift_for(
        (SCHEMA_3_VERSION, SCHEMA_3_HASH), (SCHEMA_4_VERSION, SCHEMA_4_HASH)
    )
    with pytest.raises(SchemaLiftError) as raised:
        verify_lift(lift, _with_nested_subclass())
    assert "not admissible together" in str(raised.value)
    assert "must be DiceExpression" in str(raised.value)


def test_validation_refuses_a_nested_subclass_before_gating_or_publication() -> None:
    """The gate and publication both read a validated draft; this is that gate."""
    findings = validate_representation(
        _with_nested_subclass(), build_ledger(), bound_corpus()
    )
    assert any("must be DiceExpression" in f for f in findings), findings


def test_persistence_stores_only_declared_state(session) -> None:  # type: ignore[no-untyped-def]
    """Storage never receives the undeclared half, so nothing comes to rest in it.

    ``persist_draft`` deliberately does *not* re-validate — it writes the
    canonical payload, which the walker has already narrowed to declared fields.
    Reconstruction therefore returns the honest declared object, and the
    undeclared state has no column to land in. This is asserted rather than
    assumed because "the payload is narrowed" is the whole reason the seam
    audit had to look at identity rather than at stored bytes.
    """
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), _with_nested_subclass())
    )
    persist_draft(session, identified, now=NOW)
    session.flush()
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    dice = rebuilt.representation.components[0].facts[0].dice  # type: ignore[union-attr]
    assert type(dice) is DiceExpression
    assert not hasattr(dice, "scope")


def test_publication_refuses_a_subclass_derived_candidate() -> None:
    """The gate's own validator is the refusal before anything is published.

    ``validate_candidate`` is what ``run_publication_gate`` runs at step 5, and
    it reports the subclass as a semantic-validation failure rather than
    publishing a projection whose payload does not represent what it holds.
    """
    candidate = candidate_of(RELEASE_BINDING, build_ledger(), _with_nested_subclass())
    findings = validate_candidate(candidate, bound_corpus())
    assert any("must be DiceExpression" in f for f in findings), findings


def test_the_override_door_cannot_construct_a_subclass_at_all() -> None:
    """Safe by construction rather than by a gate, and pinned so it stays so.

    Every patch reaches ``patch_payload`` through ``patch_from_payload``, which
    rebuilds facts through the projection's own ``fact_from_payload`` and value
    objects through their declared constructors. There is no JSON that names a
    subclass, so no gate is needed and none is claimed.
    """
    from afterworlds.models.enums import OverrideOperationEnum
    from afterworlds.services.rules_authority.patches import patch_from_payload
    from afterworlds.services.rules_authority.targets import (
        MechanicalTarget,
        MechanicalTargetKind,
    )

    patch = patch_from_payload(
        {
            "patch": "append_fact",
            "fact": fact_payload(_damage(DiceExpression(2, DieSize.D6, 3))),
        },
        operation=OverrideOperationEnum.APPEND,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=SPELL_KEY,
            component_key="descriptor",
        ),
    )
    assert type(patch.fact) is DamageFact  # type: ignore[union-attr]
    assert type(patch.fact.dice) is DiceExpression  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# And the seam refuses through its real entry point, not only its helper
# ---------------------------------------------------------------------------


def test_accept_proposal_refuses_rather_than_merging() -> None:
    """End to end at the real seam: an ``AcceptanceError``, not a merged artifact.

    Against the committed prior, so the refusal is proved on the path a real
    acceptance takes rather than on a synthetic one built to suit the test.
    """
    prior = load_accepted_inputs(ARTIFACT_PATH)
    span = SemanticSpan(
        span_id=PROBE_SPAN,
        leaf_id=PROBE_LEAF,
        char_start=0,
        char_end=28,
        disposition=SemanticDisposition.SUBSTANTIVE,
        review_state=ReviewState.PROPOSED,
    )
    tampered = RepresentationDraft(
        records=(
            RecordDraft(semantic_key=PROBE_RECORD, kind=RecordKind.GLOSSARY_RULE),
        ),
        components=(
            ComponentDraft(
                record_key=PROBE_RECORD,
                semantic_key="accrual",
                handling=ComponentHandling.STRUCTURED,
                facts=(_damage(DiceWithScope(2, DieSize.D6, 3, "allies")),),
            ),
        ),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )
    proposal = MechanicalProposal(
        binding=prior.oracle.binding,
        policy_version=prior.oracle.policy_version,
        policy_hash=prior.oracle.policy_hash,
        schema_version=prior.oracle.schema_version,
        schema_hash=prior.oracle.schema_hash,
        proposed_spans=(
            ProposedSpan(span=span, origin="subclass-probe", rationale="probe"),
        ),
        proposed_representation=tampered,
        proposal_origin="test_subclass_refusal_at_authority_seams",
    )
    with pytest.raises(AcceptanceError) as raised:
        accept_proposal(
            proposal,
            batch_id="subclass-probe-1",
            rule="the probe span",
            resolved_scope=(PROBE_SPAN,),
            reviewer="Test",
            accepted_at="2026-08-26T00:00:00Z",
            prior=prior,
        )
    # Refused by the binding invariant, which runs before the merge — the merge
    # seam still carries its own check, and either would refuse this.
    assert "not admissible under it" in str(raised.value)
    assert "must be DiceExpression" in str(raised.value)


# ---------------------------------------------------------------------------
# Round 10 — the closed structure is one structure, checked whole
# ---------------------------------------------------------------------------
#
# The nested half above was closed at the merge seam and, through
# ``declared_meaning_violations``, at every seam that admits authority. The
# *top* half was not: ``representation_draft_violations`` existed and was
# enforced at ``accept_proposal`` and ``validate_representation``, but the
# shared invariant never called it — so ``verify_lift`` certified a subclassed
# draft, a subclassed collection and a subclassed record as unchanged. All
# three canonicalize to their declared base's payload, which is precisely why
# byte-identity is the wrong proof to run on them.
#
# Three axes, because the top-level boundary has three and closing two of them
# is how this was missed the first time.


def _hostile_draft(base: RepresentationDraft) -> object:
    """Axis 1: the draft itself, carrying a field no payload emits."""

    @dataclass(frozen=True)
    class DraftWithScope(RepresentationDraft):
        scope: str = "allies"

    return DraftWithScope(**{f.name: getattr(base, f.name) for f in fields(base)})


def _hostile_collection(base: RepresentationDraft) -> RepresentationDraft:
    """Axis 2: one collection held as a ``tuple`` subclass.

    A tuple subclass *is* a tuple, so ``isinstance`` admits it. It can carry
    undeclared metadata the payload never emits, and it can override
    ``__iter__`` so validation and serialization observe different elements from
    the same object.
    """

    class RecordsWithScope(tuple):  # type: ignore[type-arg]
        scope = "allies"

    return replace(base, records=RecordsWithScope(base.records))


def _hostile_element(base: RepresentationDraft) -> RepresentationDraft:
    """Axis 3: one top-level element of a collection."""

    @dataclass(frozen=True)
    class RecordWithScope(RecordDraft):
        scope: str = "allies"

    first = base.records[0]
    return replace(
        base,
        records=(
            RecordWithScope(**{f.name: getattr(first, f.name) for f in fields(first)}),
            *base.records[1:],
        ),
    )


TOP_LEVEL_AXES = [
    pytest.param(
        _hostile_draft, "representation must be RepresentationDraft", id="draft"
    ),
    pytest.param(
        _hostile_collection, "representation.records must be tuple", id="collection"
    ),
    pytest.param(
        _hostile_element, "representation.records[0] must be RecordDraft", id="element"
    ),
]


@pytest.mark.parametrize(("tamper", "expected"), TOP_LEVEL_AXES)
def test_the_shared_invariant_refuses_every_top_level_subclass(
    tamper, expected: str
) -> None:  # type: ignore[no-untyped-def]
    """The common boundary, so no seam reading it can be missing an axis.

    Exactly one finding, and it is the shape finding. That is the ordering
    requirement stated as an assertion: ``RepresentationDraft`` is not a closed
    value object, so the post-schema-3 walk would resolve a hostile draft to
    *itself* and read its smuggled field, and the nested walk would consult a
    hostile collection's ``__iter__``. Neither runs, because the shape is
    refused before anything observes the value.
    """
    findings = declared_meaning_violations(
        tamper(build_representation()),  # type: ignore[arg-type]
        SCHEMA_3_VERSION,
    )
    assert len(findings) == 1, findings
    assert findings[0].startswith(expected)


@pytest.mark.parametrize(("tamper", "expected"), TOP_LEVEL_AXES)
def test_a_verified_lift_refuses_every_top_level_subclass(
    tamper, expected: str
) -> None:  # type: ignore[no-untyped-def]
    """The reported defect: each of these was certified as unchanged."""
    lift = lift_for(
        (SCHEMA_3_VERSION, SCHEMA_3_HASH), (SCHEMA_4_VERSION, SCHEMA_4_HASH)
    )
    with pytest.raises(SchemaLiftError) as raised:
        verify_lift(lift, tamper(build_representation()))  # type: ignore[arg-type]
    assert "not admissible together" in str(raised.value)
    assert expected in str(raised.value)


@pytest.mark.parametrize(("tamper", "expected"), TOP_LEVEL_AXES)
@pytest.mark.parametrize("target", [SCHEMA_4, SCHEMA_3], ids=["crossing", "no-op"])
def test_lifting_accepted_inputs_refuses_every_top_level_subclass(
    tamper, expected: str, target: tuple[str, str]
) -> None:  # type: ignore[no-untyped-def]
    """Both paths through ``lift_accepted_inputs``, including the new no-op.

    The no-op is where an axis would most easily reopen: it returns the input
    untouched, so if it did not check the shape it would hand a hostile artifact
    back certified as already at its target.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    tampered = tamper(inputs.oracle.representation)  # type: ignore[arg-type]
    hostile = replace(inputs, oracle=replace(inputs.oracle, representation=tampered))
    with pytest.raises(SchemaLiftError) as raised:
        lift_accepted_inputs(hostile, target)
    assert expected in str(raised.value)


def test_the_exact_base_types_still_lift_and_validate() -> None:
    """The over-refusal control: honest declared shapes are untouched.

    A shape check that fired here would be accusing the bounded fixture and the
    committed artifact of the thing it exists to refuse.
    """
    honest = build_representation()
    assert declared_meaning_violations(honest, SCHEMA_3_VERSION) == []
    lift = lift_for(
        (SCHEMA_3_VERSION, SCHEMA_3_HASH), (SCHEMA_4_VERSION, SCHEMA_4_HASH)
    )
    assert verify_lift(lift, honest).lift_id == "5d-lift-schema-3-to-4"

    committed = load_accepted_inputs(ARTIFACT_PATH).oracle.representation
    assert declared_meaning_violations(committed, SCHEMA_3_VERSION) == []


def test_the_nested_half_is_still_reached_when_the_shape_is_honest() -> None:
    """The early return closes an axis; it must not shadow the nested rule.

    A ``return`` on the top-level findings would be a regression if it also
    returned when there were none — this pins that the nested walk still runs
    for a draft whose top-level shape is exactly right.
    """
    findings = declared_meaning_violations(_with_nested_subclass(), SCHEMA_3_VERSION)
    assert any("must be DiceExpression" in f for f in findings), findings
