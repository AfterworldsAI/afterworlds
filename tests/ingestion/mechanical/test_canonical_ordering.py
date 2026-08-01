"""Authoring order never reaches the identity — CRD Issue 5d, review round 3.

The defect these cover is structural, not a list of examples: a sort key that
names some fields makes two semantically different elements compare equal, and
Python's stable sort then leaks the order they were written in into the
projection UUID. So the tests are permutation-driven — every unordered
collection, every permutation, one assertion — rather than one test per
handwritten tuple.
"""

from __future__ import annotations

from itertools import permutations
from typing import Any

import pytest

from afterworlds.ingestion.mechanical.accounting import classification_payload
from afterworlds.ingestion.mechanical.canonical import canonical_order
from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    projection_payload,
    projection_uuid,
)
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    ComponentDraft,
    DcKind,
    ProseBindingDraft,
    ProvenanceRole,
    ReferenceDraft,
    RelationshipDraft,
    RelationshipKind,
)
from tests.ingestion.mechanical.conftest import (
    CREATURE_KEY,
    DESCRIPTOR_FACT,
    DESCRIPTOR_KEY,
    OPEN_ENDED_KEY,
    PROSE_SPAN,
    SECOND_CHUNK,
    SPELL_KEY,
    WISH_CHUNK,
    binding_claim,
    build_candidate,
    build_ledger,
    build_representation,
    reference_claim,
)

# Collections whose order carries no meaning, and therefore must not reach the
# identity. `resolved_scope` is deliberately absent: it is retained reviewer
# evidence whose order *is* meaningful.
UNORDERED = (
    "records",
    "components",
    "prose_bindings",
    "relationships",
    "references",
    "provenance",
)


def _candidate(**overrides: object) -> ProjectionCandidate:
    return build_candidate(**overrides)


def _permuted(draft: Any, field: str, order: tuple[int, ...]) -> dict[str, Any]:
    items = getattr(draft, field)
    return {field: tuple(items[i] for i in order)}


@pytest.mark.parametrize("field", UNORDERED)
def test_reordering_an_unordered_collection_changes_nothing(field: str) -> None:
    draft = build_representation()
    base = _candidate()
    baseline_payload = projection_payload(base)
    baseline_uuid = projection_uuid(base)

    for order in permutations(range(len(getattr(draft, field)))):
        candidate = _candidate(**_permuted(draft, field, order))
        assert projection_payload(candidate) == baseline_payload, field
        assert projection_uuid(candidate) == baseline_uuid, field


def test_reordering_facts_within_a_component_changes_nothing() -> None:
    facts = (
        DESCRIPTOR_FACT,
        AbilityCheckFact(AbilityScore.WISDOM, DcKind.FIXED, 15),
    )
    forward, reverse = (
        _candidate(
            components=(
                ComponentDraft(
                    SPELL_KEY,
                    DESCRIPTOR_KEY,
                    ComponentHandling.STRUCTURED,
                    facts=ordered,
                ),
                build_representation().components[1],
            )
        )
        for ordered in (facts, tuple(reversed(facts)))
    )
    assert projection_payload(forward) == projection_payload(reverse)
    assert projection_uuid(forward) == projection_uuid(reverse)


def test_reordering_classification_spans_changes_nothing() -> None:
    spans = build_ledger().spans
    for order in permutations(range(len(spans))):
        permuted = build_ledger(spans=tuple(spans[i] for i in order))
        assert classification_payload(permuted) == classification_payload(
            build_ledger()
        )


# -- the exact collisions the partial sort keys allowed ----------------------


def _two_reference_candidates(a: ReferenceDraft, b: ReferenceDraft) -> tuple[str, str]:
    base = build_representation().provenance
    forward = _candidate(
        references=(a, b), provenance=base + (reference_claim(a), reference_claim(b))
    )
    reverse = _candidate(
        references=(b, a), provenance=base + (reference_claim(b), reference_claim(a))
    )
    return projection_uuid(forward), projection_uuid(reverse)


def test_references_differing_only_in_source_component() -> None:
    a = ReferenceDraft(
        SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", CREATURE_KEY
    )
    b = ReferenceDraft(
        SPELL_KEY, OPEN_ENDED_KEY, "the servant", "spell:wish", CREATURE_KEY
    )
    forward, reverse = _two_reference_candidates(a, b)
    assert forward == reverse


def test_references_differing_only_in_target_record() -> None:
    a = ReferenceDraft(
        SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", CREATURE_KEY
    )
    b = ReferenceDraft(
        SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", SPELL_KEY
    )
    forward, reverse = _two_reference_candidates(a, b)
    assert forward == reverse


def _two_binding_candidates(
    a: ProseBindingDraft, b: ProseBindingDraft
) -> tuple[str, str]:
    base = build_representation().provenance
    extra = (binding_claim(b, PROSE_SPAN, ProvenanceRole.CONTEXTUAL),)
    forward = _candidate(prose_bindings=(a, b), provenance=base + extra)
    reverse = _candidate(prose_bindings=(b, a), provenance=base + extra)
    return projection_uuid(forward), projection_uuid(reverse)


def test_prose_bindings_on_one_component_differing_in_chunk() -> None:
    a = ProseBindingDraft(OPEN_ENDED_KEY, SPELL_KEY, WISH_CHUNK, "open_ended_effect")
    b = ProseBindingDraft(OPEN_ENDED_KEY, SPELL_KEY, SECOND_CHUNK, "open_ended_effect")
    forward, reverse = _two_binding_candidates(a, b)
    assert forward == reverse


def test_prose_bindings_differing_only_in_the_reason() -> None:
    a = ProseBindingDraft(OPEN_ENDED_KEY, SPELL_KEY, WISH_CHUNK, "open_ended_effect")
    b = ProseBindingDraft(OPEN_ENDED_KEY, SPELL_KEY, WISH_CHUNK, "subjective_judgment")
    forward, reverse = _two_binding_candidates(a, b)
    assert forward == reverse


def test_relationships_differing_only_in_kind() -> None:
    a = RelationshipDraft(CREATURE_KEY, SPELL_KEY, RelationshipKind.SCOPED_WITHIN)
    b = RelationshipDraft(CREATURE_KEY, SPELL_KEY, RelationshipKind.PREREQUISITE)
    forward = projection_uuid(_candidate(relationships=(a, b)))
    reverse = projection_uuid(_candidate(relationships=(b, a)))
    assert forward == reverse


# -- ordering must not flatten meaning ---------------------------------------


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "references": (
                ReferenceDraft(
                    SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", CREATURE_KEY
                ),
            )
        },
        {
            "prose_bindings": (
                ProseBindingDraft(
                    OPEN_ENDED_KEY, SPELL_KEY, SECOND_CHUNK, "open_ended_effect"
                ),
            )
        },
        {
            "relationships": (
                RelationshipDraft(
                    CREATURE_KEY, SPELL_KEY, RelationshipKind.PREREQUISITE
                ),
            )
        },
    ],
)
def test_changing_an_identity_bearing_value_changes_the_identity(
    overrides: dict[str, Any],
) -> None:
    assert projection_uuid(_candidate(**overrides)) != projection_uuid(_candidate())


def test_canonical_order_preserves_duplicates() -> None:
    # Deduplicating here would hide a duplicate from the validator that exists
    # to reject it.
    payloads = [{"a": 1}, {"a": 1}, {"a": 0}]
    assert canonical_order(payloads) == [{"a": 0}, {"a": 1}, {"a": 1}]


def test_canonical_order_is_independent_of_input_order() -> None:
    payloads = [{"b": 2, "a": 1}, {"a": 1, "b": 3}, {"a": 0, "b": 9}]
    assert canonical_order(payloads) == canonical_order(list(reversed(payloads)))


def test_provenance_claims_differing_only_in_role_are_ordered() -> None:
    base = build_representation().provenance
    extra = base[0]
    swapped = (extra,) + base[1:] + (base[0],)
    # A duplicated edge is still ordered deterministically even though the
    # validator rejects it; canonicalization is not where duplicates die.
    assert projection_payload(_candidate(provenance=swapped)) == projection_payload(
        _candidate(provenance=tuple(reversed(swapped)))
    )
