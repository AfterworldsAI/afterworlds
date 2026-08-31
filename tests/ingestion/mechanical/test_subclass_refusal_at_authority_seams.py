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

import json
import pathlib
from dataclasses import dataclass, fields, replace
from typing import Any, cast

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
    accepted_inputs_payload,
    load_accepted_inputs,
    load_oracle,
    oracle_identity,
)
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    reconstruct_candidate,
)
from afterworlds.ingestion.mechanical.projection import (
    identify_projection,
    validate_candidate,
    validate_schema_binding,
)
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, ProposedSpan
from afterworlds.ingestion.mechanical.representation import (
    _CLOSED_TYPES,
    _DRAFT_ELEMENT_TYPES,
    AbilityCheckFact,
    AbilityScore,
    Applicability,
    ApplicabilityKind,
    ComponentDraft,
    ComponentOption,
    CreatureSize,
    DamageFact,
    DamageResponseFact,
    DamageResponseKind,
    DamageScope,
    DamageType,
    DcKind,
    DiceExpression,
    DieSize,
    FactQualifier,
    MeasureUnit,
    ParticipantRole,
    Phase,
    Rational,
    RecordDraft,
    RecordKind,
    Recurrence,
    RecurrenceBoundary,
    RepresentationDraft,
    RequiredQuantity,
    RollActor,
    RollContext,
    RollSpec,
    SizeComparison,
    SizeKeyedQuantityFact,
    SizeQuantity,
    Skill,
    TimePeriod,
    UnknownFactFamilyError,
    declared_meaning_violations,
    fact_invariant_violations,
    fact_key,
    fact_payload,
    held_structure_violations,
    representation_draft_violations,
    representation_schema_hash,
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
COMMITTED_ORACLE_IDENTITY = "a0f0bd2f6f6f05d3b0b46b63d1dfa9c5e4c3bf0741118b063a5d2b6adf401fda"  # noqa: E501  # pragma: allowlist secret
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


@pytest.mark.parametrize(("tamper", "expected"), TOP_LEVEL_AXES)
def test_direct_candidate_schema_validation_refuses_them_too(
    tamper, expected: str
) -> None:  # type: ignore[no-untyped-def]
    """The third seam reading the shared boundary, asserted rather than inferred.

    ``validate_schema_binding`` reports rather than raises, so an illegal
    candidate reaches the publication gate as a verdict instead of an exception
    out of the payload renderer. That is the path a persisted-state
    reconstruction takes, where neither the loader nor ``accept_proposal``
    stands between the candidate and publication.
    """
    candidate = candidate_of(
        RELEASE_BINDING,
        build_ledger(),
        tamper(build_representation()),  # type: ignore[arg-type]
    )
    findings = validate_schema_binding(candidate)
    assert any(expected in f for f in findings), findings


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


# ---------------------------------------------------------------------------
# Round 11 — the container, not only the element
# ---------------------------------------------------------------------------
#
# Round 10 closed the *top-level* boundary: the draft, the exact ``tuple`` type
# of each of the six collections, and the exact type of every element in them.
# It did not reach the tuples nested inside those elements, and every one of
# them was checked with ``isinstance`` — which admits a subclass — or was not
# checked at all.
#
# Three distinct leaks, and each is a different failure:
#
#   hidden state     a subclass carries meaning no canonical payload emits, so
#                    two facts asserting different authority hash identically;
#   hostile __iter__ the validator and the serializer observe different contents
#                    from one object, so the finding produced is about content
#                    the artifact does not have;
#   hostile __hash__ ``ProvenanceClaim.target_key`` is a *key*, resolved by set
#                    membership, so a subclass can match a target it is not.
#
# The rule is ``exact_tuple_violations`` and it never touches the value — no
# iteration, no length, and deliberately no ``repr``, because a refusal that
# renders the thing it refuses has observed it.


class SmuggledTuple(tuple):  # type: ignore[type-arg]
    """Hidden meaning-bearing state that no canonical payload emits."""

    scope = "allies only"


class HostileTuple(tuple):  # type: ignore[type-arg]
    """Refuses to be observed at all: iteration *and* rendering raise.

    ``__repr__`` is overridden alongside ``__iter__`` on purpose. It is what
    makes this a test of the *helper* rather than of the call site: reusing
    ``exact_type_violations`` here would interpolate the value into the finding
    and raise out of the refusal itself.
    """

    def __iter__(self):  # type: ignore[no-untyped-def]
        raise AssertionError("the hostile container's __iter__ was invoked")

    def __repr__(self) -> str:
        raise AssertionError("the hostile container's __repr__ was invoked")


class TwoFacedTuple(tuple):  # type: ignore[type-arg]
    """Answers ``__iter__`` with contents that disagree with what it holds."""

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(())


ALTERNATIVE_ROLLS = (
    RollSpec(
        context=RollContext.ABILITY_CHECK,
        actor=RollActor.SUBJECT,
        ability=AbilityScore.DEXTERITY,
        skill=Skill.ACROBATICS,
    ),
    RollSpec(
        context=RollContext.ABILITY_CHECK,
        actor=RollActor.SUBJECT,
        ability=AbilityScore.STRENGTH,
        skill=Skill.ATHLETICS,
    ),
)
SIZE_ROWS = (SizeQuantity(CreatureSize.TINY, Rational(1, 4), MeasureUnit.GALLON),)
SIZE_COMPARISONS = (
    SizeComparison(category=CreatureSize.TINY, measured=ParticipantRole.SUBJECT),
)
_OPTION_A = ComponentOption(
    semantic_key="a", facts=(DamageFact(damage_type=DamageType.FIRE, flat_amount=1),)
)
_OPTION_B = ComponentOption(
    semantic_key="b", facts=(DamageFact(damage_type=DamageType.COLD, flat_amount=1),)
)


def _ability_check(alternatives: object) -> AbilityCheckFact:
    return AbilityCheckFact(
        ability=AbilityScore.STRENGTH,
        dc_kind=DcKind.FIXED,
        dc_value=15,
        skill=Skill.ATHLETICS,
        alternatives=cast(Any, alternatives),
    )


def _size_keyed(values: object) -> SizeKeyedQuantityFact:
    return SizeKeyedQuantityFact(
        quantity=RequiredQuantity.WATER,
        period=TimePeriod.DAY,
        values=cast(Any, values),
    )


def _damage_response(except_types: object) -> DamageResponseFact:
    return DamageResponseFact(
        response=DamageResponseKind.IMMUNITY,
        scope=DamageScope.ALL,
        except_types=cast(Any, except_types),
    )


def _size_applicability(any_of: object) -> Applicability:
    return Applicability(
        kind=ApplicabilityKind.SIZE_COMPARISON,
        negated=False,
        any_of=cast(Any, any_of),
    )


def _first_component(**overrides: object) -> RepresentationDraft:
    """The bounded fixture with one field of its first component replaced."""
    base = build_representation()
    return replace(
        base,
        components=(replace(base.components[0], **overrides), *base.components[1:]),
    )


def _with_fact(fact: object) -> RepresentationDraft:
    return _first_component(facts=(fact,), options=(), fact_qualifiers=())


def _with_applicability(applies_when: object) -> RepresentationDraft:
    return _first_component(applies_when=applies_when)


def _with_provenance(target_key: object) -> RepresentationDraft:
    base = build_representation()
    return replace(
        base,
        provenance=(
            replace(base.provenance[0], target_key=cast(Any, target_key)),
            *base.provenance[1:],
        ),
    )


#: Every tuple-valued field of a serialized frozen authority dataclass that is
#: nested *below* the top-level boundary round 10 closed. Derived from the
#: dataclass declarations rather than listed from the review comment — see
#: ``test_the_audited_inventory_is_the_whole_declared_surface``, which fails if
#: a new authority dataclass adds a tuple field and this table does not gain a
#: row for it.
NESTED_TUPLE_FIELDS = [
    pytest.param(
        lambda c: _with_fact(_ability_check(c(ALTERNATIVE_ROLLS))),
        "alternatives",
        id="AbilityCheckFact.alternatives",
    ),
    pytest.param(
        lambda c: _with_fact(_size_keyed(c(SIZE_ROWS))),
        "values",
        id="SizeKeyedQuantityFact.values",
    ),
    pytest.param(
        lambda c: _with_fact(_damage_response(c((DamageType.FIRE,)))),
        "except_types",
        id="DamageResponseFact.except_types",
    ),
    pytest.param(
        lambda c: _with_applicability(_size_applicability(c(SIZE_COMPARISONS))),
        "any_of",
        id="Applicability.any_of",
    ),
    pytest.param(
        lambda c: _first_component(facts=c(build_representation().components[0].facts)),
        "facts",
        id="ComponentDraft.facts",
    ),
    pytest.param(
        lambda c: _first_component(facts=(), options=c((_OPTION_A, _OPTION_B))),
        "options",
        id="ComponentDraft.options",
    ),
    pytest.param(
        lambda c: _first_component(
            fact_qualifiers=c(build_representation().components[0].fact_qualifiers)
        ),
        "fact_qualifiers",
        id="ComponentDraft.fact_qualifiers",
    ),
    pytest.param(
        lambda c: _first_component(
            facts=(),
            options=(
                replace(_OPTION_A, facts=cast(Any, c(_OPTION_A.facts))),
                _OPTION_B,
            ),
        ),
        "facts",
        id="ComponentOption.facts",
    ),
    pytest.param(
        lambda c: _with_provenance(c(build_representation().provenance[0].target_key)),
        "target_key",
        id="ProvenanceClaim.target_key",
    ),
]


def test_the_audited_inventory_is_the_whole_declared_surface() -> None:
    """The audit is bounded by the declarations, not by the review comment.

    Derives every tuple-valued field of every serialized authority dataclass
    from ``fields()`` and asserts the parametrized table above accounts for all
    of them — the nine nested ones by name, and the six top-level collections as
    the boundary round 10 already closed. A new authority dataclass with a tuple
    field fails here rather than shipping unaudited.
    """
    declared = {
        f"{cls.__name__}.{field.name}"
        for cls in set(_CLOSED_TYPES)
        | set(_DRAFT_ELEMENT_TYPES.values())
        | {RepresentationDraft}
        for field in fields(cls)
        if str(field.type).lower().startswith("tuple")
    }
    top_level = {f"RepresentationDraft.{name}" for name in _DRAFT_ELEMENT_TYPES}
    audited = {case.id for case in NESTED_TUPLE_FIELDS}

    assert top_level <= declared, "the six collections round 10 closed"
    assert declared - top_level == audited, (
        "every nested tuple-valued authority field must have a witness above; "
        f"unaudited: {sorted(declared - top_level - audited)}"
    )


@pytest.mark.parametrize(("tamper", "field"), NESTED_TUPLE_FIELDS)
def test_every_nested_tuple_field_refuses_a_subclass_carrying_hidden_state(
    tamper, field: str
) -> None:  # type: ignore[no-untyped-def]
    """The reported defect, one witness per audited field.

    ``isinstance`` admitted every one of these, and the element scans behind it
    iterated the container to find that out.
    """
    findings = held_structure_violations(tamper(SmuggledTuple))
    assert any(
        f"{field} must be tuple, got SmuggledTuple" in f for f in findings
    ), findings


@pytest.mark.parametrize(("tamper", "field"), NESTED_TUPLE_FIELDS)
def test_every_nested_tuple_field_refuses_before_observing_the_container(
    tamper, field: str
) -> None:  # type: ignore[no-untyped-def]
    """The ordering requirement, proved by a container that raises if observed.

    Both ``__iter__`` and ``__repr__`` raise, so this fails loudly if validation
    iterates the collection *or* renders it into the finding. Nothing normalizes
    it and nothing inspects it: the type name is the whole report.
    """
    findings = held_structure_violations(tamper(HostileTuple))
    assert any(
        f"{field} must be tuple, got HostileTuple" in f for f in findings
    ), findings


def test_the_two_faced_container_is_refused_rather_than_read() -> None:
    """The sharpest form of the leak, stated as its own case.

    A container answering ``__iter__`` with contents that disagree with what it
    holds made validation and serialization observe different objects. Before
    this round the invariant returned a finding about the *empty* iteration —
    a complaint about content the fact does not have — rather than refusing the
    container. Indexing still shows both rolls, so the disagreement is real.
    """
    two_faced = TwoFacedTuple(ALTERNATIVE_ROLLS)
    assert len(list(iter(two_faced))) == 0
    assert len(two_faced) == 2

    findings = fact_invariant_violations(_ability_check(two_faced))
    assert list(findings) == ["alternatives must be tuple, got TwoFacedTuple"]


@pytest.mark.parametrize(("tamper", "field"), NESTED_TUPLE_FIELDS)
def test_exact_tuples_with_valid_elements_still_pass(
    tamper, field: str
) -> None:  # type: ignore[no-untyped-def]
    """The over-refusal control: the same shapes, held in an ordinary tuple.

    Each case is built with ``tuple`` in place of the subclass, so anything the
    container rule rejects here would be rejecting honest authority. Only the
    container finding is asserted absent — a case may still have its own
    semantic findings, which are not this round's subject.
    """
    findings = held_structure_violations(tamper(tuple))
    assert not [f for f in findings if "must be tuple" in f], findings


def test_the_bounded_fixture_and_committed_artifact_report_nothing() -> None:
    """Honest authority, through both halves of the closed-structure rule."""
    honest = build_representation()
    assert held_structure_violations(honest) == []
    assert declared_meaning_violations(honest, SCHEMA_3_VERSION) == []

    committed = load_accepted_inputs(ARTIFACT_PATH).oracle.representation
    assert held_structure_violations(committed) == []
    assert declared_meaning_violations(committed, SCHEMA_3_VERSION) == []


# ---------------------------------------------------------------------------
# The seams, so the shared path protects all of them
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("tamper", "field"), NESTED_TUPLE_FIELDS)
def test_a_verified_lift_refuses_every_nested_tuple_subclass(
    tamper, field: str
) -> None:  # type: ignore[no-untyped-def]
    """Byte-identity would certify these: they canonicalize to the base payload."""
    lift = lift_for(
        (SCHEMA_3_VERSION, SCHEMA_3_HASH), (SCHEMA_4_VERSION, SCHEMA_4_HASH)
    )
    with pytest.raises(SchemaLiftError) as raised:
        verify_lift(lift, tamper(SmuggledTuple))
    assert "not admissible together" in str(raised.value)
    assert f"{field} must be tuple" in str(raised.value)


@pytest.mark.parametrize(("tamper", "field"), NESTED_TUPLE_FIELDS)
@pytest.mark.parametrize("target", [SCHEMA_4, SCHEMA_3], ids=["crossing", "no-op"])
def test_lifting_accepted_inputs_refuses_them_on_both_paths(
    tamper, field: str, target: tuple[str, str]
) -> None:  # type: ignore[no-untyped-def]
    """Including R10-1's equal-schema no-op, which returns its input untouched."""
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    hostile = replace(
        inputs, oracle=replace(inputs.oracle, representation=tamper(SmuggledTuple))
    )
    with pytest.raises(SchemaLiftError) as raised:
        lift_accepted_inputs(hostile, target)
    assert f"{field} must be tuple" in str(raised.value)


@pytest.mark.parametrize(("tamper", "field"), NESTED_TUPLE_FIELDS)
def test_direct_candidate_schema_validation_refuses_them(
    tamper, field: str
) -> None:  # type: ignore[no-untyped-def]
    """Publication validation, which reports rather than raises."""
    candidate = candidate_of(RELEASE_BINDING, build_ledger(), tamper(SmuggledTuple))
    findings = validate_schema_binding(candidate)
    assert any(f"{field} must be tuple" in f for f in findings), findings


def test_acceptance_refuses_them_before_merging_or_minting_an_identity() -> None:
    """The seam with no ledger and no corpus, where the merge itself is the risk.

    Asserted as two facts rather than one: acceptance raises, and it raises with
    nothing produced — so no merged representation and no oracle identity exist
    to have been minted from a container whose contents nothing can trust.
    """
    prior = load_accepted_inputs(ARTIFACT_PATH)
    tampered = _with_fact(_ability_check(SmuggledTuple(ALTERNATIVE_ROLLS)))
    proposal = MechanicalProposal(
        binding=prior.oracle.binding,
        policy_version=prior.oracle.policy_version,
        policy_hash=prior.oracle.policy_hash,
        schema_version=prior.oracle.schema_version,
        schema_hash=prior.oracle.schema_hash,
        proposed_spans=(
            ProposedSpan(
                span=SemanticSpan(
                    span_id=PROBE_SPAN,
                    leaf_id=PROBE_LEAF,
                    char_start=0,
                    char_end=28,
                    disposition=SemanticDisposition.SUBSTANTIVE,
                    review_state=ReviewState.PROPOSED,
                ),
                origin="nested-container-probe",
                rationale="probe",
            ),
        ),
        proposed_representation=tampered,
        proposal_origin="test_subclass_refusal_at_authority_seams",
    )
    with pytest.raises(AcceptanceError) as raised:
        accept_proposal(
            proposal,
            batch_id="nested-container-probe-1",
            rule="the probe span",
            resolved_scope=(PROBE_SPAN,),
            reviewer="Test",
            accepted_at="2026-08-31T00:00:00Z",
            prior=prior,
        )
    assert "alternatives must be tuple" in str(raised.value)

    # The prior is untouched by the refused acceptance, so nothing was merged.
    assert load_accepted_inputs(ARTIFACT_PATH).batches == prior.batches


def test_the_committed_artifact_is_unmoved_by_this_round() -> None:
    """Zero movement, asserted where a container rule could have reached it."""
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    draft = inputs.oracle.representation
    assert accepted_inputs_payload(inputs) == json.loads(
        ARTIFACT_PATH.read_text(encoding="utf-8")
    )
    assert (len(draft.provenance), len(draft.references)) == (185, 15)
    assert [b.proposal_identity for b in inputs.batches] == [
        inputs.batches[0].proposal_identity
    ]
    assert oracle_identity(inputs.oracle) == COMMITTED_ORACLE_IDENTITY
    assert representation_schema_hash() == SCHEMA_4_HASH
    # Every top-level collection is an exact tuple in the artifact as committed,
    # which is what makes the new rule a refusal rather than a restriction.
    assert all(type(getattr(draft, name)) is tuple for name in _DRAFT_ELEMENT_TYPES)
