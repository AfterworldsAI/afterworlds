"""The real CRD Issue 5c release — CRD Issue 5d production control.

Everything else in this suite runs against a bounded fixture. This module runs
against the *actual* published SRD 5.2.1 corpus: built from the committed PDF,
finalized through CRD Issue 5c's own persist → reconstruct → digest → gate →
publish lifecycle, then re-persisted into a private database.

It proves the claim this PR must not overstate — the publication machinery is
complete and the production mechanical projection is not — and it proves it
*structurally*.

The projection used here is the strongest possible incomplete one. It is built
over real leaves of the real release, it is internally honest, its
persisted-state proof is recorded, and the accepted oracle judging it states
exactly what it contains, down to deriving the same projection identity. Every
comparison the gate makes against that oracle passes. It is refused anyway,
because the release represents leaves it never classified — reported per leaf,
with no count, threshold, floor, or percentage anywhere in the decision.

Session-scoped 5c fixtures are shared with the CRD Issue 5c suite through
``tests/ingestion/conftest.py``, so this costs no second corpus build.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.persistence import persist_release
from afterworlds.ingestion.corpus.pipeline import ReleaseArtifacts
from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.bound_corpus import load_bound_corpus
from afterworlds.ingestion.mechanical.gate import (
    GateFailureCategory,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.models import (
    AcceptanceRecord,
    ClassificationLedger,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedOracle,
    committed_oracle_for,
)
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import (
    ReleaseBinding,
    identify_projection,
)
from afterworlds.ingestion.mechanical.publication import (
    PublicationOutcome,
    _publish_projection,
    publish_from_committed_oracle,
    resolve_active_projection,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    RepresentationDraft,
    representation_schema_hash,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from tests.ingestion.mechanical.conftest import NOW, candidate_of

#: How many real leaves the incomplete projection classifies. Three, for the
#: same reason the bounded fixture has three: the point is that it is not the
#: release's population, not how far short it falls.
CLASSIFIED_LEAVES = 3

EMPTY_REPRESENTATION = RepresentationDraft(
    records=(),
    components=(),
    prose_bindings=(),
    relationships=(),
    references=(),
    provenance=(),
)


@dataclass(frozen=True)
class ProductionFixture:
    """One real release, one incomplete projection over it, and its oracle."""

    session: Session
    release: ReleaseArtifacts
    binding: ReleaseBinding
    projection_uuid: str
    oracle: AcceptedOracle


def _binding(release: ReleaseArtifacts) -> ReleaseBinding:
    identity = release.release.identity
    assert identity.persisted_corpus_digest is not None
    return ReleaseBinding(
        package_uuid=release.release.package_uuid,
        release_version=release.release.release_version,
        authoritative_source_hash=identity.authoritative_source_hash,
        transform_config_hash=identity.transform_config_hash,
        bundle_root_hash=identity.bundle_root_hash,
        persisted_corpus_digest=identity.persisted_corpus_digest,
    )


def _publish_persisted_release(session: Session, pkg: str) -> None:
    """Transition a re-persisted 5c release to published, as finalize does."""
    session.execute(
        select(CorpusReleaseORM).where(CorpusReleaseORM.package_uuid == pkg)
    ).scalar_one().publication_status = "published"
    package_row = session.execute(
        select(RulesPackageORM).where(RulesPackageORM.rules_package_id == pkg)
    ).scalar_one()
    package_row.publication_status = "published"
    package_row.published_at = NOW
    session.flush()


@pytest.fixture(scope="module")
def production(full_release: ReleaseArtifacts):  # type: ignore[no-untyped-def]
    """The real release persisted into a private store, plus one draft over it.

    Module-scoped because writing 5c's full persisted state is expensive and
    nothing in this module publishes successfully — every attempt is refused,
    so no test can leave state another test would read.
    """
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with create_session_factory(engine)() as session:
        persist_release(session, full_release, now=NOW)
        # ``persist_release`` writes step-c drafts; in 5c the transition to
        # published is the last step of a gate that has already passed. This
        # store is a re-persist of an already-finalized release, so the
        # transition is restated here rather than left implied — the 5d gate
        # now refuses to publish over a draft 5c release, and it is right to.
        _publish_persisted_release(session, full_release.release.package_uuid)
        binding = _binding(full_release)
        corpus = load_bound_corpus(
            session, binding.package_uuid, binding.release_version
        )

        # Real leaves of the real release, classified honestly and completely:
        # one gap-free span each, non-mechanical under a closed catalog reason,
        # with explicit acceptance evidence. Nothing about these three claims is
        # wrong — there are simply tens of thousands more.
        chosen = sorted(corpus.leaf_lengths)[:CLASSIFIED_LEAVES]
        spans = tuple(
            SemanticSpan(
                span_id=derive_span_id(leaf_id, 0, corpus.leaf_lengths[leaf_id]),
                leaf_id=leaf_id,
                char_start=0,
                char_end=corpus.leaf_lengths[leaf_id],
                disposition=SemanticDisposition.NON_MECHANICAL,
                review_state=ReviewState.ACCEPTED,
                non_mechanical_reason_code="legal_licensing",
            )
            for leaf_id in chosen
        )
        classification = ClassificationLedger(
            package_uuid=binding.package_uuid,
            release_version=binding.release_version,
            policy_version=SEMANTIC_POLICY_VERSION,
            policy_hash=semantic_policy_hash(),
            spans=spans,
            batches=(),
            acceptances=tuple(
                AcceptanceRecord(s.span_id, None, "owner", NOW) for s in spans
            ),
        )
        identified = identify_projection(
            candidate_of(
                binding=binding,
                classification=classification,
                representation=EMPTY_REPRESENTATION,
            )
        )
        persist_draft(session, identified, now=NOW)
        record_persisted_state_digest(session, identified.projection_uuid)

        yield ProductionFixture(
            session=session,
            release=full_release,
            binding=binding,
            projection_uuid=identified.projection_uuid,
            # The accepted authority states exactly this content — so every
            # oracle comparison passes and only the release's own population
            # can refuse it.
            oracle=AcceptedOracle(
                binding=binding,
                policy_version=SEMANTIC_POLICY_VERSION,
                policy_hash=semantic_policy_hash(),
                schema_version=REPRESENTATION_SCHEMA_VERSION,
                schema_hash=representation_schema_hash(),
                spans=spans,
                representation=EMPTY_REPRESENTATION,
                obligations=(),
            ),
        )
    engine.dispose()


# ---------------------------------------------------------------------------
# The release supplies the population
# ---------------------------------------------------------------------------


def test_the_bound_release_supplies_the_accounting_population(
    production: ProductionFixture,
) -> None:
    """Population comes from 5c, not from any CRD Issue 5d input.

    The exact total is a drift canary, not a contract — what matters is that it
    is tens of thousands of leaves and that it is read from the release.
    """
    corpus = load_bound_corpus(
        production.session,
        production.binding.package_uuid,
        production.binding.release_version,
    )
    assert len(corpus.leaf_lengths) > 10_000
    assert corpus.authoritative_chunk_ids


# ---------------------------------------------------------------------------
# The production projection cannot be published
# ---------------------------------------------------------------------------


def test_the_accepted_oracle_for_the_production_release_resolves(
    production: ProductionFixture,
) -> None:
    """Accepted authority exists for the real SRD release — two accepted batches.

    It judges 22 records — 15 conditions and 5 hazards, plus the glossary entry
    that defines each list — and nothing else, which is exactly why the
    publication test below still refuses: the SRD has far more than 22 records.
    """
    resolved = committed_oracle_for(
        production.binding.package_uuid, production.binding.release_version
    )
    assert resolved is not None
    assert resolved.binding == production.binding
    assert len(resolved.representation.records) == 22
    assert len(resolved.spans) == 281


def test_the_production_path_refuses_the_real_release(
    production: ProductionFixture,
) -> None:
    """``publish_from_committed_oracle`` still fails closed — for a new reason.

    Before ``conditions-1`` was accepted this returned ``ABSENT``: no authority
    judged the release at all. Authority now exists and resolves, so the refusal
    moves to ``INCOMPLETE`` — the accepted artifact covers 16 condition records
    while the persisted projection covers the whole SRD. The change of *reason*
    is the point: publication is refused because the CRD Issue 5d corpus is
    unfinished, not because nothing was ever reviewed.
    """
    result = publish_from_committed_oracle(
        production.session, production.projection_uuid, now=NOW
    )
    assert result.outcome is PublicationOutcome.INCOMPLETE
    assert (
        resolve_active_projection(
            production.session, production.binding.package_uuid
        ).outcome
        is PublicationOutcome.UNPUBLISHED
    )


def test_everything_the_projection_claims_is_accepted(
    production: ProductionFixture,
) -> None:
    """The control is not passing for an incidental reason.

    Its persisted state proves out, its accepted oracle derives the very same
    projection identity, and no comparison against that oracle fails. If any of
    this stopped holding, the population failure below would no longer be the
    thing being tested.

    The only two categories present are the uncovered population and the
    candidate validator's own view of the same leaves — one uncovered leaf,
    reported by both layers. Nothing about release binding, policy, review
    residue, missing/unexpected/duplicate authority, obligations, or identity
    is wrong here.
    """
    result = run_publication_gate(
        production.session, production.projection_uuid, production.oracle
    )
    assert result.expected_projection_uuid == production.projection_uuid
    assert result.persisted_state_digest is not None
    assert result.categories() == {
        GateFailureCategory.POPULATION_MISMATCH,
        GateFailureCategory.SEMANTIC_VALIDATION,
    }
    assert all(
        "no semantic spans" in f.detail
        for f in result.failures
        if f.category is GateFailureCategory.SEMANTIC_VALIDATION
    )


def test_the_incomplete_production_projection_fails_the_real_gate(
    production: ProductionFixture,
) -> None:
    """It fails per uncovered leaf, structurally, with no aggregate involved."""
    result = run_publication_gate(
        production.session, production.projection_uuid, production.oracle
    )
    assert not result.passed

    missing = [
        f
        for f in result.failures
        if f.category is GateFailureCategory.POPULATION_MISMATCH
    ]
    assert len(missing) > 10_000
    assert all(
        "represented by the bound 5c release, absent from the accepted "
        "classification" in f.detail
        for f in missing
    )

    corpus = load_bound_corpus(
        production.session,
        production.binding.package_uuid,
        production.binding.release_version,
    )
    assert len(missing) == len(corpus.leaf_lengths) - CLASSIFIED_LEAVES


def test_the_incomplete_production_projection_is_refused_as_incomplete(
    production: ProductionFixture,
) -> None:
    """Typed refusal, nothing written, nothing activated."""
    result = _publish_projection(
        production.session, production.projection_uuid, production.oracle, now=NOW
    )
    assert result.outcome is PublicationOutcome.INCOMPLETE
    assert (
        resolve_active_projection(
            production.session, production.binding.package_uuid
        ).outcome
        is PublicationOutcome.UNPUBLISHED
    )


def test_classifying_more_leaves_does_not_help(
    production: ProductionFixture,
) -> None:
    """Partial progress is not partial success.

    A projection covering nearly the whole release fails exactly as the
    three-leaf one does. Publication is not a threshold that better coverage
    eventually crosses (ADR-005d Decision 5).
    """
    corpus = load_bound_corpus(
        production.session,
        production.binding.package_uuid,
        production.binding.release_version,
    )
    nearly_all = sorted(corpus.leaf_lengths)[:-1]
    spans = tuple(
        SemanticSpan(
            span_id=derive_span_id(leaf_id, 0, corpus.leaf_lengths[leaf_id]),
            leaf_id=leaf_id,
            char_start=0,
            char_end=corpus.leaf_lengths[leaf_id],
            disposition=SemanticDisposition.NON_MECHANICAL,
            review_state=ReviewState.ACCEPTED,
            non_mechanical_reason_code="legal_licensing",
        )
        for leaf_id in nearly_all
    )
    classification = replace(
        ClassificationLedger(
            package_uuid=production.binding.package_uuid,
            release_version=production.binding.release_version,
            policy_version=SEMANTIC_POLICY_VERSION,
            policy_hash=semantic_policy_hash(),
            spans=spans,
            batches=(),
            acceptances=tuple(
                AcceptanceRecord(s.span_id, None, "owner", NOW) for s in spans
            ),
        )
    )
    identified = identify_projection(
        candidate_of(
            binding=production.binding,
            classification=classification,
            representation=EMPTY_REPRESENTATION,
        )
    )
    persist_draft(production.session, identified, now=NOW)
    record_persisted_state_digest(production.session, identified.projection_uuid)

    oracle = replace(production.oracle, spans=spans)
    result = _publish_projection(
        production.session, identified.projection_uuid, oracle, now=NOW
    )
    assert result.outcome is PublicationOutcome.INCOMPLETE
    assert result.gate is not None
    assert GateFailureCategory.POPULATION_MISMATCH in result.gate.categories()


def test_the_evidence_report_names_the_exact_production_release(
    production: ProductionFixture,
) -> None:
    """A refusal is auditable: the report says what was judged, and by what."""
    result = _publish_projection(
        production.session, production.projection_uuid, production.oracle, now=NOW
    )
    assert result.report is not None
    payload = result.report.payload
    binding = production.binding

    assert payload["source_release"] == {
        "package_uuid": binding.package_uuid,
        "release_version": binding.release_version,
        "authoritative_source_hash": binding.authoritative_source_hash,
        "transform_config_hash": binding.transform_config_hash,
        "bundle_root_hash": binding.bundle_root_hash,
        "persisted_corpus_digest": binding.persisted_corpus_digest,
    }
    gate_payload = payload["gate"]
    assert isinstance(gate_payload, dict)
    assert gate_payload["passed"] is False
    assert gate_payload["failure_categories"] == [
        "population_mismatch",
        "semantic_validation",
    ]

    diagnostics = payload["drift_diagnostics"]
    assert isinstance(diagnostics, dict)
    assert diagnostics["classified_leaves"] == CLASSIFIED_LEAVES
    assert diagnostics["represented_leaves"] > 10_000
