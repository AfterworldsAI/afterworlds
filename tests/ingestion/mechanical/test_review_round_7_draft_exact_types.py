"""The complete representation-draft exact-type boundary — PR #155, round 8.

Owner Decision 2026-08-20: close the closed-structure identity leak coherently
across the whole top-level draft boundary before schema 2 merges.

**The earlier accounting was incomplete, and this corrects it.** PR #155's
round-4 sibling audit named four deferred structures — ``ComponentDraft``,
``RecordDraft``, ``ProseBindingDraft``, ``ProvenanceClaim``. That list missed
``RelationshipDraft`` and ``ReferenceDraft``, which are direct
``RepresentationDraft`` collection elements exactly as the other four are, and
did not consider ``RepresentationDraft`` itself, which can equally be
subclassed. The real boundary is **seven** types, and the set is derived from
``dataclasses.fields`` here rather than restated, so an eighth cannot be added
silently.

The leak: a subclass may carry an undeclared meaning-bearing field, shadow a
declared one, or redefine ``__eq__``/``__hash__``. Validation reads these
objects as their base classes while ``representation_payload`` emits only the
declared base fields, so distinct authority validates cleanly, canonicalizes to
the same bytes, and receives one projection identity. A hostile ``__eq__`` need
only be consulted once, in a set or dict comprehension, to collapse two
elements into one.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import get_args

import pytest

from afterworlds.ingestion.mechanical.acceptance import AcceptanceError
from afterworlds.ingestion.mechanical.projection import representation_payload
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    ComponentDraft,
    ComponentHandling,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RelationshipDraft,
    RelationshipKind,
    RepresentationDraft,
    representation_draft_violations,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from tests.ingestion.mechanical.conftest import bound_corpus, build_ledger

# ---------------------------------------------------------------------------
# The boundary, derived rather than restated
# ---------------------------------------------------------------------------

#: Field -> the exact element type it must hold. Mirrors the production map;
#: the change-detector below proves the two agree with the dataclass itself.
EXPECTED_ELEMENTS: dict[str, type] = {
    "records": RecordDraft,
    "components": ComponentDraft,
    "prose_bindings": ProseBindingDraft,
    "relationships": RelationshipDraft,
    "references": ReferenceDraft,
    "provenance": ProvenanceClaim,
}


def test_every_direct_collection_is_accounted_for() -> None:
    """A future sibling cannot enter the authority boundary ungated.

    This is the change detector the incomplete round-4 accounting needed. It
    reads the dataclass, so adding a seventh collection to
    ``RepresentationDraft`` fails here rather than silently bypassing the gate.
    """
    declared = {f.name for f in fields(RepresentationDraft)}
    assert declared == set(EXPECTED_ELEMENTS), (
        "RepresentationDraft's collections changed; the exact-type gate and "
        "this table must change with it"
    )
    for field in fields(RepresentationDraft):
        (element_type,) = get_args(field.type) or (None,)
        if element_type is Ellipsis or element_type is None:
            continue
        assert EXPECTED_ELEMENTS[field.name].__name__ in str(field.type), field.name


# ---------------------------------------------------------------------------
# Valid base-class fixtures
# ---------------------------------------------------------------------------

RECORD = RecordDraft(semantic_key="spell:wish", kind=RecordKind.SPELL)
OTHER_RECORD = RecordDraft(semantic_key="spell:mend", kind=RecordKind.SPELL)
COMPONENT = ComponentDraft(
    record_key="spell:wish",
    semantic_key="descriptor",
    handling=ComponentHandling.PROSE_BOUND,
    irreducibility_reason_code="open_ended_effect",
)
BINDING = ProseBindingDraft(
    record_key="spell:wish",
    component_key="descriptor",
    chunk_id="chunk-1",
    span_id="span-1",
    chunk_char_start=0,
    chunk_char_end=10,
    irreducibility_reason_code="open_ended_effect",
)
RELATIONSHIP = RelationshipDraft(
    source_record_key="spell:wish",
    target_record_key="spell:mend",
    kind=RelationshipKind.SPELL_LIST_MEMBER,
)
REFERENCE = ReferenceDraft(
    from_record_key="spell:wish",
    from_component_key="descriptor",
    source_text="mending",
    scope_key="spell:wish",
    target_record_key="spell:mend",
)
CLAIM = ProvenanceClaim(
    ProvenanceTargetKind.RECORD, ("spell:wish",), "span-1", ProvenanceRole.PRIMARY
)


def draft(**overrides: object) -> RepresentationDraft:
    fields_: dict[str, object] = {
        "records": (RECORD, OTHER_RECORD),
        "components": (COMPONENT,),
        "prose_bindings": (BINDING,),
        "relationships": (RELATIONSHIP,),
        "references": (REFERENCE,),
        "provenance": (CLAIM,),
    }
    fields_.update(overrides)
    return RepresentationDraft(**fields_)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 1. Every susceptible structure rejects an extra-field subclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RecordWithTier(RecordDraft):
    tier: int = 3


@dataclass(frozen=True)
class ComponentWithWeight(ComponentDraft):
    weight: int = 7


@dataclass(frozen=True)
class BindingWithPriority(ProseBindingDraft):
    priority: int = 2


@dataclass(frozen=True)
class RelationshipWithStrength(RelationshipDraft):
    strength: int = 5


@dataclass(frozen=True)
class ReferenceWithConfidence(ReferenceDraft):
    confidence: int = 9


@dataclass(frozen=True)
class ClaimWithWeight(ProvenanceClaim):
    weight: int = 4


SUBCLASSED = [
    (
        "records",
        (RecordWithTier(semantic_key="spell:wish", kind=RecordKind.SPELL),),
        "RecordDraft",
    ),
    (
        "components",
        (
            ComponentWithWeight(
                record_key="spell:wish",
                semantic_key="descriptor",
                handling=ComponentHandling.PROSE_BOUND,
                irreducibility_reason_code="open_ended_effect",
            ),
        ),
        "ComponentDraft",
    ),
    (
        "prose_bindings",
        (
            BindingWithPriority(
                record_key="spell:wish",
                component_key="descriptor",
                chunk_id="chunk-1",
                span_id="span-1",
                chunk_char_start=0,
                chunk_char_end=10,
                irreducibility_reason_code="open_ended_effect",
            ),
        ),
        "ProseBindingDraft",
    ),
    (
        "relationships",
        (
            RelationshipWithStrength(
                source_record_key="spell:wish",
                target_record_key="spell:mend",
                kind=RelationshipKind.SPELL_LIST_MEMBER,
            ),
        ),
        "RelationshipDraft",
    ),
    (
        "references",
        (
            ReferenceWithConfidence(
                from_record_key="spell:wish",
                from_component_key="descriptor",
                source_text="mending",
                scope_key="spell:wish",
                target_record_key="spell:mend",
            ),
        ),
        "ReferenceDraft",
    ),
    (
        "provenance",
        (
            ClaimWithWeight(
                ProvenanceTargetKind.RECORD,
                ("spell:wish",),
                "span-1",
                ProvenanceRole.PRIMARY,
            ),
        ),
        "ProvenanceClaim",
    ),
]


@pytest.mark.parametrize(
    ("field_name", "value", "expected"),
    SUBCLASSED,
    ids=[c[0] for c in SUBCLASSED],
)
def test_an_extra_field_subclass_is_refused(
    field_name: str, value: tuple[object, ...], expected: str
) -> None:
    findings = representation_draft_violations(draft(**{field_name: value}))
    assert findings
    assert all(f"must be {expected}" in f for f in findings), findings


def test_the_subclass_matrix_covers_every_collection() -> None:
    """The parametrization above is exhaustive, and stays that way."""
    assert {c[0] for c in SUBCLASSED} == set(EXPECTED_ELEMENTS)


# ---------------------------------------------------------------------------
# 6. RepresentationDraft itself
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DraftWithExtraCollection(RepresentationDraft):
    """A top-level collection no payload emits — the leak, one level up."""

    rulings: tuple[str, ...] = ()


def test_the_draft_itself_rejects_a_subclass() -> None:
    hostile = DraftWithExtraCollection(
        records=(RECORD, OTHER_RECORD),
        components=(COMPONENT,),
        prose_bindings=(BINDING,),
        relationships=(RELATIONSHIP,),
        references=(REFERENCE,),
        provenance=(CLAIM,),
        rulings=("a house ruling nothing serializes",),
    )
    (finding,) = representation_draft_violations(hostile)
    assert "representation must be RepresentationDraft" in finding


def test_a_hostile_draft_is_refused_before_its_elements_are_read() -> None:
    """One finding about the draft, not six about elements it happens to hold."""
    hostile = DraftWithExtraCollection(
        records=(RecordWithTier(semantic_key="spell:wish", kind=RecordKind.SPELL),),
        components=(),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )
    assert len(representation_draft_violations(hostile)) == 1


# ---------------------------------------------------------------------------
# 2. Field shadowing fails before the shadowed field is read
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RecordShadowingKind(RecordDraft):
    """``kind`` shadowed with something that is not a ``RecordKind`` at all."""

    kind: object = "not-a-record-kind"  # type: ignore[assignment]


@dataclass(frozen=True)
class ClaimShadowingRole(ProvenanceClaim):
    """``role`` shadowed with something that is not a ``ProvenanceRole``.

    The last declared field, so the subclass still constructs — the point is
    that the gate refuses the object before anything reads ``role`` and
    reports a misleading enum finding about it.
    """

    role: object = "not-a-provenance-role"  # type: ignore[assignment]


def test_a_shadowed_enum_field_fails_as_a_type_refusal() -> None:
    """Not as a downstream ``AttributeError`` or a misleading enum finding."""
    findings = representation_draft_violations(
        draft(records=(RecordShadowingKind(semantic_key="spell:wish"),))
    )
    assert findings == [
        "representation.records[0] must be RecordDraft, got RecordShadowingKind"
    ]


def test_a_shadowed_provenance_discriminator_fails_the_same_way() -> None:
    findings = representation_draft_violations(
        draft(
            provenance=(
                ClaimShadowingRole(
                    ProvenanceTargetKind.RECORD, ("spell:wish",), "span-1"
                ),
            )
        )
    )
    assert findings
    assert all("must be ProvenanceClaim" in f for f in findings)


# ---------------------------------------------------------------------------
# 3. Equality/hash overrides cannot evade duplicate checks
# ---------------------------------------------------------------------------


@dataclass(frozen=True, eq=False)
class RecordIgnoringTier(RecordDraft):
    """``eq=False`` inherits the base ``__eq__``, which ignores ``tier``.

    Two of these with different tiers are "equal" and collapse into one member
    of ``{r.semantic_key for r in draft.records}``-style sets — and of any set
    of the objects themselves — so the duplicate they represent is never seen.
    """

    tier: int = 1


def test_an_equality_override_collapses_two_distinct_records() -> None:
    """The evasion vector, demonstrated before it is refused."""
    a = RecordIgnoringTier(semantic_key="spell:wish", kind=RecordKind.SPELL, tier=1)
    b = RecordIgnoringTier(semantic_key="spell:wish", kind=RecordKind.SPELL, tier=99)
    assert a == b and a.tier != b.tier
    assert len({a, b}) == 1  # the collapse a dedup check would have seen


def test_the_gate_refuses_them_before_any_dedup_runs() -> None:
    findings = representation_draft_violations(
        draft(
            records=(
                RecordIgnoringTier(semantic_key="spell:wish", kind=RecordKind.SPELL),
                RecordIgnoringTier(
                    semantic_key="spell:wish", kind=RecordKind.SPELL, tier=99
                ),
            )
        )
    )
    assert len(findings) == 2
    assert all("must be RecordDraft" in f for f in findings)


# ---------------------------------------------------------------------------
# 4. The leak itself: one payload, two authorities
# ---------------------------------------------------------------------------


def test_undeclared_meaning_would_otherwise_share_canonical_bytes() -> None:
    """The *would otherwise* is the point, so it is run rather than asserted.

    Two drafts asserting different authority emit byte-identical canonical
    payloads, because the emitter writes only declared base fields. Both are
    now refused, which is what stops them reaching identity.
    """
    light = draft(
        records=(
            RecordWithTier(semantic_key="spell:wish", kind=RecordKind.SPELL, tier=1),
        )
    )
    heavy = draft(
        records=(
            RecordWithTier(semantic_key="spell:wish", kind=RecordKind.SPELL, tier=99),
        )
    )
    assert light != heavy
    assert representation_payload(light) == representation_payload(heavy)

    assert representation_draft_violations(light)
    assert representation_draft_violations(heavy)


# ---------------------------------------------------------------------------
# 5 / 8. Exact base classes stay accepted, and nothing else moved
# ---------------------------------------------------------------------------


def test_an_exact_base_class_draft_is_accepted() -> None:
    assert representation_draft_violations(draft()) == []


def test_an_empty_draft_is_accepted() -> None:
    assert (
        representation_draft_violations(
            RepresentationDraft(
                records=(),
                components=(),
                prose_bindings=(),
                relationships=(),
                references=(),
                provenance=(),
            )
        )
        == []
    )


def test_a_non_tuple_collection_is_refused() -> None:
    """A list is not the declared shape, and would sort/dedup differently.

    Reported through the same ``exact_type_violations`` rule as every other
    type refusal here, rather than through a bespoke message.
    """
    findings = representation_draft_violations(draft(records=[RECORD]))  # type: ignore[arg-type]
    assert any("must be tuple" in f for f in findings)


def test_the_schema_version_and_hash_are_unchanged() -> None:
    """Checker code changed; the wire contract did not. No schema 3."""
    assert REPRESENTATION_SCHEMA_VERSION == "5d-representation-schema-4"
    assert representation_schema_hash() == (
        "241860418b183f67bcc4d914d1fdaa3bbcea1705f28cdd460eb05716d40ce3e9"  # noqa: E501  # pragma: allowlist secret
    )


# ---------------------------------------------------------------------------
# The authority-bearing routes
# ---------------------------------------------------------------------------


def test_validation_refuses_a_hostile_draft_and_reports_only_that() -> None:
    """Early return: the type refusal, not downstream noise from reading it."""
    findings = validate_representation(
        draft(
            records=(RecordWithTier(semantic_key="spell:wish", kind=RecordKind.SPELL),)
        ),
        build_ledger(),
        bound_corpus(),
    )
    assert findings
    assert all("must be RecordDraft" in f for f in findings)


def test_the_acceptance_merge_refuses_a_hostile_representation() -> None:
    """The second authority-bearing route: a proposal becoming accepted.

    ``MechanicalProposal`` has no loader in ``src/`` — it is built in process —
    so this is the seam where an unvalidated draft can reach the keyed union,
    whose ``key_of`` construction and equality comparisons are exactly what a
    hostile subclass subverts.
    """
    from afterworlds.ingestion.mechanical.acceptance import _merge_representation

    hostile = draft(
        records=(RecordWithTier(semantic_key="spell:wish", kind=RecordKind.SPELL),)
    )
    with pytest.raises(AcceptanceError, match="closed declared shape"):
        _merge_representation(None, hostile)
    with pytest.raises(AcceptanceError, match="closed declared shape"):
        _merge_representation(hostile, draft())


def test_the_acceptance_merge_still_accepts_exact_drafts() -> None:
    from afterworlds.ingestion.mechanical.acceptance import _merge_representation

    merged = _merge_representation(None, draft())
    assert merged == draft()
    assert _merge_representation(draft(), draft()) == draft()


# ---------------------------------------------------------------------------
# The collection itself must be exactly ``tuple``
# ---------------------------------------------------------------------------
#
# Round 8's first cut wrote ``isinstance(held, tuple)`` inside the very gate
# that exists to forbid ``isinstance``. A tuple subclass *is* a tuple, so the
# collection was the one place the boundary still leaked: it can carry
# undeclared metadata the payload never emits, and it can override ``__iter__``
# so validation and serialization observe different elements from one object.


class TupleWithMetadata(tuple):  # noqa: SLOT001 - a deliberate hostile shape
    """A tuple carrying meaning no canonical payload emits."""

    provenance_note: str

    def __new__(
        cls, items: tuple[object, ...], provenance_note: str = ""
    ) -> TupleWithMetadata:
        created = super().__new__(cls, items)  # type: ignore[arg-type]
        created.provenance_note = provenance_note
        return created


class TupleThatLiesWhenIterated(tuple):  # noqa: SLOT001 - deliberate
    """Iterating raises. Reaching the raise at all is the defect."""

    def __iter__(self) -> object:  # type: ignore[override]
        raise AssertionError(
            "the gate iterated a collection whose exact type it had not checked"
        )


def test_a_tuple_subclass_holding_valid_elements_is_refused() -> None:
    """The elements are exact; the container is not. That is enough."""
    findings = representation_draft_violations(
        draft(records=TupleWithMetadata((RECORD, OTHER_RECORD)))
    )
    assert findings == ["representation.records must be tuple, got TupleWithMetadata"]


@pytest.mark.parametrize("field_name", sorted(EXPECTED_ELEMENTS))
def test_every_collection_field_requires_an_exact_tuple(field_name: str) -> None:
    """Not just ``records`` — all six, so the fix is not one-field-deep."""
    existing = getattr(draft(), field_name)
    findings = representation_draft_violations(
        draft(**{field_name: TupleWithMetadata(existing)})
    )
    assert findings
    assert all(
        f"representation.{field_name} must be tuple" in f for f in findings
    ), findings


def test_undeclared_container_metadata_would_otherwise_share_canonical_bytes() -> None:
    """The leak, run rather than asserted — same shape as the element-level case.

    Two drafts whose collections hold identical elements but different
    container-level metadata emit byte-identical canonical payloads, because
    the emitter walks elements and never sees the container's own state.
    """
    quiet = draft(records=TupleWithMetadata((RECORD, OTHER_RECORD), "reviewed"))
    loud = draft(records=TupleWithMetadata((RECORD, OTHER_RECORD), "disputed"))
    assert quiet.records.provenance_note != loud.records.provenance_note  # type: ignore[union-attr]
    assert representation_payload(quiet) == representation_payload(loud)

    assert representation_draft_violations(quiet)
    assert representation_draft_violations(loud)


def test_a_hostile_iterator_is_never_reached() -> None:
    """The check precedes iteration, so the raise never fires.

    If the gate iterated first to discover the type, this test would fail with
    the subclass's own ``AssertionError`` rather than returning a finding.
    """
    findings = representation_draft_violations(
        draft(records=TupleThatLiesWhenIterated((RECORD,)))
    )
    assert findings
    assert all("must be tuple" in f for f in findings), findings


def test_a_list_is_still_refused_with_the_same_rule() -> None:
    """The looser wrong type keeps failing, now through one shared rule."""
    findings = representation_draft_violations(draft(records=[RECORD]))  # type: ignore[arg-type]
    assert findings == ["representation.records must be tuple, got list"]


def test_exact_tuples_are_still_accepted_after_the_tightening() -> None:
    assert representation_draft_violations(draft()) == []
    assert (
        representation_draft_violations(
            RepresentationDraft(
                records=(),
                components=(),
                prose_bindings=(),
                relationships=(),
                references=(),
                provenance=(),
            )
        )
        == []
    )


def test_the_element_map_is_explicit_and_guarded_not_derived() -> None:
    """States the actual guarantee, correcting an earlier overclaim.

    ``_DRAFT_ELEMENT_TYPES`` is a hand-maintained literal. Nothing derives it;
    what protects it is this file's dataclass-derived change detector, which is
    a different and weaker claim than "derived" — and worth being precise about,
    since an earlier comment said the wrong one.
    """
    from afterworlds.ingestion.mechanical.representation import _DRAFT_ELEMENT_TYPES

    assert dict(_DRAFT_ELEMENT_TYPES) == EXPECTED_ELEMENTS
    assert set(_DRAFT_ELEMENT_TYPES) == {f.name for f in fields(RepresentationDraft)}
