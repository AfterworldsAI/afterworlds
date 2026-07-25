"""Acyclic reproducible production build — CRD Issue 5c, Component K (a0–g).

Drives the fixed acyclic order that produces every proof identity, so no
artifact is ever covered by a hash it contains and the evidence report is never
generated before the (actual, persisted) state it reports on exists:

    a0  freeze the reconciliation policy (committed input, covered by B)
    a1  derive and hash the frozen source ledger
    a2  generate the canonical corpus members from the frozen ledger
    a3  apply only the frozen policy → reconciliation member
    b   compute the bundle-root hash                                  } build_candidate
    ------------------------------------------------------------------
    c   persist — see persistence.finalize_release
    d   compute the persisted-corpus digest from the actual persisted
        (and reconstructed) state
    e   generate the evidence report (post-persistence)
    f   hash the completed evidence report
    g   record the five top-level hashes in the release record and    } finalize_release
        run the final publication gate                                (persistence.py)

``build_candidate`` performs only steps a0–b: everything that is a pure,
deterministic function of the committed PDF and frozen policy, and nothing
else. Its result, :class:`CandidateRelease`, structurally cannot claim that
persistence occurred — it has no evidence report, no persisted-corpus digest,
and no external release/publication record, because steps c–g require an
actual database and cannot be produced, or faked via a boolean flag, in
memory. :func:`afterworlds.ingestion.corpus.persistence.finalize_release`
performs steps c–g against a live session and returns the completed
:class:`ReleaseArtifacts`.

A clean checkout regenerates a0–g byte-for-byte from committed inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from afterworlds.ingestion.corpus.bundle import (
    build_bundle,
    derive_package_uuid,
    derive_release_version,
    reconciliation_hash,
    transform_config_hash,
    transform_config_payload,
)
from afterworlds.ingestion.corpus.concordance import CanaryResult, ConcordanceResult
from afterworlds.ingestion.corpus.ledger import build_ledger, ledger_hash
from afterworlds.ingestion.corpus.models import (
    CanonicalBundle,
    CorpusBundleMembers,
    ReconciliationMember,
    ReconciliationPolicy,
    ReleaseRecord,
    SourceLedger,
)
from afterworlds.ingestion.corpus.pdf_source import (
    PDF_SHA256,
    ExtractedPage,
    extract_pages,
    extraction_config,
)
from afterworlds.ingestion.corpus.policy import FROZEN_POLICY, policy_hash
from afterworlds.ingestion.corpus.reconcile import reconcile
from afterworlds.ingestion.corpus.report import EvidenceReport
from afterworlds.ingestion.corpus.transform import build_corpus
from afterworlds.models.retrieval import rules_corpus_vector_identity
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig


@dataclass(frozen=True)
class CandidateRelease:
    """Everything derivable before persistence exists (Component K steps a0–b).

    This type cannot claim persistence occurred: it carries no evidence report,
    no persisted-corpus digest, and no external release/publication record. Those
    require an actual persisted (and reconstructed) database state and are the
    sole responsibility of :func:`persistence.finalize_release` (steps c–g).
    """

    pages: list[ExtractedPage]
    ledger: SourceLedger
    members: CorpusBundleMembers
    reconciliation: ReconciliationMember
    policy: ReconciliationPolicy
    bundle: CanonicalBundle
    package_uuid: str
    release_version: str
    authoritative_source_hash: str
    transform_config_hash: str
    transform_config: dict[str, object]
    ledger_hash: str
    policy_hash: str
    reconciliation_hash: str


def build_candidate(
    pdf_path: Path,
    *,
    policy: ReconciliationPolicy = FROZEN_POLICY,
    retrieval_config: RetrievalMemoryConfig,
) -> CandidateRelease:
    """Execute steps a0–b: the pre-persistence candidate build.

    Deterministic and side-effect-free; touches no database. The returned
    ``package_uuid``/``release_version`` are content-derived from the committed
    PDF and frozen transform/policy inputs (Owner Decision 1) and are therefore
    already stable at this stage — but nothing about the state described here is
    yet proven persisted or runtime-visible.

    ``retrieval_config`` is resolved by the caller *before* this build so its
    identity-bearing rules-corpus vector configuration (the embedding model +
    logical schema/ID/metadata contract) is bound into the transform config,
    hence the package UUID and release version (PR #134 P1). A model change
    therefore mints a new immutable release rather than colliding on reuse.
    """
    # a0 — freeze policy + resolve the vector identity (both committed inputs).
    p_hash = policy_hash(policy)
    ex_cfg = extraction_config()
    vector_identity = rules_corpus_vector_identity(retrieval_config.embedding_model_id)
    tconfig = transform_config_payload(ex_cfg, policy, vector_identity)
    thash = transform_config_hash(ex_cfg, policy, vector_identity)

    # a1 — derive + hash the frozen source ledger.
    pages = extract_pages(pdf_path)
    ledger = build_ledger(pages)
    l_hash = ledger_hash(ledger)

    package_uuid = derive_package_uuid(PDF_SHA256, thash)
    release_version = derive_release_version(PDF_SHA256, thash)

    # a2 — generate canonical corpus members from the frozen ledger.
    members = build_corpus(ledger)

    # a3 — reconciliation by applying only the frozen policy.
    recon = reconcile(ledger, members, policy)
    r_hash = reconciliation_hash(recon)

    # b — bundle-root hash.
    bundle = build_bundle(ledger, members, recon)

    return CandidateRelease(
        pages=pages,
        ledger=ledger,
        members=members,
        reconciliation=recon,
        policy=policy,
        bundle=bundle,
        package_uuid=package_uuid,
        release_version=release_version,
        authoritative_source_hash=PDF_SHA256,
        transform_config_hash=thash,
        transform_config=tconfig,
        ledger_hash=l_hash,
        policy_hash=p_hash,
        reconciliation_hash=r_hash,
    )


@dataclass(frozen=True)
class ReleaseArtifacts:
    """The completed, post-persistence release (Component K steps a0–g).

    Produced only by :func:`persistence.finalize_release` from a candidate plus
    the actual reconstructed persisted state — never assembled directly from a
    :class:`CandidateRelease` alone.
    """

    pages: list[ExtractedPage]
    ledger: SourceLedger
    members: CorpusBundleMembers
    reconciliation: ReconciliationMember
    policy: ReconciliationPolicy
    bundle: CanonicalBundle
    report: EvidenceReport
    release: ReleaseRecord
    concordance: ConcordanceResult
    canaries: tuple[CanaryResult, ...]
    # The actual verified vector logical state read back from the real Chroma
    # collection at publish/reuse time (Component K step c + digest, PR #134
    # defect family 1). A plain serializable payload so the gate can recompute
    # the persisted-corpus digest without a Chroma dependency of its own.
    vector_state: dict[str, object]
