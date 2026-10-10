"""The source-built release through the real publication lifecycle — 5c/5d step 3.

These are the shared lifecycle and integrity guarantees the clean restart owes,
restored against the replacement corpus rather than against the retired
PDF-geometric product: a real ``finalize_source_release`` into an isolated
SQLite database and an isolated on-disk Chroma store, idempotent reuse of what
it published, detection of a tampered or missing persisted row, refusal and
compensation of an incomplete publication, and identification of the new release
by the operational read path.

Publication costs about fifteen seconds on top of the shared half-minute build,
so the published state is established once per session and every read-only fact
is asserted from it. The cases that must *not* see a published release — refusal
and rollback — get their own stores, because what they prove is exactly that
nothing was left behind.
"""

from __future__ import annotations

import dataclasses
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from chromadb.api import ClientAPI
from sqlalchemy import delete, event, select
from sqlalchemy.orm import Session

import afterworlds.ingestion.corpus.persistence as persistence_mod
from afterworlds.ingestion.corpus.bundle import (
    derive_package_uuid,
    derive_release_version,
)
from afterworlds.ingestion.corpus.concordance import verify_citations
from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.corpus.models import CorpusChunk
from afterworlds.ingestion.corpus.operational import (
    CORPUS_CONTRACT_VERSION,
    load_verified_operational_corpus,
)
from afterworlds.ingestion.corpus.persistence import (
    FinalizeResult,
    finalize_source_release,
    verify_chunk_runtime_membership,
    verify_persisted_digest,
    verify_single_source,
)
from afterworlds.ingestion.corpus.pipeline import CandidateRelease
from afterworlds.ingestion.corpus.policy import PolicyReconstructionError
from afterworlds.ingestion.corpus.source_ledger import (
    CITATION_VERIFICATION,
    PAGE_SUBSTRING,
    SOURCE_PARTITION,
)
from afterworlds.ingestion.corpus.vector_publication import read_actual_vector_state
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import (
    CorpusReleaseORM,
    ReconciliationPolicyORM,
)
from afterworlds.persistence.orm.rules_package import (
    RuleChunkORM,
    RuleSourceORM,
    RulesPackageORM,
)
from afterworlds.pipeline.retrieval.client import build_isolated_test_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.pipeline.retrieval.corpus_windows import derive_windows
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction
from afterworlds.quarantine import (
    QUARANTINED_PACKAGE_UUIDS,
    QUARANTINED_RELEASE_VERSIONS,
    QuarantinedAuthorityError,
)

from ..conftest import NOW, finalize_in_fresh_db


class _Boom(RuntimeError):
    """An unexpected failure raised from inside the publication window."""


@dataclasses.dataclass
class _Stores:
    """A live, isolated SQL session and Chroma client, plus what published there."""

    session: Session
    chroma_client: ClientAPI
    candidate: CandidateRelease
    result: FinalizeResult | None = None


@contextmanager
def _isolated_stores(candidate: CandidateRelease) -> Iterator[_Stores]:
    """A brand-new SQLite database and private on-disk Chroma store.

    ``finalize_in_fresh_db`` closes its stores on the way out, which is right for
    a case that only reads the returned result. The cases here inspect the rows
    and the collection themselves, so the stores have to outlive the call.
    """
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def _fk(dbapi, _record):  # type: ignore[no-untyped-def]
        dbapi.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    session = create_session_factory(engine)()
    client = build_isolated_test_chroma_client(tempfile.mkdtemp(prefix="src-chroma-"))
    try:
        yield _Stores(session, client, candidate)
    finally:
        session.close()
        engine.dispose()


def _publish(stores: _Stores) -> FinalizeResult:
    return finalize_source_release(
        stores.session,
        stores.candidate,
        now=NOW,
        chroma_client=stores.chroma_client,
        retrieval_config=RetrievalMemoryConfig(),
        embedding_function=DeterministicFakeEmbeddingFunction(),
    )


def _vector_count(stores: _Stores) -> int:
    return read_actual_vector_state(
        stores.chroma_client,
        stores.candidate.package_uuid,
        RetrievalMemoryConfig(),
        DeterministicFakeEmbeddingFunction(),
    ).count


@pytest.fixture(scope="session")
def published(source_candidate: CandidateRelease) -> Iterator[_Stores]:
    """The source candidate published once, with both stores left open."""
    with _isolated_stores(source_candidate) as stores:
        stores.result = _publish(stores)
        assert stores.result.published, stores.result.gate
        yield stores


@pytest.fixture()
def damaged(published: _Stores) -> Iterator[Session]:
    """A savepoint around one case's damage, so the published state survives it.

    Each of these needs the *published* rows to break, and republishing per case
    would repeat a full reindex each time. The damage is written inside a
    savepoint and discarded afterwards, so the cases stay independent without
    paying for the expensive part again.
    """
    session = published.session
    session.begin_nested()
    try:
        yield session
    finally:
        session.rollback()


def _reconstructed_chunks(session: Session, pkg: str) -> tuple[CorpusChunk, ...]:
    """The members as the reconstruction reads them back out of the rows."""
    ledger = persistence_mod._load_ledger(session, pkg)
    return persistence_mod._load_members(session, pkg, ledger).chunks


# ---------------------------------------------------------------------------
# Publication
# ---------------------------------------------------------------------------


def test_the_source_corpus_publishes_through_the_real_gate(published: _Stores) -> None:
    """The whole point: persist → reconstruct → digest → gate → publish.

    Not an in-memory approximation — every fact below is read back out of the
    two stores the release was actually written into.
    """
    assert published.result is not None
    assert published.result.published and not published.result.reused
    gate = published.result.gate
    assert gate is not None
    assert gate.passed, gate.failures
    pkg = published.candidate.package_uuid
    rows = (
        published.session.execute(
            select(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg)
        )
        .scalars()
        .all()
    )
    assert len(rows) == len(published.candidate.members.chunks)
    # One chunk is one or more bounded embedding documents, so the vector count
    # is a document count: every chunk is represented, and the long ones are
    # represented by more than one window (corpus_windows). Checked against the
    # same derivation the writer used rather than a pinned number, and bounded
    # above so a windowing regression that exploded the corpus is not silently
    # accepted as "more than chunks".
    expected_documents = sum(
        len(derive_windows(row.content, row.source_section_label)) for row in rows
    )
    assert _vector_count(published) == expected_documents
    assert len(rows) < expected_documents < len(rows) * 2
    release = published.session.get(CorpusReleaseORM, pkg)
    assert release is not None and release.publication_status == "published"


def test_the_evidence_report_names_the_verification_that_actually_ran(
    published: _Stores,
) -> None:
    """A report naming neither mode would read as if the retired check had run."""
    assert published.result is not None and published.result.artifacts is not None
    payload = published.result.artifacts.report.payload
    assert payload["citation_verification"] == SOURCE_PARTITION
    assert payload["uncarried_source_units"] == 0
    assert payload["concordance_failures"] == 0
    assert payload["invalid_locators"] == 0
    assert payload["prepublication_validation_status"] == "pass"
    canaries = payload["version_canaries"]
    assert isinstance(canaries, dict)
    assert all(canaries.values())
    # The mapping the citation pass computed, carried rather than discarded.
    # Each mechanism is counted apart on purpose, and together they account for
    # every unit, so a consumer can weigh a text match against an inference.
    mapping = payload["source_citation_mapping"]
    assert mapping is not None
    assert isinstance(mapping, dict)
    assert mapping["units"] == sum(
        mapping[k] for k in ("located", "placed", "anchored", "inherited")
    )
    assert mapping["unresolved_units"] == []
    assert mapping["uncited_body_pages"] == []
    assert mapping["multi_page_units"] > 0


def test_publishing_the_same_inputs_again_is_a_verified_no_op(
    published: _Stores,
) -> None:
    """Reuse re-proves the cross-store state; it does not re-persist or rewrite."""
    before = _vector_count(published)
    again = _publish(published)
    assert again.published and again.reused
    # Reuse re-runs the *full* gate against the reconstructed state rather than
    # trusting the idempotency select, so a passing gate here is a re-proof.
    assert again.gate is not None and again.gate.passed
    assert again.artifacts is not None
    assert published.result is not None and published.result.artifacts is not None
    # The report the reuse path serves is loaded from the persisted row, not
    # rebuilt, so this is the mapping surviving a round trip through the DB.
    assert (
        again.artifacts.report.payload["source_citation_mapping"]
        == published.result.artifacts.report.payload["source_citation_mapping"]
    )
    assert (
        again.artifacts.release.identity.persisted_corpus_digest
        == published.result.artifacts.release.identity.persisted_corpus_digest
    )
    assert _vector_count(published) == before


# ---------------------------------------------------------------------------
# What a damaged persisted release does
# ---------------------------------------------------------------------------


def test_reuse_refuses_a_release_whose_persisted_chunk_was_tampered_with(
    published: _Stores, damaged: Session
) -> None:
    """The reuse path re-proves the stored state; it does not trust the select.

    The other damage cases call the verifications directly, which shows the
    verification works but not that finalization consults it. This drives the
    real production entry a second time against a damaged store and requires a
    refusal, which is the whole meaning of an idempotent reuse being *verified*
    rather than merely recognized.
    """
    row = damaged.execute(
        select(RuleChunkORM)
        .where(RuleChunkORM.rules_package_id == published.candidate.package_uuid)
        .limit(1)
    ).scalar_one()
    row.content = row.content + " tampered"
    damaged.flush()
    result = _publish(published)
    assert not result.published and not result.reused
    assert result.gate is not None and not result.gate.passed


def test_a_tampered_persisted_chunk_fails_the_citation_re_derivation(
    published: _Stores,
    damaged: Session,
) -> None:
    """The source verification reads the persisted rows, not the built candidate.

    Editing one published chunk is visible to the check that re-derives the
    corpus from the pinned bytes, and visible *twice*: the edited text matches no
    source unit, and the unit it used to carry is now carried by nothing.
    """
    pkg = published.candidate.package_uuid
    row = damaged.execute(
        select(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg).limit(1)
    ).scalar_one()
    row.content = row.content + " TAMPERED"
    damaged.flush()
    result = verify_citations(
        _reconstructed_chunks(damaged, pkg),
        published.candidate.pages,
        published.candidate.transform_config,
        source_texts=published.candidate.source_texts,
    )
    assert not result.passed
    assert len(result.content_failures) == 1
    assert len(result.omissions) == 1


def test_a_reassigned_persisted_locator_breaks_the_release_digest(
    published: _Stores,
    damaged: Session,
) -> None:
    """Citation verification is not the only instrument: the digest moves too."""
    pkg = published.candidate.package_uuid
    row = damaged.execute(
        select(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg).limit(1)
    ).scalar_one()
    row.source_locator_value = "p. 9999"
    damaged.flush()
    state = read_actual_vector_state(
        published.chroma_client,
        pkg,
        RetrievalMemoryConfig(),
        DeterministicFakeEmbeddingFunction(),
    ).to_payload()
    assert not verify_persisted_digest(damaged, pkg, state)


def test_a_second_persisted_source_fails_the_single_source_invariant(
    published: _Stores,
    damaged: Session,
) -> None:
    """The release has exactly one authoritative source; an interloper is caught.

    Carried over from the retired compact-fixture suite, where the source
    membership checks last ran: the published state is clean, and one extra,
    otherwise-valid ``RuleSource`` row both violates the invariant and moves the
    digest.
    """
    pkg = published.candidate.package_uuid
    assert verify_single_source(damaged, pkg) == ()
    damaged.add(
        RuleSourceORM(
            source_id="1" * 36,
            rules_package_id=pkg,
            name="Interloper Source",
            category="supplement",
            precedence_rank=2,
            is_enabled=True,
            created_at=NOW,
        )
    )
    damaged.flush()
    state = read_actual_vector_state(
        published.chroma_client,
        pkg,
        RetrievalMemoryConfig(),
        DeterministicFakeEmbeddingFunction(),
    ).to_payload()
    assert verify_single_source(damaged, pkg)
    assert not verify_persisted_digest(damaged, pkg, state)


def test_a_deleted_persisted_policy_row_fails_closed(
    published: _Stores,
    damaged: Session,
) -> None:
    """Reconstruction reads the persisted policy, never ``FROZEN_POLICY``.

    Carried over from the retired compact-fixture suite: with the policy row
    gone, the digest check refuses before it reads any vector state.
    """
    pkg = published.candidate.package_uuid
    damaged.execute(
        delete(ReconciliationPolicyORM).where(
            ReconciliationPolicyORM.package_uuid == pkg
        )
    )
    damaged.flush()
    with pytest.raises(PolicyReconstructionError):
        verify_persisted_digest(damaged, pkg, {})


def test_an_orphan_enabled_chunk_breaks_runtime_membership(
    published: _Stores,
    damaged: Session,
) -> None:
    """An enabled chunk with no declared projection would be served at runtime.

    Carried over from the retired compact-fixture suite. The digest is scoped to
    the declared projection set, so only the separate membership verification
    sees the stray row.
    """
    pkg = published.candidate.package_uuid
    assert verify_chunk_runtime_membership(damaged, pkg) == ()
    damaged.add(
        RuleChunkORM(
            chunk_id="orphan-chunk-1",
            rules_package_id=pkg,
            source_id=pkg,
            subsystem="general",
            content="stray content with no declared projection",
            source_document="D&D SRD 5.2.1",
            source_locator_type="page",
            source_locator_value="p. 1",
            is_enabled=True,
            created_at=NOW,
        )
    )
    damaged.flush()
    violations = verify_chunk_runtime_membership(damaged, pkg)
    assert any("orphan-chunk-1" in v for v in violations)


def test_an_omitted_persisted_chunk_is_detected_as_an_uncarried_source_unit(
    published: _Stores,
    damaged: Session,
) -> None:
    """A chunk-by-chunk check cannot see this at all: the chunk is simply gone."""
    pkg = published.candidate.package_uuid
    row = damaged.execute(
        select(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg).limit(1)
    ).scalar_one()
    damaged.delete(row)
    damaged.flush()
    result = verify_citations(
        _reconstructed_chunks(damaged, pkg),
        published.candidate.pages,
        published.candidate.transform_config,
        source_texts=published.candidate.source_texts,
    )
    assert not result.passed
    assert result.content_failures == ()
    assert len(result.omissions) == 1


# ---------------------------------------------------------------------------
# Refusal, rollback, compensation
# ---------------------------------------------------------------------------


def test_a_release_that_declares_the_wrong_verification_never_reaches_a_store(
    source_candidate: CandidateRelease,
) -> None:
    """The guard runs before the transaction opens, so there is nothing to undo."""
    config = dict(source_candidate.transform_config)
    config[CITATION_VERIFICATION] = PAGE_SUBSTRING
    wrong = dataclasses.replace(source_candidate, transform_config=config)
    result = finalize_in_fresh_db(wrong)
    assert not result.published and not result.reused
    assert result.artifacts is None
    assert result.gate is not None
    assert any("source_partition" in f for f in result.gate.failures)


def test_a_release_carrying_stale_source_bytes_is_refused(
    source_candidate: CandidateRelease,
) -> None:
    """A snapshot that no longer hashes to the pinned digests is a different
    source, and republishing it under this release's identity would be a lie."""
    sources = dict(source_candidate.source_texts or {})
    sources["legal-information.md"] += "\nlocally edited\n"
    stale = dataclasses.replace(source_candidate, source_texts=sources)
    result = finalize_in_fresh_db(stale)
    assert not result.published
    assert result.gate is not None
    assert any("digest" in f for f in result.gate.failures)


def test_a_failure_inside_the_publication_window_leaves_neither_store_written(
    source_candidate: CandidateRelease, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Compensation, proven where it actually matters.

    ``run_gate`` executes after the reindex returned having verified it wrote
    N>0 documents, so the collection provably existed and a count of zero
    afterwards is removal rather than absence. One checkpoint is enough here: the
    window is a single exception boundary in shared code, and each case pays a
    full reindex.
    """

    def boom(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise _Boom("gate failed")

    with _isolated_stores(source_candidate) as stores:
        monkeypatch.setattr(persistence_mod, "run_gate", boom)
        with pytest.raises(_Boom):
            _publish(stores)
        monkeypatch.undo()
        pkg = source_candidate.package_uuid
        assert stores.session.get(CorpusReleaseORM, pkg) is None
        assert stores.session.get(RulesPackageORM, pkg) is None
        assert (
            stores.session.execute(
                select(RuleChunkORM).where(RuleChunkORM.rules_package_id == pkg)
            ).first()
            is None
        )
        assert _vector_count(stores) == 0
        # And the compensated state is publishable: rollback restored a clean
        # database rather than one wedged by its own failed attempt.
        retry = _publish(stores)
        assert retry.published and not retry.reused, retry.gate


# ---------------------------------------------------------------------------
# Versioning and release identification
# ---------------------------------------------------------------------------


def test_a_changed_recipe_mints_a_new_release_rather_than_colliding(
    source_candidate: CandidateRelease,
) -> None:
    """``rp_packages`` is unique on (name, version, system) and the corpus name
    is fixed, so a recipe change that moved only the UUID would collide on the
    old version instead of drafting a new release. Both identities move."""
    identity = dict(source_candidate.transform_config["transform_identity"])  # type: ignore[call-overload]
    identity["tool_version"] = "an-explicitly-different-recipe"
    changed = hash_obj(
        {**source_candidate.transform_config, "transform_identity": identity}
    )
    source = source_candidate.authoritative_source_hash
    assert changed != source_candidate.transform_config_hash
    assert derive_package_uuid(source, changed) != source_candidate.package_uuid
    assert derive_release_version(source, changed) != source_candidate.release_version


def test_the_operational_read_path_identifies_this_release_and_no_other(
    published: _Stores,
) -> None:
    """Derived retrieval must name the new release, not fall back to old authority."""
    candidate = published.candidate
    assert published.result is not None and published.result.artifacts is not None
    release = published.result.artifacts.release
    snapshot = load_verified_operational_corpus(
        published.session,
        candidate.package_uuid,
        release_version=candidate.release_version,
        authoritative_source_hash=candidate.authoritative_source_hash,
        transform_config_hash=candidate.transform_config_hash,
        bundle_root_hash=candidate.bundle.bundle_root_hash,
        persisted_corpus_digest=release.identity.persisted_corpus_digest,
        supported_contract_versions=frozenset({CORPUS_CONTRACT_VERSION}),
    )
    assert snapshot.package_uuid == candidate.package_uuid
    assert snapshot.release_version == candidate.release_version
    assert len(snapshot.chunks) == len(candidate.members.chunks)
    # The retired release is not merely absent from this database: it is refused
    # by identity, so a store that still held it could not serve it either.
    with pytest.raises(QuarantinedAuthorityError):
        load_verified_operational_corpus(
            published.session,
            next(iter(QUARANTINED_PACKAGE_UUIDS)),
            release_version=next(iter(QUARANTINED_RELEASE_VERSIONS)),
            authoritative_source_hash=candidate.authoritative_source_hash,
            transform_config_hash=candidate.transform_config_hash,
            bundle_root_hash=candidate.bundle.bundle_root_hash,
            persisted_corpus_digest=release.identity.persisted_corpus_digest,
            supported_contract_versions=frozenset({CORPUS_CONTRACT_VERSION}),
        )
