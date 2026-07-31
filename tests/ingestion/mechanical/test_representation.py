"""Representation validation — CRD Issue 5d, Decisions 3, 4, and 7."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    ComponentDraft,
    DcKind,
    ProgressionEntryFact,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RelationshipDraft,
    RelationshipKind,
    UnknownFactFamilyError,
    fact_key,
    fact_payload,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from tests.ingestion.mechanical.conftest import (
    CREATURE_KEY,
    DESCRIPTOR_FACT,
    DESCRIPTOR_FACT_KEY,
    DESCRIPTOR_KEY,
    OPEN_ENDED_KEY,
    PROSE_SPAN,
    SPELL_KEY,
    SPELL_SPAN,
    SUPPORT_SPAN,
    build_ledger,
    build_representation,
)


def _findings(**overrides: object) -> tuple[str, ...]:
    return validate_representation(build_representation(**overrides), build_ledger())


# -- the closed typed-fact union ---------------------------------------------


def test_honest_representation_passes() -> None:
    assert _findings() == ()


def test_declared_family_serializes_with_its_discriminator() -> None:
    payload = fact_payload(AbilityCheckFact(AbilityScore.WISDOM, DcKind.SPELL_SAVE_DC))
    assert payload["family"] == "ability_check"
    assert payload["ability"] == "wisdom"
    assert payload["dc_value"] is None


def test_unknown_family_is_rejected_not_absorbed() -> None:
    @dataclass(frozen=True)
    class ImprovisedFact:
        anything: dict[str, str]

    with pytest.raises(UnknownFactFamilyError):
        fact_payload(ImprovisedFact({"dc": "12"}))

    findings = _findings(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=DESCRIPTOR_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=(ImprovisedFact({"dc": "12"}),),  # type: ignore[arg-type]
            ),
        )
    )
    assert any("not a member of the closed typed-fact union" in f for f in findings)


def test_a_plain_dict_is_not_a_fact() -> None:
    with pytest.raises(UnknownFactFamilyError):
        fact_payload({"family": "ability_check", "ability": "wisdom"})


def test_fact_key_is_content_derived_not_positional() -> None:
    first = ProgressionEntryFact(level=3, entitlement_key="feature:x")
    same = ProgressionEntryFact(level=3, entitlement_key="feature:x")
    other = ProgressionEntryFact(level=4, entitlement_key="feature:x")
    assert fact_key(first) == fact_key(same)
    assert fact_key(first) != fact_key(other)


def test_duplicate_facts_on_one_component_are_rejected() -> None:
    findings = _findings(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=DESCRIPTOR_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=(DESCRIPTOR_FACT, DESCRIPTOR_FACT),
            ),
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=OPEN_ENDED_KEY,
                handling=ComponentHandling.PROSE_BOUND,
                irreducibility_reason_code="open_ended_effect",
            ),
        )
    )
    assert any("duplicate typed fact" in f for f in findings)


# -- records and assembly ----------------------------------------------------


def test_duplicate_record_keys_are_rejected() -> None:
    findings = _findings(
        records=(
            RecordDraft(SPELL_KEY, RecordKind.SPELL),
            RecordDraft(SPELL_KEY, RecordKind.CONDITION),
        )
    )
    assert any("duplicate semantic key" in f for f in findings)


def test_nested_record_with_unknown_parent_is_rejected() -> None:
    findings = _findings(
        records=(
            RecordDraft(SPELL_KEY, RecordKind.SPELL),
            RecordDraft(CREATURE_KEY, RecordKind.CREATURE, parent_key="spell:ghost"),
        )
    )
    assert any("unknown parent spell:ghost" in f for f in findings)


def test_parent_cycle_is_rejected() -> None:
    findings = _findings(
        records=(
            RecordDraft(SPELL_KEY, RecordKind.SPELL, parent_key=CREATURE_KEY),
            RecordDraft(CREATURE_KEY, RecordKind.CREATURE, parent_key=SPELL_KEY),
        )
    )
    assert any("parent cycle" in f for f in findings)


def test_component_on_an_unknown_record_is_rejected() -> None:
    findings = _findings(
        components=(
            ComponentDraft(
                record_key="spell:ghost",
                semantic_key=DESCRIPTOR_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=(DESCRIPTOR_FACT,),
            ),
        )
    )
    assert any("unknown record spell:ghost" in f for f in findings)


# -- handling honesty --------------------------------------------------------


def test_structured_component_without_facts_is_rejected() -> None:
    findings = _findings(
        components=(
            ComponentDraft(SPELL_KEY, DESCRIPTOR_KEY, ComponentHandling.STRUCTURED),
        )
    )
    assert any("structured handling with no typed facts" in f for f in findings)


def test_prose_bound_component_without_bound_prose_is_rejected() -> None:
    findings = _findings(prose_bindings=())
    assert any("prose-bound handling with no bound prose" in f for f in findings)


def test_prose_bound_component_carrying_facts_is_rejected() -> None:
    findings = _findings(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=OPEN_ENDED_KEY,
                handling=ComponentHandling.PROSE_BOUND,
                irreducibility_reason_code="open_ended_effect",
                facts=(DESCRIPTOR_FACT,),
            ),
        )
    )
    assert any("prose-bound handling with typed facts" in f for f in findings)


def test_mixed_component_requires_both() -> None:
    findings = _findings(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=OPEN_ENDED_KEY,
                handling=ComponentHandling.MIXED,
                irreducibility_reason_code="open_ended_effect",
            ),
        )
    )
    assert any("mixed handling with no typed facts" in f for f in findings)


def test_irreducibility_reason_must_be_closed() -> None:
    findings = _findings(
        prose_bindings=(
            ProseBindingDraft(
                component_key=OPEN_ENDED_KEY,
                record_key=SPELL_KEY,
                chunk_id="chunk-wish-0001",
                irreducibility_reason_code="too_hard",
            ),
        )
    )
    assert any("is not closed" in f for f in findings)


def test_prose_binding_requires_an_authoritative_chunk() -> None:
    findings = _findings(
        prose_bindings=(
            ProseBindingDraft(OPEN_ENDED_KEY, SPELL_KEY, "  ", "open_ended_effect"),
        )
    )
    assert any("no authoritative chunk bound" in f for f in findings)


# -- relationships and references --------------------------------------------


def test_relationship_to_an_unknown_record_is_rejected() -> None:
    findings = _findings(
        relationships=(
            RelationshipDraft(SPELL_KEY, "creature:ghost", RelationshipKind.GRANTS),
        )
    )
    assert any("unknown record creature:ghost" in f for f in findings)


def test_unresolved_reference_is_rejected() -> None:
    findings = _findings(
        references=(
            ReferenceDraft(SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", ""),
        )
    )
    assert any("unresolved reference" in f for f in findings)


def test_ambiguous_reference_within_one_scope_is_rejected() -> None:
    findings = _findings(
        references=(
            ReferenceDraft(
                SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", SPELL_KEY
            ),
            ReferenceDraft(
                SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", CREATURE_KEY
            ),
        )
    )
    assert any("ambiguous" in f for f in findings)


def test_same_wording_in_two_scopes_is_not_ambiguous() -> None:
    # The scoped-collision canary: a repeated name resolves per committed scope.
    findings = _findings(
        references=(
            ReferenceDraft(
                SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", CREATURE_KEY
            ),
            ReferenceDraft(
                SPELL_KEY, DESCRIPTOR_KEY, "the servant", "chapter:appendix", SPELL_KEY
            ),
        )
    )
    assert not any("ambiguous" in f for f in findings)


def test_reference_without_a_committed_scope_is_rejected() -> None:
    findings = _findings(
        references=(
            ReferenceDraft(SPELL_KEY, DESCRIPTOR_KEY, "the servant", " ", CREATURE_KEY),
        )
    )
    assert any("no committed resolution scope" in f for f in findings)


# -- provenance --------------------------------------------------------------


def test_substantive_span_nothing_claims_is_rejected() -> None:
    findings = _findings(
        provenance=(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                (SPELL_KEY, DESCRIPTOR_KEY, DESCRIPTOR_FACT_KEY),
                SPELL_SPAN,
                ProvenanceRole.PRIMARY,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.RECORD,
                (SPELL_KEY,),
                SUPPORT_SPAN,
                ProvenanceRole.CONTEXTUAL,
            ),
        )
    )
    assert any(f"span {PROSE_SPAN}: substantive but unclaimed" in f for f in findings)


def test_supporting_span_nothing_links_is_rejected() -> None:
    keep = build_representation().provenance[:2]
    findings = _findings(provenance=keep)
    assert any(
        f"span {SUPPORT_SPAN}: supporting authority but unlinked" in f for f in findings
    )


def test_conflicting_primary_claims_are_rejected() -> None:
    base = build_representation().provenance
    findings = _findings(
        provenance=base
        + (
            ProvenanceClaim(
                ProvenanceTargetKind.RECORD,
                (SPELL_KEY,),
                SPELL_SPAN,
                ProvenanceRole.PRIMARY,
            ),
        )
    )
    assert any("conflicting primary claims" in f for f in findings)


def test_contextual_overlap_is_permitted() -> None:
    base = build_representation().provenance
    findings = _findings(
        provenance=base
        + (
            ProvenanceClaim(
                ProvenanceTargetKind.COMPONENT,
                (SPELL_KEY, DESCRIPTOR_KEY),
                SPELL_SPAN,
                ProvenanceRole.CONTEXTUAL,
            ),
        )
    )
    assert findings == ()


def test_provenance_for_an_undeclared_element_is_rejected() -> None:
    base = build_representation().provenance
    findings = _findings(
        provenance=base
        + (
            ProvenanceClaim(
                ProvenanceTargetKind.COMPONENT,
                (SPELL_KEY, "ghost-component"),
                SUPPORT_SPAN,
                ProvenanceRole.CONTEXTUAL,
            ),
        )
    )
    assert any("claim for an undeclared element" in f for f in findings)


def test_provenance_naming_an_unknown_span_is_rejected() -> None:
    base = build_representation().provenance
    findings = _findings(
        provenance=base
        + (
            ProvenanceClaim(
                ProvenanceTargetKind.RECORD,
                (SPELL_KEY,),
                "span-ghost",
                ProvenanceRole.CONTEXTUAL,
            ),
        )
    )
    assert any("unknown span span-ghost" in f for f in findings)
