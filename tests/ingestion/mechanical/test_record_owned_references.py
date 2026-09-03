"""A record may own its own citations — CRD Issue 5d, H-8.

Some records cite other records in their own right. The hazard umbrella names
the five hazards it collects, and no component of that umbrella states the
naming: the record does. Before schema 4 the only way to project such a
reference was to invent a component to hang it on, which publishes a component
the source never states.

Schema 4 widens ``ReferenceDraft.from_component_key`` rather than adding an
ownership field beside it, so:

* every accepted component-owned reference keeps its exact payload and its exact
  provenance coordinate — proved here against the committed oracle, not asserted;
* a record-owned reference names its source record and carries no component that
  could dangle;
* a record publishing one citation *both* ways is refused, because record
  ownership means no component states it; and
* a schema-3 declaration carrying record-owned meaning fails closed rather than
  serializing bytes an earlier reviewer would read as a component named ``""``.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import replace

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.hashing import canonical_bytes
from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.gate import _comparable_collections
from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import load_oracle
from afterworlds.ingestion.mechanical.persistence import (
    PersistedStateReconstructionError,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_persisted_state,
)
from afterworlds.ingestion.mechanical.projection import (
    SCHEMA_3_VERSION,
    LegacySchemaPayloadError,
    identify_projection,
    representation_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    RECORD_OWNED_REFERENCE,
    ComponentDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    prose_binding_target_key,
    reference_target_key,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from afterworlds.persistence.orm.mechanical import MechanicalReferenceORM
from tests.ingestion.mechanical.conftest import (
    CREATURE_KEY,
    DESCRIPTOR_KEY,
    NOW,
    PROSE_LEAF,
    PROSE_SPAN,
    RELEASE_BINDING,
    SPELL_KEY,
    SPELL_LEAF,
    SPELL_SPAN,
    bound_corpus,
    build_ledger,
    build_representation,
    candidate_of,
    reference_claim,
)

#: The **legacy specimen**: the committed accepted artifact exactly as it stood
#: before hazards-1 was accepted into it - the conditions-1 batch alone,
#: reviewed under schema 3. What this module asserts is true of that accepted
#: content, so it reads the frozen copy rather than whatever the release
#: currently accepts. Byte-identical to the file this repository committed
#: (Git blob 42faeca2...), so every identity pinned here is unchanged.
LEGACY_PATH = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "legacy_conditions_1_unanchored_schema3.json"
)

RECORD_OWNED = ReferenceDraft(
    from_record_key=SPELL_KEY,
    from_component_key=RECORD_OWNED_REFERENCE,
    source_text="the servant",
    scope_key="spell:wish",
    target_record_key=CREATURE_KEY,
)
COMPONENT_OWNED = replace(RECORD_OWNED, from_component_key=DESCRIPTOR_KEY)


def _with(*references: ReferenceDraft):
    """The bounded fixture carrying *references*, each with its own edge.

    ``REFERENCE`` is a provenance-required kind, so a reference with no claim
    fails for the wrong reason and would make every assertion below ambiguous.
    """
    base = build_representation()
    return replace(
        base,
        references=references,
        provenance=(
            *base.provenance,
            *(reference_claim(r, SPELL_SPAN) for r in references),
        ),
    )


def _validate(draft):
    """Every finding the bounded fixture's own corpus snapshot produces."""
    return validate_representation(draft, build_ledger(), bound_corpus())


def _validate_with(draft, ledger):
    """The same gate, against a ledger a test supplies itself."""
    return validate_representation(draft, ledger, bound_corpus())


# ---------------------------------------------------------------------------
# Success, and the backward compatibility it must not disturb
# ---------------------------------------------------------------------------


def test_a_record_can_own_a_reference_no_component_states() -> None:
    """The H-8 case: the record cites, and no component is invented for it."""
    assert _validate(_with(RECORD_OWNED)) == ()


def test_a_component_owned_reference_is_unchanged() -> None:
    """The pre-schema-4 form still validates exactly as it did."""
    assert _validate(_with(COMPONENT_OWNED)) == ()


def test_two_components_may_still_cite_the_same_wording() -> None:
    """Not a duplication: each component's citation is its own claim.

    Guards the cross-form check from over-reaching into the case
    ``reference_target_key`` was always built to admit.
    """
    other = replace(COMPONENT_OWNED, from_component_key="open-ended-clause")
    assert _validate(_with(COMPONENT_OWNED, other)) == ()


def test_the_two_forms_produce_distinct_provenance_coordinates() -> None:
    """Same citation, two owners, two keys — and both are five-tuples.

    Nothing downstream reads a coordinate's *length* to learn what it addresses,
    so the record-owned form keeps the shape rather than dropping a position.
    """
    record_key = reference_target_key(RECORD_OWNED)
    component_key = reference_target_key(COMPONENT_OWNED)
    assert record_key != component_key
    assert len(record_key) == len(component_key) == 5
    assert record_key[1] == RECORD_OWNED_REFERENCE


# ---------------------------------------------------------------------------
# Missing and contradictory owners
# ---------------------------------------------------------------------------


def test_a_record_owned_reference_from_a_record_that_does_not_exist_fails() -> None:
    """Record ownership still has to name a real record."""
    orphan = replace(RECORD_OWNED, from_record_key="spell:absent")
    findings = _validate(_with(orphan))
    assert any("unknown source record spell:absent" in f for f in findings)


def test_a_component_owned_reference_may_not_dangle() -> None:
    """Unchanged: a named component has to exist within the source record."""
    dangling = replace(RECORD_OWNED, from_component_key="component:invented")
    findings = _validate(_with(dangling))
    assert any("unknown source component component:invented" in f for f in findings)


def test_a_record_may_not_state_one_citation_both_ways() -> None:
    """Record ownership means *no component states it*, so both is a contradiction.

    The reference-shaped case of the duplicated-projection defect ADR-005d
    Decision 5 forbids: one source statement published twice.
    """
    findings = _validate(_with(RECORD_OWNED, COMPONENT_OWNED))
    assert any(
        "states it both directly and through" in f and DESCRIPTOR_KEY in f
        for f in findings
    ), findings


def test_a_blank_component_key_is_refused_so_the_sentinel_cannot_collide() -> None:
    """What makes ``RECORD_OWNED_REFERENCE`` collision-free by construction.

    A component keyed ``""`` would share every record-owned reference coordinate
    of its own record, so the sentinel's uniqueness rests on this refusal rather
    than on nobody having tried it.
    """
    base = build_representation()
    blank = replace(base.components[0], semantic_key="   ")
    findings = _validate(replace(base, components=(blank, *base.components[1:])))
    assert any("blank semantic key" in f for f in findings), findings


# ---------------------------------------------------------------------------
# Schema 3 refuses the meaning
# ---------------------------------------------------------------------------


def test_schema_3_refuses_to_serialize_a_record_owned_reference() -> None:
    """Fails closed rather than emitting a component named ``""``."""
    with pytest.raises(LegacySchemaPayloadError) as raised:
        representation_payload(_with(RECORD_OWNED), schema_version=SCHEMA_3_VERSION)
    message = str(raised.value)
    assert "record-owned reference form" in message
    assert "5d-representation-schema-4" in message


def test_schema_3_still_serializes_a_component_owned_reference() -> None:
    """The refusal is about the *meaning*, not about references in general."""
    payload = representation_payload(
        _with(COMPONENT_OWNED), schema_version=SCHEMA_3_VERSION
    )
    assert payload["references"] == [
        {
            "from_record_key": SPELL_KEY,
            "from_component_key": DESCRIPTOR_KEY,
            "source_text": "the servant",
            "scope_key": "spell:wish",
            "target_record_key": CREATURE_KEY,
        }
    ]


def test_the_gates_comparison_seam_refuses_rather_than_raising() -> None:
    """The gate's canonicalizing seam is where the refusal has to be catchable.

    ``run_publication_gate`` turns a ``LegacySchemaPayloadError`` from either
    side into a ``SCHEMA_MISMATCH`` failure — proved generically in
    ``test_representation_schema_identity``. What this asserts is that a
    record-owned reference reaches that seam as *that* error class, rather than
    as some other exception the gate does not categorize.
    """
    with pytest.raises(LegacySchemaPayloadError):
        _comparable_collections(_with(RECORD_OWNED), SCHEMA_3_VERSION)
    # The same content under its own declaration canonicalizes fine.
    assert _comparable_collections(_with(RECORD_OWNED), "5d-representation-schema-4")


# ---------------------------------------------------------------------------
# Persistence, reconstruction, digest
# ---------------------------------------------------------------------------


def test_a_record_owned_reference_round_trips_through_storage(
    session: Session,
) -> None:
    """Stored, reconstructed, and still record-owned — with the digest verifying."""
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), _with(RECORD_OWNED))
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()

    stored = session.scalars(
        select(MechanicalReferenceORM).where(
            MechanicalReferenceORM.projection_uuid == identified.projection_uuid
        )
    ).all()
    assert [r.from_component_key for r in stored] == [RECORD_OWNED_REFERENCE]

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert rebuilt.representation.references == (RECORD_OWNED,)
    assert verify_persisted_state(session, identified.projection_uuid) == ()


def test_ownership_is_identity_bearing(session: Session) -> None:
    """Two owners are two projections; the identity is not blind to the change."""
    record_owned = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), _with(RECORD_OWNED))
    )
    component_owned = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), _with(COMPONENT_OWNED))
    )
    assert record_owned.projection_uuid != component_owned.projection_uuid


def test_persistence_closure_refuses_a_dangling_record_owned_row(
    session: Session,
) -> None:
    """The record-owned branch checks its owner *positively*.

    Skipping the component check without asserting the record would let a
    dangling record-owned row pass closure precisely because it carried less.
    """
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), _with(RECORD_OWNED))
    )
    persist_draft(session, identified, now=NOW)
    session.flush()
    row = session.scalars(
        select(MechanicalReferenceORM).where(
            MechanicalReferenceORM.projection_uuid == identified.projection_uuid
        )
    ).one()
    row.from_record_key = "spell:never-persisted"
    session.flush()

    with pytest.raises(PersistedStateReconstructionError) as raised:
        reconstruct_candidate(session, identified.projection_uuid)
    assert "spell:never-persisted" in str(raised.value)


# ---------------------------------------------------------------------------
# Inherited accepted authority does not move
# ---------------------------------------------------------------------------


def test_every_accepted_reference_keeps_its_exact_payload_and_coordinate() -> None:
    """The fifteen conditions-1 references, against the committed bytes.

    None of them is record-owned, so widening the domain leaves every one of
    them byte-identical and every coordinate exactly where it was — which is
    what Owner Decision 2026-08-24 requires and what makes the widening, rather
    than a new field, the only admissible shape.
    """
    committed = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
    oracle = load_oracle(LEGACY_PATH)
    references = oracle.representation.references
    assert len(references) == 15
    assert all(r.from_component_key != RECORD_OWNED_REFERENCE for r in references)

    for version in (SCHEMA_3_VERSION, oracle.schema_version):
        payload = representation_payload(oracle.representation, schema_version=version)
        assert canonical_bytes(payload["references"]) == canonical_bytes(
            committed["representation"]["references"]
        ), version

    stored = {
        tuple(c.target_key)
        for c in oracle.representation.provenance
        if c.target_kind is ProvenanceTargetKind.REFERENCE
    }
    assert {reference_target_key(r) for r in references} <= stored


# ---------------------------------------------------------------------------
# The hazard umbrella, which is why H-8 exists
# ---------------------------------------------------------------------------

UMBRELLA = "glossary.hazard"
HAZARDS = (
    "hazard.burning",
    "hazard.dehydration",
    "hazard.falling",
    "hazard.malnutrition",
    "hazard.suffocation",
)


#: One span per name. The umbrella prints five names in one list, so each
#: citation stands on its own subspan — which is also what makes each of the
#: five a PRIMARY claim without contending for a span with its siblings.
NAME_SPANS = {
    hazard: derive_span_id(SPELL_LEAF, i * 8, i * 8 + 8)
    for i, hazard in enumerate(HAZARDS)
}


def _umbrella_ledger() -> ClassificationLedger:
    """Five accepted name subspans, plus the span the umbrella's prose binds."""
    return build_ledger(
        spans=(
            *(
                SemanticSpan(
                    span_id=NAME_SPANS[h],
                    leaf_id=SPELL_LEAF,
                    char_start=i * 8,
                    char_end=i * 8 + 8,
                    disposition=SemanticDisposition.SUBSTANTIVE,
                    review_state=ReviewState.ACCEPTED,
                )
                for i, h in enumerate(HAZARDS)
            ),
            SemanticSpan(
                span_id=PROSE_SPAN,
                leaf_id=PROSE_LEAF,
                char_start=0,
                char_end=30,
                disposition=SemanticDisposition.SUBSTANTIVE,
                review_state=ReviewState.ACCEPTED,
            ),
        )
    )


def _umbrella_representation():
    """The umbrella's shape: five child records it names, and no component doing so.

    Built here rather than generated from the hazards batch — this proves the
    *mechanism* carries the shape, and PR A neither generates nor accepts that
    proposal.

    The umbrella's one component is prose-bound: its list is governing prose,
    and the naming it performs is the record's, not that component's. That is
    exactly the situation H-8 exists for, and before schema 4 the five citations
    had nowhere to attach that did not misdescribe the source.
    """
    base = build_representation()
    binding = replace(
        base.prose_bindings[0], record_key=UMBRELLA, component_key="hazard-list"
    )
    references = tuple(
        ReferenceDraft(
            from_record_key=UMBRELLA,
            from_component_key=RECORD_OWNED_REFERENCE,
            source_text=h.removeprefix("hazard.").capitalize(),
            scope_key="srd-5.2.1/rules-glossary",
            target_record_key=h,
        )
        for h in HAZARDS
    )
    return replace(
        base,
        records=(
            RecordDraft(semantic_key=UMBRELLA, kind=RecordKind.GLOSSARY_RULE),
            *(
                RecordDraft(
                    semantic_key=h,
                    kind=RecordKind.GLOSSARY_RULE,
                    parent_key=UMBRELLA,
                )
                for h in HAZARDS
            ),
        ),
        components=(
            ComponentDraft(
                record_key=UMBRELLA,
                semantic_key="hazard-list",
                handling=ComponentHandling.PROSE_BOUND,
                irreducibility_reason_code="open_ended_effect",
            ),
        ),
        prose_bindings=(binding,),
        relationships=(),
        references=references,
        provenance=(
            ProvenanceClaim(
                ProvenanceTargetKind.PROSE_BINDING,
                prose_binding_target_key(binding),
                PROSE_SPAN,
                ProvenanceRole.PRIMARY,
            ),
            *(
                ProvenanceClaim(
                    ProvenanceTargetKind.REFERENCE,
                    reference_target_key(r),
                    NAME_SPANS[r.target_record_key],
                    ProvenanceRole.PRIMARY,
                )
                for r in references
            ),
        ),
    )


def test_the_umbrella_validates_with_five_record_owned_references() -> None:
    """The whole proof, through the real representation and provenance gate.

    Not a structural assertion about the draft: ``validate_representation``
    resolves every target, requires an edge for each provenance-required kind,
    enforces primary-by-span uniqueness, and refuses an unclaimed substantive
    span. Five record-owned references pass all of it.
    """
    assert _validate_with(_umbrella_representation(), _umbrella_ledger()) == ()


def test_a_record_owned_reference_still_owes_its_own_provenance() -> None:
    """The negative control for the test above: the edges are load-bearing.

    Record ownership widens who may own a citation; it does not exempt one from
    ``PROVENANCE_REQUIRED_KINDS``.
    """
    umbrella = _umbrella_representation()
    stripped = replace(
        umbrella,
        provenance=tuple(
            c
            for c in umbrella.provenance
            if c.target_kind is not ProvenanceTargetKind.REFERENCE
        ),
    )
    findings = _validate_with(stripped, _umbrella_ledger())
    assert sum("no provenance to a 5c leaf subspan" in f for f in findings) == 5


def test_the_umbrella_owns_five_references_to_its_five_hazards() -> None:
    """Each of the five resolves to an in-batch record, with its own span edge.

    The shape H-8 was raised for: the umbrella states the naming, so the
    umbrella owns the citations and no component is invented to carry them.
    """
    representation = _umbrella_representation()
    assert len(representation.references) == 5
    assert {r.target_record_key for r in representation.references} == set(HAZARDS)
    assert all(
        r.from_component_key == RECORD_OWNED_REFERENCE
        for r in representation.references
    )
    # Every target is a record this batch really projects.
    projected = {r.semantic_key for r in representation.records}
    assert {r.target_record_key for r in representation.references} <= projected
    # Each carries its own provenance edge — REFERENCE is a required kind.
    claimed = {
        tuple(c.target_key)
        for c in representation.provenance
        if c.target_kind is ProvenanceTargetKind.REFERENCE
    }
    assert claimed == {reference_target_key(r) for r in representation.references}
    assert len(claimed) == 5


def test_the_umbrella_needs_no_component_to_carry_its_citations() -> None:
    """No component of the umbrella states any of the five."""
    representation = _umbrella_representation()
    component_keys = {c.semantic_key for c in representation.components}
    assert component_keys == {"hazard-list"}
    assert all(
        r.from_component_key not in component_keys for r in representation.references
    )
