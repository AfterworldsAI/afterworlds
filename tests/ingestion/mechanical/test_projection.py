"""Projection identity — CRD Issue 5d, Decisions 6 and 8.

Two properties matter here and are easy to lose: identity derivation is
acyclic (payload → projection UUID → subidentities, never the reverse), and a
computed identity is not a licence to publish.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.hashing import canonical_json
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    ReleaseBinding,
    identify_projection,
    projection_payload,
    projection_uuid,
    validate_candidate,
)
from afterworlds.ingestion.mechanical.representation import (
    ComponentDraft,
    ProgressionEntryFact,
    RecordDraft,
    RecordKind,
    SpellDescriptorFact,
    SpellSchool,
)
from tests.ingestion.mechanical.conftest import (
    CREATURE_KEY,
    DESCRIPTOR_FACT,
    DESCRIPTOR_KEY,
    LEAF_LENGTHS,
    OPEN_ENDED_KEY,
    SPELL_KEY,
    SPELL_LEAF,
    build_candidate,
    build_ledger,
    build_representation,
)

# -- acyclic derivation ------------------------------------------------------


def test_payload_contains_no_derived_identity() -> None:
    identified = identify_projection(build_candidate())
    serialized = canonical_json(projection_payload(identified.candidate))
    assert identified.projection_uuid not in serialized
    for derived in (
        *identified.record_ids.values(),
        *identified.component_ids.values(),
        *identified.fact_ids.values(),
    ):
        assert derived not in serialized


def test_subidentities_derive_from_the_projection_identity() -> None:
    identified = identify_projection(build_candidate())
    assert set(identified.record_ids) == {SPELL_KEY, CREATURE_KEY}
    assert (SPELL_KEY, DESCRIPTOR_KEY) in identified.component_ids
    assert len(identified.fact_ids) == 1
    # Distinct kinds never collide even on identical semantic keys.
    assert (
        identified.record_ids[SPELL_KEY]
        != identified.component_ids[(SPELL_KEY, DESCRIPTOR_KEY)]
    )


def test_identity_is_reproducible_for_identical_content() -> None:
    assert projection_uuid(build_candidate()) == projection_uuid(build_candidate())


def test_identity_is_order_independent() -> None:
    draft = build_representation()
    reordered = build_representation(
        records=tuple(reversed(draft.records)),
        components=tuple(reversed(draft.components)),
        provenance=tuple(reversed(draft.provenance)),
    )
    assert projection_uuid(build_candidate()) == projection_uuid(
        ProjectionCandidate(
            binding=build_candidate().binding,
            classification=build_ledger(),
            representation=reordered,
        )
    )


def test_unrelated_sibling_insertion_does_not_churn_existing_subidentities() -> None:
    before = identify_projection(build_candidate())
    draft = build_representation()
    with_sibling = build_representation(
        records=draft.records + (RecordDraft("spell:other", RecordKind.SPELL),)
    )
    after = identify_projection(
        ProjectionCandidate(
            binding=before.candidate.binding,
            classification=build_ledger(),
            representation=with_sibling,
        )
    )
    # The projection identity changes — meaning changed. What must not happen is
    # a *positional* churn: the surviving keys keep deriving the same way from
    # whatever projection identity they belong to.
    assert after.projection_uuid != before.projection_uuid
    assert set(before.record_ids) < set(after.record_ids)
    assert after.record_ids[SPELL_KEY] != before.record_ids[SPELL_KEY]


# -- meaning-bearing payload -------------------------------------------------


def _uuid_with(**overrides: object) -> str:
    return projection_uuid(build_candidate(**overrides))


def test_identity_changes_when_the_bound_release_changes() -> None:
    base = build_candidate()
    other = ProjectionCandidate(
        binding=ReleaseBinding(
            package_uuid=base.binding.package_uuid,
            release_version=base.binding.release_version,
            authoritative_source_hash=base.binding.authoritative_source_hash,
            transform_config_hash=base.binding.transform_config_hash,
            bundle_root_hash=base.binding.bundle_root_hash,
            persisted_corpus_digest="e" * 64,
        ),
        classification=base.classification,
        representation=base.representation,
    )
    assert projection_uuid(other) != projection_uuid(base)


def test_identity_changes_when_a_fact_value_changes() -> None:
    changed = build_representation(
        components=(
            ComponentDraft(
                SPELL_KEY,
                DESCRIPTOR_KEY,
                ComponentHandling.STRUCTURED,
                facts=(
                    SpellDescriptorFact(
                        level=8,  # was 9
                        school=SpellSchool.CONJURATION,
                        ritual=False,
                        concentration=False,
                    ),
                ),
            ),
            build_representation().components[1],
        )
    )
    assert projection_uuid(
        ProjectionCandidate(build_candidate().binding, build_ledger(), changed)
    ) != projection_uuid(build_candidate())


def test_identity_changes_when_record_assembly_changes() -> None:
    assert _uuid_with(
        records=(
            RecordDraft(SPELL_KEY, RecordKind.SPELL),
            RecordDraft(CREATURE_KEY, RecordKind.CREATURE),  # no longer nested
        )
    ) != projection_uuid(build_candidate())


def test_identity_changes_when_a_prose_binding_changes() -> None:
    draft = build_representation()
    rebound = build_representation(
        prose_bindings=(
            type(draft.prose_bindings[0])(
                component_key=OPEN_ENDED_KEY,
                record_key=SPELL_KEY,
                chunk_id="chunk-wish-0002",
                irreducibility_reason_code="open_ended_effect",
            ),
        )
    )
    assert projection_uuid(
        ProjectionCandidate(build_candidate().binding, build_ledger(), rebound)
    ) != projection_uuid(build_candidate())


def test_identity_changes_when_provenance_changes() -> None:
    draft = build_representation()
    assert _uuid_with(provenance=draft.provenance[:-1]) != projection_uuid(
        build_candidate()
    )


def test_identity_changes_when_the_accepted_classification_changes() -> None:
    spans = build_ledger().spans
    relabelled = build_ledger(
        spans=(
            SemanticSpan(
                span_id=spans[0].span_id,
                leaf_id=spans[0].leaf_id,
                char_start=0,
                char_end=40,
                disposition=SemanticDisposition.SUPPORTING_AUTHORITY,
                review_state=ReviewState.ACCEPTED,
            ),
            *spans[1:],
        )
    )
    assert projection_uuid(
        ProjectionCandidate(
            build_candidate().binding, relabelled, build_representation()
        )
    ) != projection_uuid(build_candidate())


# -- identification is not publication ---------------------------------------


def test_honest_candidate_has_no_blocking_findings() -> None:
    assert validate_candidate(build_candidate(), LEAF_LENGTHS) == ()


def test_a_dishonest_candidate_still_computes_an_identity() -> None:
    # This is the invariant: identity is computable for anything, so it can
    # never stand in for proof. The findings are what block publication.
    broken = build_candidate(
        components=(
            ComponentDraft(SPELL_KEY, DESCRIPTOR_KEY, ComponentHandling.STRUCTURED),
        )
    )
    assert projection_uuid(broken)
    assert validate_candidate(broken, LEAF_LENGTHS) != ()


def test_classified_leaf_outside_the_bound_release_is_rejected() -> None:
    findings = validate_candidate(
        build_candidate(), {k: v for k, v in LEAF_LENGTHS.items() if k != SPELL_LEAF}
    )
    assert any("classified but not in the bound release" in f for f in findings)


def test_release_leaf_with_no_classification_is_rejected() -> None:
    findings = validate_candidate(
        build_candidate(), {**LEAF_LENGTHS, "leaf-unreviewed": 12}
    )
    assert any("leaf-unreviewed: no semantic spans" in f for f in findings)


def test_candidate_under_a_stale_policy_declaration_is_rejected() -> None:
    stale = build_ledger()
    stale = type(stale)(
        package_uuid=stale.package_uuid,
        release_version=stale.release_version,
        policy_version="5d-semantic-policy-0",
        policy_hash=stale.policy_hash,
        spans=stale.spans,
        batches=stale.batches,
        acceptances=stale.acceptances,
    )
    findings = validate_candidate(
        ProjectionCandidate(build_candidate().binding, stale, build_representation()),
        LEAF_LENGTHS,
    )
    assert any("build uses" in f for f in findings)


def test_fact_families_stay_distinct_under_identity() -> None:
    # Two different families with coincidentally similar values must not
    # collapse: the discriminator is part of the payload.
    a = ProgressionEntryFact(level=9, entitlement_key="x")
    b = DESCRIPTOR_FACT
    assert projection_uuid(
        build_candidate(
            components=(
                ComponentDraft(
                    SPELL_KEY, DESCRIPTOR_KEY, ComponentHandling.STRUCTURED, facts=(a,)
                ),
                build_representation().components[1],
            )
        )
    ) != projection_uuid(
        build_candidate(
            components=(
                ComponentDraft(
                    SPELL_KEY, DESCRIPTOR_KEY, ComponentHandling.STRUCTURED, facts=(b,)
                ),
                build_representation().components[1],
            )
        )
    )
