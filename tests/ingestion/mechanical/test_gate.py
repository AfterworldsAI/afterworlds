"""The exact completeness gate — CRD Issue 5d, Decision 5.

The bounded fixture is a *complete* projection of its bound release: three
represented leaves, all classified, every element declared by the committed
oracle. That is what makes the negative controls meaningful — each one changes
exactly one thing about the persisted state, and the accepted authority never
moves.

Every control asserts a **specific failure category**. Asserting only
``passed is False`` would pass even if the gate rejected for an unrelated
reason, which is how a completeness proof rots into a smoke test.

Aggregate totals appear once, and only to prove they are diagnostics: the
all-prose and duplicated-fact controls both keep a plausible-looking element
count and are rejected anyway (ADR-005d Decision 5).
"""

from __future__ import annotations

import dataclasses

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.gate import (
    GateFailureCategory,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.models import (
    AcceptanceRecord,
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
)
from afterworlds.ingestion.mechanical.oracle import AcceptedOracle
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    identify_projection,
)
from afterworlds.ingestion.mechanical.representation import (
    ComponentDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    ReferenceDraft,
    fact_key,
)
from afterworlds.persistence.orm.corpus import LedgerLeafORM
from afterworlds.persistence.orm.mechanical import (
    MechanicalFactORM,
    MechanicalProjectionORM,
    MechanicalRecordORM,
    MechanicalSpanORM,
)
from tests.ingestion.mechanical.conftest import (
    DESCRIPTOR_FACT,
    DESCRIPTOR_FACT_KEY,
    DESCRIPTOR_KEY,
    NOW,
    OPEN_ENDED_KEY,
    PROSE_SPAN,
    SPELL_KEY,
    SPELL_SPAN,
    SUPPORT_SPAN,
    build_candidate,
    build_ledger,
    build_representation,
    current_release_binding,
    rerecord_release_proof,
)


def persist(session: Session, candidate: ProjectionCandidate | None = None) -> str:
    """Persist a draft and record its persisted-state proof, as PR #139 does."""
    identified = identify_projection(
        build_candidate() if candidate is None else candidate
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    return identified.projection_uuid


def categories(session: Session, uuid: str, oracle: AcceptedOracle) -> set[str]:
    result = run_publication_gate(session, uuid, oracle)
    assert not result.passed
    return {c.value for c in result.categories()}


# ---------------------------------------------------------------------------
# The complete bounded projection passes
# ---------------------------------------------------------------------------


def test_a_complete_bounded_projection_passes(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    uuid = persist(session)
    result = run_publication_gate(session, uuid, committed_oracle)
    assert result.passed, result.failures
    assert result.expected_projection_uuid == uuid
    assert result.persisted_state_digest is not None
    assert all(o.satisfied for o in result.obligations)
    assert {o.record_key for o in result.obligations} == {
        "spell:wish",
        "creature:wish-scoped-servant",
    }


def test_a_passing_gate_records_every_obligation_not_only_failures(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """A verdict with no evidence behind it is an assertion, not a proof."""
    result = run_publication_gate(session, persist(session), committed_oracle)
    assert [(o.record_key, o.satisfied, o.failures) for o in result.obligations] == [
        ("spell:wish", True, ()),
        ("creature:wish-scoped-servant", True, ()),
    ]


def test_the_gate_writes_nothing(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    uuid = persist(session)
    run_publication_gate(session, uuid, committed_oracle)
    header = session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == uuid
        )
    ).scalar_one()
    assert header.publication_status == "draft"
    assert header.evidence_report_hash is None
    assert header.oracle_identity is None


# ---------------------------------------------------------------------------
# Omitted authority
# ---------------------------------------------------------------------------


def test_omitted_represented_text_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """A leaf the bound 5c release represents but nobody classified.

    Population equality is read from the release, not from the oracle, so this
    is structural: the projection simply is not over that release's population.
    """
    uuid = persist(session)
    session.execute(
        MechanicalSpanORM.__table__.delete().where(
            MechanicalSpanORM.span_id == SUPPORT_SPAN
        )
    )
    session.flush()
    found = categories(session, uuid, committed_oracle)
    assert GateFailureCategory.POPULATION_MISMATCH.value in found
    assert GateFailureCategory.CLASSIFICATION_MISMATCH.value in found


def test_omitted_accepted_obligation_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """The accepted prose-bound clause is dropped from the persisted record."""
    without_clause = build_representation(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=DESCRIPTOR_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=(DESCRIPTOR_FACT,),
            ),
        ),
        prose_bindings=(),
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
                PROSE_SPAN,
                ProvenanceRole.PRIMARY,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.RECORD,
                (SPELL_KEY,),
                SUPPORT_SPAN,
                ProvenanceRole.CONTEXTUAL,
            ),
        ),
        relationships=(),
    )
    uuid = persist(
        session,
        dataclasses.replace(build_candidate(), representation=without_clause),
    )
    found = categories(session, uuid, committed_oracle)
    assert GateFailureCategory.UNSATISFIED_OBLIGATION.value in found
    assert GateFailureCategory.MISSING_AUTHORITY.value in found


# ---------------------------------------------------------------------------
# Residue
# ---------------------------------------------------------------------------


def test_a_proposed_span_fails_as_unreviewed(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    uuid = persist(session)
    row = session.execute(
        select(MechanicalSpanORM).where(MechanicalSpanORM.span_id == SPELL_SPAN)
    ).scalar_one()
    row.review_state = ReviewState.PROPOSED.value
    session.flush()
    assert GateFailureCategory.UNREVIEWED_RESIDUE.value in categories(
        session, uuid, committed_oracle
    )


def test_a_span_with_no_acceptance_record_fails_as_unreviewed(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Silence is never acceptance, even when the row claims it is accepted."""
    ledger = build_ledger()
    unaccepted = dataclasses.replace(
        ledger,
        acceptances=tuple(a for a in ledger.acceptances if a.span_id != PROSE_SPAN),
    )
    uuid = persist(
        session,
        dataclasses.replace(build_candidate(), classification=unaccepted),
    )
    assert GateFailureCategory.UNREVIEWED_RESIDUE.value in categories(
        session, uuid, committed_oracle
    )


def test_an_unresolved_span_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    uuid = persist(session)
    row = session.execute(
        select(MechanicalSpanORM).where(MechanicalSpanORM.span_id == SUPPORT_SPAN)
    ).scalar_one()
    row.disposition = SemanticDisposition.UNRESOLVED.value
    session.flush()
    assert GateFailureCategory.UNRESOLVED_RESIDUE.value in categories(
        session, uuid, committed_oracle
    )


# ---------------------------------------------------------------------------
# Under-extraction and inflated coverage
# ---------------------------------------------------------------------------


def test_all_prose_under_extraction_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Every component re-described as prose, none of the accepted facts kept.

    The element count barely moves. The obligation is what refuses it: the
    accepted spell-descriptor authority is not represented by typed facts.
    """
    all_prose = build_representation(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=DESCRIPTOR_KEY,
                handling=ComponentHandling.PROSE_BOUND,
                irreducibility_reason_code="open_ended_effect",
            ),
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=OPEN_ENDED_KEY,
                handling=ComponentHandling.PROSE_BOUND,
                irreducibility_reason_code="open_ended_effect",
            ),
        )
    )
    uuid = persist(
        session, dataclasses.replace(build_candidate(), representation=all_prose)
    )
    result = run_publication_gate(session, uuid, committed_oracle)
    assert not result.passed
    assert GateFailureCategory.UNSATISFIED_OBLIGATION.value in {
        c.value for c in result.categories()
    }
    assert any(
        "not represented by typed facts" in f
        for o in result.obligations
        for f in o.failures
    )


def test_reference_only_coverage_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """A record covered by references alone satisfies no obligation.

    References are added and the facts removed, so coverage *looks* present.
    A reference is not a fact, so the accepted structured authority is absent.
    """
    reference = ReferenceDraft(
        from_record_key=SPELL_KEY,
        from_component_key=DESCRIPTOR_KEY,
        source_text="see the descriptor table",
        scope_key="spell:wish",
        target_record_key=SPELL_KEY,
    )
    reference_only = build_representation(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=DESCRIPTOR_KEY,
                handling=ComponentHandling.PROSE_BOUND,
                irreducibility_reason_code="open_ended_effect",
            ),
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=OPEN_ENDED_KEY,
                handling=ComponentHandling.PROSE_BOUND,
                irreducibility_reason_code="open_ended_effect",
            ),
        ),
        references=(reference,),
    )
    uuid = persist(
        session, dataclasses.replace(build_candidate(), representation=reference_only)
    )
    found = categories(session, uuid, committed_oracle)
    assert GateFailureCategory.UNSATISFIED_OBLIGATION.value in found
    assert GateFailureCategory.UNEXPECTED_AUTHORITY.value in found


def test_a_duplicated_fact_row_fails_as_duplicate_not_unexpected(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """One accepted fact, persisted twice: coverage inflated, meaning unchanged.

    Multiset comparison is what separates this from carrying something nobody
    accepted — collapsing the two categories would let inflation hide inside
    "unexpected".
    """
    uuid = persist(session)
    row = session.execute(select(MechanicalFactORM)).scalars().one()
    session.add(
        MechanicalFactORM(
            projection_uuid=uuid,
            fact_id=row.fact_id,
            record_key=row.record_key,
            component_key=row.component_key,
            fact_key=row.fact_key,
            family=row.family,
            payload=dict(row.payload),
        )
    )
    session.flush()
    found = categories(session, uuid, committed_oracle)
    assert GateFailureCategory.DUPLICATE_AUTHORITY.value in found
    assert GateFailureCategory.UNEXPECTED_AUTHORITY.value not in found


def test_a_duplicated_provenance_edge_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """The same claim recorded twice is one claim, not two."""
    duplicated = build_representation()
    uuid = persist(
        session,
        dataclasses.replace(
            build_candidate(),
            representation=dataclasses.replace(
                duplicated, provenance=duplicated.provenance + duplicated.provenance[:1]
            ),
        ),
    )
    found = categories(session, uuid, committed_oracle)
    assert GateFailureCategory.DUPLICATE_AUTHORITY.value in found


def test_an_unexpected_record_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Authority outside the accepted oracle, however plausible it looks."""
    uuid = persist(session)
    row = session.execute(select(MechanicalRecordORM)).scalars().first()
    assert row is not None
    session.add(
        MechanicalRecordORM(
            projection_uuid=uuid,
            record_id="unexpected-record-id",
            semantic_key="spell:invented",
            kind=row.kind,
            parent_key=None,
        )
    )
    session.flush()
    assert GateFailureCategory.UNEXPECTED_AUTHORITY.value in categories(
        session, uuid, committed_oracle
    )


# ---------------------------------------------------------------------------
# Binding, identity, and persisted state
# ---------------------------------------------------------------------------


def test_a_stale_5c_binding_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """A projection built over a different source hash of the same release.

    Refused as a bound-release failure rather than as a mismatch against the
    oracle: the declared binding names no published 5c release at all, which is
    a stronger statement than "the oracle judges something else" and is decided
    before any accepted-authority comparison runs.
    """
    stale = dataclasses.replace(
        build_candidate(),
        binding=dataclasses.replace(
            build_candidate().binding, authoritative_source_hash="9" * 64
        ),
    )
    uuid = persist(session, stale)
    assert GateFailureCategory.BOUND_RELEASE.value in categories(
        session, uuid, committed_oracle
    )


def test_a_mismatched_release_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """An oracle accepted over a different release judges nothing here."""
    uuid = persist(session)
    other = dataclasses.replace(
        committed_oracle,
        binding=dataclasses.replace(
            committed_oracle.binding, release_version="rel-other"
        ),
    )
    assert GateFailureCategory.MISMATCHED_RELEASE.value in categories(
        session, uuid, other
    )


def test_a_mismatched_semantic_policy_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    uuid = persist(session)
    older = dataclasses.replace(committed_oracle, policy_version="5d-semantic-policy-0")
    assert GateFailureCategory.POLICY_MISMATCH.value in categories(session, uuid, older)


def test_tampered_persisted_state_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """A fact payload edited after the digest was recorded."""
    uuid = persist(session)
    row = session.execute(select(MechanicalFactORM)).scalars().one()
    payload = dict(row.payload)
    payload["level"] = 1
    row.payload = payload
    session.flush()
    assert GateFailureCategory.PERSISTED_STATE.value in categories(
        session, uuid, committed_oracle
    )


def test_an_altered_derived_identity_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Every semantic value intact; only a stored derived id was rewritten."""
    uuid = persist(session)
    row = session.execute(select(MechanicalRecordORM)).scalars().first()
    assert row is not None
    row.record_id = "0" * 36
    session.flush()
    assert GateFailureCategory.PERSISTED_STATE.value in categories(
        session, uuid, committed_oracle
    )


def test_an_unrecorded_persisted_state_digest_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """A draft that was never proven cannot be gated into publication."""
    identified = identify_projection(build_candidate())
    persist_draft(session, identified, now=NOW)
    found = categories(session, identified.projection_uuid, committed_oracle)
    assert GateFailureCategory.PERSISTED_STATE.value in found


def test_an_altered_recorded_digest_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    uuid = persist(session)
    header = session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == uuid
        )
    ).scalar_one()
    header.persisted_state_digest = "f" * 64
    session.flush()
    assert GateFailureCategory.PERSISTED_STATE.value in categories(
        session, uuid, committed_oracle
    )


def test_an_ambiguous_reference_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Identical wording in one committed scope resolving two ways."""
    ambiguous = build_representation(
        references=(
            ReferenceDraft(
                SPELL_KEY, DESCRIPTOR_KEY, "the servant", "spell:wish", SPELL_KEY
            ),
            ReferenceDraft(
                SPELL_KEY,
                DESCRIPTOR_KEY,
                "the servant",
                "spell:wish",
                "creature:wish-scoped-servant",
            ),
        )
    )
    uuid = persist(
        session, dataclasses.replace(build_candidate(), representation=ambiguous)
    )
    found = categories(session, uuid, committed_oracle)
    assert GateFailureCategory.SEMANTIC_VALIDATION.value in found


def test_a_missing_projection_is_reported_not_raised(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    result = run_publication_gate(session, "no-such-projection", committed_oracle)
    assert not result.passed
    assert result.categories() == {GateFailureCategory.PERSISTED_STATE}


# ---------------------------------------------------------------------------
# Counts are diagnostics, never proof
# ---------------------------------------------------------------------------


def test_diagnostics_are_reported_but_never_decide(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """The all-prose projection keeps the same component and record totals.

    If totals proved anything, this projection would pass. It does not.
    """
    honest = run_publication_gate(session, persist(session), committed_oracle)
    assert honest.diagnostics["represented_leaves"] == 3
    assert honest.diagnostics["classified_leaves"] == 3
    assert honest.diagnostics["facts"] == 1


def test_a_leaf_classified_outside_the_release_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """5c decides the population; a projection cannot add to it.

    The release is re-proven after the edit and the projection is rebuilt
    against *that* release, so this asserts the population rule rather than the
    bound-release refusal: a 5c release that legitimately represents two
    leaves, and a projection genuinely bound to it that classifies three.
    """
    session.execute(
        LedgerLeafORM.__table__.delete().where(LedgerLeafORM.leaf_id == "leaf-support")
    )
    rerecord_release_proof(session)
    uuid = persist(
        session,
        dataclasses.replace(
            build_candidate(), binding=current_release_binding(session)
        ),
    )
    found = categories(session, uuid, committed_oracle)
    assert GateFailureCategory.POPULATION_MISMATCH.value in found


def test_a_dropped_structured_component_fails(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """The accepted structured component is gone; the prose-bound one remains.

    (Dropping the prose-bound one instead is
    ``test_omitted_accepted_obligation_fails``, which must also drop the prose
    binding — an orphaned binding never reaches the gate, because persisted
    state that will not reconstruct is rejected before it.)
    """
    kept = tuple(
        c for c in build_representation().components if c.semantic_key != DESCRIPTOR_KEY
    )
    representation = dataclasses.replace(
        build_representation(),
        components=kept,
        provenance=tuple(
            p
            for p in build_representation().provenance
            if p.target_kind is not ProvenanceTargetKind.FACT
        ),
    )
    uuid = persist(
        session, dataclasses.replace(build_candidate(), representation=representation)
    )
    found = categories(session, uuid, committed_oracle)
    assert GateFailureCategory.MISSING_AUTHORITY.value in found
    assert GateFailureCategory.UNSATISFIED_OBLIGATION.value in found


def test_fact_key_is_content_derived_so_a_changed_fact_is_a_different_element(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    changed = dataclasses.replace(DESCRIPTOR_FACT, level=8)
    assert fact_key(changed) != DESCRIPTOR_FACT_KEY
    components = (
        dataclasses.replace(build_representation().components[0], facts=(changed,)),
        build_representation().components[1],
    )
    representation = dataclasses.replace(
        build_representation(),
        components=components,
        provenance=tuple(
            (
                dataclasses.replace(
                    p, target_key=(SPELL_KEY, DESCRIPTOR_KEY, fact_key(changed))
                )
                if p.target_kind is ProvenanceTargetKind.FACT
                else p
            )
            for p in build_representation().provenance
        ),
    )
    uuid = persist(
        session, dataclasses.replace(build_candidate(), representation=representation)
    )
    found = categories(session, uuid, committed_oracle)
    assert GateFailureCategory.MISSING_AUTHORITY.value in found
    assert GateFailureCategory.UNEXPECTED_AUTHORITY.value in found


def test_extra_acceptance_evidence_does_not_change_the_verdict(
    session: Session, committed_oracle: AcceptedOracle
) -> None:
    """Reviewer and timestamp are audit metadata, not accepted meaning."""
    ledger = build_ledger()
    relabelled = dataclasses.replace(
        ledger,
        acceptances=tuple(
            AcceptanceRecord(a.span_id, a.batch_id, "another-reviewer", a.accepted_at)
            for a in ledger.acceptances
        ),
    )
    uuid = persist(
        session, dataclasses.replace(build_candidate(), classification=relabelled)
    )
    assert run_publication_gate(session, uuid, committed_oracle).passed
