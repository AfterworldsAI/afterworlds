"""Provenance as a closed relation — CRD Issue 5d, review round 3.

Forward validation alone let two things through: an authoritative element with
no evidence of its own (because some *other* element happened to claim the same
span), and a claim citing text the accepted classification says states no
mechanic. Both are covered here, together with the target-key precision that
makes the reverse obligation addressable at all.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.representation import (
    ComponentDraft,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    ReferenceDraft,
    RelationshipDraft,
    RelationshipKind,
    fact_target_key,
    prose_binding_target_key,
    reference_target_key,
    relationship_target_key,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from tests.ingestion.mechanical.conftest import (
    CREATURE_KEY,
    DESCRIPTOR_FACT,
    DESCRIPTOR_KEY,
    OPEN_ENDED_KEY,
    PROSE_SPAN,
    SCOPED_WITHIN,
    SECOND_CHUNK,
    SPELL_KEY,
    SPELL_SPAN,
    SUPPORT_LEAF,
    SUPPORT_SPAN,
    WISH_BINDING,
    WISH_CHUNK,
    binding_claim,
    bound_corpus,
    build_ledger,
    build_representation,
    reference_claim,
)

FACT_KEY = fact_target_key(SPELL_KEY, DESCRIPTOR_KEY, DESCRIPTOR_FACT)


def _findings(ledger=None, **overrides: object) -> tuple[str, ...]:  # type: ignore[no-untyped-def]
    return validate_representation(
        build_representation(**overrides),
        ledger if ledger is not None else build_ledger(),
        bound_corpus(),
    )


def _without(kind: ProvenanceTargetKind) -> tuple[ProvenanceClaim, ...]:
    """The default provenance minus every claim of *kind*."""
    return tuple(
        c for c in build_representation().provenance if c.target_kind is not kind
    )


# -- reverse obligation: every authoritative element carries its own edge -----


def test_fact_without_provenance_is_rejected_when_only_its_component_claims() -> None:
    # The component claims the very span the fact came from. That is coverage
    # of the span, not traceability of the fact.
    claims = _without(ProvenanceTargetKind.FACT) + (
        ProvenanceClaim(
            ProvenanceTargetKind.COMPONENT,
            (SPELL_KEY, DESCRIPTOR_KEY),
            SPELL_SPAN,
            ProvenanceRole.PRIMARY,
        ),
    )
    findings = _findings(provenance=claims)
    assert any("fact" in f and "no provenance" in f for f in findings)


def test_prose_binding_without_provenance_is_rejected() -> None:
    findings = _findings(provenance=_without(ProvenanceTargetKind.PROSE_BINDING))
    assert any("prose_binding" in f and "no provenance" in f for f in findings)


def test_relationship_without_provenance_is_rejected() -> None:
    findings = _findings(provenance=_without(ProvenanceTargetKind.RELATIONSHIP))
    assert any("relationship" in f and "no provenance" in f for f in findings)


def test_resolved_reference_without_provenance_is_rejected() -> None:
    reference = ReferenceDraft(
        SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", CREATURE_KEY
    )
    findings = _findings(references=(reference,))
    assert any("reference" in f and "no provenance" in f for f in findings)


def test_one_of_several_bindings_lacking_provenance_is_rejected() -> None:
    second = ProseBindingDraft(
        OPEN_ENDED_KEY, SPELL_KEY, SECOND_CHUNK, "open_ended_effect"
    )
    findings = _findings(prose_bindings=(WISH_BINDING, second))
    assert any(SECOND_CHUNK in f and "no provenance" in f for f in findings)


def test_one_of_two_similar_references_lacking_provenance_is_rejected() -> None:
    a = ReferenceDraft(
        SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", CREATURE_KEY
    )
    b = ReferenceDraft(
        SPELL_KEY, OPEN_ENDED_KEY, "the servant", "spell:wish", CREATURE_KEY
    )
    findings = _findings(
        references=(a, b),
        provenance=build_representation().provenance + (reference_claim(a),),
    )
    assert any(OPEN_ENDED_KEY in f and "reference" in f for f in findings)


def test_every_element_with_its_own_edge_passes() -> None:
    reference = ReferenceDraft(
        SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", CREATURE_KEY
    )
    findings = _findings(
        references=(reference,),
        provenance=build_representation().provenance + (reference_claim(reference),),
    )
    assert findings == ()


# -- disposition / role admissibility ----------------------------------------


def _ledger_with_support_disposition(
    disposition: SemanticDisposition, reason: str | None = None
):  # type: ignore[no-untyped-def]
    spans = build_ledger().spans
    return build_ledger(
        spans=spans[:2]
        + (
            SemanticSpan(
                span_id=SUPPORT_SPAN,
                leaf_id=SUPPORT_LEAF,
                char_start=0,
                char_end=20,
                disposition=disposition,
                review_state=ReviewState.ACCEPTED,
                non_mechanical_reason_code=reason,
            ),
        )
    )


@pytest.mark.parametrize("role", [ProvenanceRole.PRIMARY, ProvenanceRole.CONTEXTUAL])
def test_claim_on_a_non_mechanical_span_is_rejected(role: ProvenanceRole) -> None:
    ledger = _ledger_with_support_disposition(
        SemanticDisposition.NON_MECHANICAL, "navigation_only"
    )
    claims = _without(ProvenanceTargetKind.RECORD) + (
        ProvenanceClaim(ProvenanceTargetKind.RECORD, (SPELL_KEY,), SUPPORT_SPAN, role),
    )
    findings = _findings(ledger=ledger, provenance=claims)
    assert any(f"{role.value} claim on a non_mechanical span" in f for f in findings)


def test_primary_claim_on_a_supporting_span_is_rejected() -> None:
    # Supporting authority explains a mechanic; it is never the primary
    # statement of one.
    claims = _without(ProvenanceTargetKind.RECORD) + (
        ProvenanceClaim(
            ProvenanceTargetKind.RECORD,
            (SPELL_KEY,),
            SUPPORT_SPAN,
            ProvenanceRole.PRIMARY,
        ),
    )
    findings = _findings(provenance=claims)
    assert any("primary claim on a supporting_authority span" in f for f in findings)


def test_contextual_claim_on_a_supporting_span_is_permitted() -> None:
    assert _findings() == ()


def test_inadmissible_claim_does_not_satisfy_span_coverage() -> None:
    # The only claim on the substantive prose span is inadmissible, so the span
    # must still report as unclaimed rather than being covered by it.
    ledger = _ledger_with_support_disposition(
        SemanticDisposition.NON_MECHANICAL, "navigation_only"
    )
    # The relationship's only edge is the inadmissible one.
    claims = tuple(
        c
        for c in build_representation().provenance
        if c.target_kind
        not in (ProvenanceTargetKind.RELATIONSHIP, ProvenanceTargetKind.RECORD)
    ) + (
        ProvenanceClaim(
            ProvenanceTargetKind.RELATIONSHIP,
            relationship_target_key(SCOPED_WITHIN),
            SUPPORT_SPAN,
            ProvenanceRole.CONTEXTUAL,
        ),
    )
    findings = _findings(ledger=ledger, provenance=claims)
    assert any("claim on a non_mechanical span" in f for f in findings)
    assert any("relationship" in f and "no provenance" in f for f in findings)


def test_inadmissible_claim_does_not_satisfy_the_reverse_obligation() -> None:
    ledger = _ledger_with_support_disposition(
        SemanticDisposition.NON_MECHANICAL, "navigation_only"
    )
    claims = _without(ProvenanceTargetKind.PROSE_BINDING) + (
        binding_claim(WISH_BINDING, SUPPORT_SPAN, ProvenanceRole.CONTEXTUAL),
    )
    findings = _findings(ledger=ledger, provenance=claims)
    assert any("prose_binding" in f and "no provenance" in f for f in findings)


# -- uniqueness and closure --------------------------------------------------


def test_duplicate_edge_is_rejected() -> None:
    base = build_representation().provenance
    findings = _findings(provenance=base + (base[0],))
    assert any("duplicate provenance edge" in f for f in findings)


def test_duplicate_edges_do_not_satisfy_a_missing_obligation() -> None:
    fact_claim = ProvenanceClaim(
        ProvenanceTargetKind.FACT, FACT_KEY, SPELL_SPAN, ProvenanceRole.PRIMARY
    )
    claims = _without(ProvenanceTargetKind.RELATIONSHIP) + (fact_claim,)
    findings = _findings(provenance=claims)
    assert any("duplicate provenance edge" in f for f in findings)
    assert any("relationship" in f and "no provenance" in f for f in findings)


def test_claim_with_an_obsolete_prose_binding_key_is_rejected() -> None:
    # The pre-correction two-tuple no longer addresses any element.
    claims = _without(ProvenanceTargetKind.PROSE_BINDING) + (
        ProvenanceClaim(
            ProvenanceTargetKind.PROSE_BINDING,
            (SPELL_KEY, OPEN_ENDED_KEY),
            PROSE_SPAN,
            ProvenanceRole.PRIMARY,
        ),
    )
    findings = _findings(provenance=claims)
    assert any("claim for an undeclared element" in f for f in findings)
    assert any("prose_binding" in f and "no provenance" in f for f in findings)


def test_incomplete_reference_key_cannot_match_a_different_element() -> None:
    # Two references share scope, wording, and owning record but differ in the
    # component that cites them. The old three-field key matched both; the
    # complete key matches exactly one.
    a = ReferenceDraft(
        SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", CREATURE_KEY
    )
    b = ReferenceDraft(
        SPELL_KEY, OPEN_ENDED_KEY, "the servant", "spell:wish", CREATURE_KEY
    )
    assert reference_target_key(a) != reference_target_key(b)

    findings = _findings(
        references=(a, b),
        provenance=build_representation().provenance
        + (reference_claim(a), reference_claim(a)),
    )
    assert any("duplicate provenance edge" in f for f in findings)
    assert any(OPEN_ENDED_KEY in f and "reference" in f for f in findings)


def test_claim_with_a_wrong_shaped_target_key_is_rejected() -> None:
    claims = build_representation().provenance + (
        ProvenanceClaim(
            ProvenanceTargetKind.FACT,
            (SPELL_KEY,),  # too short to address a fact
            SPELL_SPAN,
            ProvenanceRole.CONTEXTUAL,
        ),
    )
    findings = _findings(provenance=claims)
    assert any("claim for an undeclared element" in f for f in findings)


def test_binding_key_distinguishes_two_bindings_of_one_component() -> None:
    second = ProseBindingDraft(
        OPEN_ENDED_KEY, SPELL_KEY, SECOND_CHUNK, "open_ended_effect"
    )
    assert prose_binding_target_key(WISH_BINDING) != prose_binding_target_key(second)
    assert WISH_BINDING.chunk_id == WISH_CHUNK


def test_many_to_many_provenance_is_still_permitted() -> None:
    # One span may support several elements contextually; that is the
    # many-to-many contract, not an overlap defect.
    extra = ProvenanceClaim(
        ProvenanceTargetKind.COMPONENT,
        (SPELL_KEY, DESCRIPTOR_KEY),
        SPELL_SPAN,
        ProvenanceRole.CONTEXTUAL,
    )
    assert _findings(provenance=build_representation().provenance + (extra,)) == ()


def test_component_without_facts_still_relies_on_span_coverage() -> None:
    # A prose-bound component carries no facts, so its obligation stays span
    # coverage rather than a per-element edge.
    findings = _findings(
        components=(
            build_representation().components[0],
            ComponentDraft(
                SPELL_KEY,
                OPEN_ENDED_KEY,
                ComponentHandling.PROSE_BOUND,
                "open_ended_effect",
            ),
        )
    )
    assert findings == ()


def test_relationship_key_includes_its_kind() -> None:
    other = RelationshipDraft(CREATURE_KEY, SPELL_KEY, RelationshipKind.PREREQUISITE)
    assert relationship_target_key(SCOPED_WITHIN) != relationship_target_key(other)
