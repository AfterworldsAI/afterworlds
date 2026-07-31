"""Family invariants, reason coherence, and release-bound prose — CRD Issue 5d.

Three review findings share one shape: a declaration that is *well-formed* was
being accepted as *valid*. A fact could belong to the closed union and still
contradict its own DC contract; a component could claim its meaning is
irreducible without saying why, or disagree with its own binding about why; and
a prose binding could name any non-empty string instead of authority that
exists in the bound release.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    ComponentDraft,
    CreatureAbilityScoreFact,
    DcKind,
    ProgressionEntryFact,
    ProseBindingDraft,
    ReferenceDraft,
    RelationshipDraft,
    RelationshipKind,
    SpellDescriptorFact,
    SpellSchool,
    fact_from_payload,
    fact_invariant_violations,
    fact_payload,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from tests.ingestion.mechanical.conftest import (
    DESCRIPTOR_FACT,
    DESCRIPTOR_KEY,
    OPEN_ENDED_KEY,
    SECOND_CHUNK,
    SPELL_KEY,
    WISH_CHUNK,
    bound_corpus,
    build_ledger,
    build_representation,
)

NON_FIXED = [DcKind.SPELL_SAVE_DC, DcKind.CONTESTED, DcKind.GAMEMASTER_SET]


def _findings(**overrides: object) -> tuple[str, ...]:
    return validate_representation(
        build_representation(**overrides), build_ledger(), bound_corpus()
    )


def _with_facts(*facts: object) -> tuple[str, ...]:
    """Findings for a structured descriptor component carrying *facts*."""
    return _findings(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=DESCRIPTOR_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=facts,  # type: ignore[arg-type]
            ),
            build_representation().components[1],
        )
    )


# -- family A: invariants inside the closed union ----------------------------


def test_fixed_dc_without_a_value_is_rejected() -> None:
    assert any(
        "fixed DC without a dc_value" in f
        for f in _with_facts(AbilityCheckFact(AbilityScore.WISDOM, DcKind.FIXED))
    )


def test_fixed_dc_with_a_value_passes() -> None:
    assert (
        fact_invariant_violations(
            AbilityCheckFact(AbilityScore.WISDOM, DcKind.FIXED, 15)
        )
        == ()
    )


@pytest.mark.parametrize("kind", NON_FIXED)
def test_non_fixed_dc_carrying_a_value_is_rejected(kind: DcKind) -> None:
    assert any(
        "carries dc_value 15" in f
        for f in _with_facts(AbilityCheckFact(AbilityScore.WISDOM, kind, 15))
    )


@pytest.mark.parametrize("kind", NON_FIXED)
def test_non_fixed_dc_without_a_value_passes(kind: DcKind) -> None:
    assert fact_invariant_violations(AbilityCheckFact(AbilityScore.WISDOM, kind)) == ()


def test_negative_ability_score_is_rejected() -> None:
    assert any(
        "negative ability score" in f
        for f in _with_facts(CreatureAbilityScoreFact(AbilityScore.STRENGTH, -1))
    )


def test_negative_spell_level_is_rejected() -> None:
    fact = SpellDescriptorFact(
        level=-1, school=SpellSchool.EVOCATION, ritual=False, concentration=False
    )
    assert any("negative spell level" in f for f in _with_facts(fact))


def test_cantrip_level_zero_passes() -> None:
    # Level 0 is a cantrip, not an error. Only a negative ordinal is intrinsic
    # nonsense; an upper bound would be SRD policy, not a property of the type.
    fact = SpellDescriptorFact(
        level=0, school=SpellSchool.EVOCATION, ritual=False, concentration=False
    )
    assert fact_invariant_violations(fact) == ()


def test_progression_entry_without_an_entitlement_key_is_rejected() -> None:
    fact = ProgressionEntryFact(level=3, entitlement_key="   ")
    assert any("without an entitlement key" in f for f in _with_facts(fact))


def test_progression_quantity_below_one_is_rejected() -> None:
    fact = ProgressionEntryFact(level=3, entitlement_key="feature:x", quantity=0)
    assert any("grants nothing" in f for f in _with_facts(fact))


def test_unspecified_progression_quantity_passes() -> None:
    fact = ProgressionEntryFact(level=3, entitlement_key="feature:x")
    assert fact_invariant_violations(fact) == ()


def test_unknown_family_reports_through_the_invariant_seam() -> None:
    @dataclass(frozen=True)
    class ImprovisedFact:
        anything: str

    assert any(
        "closed typed-fact union" in v
        for v in fact_invariant_violations(ImprovisedFact("x"))
    )


# -- family B: irreducibility reason coherence -------------------------------


def test_prose_bound_component_without_a_reason_is_rejected() -> None:
    findings = _findings(
        components=(
            ComponentDraft(SPELL_KEY, OPEN_ENDED_KEY, ComponentHandling.PROSE_BOUND),
        )
    )
    assert any(
        "prose_bound handling with no irreducibility reason" in f for f in findings
    )


def test_mixed_component_without_a_reason_is_rejected() -> None:
    findings = _findings(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=OPEN_ENDED_KEY,
                handling=ComponentHandling.MIXED,
                facts=(DESCRIPTOR_FACT,),
            ),
        )
    )
    assert any("mixed handling with no irreducibility reason" in f for f in findings)


def test_blank_component_reason_is_rejected() -> None:
    findings = _findings(
        components=(
            ComponentDraft(
                SPELL_KEY, OPEN_ENDED_KEY, ComponentHandling.PROSE_BOUND, "   "
            ),
        )
    )
    assert any(
        "prose_bound handling with no irreducibility reason" in f for f in findings
    )


def test_component_reason_outside_the_closed_catalog_is_rejected() -> None:
    findings = _findings(
        components=(
            ComponentDraft(
                SPELL_KEY, OPEN_ENDED_KEY, ComponentHandling.PROSE_BOUND, "too_hard"
            ),
        )
    )
    assert any("irreducibility reason 'too_hard' is not closed" in f for f in findings)


def test_binding_reason_outside_the_closed_catalog_is_rejected() -> None:
    findings = _findings(
        prose_bindings=(
            ProseBindingDraft(OPEN_ENDED_KEY, SPELL_KEY, WISH_CHUNK, "too_hard"),
        )
    )
    assert any("irreducibility reason 'too_hard' is not closed" in f for f in findings)


def test_component_and_binding_reasons_valid_but_unequal_are_rejected() -> None:
    # Both closed, both plausible, and they disagree about *why* this authority
    # is prose-bound. Neither copy wins.
    findings = _findings(
        prose_bindings=(
            ProseBindingDraft(
                OPEN_ENDED_KEY, SPELL_KEY, WISH_CHUNK, "subjective_judgment"
            ),
        )
    )
    assert any("disagrees with its component's" in f for f in findings)


def test_multiple_bindings_sharing_the_component_reason_pass() -> None:
    findings = _findings(
        prose_bindings=(
            ProseBindingDraft(
                OPEN_ENDED_KEY, SPELL_KEY, WISH_CHUNK, "open_ended_effect"
            ),
            ProseBindingDraft(
                OPEN_ENDED_KEY, SPELL_KEY, SECOND_CHUNK, "open_ended_effect"
            ),
        )
    )
    assert findings == ()


def test_structured_component_carrying_a_reason_is_rejected() -> None:
    findings = _findings(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=DESCRIPTOR_KEY,
                handling=ComponentHandling.STRUCTURED,
                irreducibility_reason_code="open_ended_effect",
                facts=(DESCRIPTOR_FACT,),
            ),
            build_representation().components[1],
        )
    )
    assert any(
        "structured handling with an irreducibility reason" in f for f in findings
    )


# -- family C: prose resolves against the bound release ----------------------


def test_fabricated_chunk_is_rejected() -> None:
    findings = _findings(
        prose_bindings=(
            ProseBindingDraft(
                OPEN_ENDED_KEY, SPELL_KEY, "chunk-invented", "open_ended_effect"
            ),
        )
    )
    assert any("is not authoritative prose of release" in f for f in findings)


def test_chunk_absent_from_the_bound_population_is_rejected() -> None:
    findings = validate_representation(
        build_representation(), build_ledger(), bound_corpus(chunk_ids=frozenset())
    )
    assert any("is not authoritative prose of release" in f for f in findings)


def test_authoritative_chunk_of_the_bound_release_passes() -> None:
    assert _findings() == ()


# -- guards that had no negative control -------------------------------------


def test_structured_component_carrying_prose_is_rejected() -> None:
    findings = _findings(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=OPEN_ENDED_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=(DESCRIPTOR_FACT,),
            ),
        )
    )
    assert any("structured handling with a prose binding" in f for f in findings)


def test_duplicate_component_semantic_key_is_rejected() -> None:
    duplicate = ComponentDraft(
        record_key=SPELL_KEY,
        semantic_key=DESCRIPTOR_KEY,
        handling=ComponentHandling.STRUCTURED,
        facts=(DESCRIPTOR_FACT,),
    )
    findings = _findings(
        components=(duplicate, duplicate, build_representation().components[1])
    )
    assert any("duplicate semantic key" in f for f in findings)


def test_record_related_to_itself_is_rejected() -> None:
    findings = _findings(
        relationships=(
            RelationshipDraft(SPELL_KEY, SPELL_KEY, RelationshipKind.PREREQUISITE),
        )
    )
    assert any("record related to itself" in f for f in findings)


def test_reference_from_an_unknown_record_is_rejected() -> None:
    findings = _findings(
        references=(
            ReferenceDraft(
                "spell:ghost", DESCRIPTOR_KEY, "the servant", "spell:wish", SPELL_KEY
            ),
        )
    )
    assert any("unknown source record spell:ghost" in f for f in findings)


def test_reference_from_an_unknown_component_is_rejected() -> None:
    findings = _findings(
        references=(
            ReferenceDraft(
                SPELL_KEY, "ghost-component", "the servant", "spell:wish", SPELL_KEY
            ),
        )
    )
    assert any("unknown source component ghost-component" in f for f in findings)


def test_reference_to_an_unknown_record_is_rejected() -> None:
    findings = _findings(
        references=(
            ReferenceDraft(
                SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", "spell:ghost"
            ),
        )
    )
    assert any("unknown target record spell:ghost" in f for f in findings)


def test_negative_progression_level_is_rejected() -> None:
    fact = ProgressionEntryFact(level=-1, entitlement_key="feature:x")
    assert any("negative progression level" in f for f in _with_facts(fact))


# -- persisted payloads rebuild every declared family -------------------------


@pytest.mark.parametrize(
    "fact",
    [
        AbilityCheckFact(AbilityScore.WISDOM, DcKind.FIXED, 15),
        AbilityCheckFact(AbilityScore.DEXTERITY, DcKind.SPELL_SAVE_DC),
        CreatureAbilityScoreFact(AbilityScore.CONSTITUTION, 14),
        SpellDescriptorFact(
            level=3, school=SpellSchool.ILLUSION, ritual=True, concentration=True
        ),
        ProgressionEntryFact(level=5, entitlement_key="feature:extra", quantity=2),
    ],
)
def test_every_declared_family_round_trips_through_its_payload(fact: object) -> None:
    rebuilt = fact_from_payload(fact_payload(fact))
    assert rebuilt == fact
    assert fact_invariant_violations(rebuilt) == ()
