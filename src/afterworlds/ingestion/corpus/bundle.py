"""Canonical bundle, persisted-corpus digest, transform identity — Issue 5c.

Components K (bundle root), A (five top-level identities and the persisted-corpus
digest), and B (transform source/configuration hash covering the frozen policy).

The bundle-root hash covers the frozen ledger, the canonical corpus members, the
reconciliation member, and the ordered bundle-member manifest — and excludes
itself and anything containing it (the evidence report). Proof identities are
produced in the fixed acyclic order enforced by :mod:`.pipeline`.
"""

from __future__ import annotations

from afterworlds.ingestion.corpus.hashing import content_id, hash_obj
from afterworlds.ingestion.corpus.ledger import ledger_hash, ledger_payload
from afterworlds.ingestion.corpus.models import (
    BundleMember,
    CanonicalBundle,
    CorpusBundleMembers,
    PersistedSource,
    ReconciliationMember,
    ReconciliationPolicy,
    SourceLedger,
)
from afterworlds.ingestion.corpus.policy import policy_hash, policy_payload
from afterworlds.ingestion.corpus.report import EVIDENCE_REPORT_SCHEMA_VERSION
from afterworlds.ingestion.corpus.table_inventory import committed_inventory_hash
from afterworlds.ingestion.corpus.transform_identity import transform_identity

RELEASE_VERSION_PREFIX = "5.2.1-corpus"


# ---------------------------------------------------------------------------
# Transform source/configuration hash (Component B) — covers the frozen policy.
# ---------------------------------------------------------------------------


def transform_config_payload(
    extraction_config: dict[str, object],
    policy: ReconciliationPolicy,
    vector_identity: dict[str, object],
) -> dict[str, object]:
    """The committed transform inputs (Component B).

    The extractor config and frozen policy alone do not capture a change to the
    first-party transform *code* (segmentation, chunk generation, canonical
    identity derivation). ``transform_identity`` binds a source manifest over the
    audited first-party modules, so any covered code change moves this payload's
    hash — hence the package UUID and release version (PR #134 P1).

    ``vector_identity`` binds the identity-bearing rules-corpus vector
    configuration (embedding model + logical schema/ID/metadata contract, see
    :func:`afterworlds.models.retrieval.rules_corpus_vector_identity`) so a change
    to the embedding model or the vector logical schema likewise mints a new
    immutable release instead of colliding with the predecessor on the reuse
    path (PR #134 P1). It carries no operational retrieval settings.

    ``expected_table_inventory_hash`` binds the committed independent expected-
    table oracle (``table_inventory.srd_table_inventory.json``): the expected set
    of logical tables is a candidate-affecting configuration, so changing it
    (regenerating the inventory after a reviewed table-reconstruction change)
    mints a new immutable release (PR #134 R15 F4).

    ``evidence_report_schema_version`` binds the canonical evidence-report schema
    version (Component H). The evidence-report hash is a post-persistence proof
    identity, so a *schema* change (e.g. the R16 ``reproduction_environment`` →
    ``reproduction_target`` shape change) must mint a new immutable release rather
    than being validated-and-reused under a predecessor's identity — otherwise
    reuse loads the obsolete-shape stored report and accepts it (PR #134 R17). An
    explicit version (not a byte-level hash of ``report.py``) is bound so only an
    intentional schema change remints, never a comment/logging edit.
    """
    return {
        "extraction_config": extraction_config,
        "reconciliation_policy": policy_payload(policy),
        "transform_identity": transform_identity(),
        "rules_corpus_vector_identity": vector_identity,
        "expected_table_inventory_hash": committed_inventory_hash(),
        "evidence_report_schema_version": EVIDENCE_REPORT_SCHEMA_VERSION,
    }


def transform_config_hash(
    extraction_config: dict[str, object],
    policy: ReconciliationPolicy,
    vector_identity: dict[str, object],
) -> str:
    return hash_obj(
        transform_config_payload(extraction_config, policy, vector_identity)
    )


# ---------------------------------------------------------------------------
# Canonical member payloads (Component K)
# ---------------------------------------------------------------------------


def corpus_members_payload(members: CorpusBundleMembers) -> dict[str, object]:
    return {
        "chunks": [
            {
                "chunk_id": c.chunk_id,
                "subsystem": c.subsystem,
                "content": c.content,
                "printed_page": c.printed_page,
                "section_label": c.section_label,
                "container_path": list(c.container_path),
                "source_leaf_ids": list(c.source_leaf_ids),
            }
            for c in members.chunks
        ],
        "derivative_notes": [
            {
                "note_id": n.note_id,
                "kind": n.kind,
                "content": n.content,
                "about_leaf_ids": list(n.about_leaf_ids),
            }
            for n in members.derivative_notes
        ],
    }


def reconciliation_payload(recon: ReconciliationMember) -> dict[str, object]:
    return {
        "policy_version": recon.policy_version,
        "policy_hash": recon.policy_hash,
        "dispositions": [
            {
                "leaf_id": d.leaf_id,
                "disposition": d.disposition.value,
                "exclusion_reason_code": d.exclusion_reason_code,
            }
            for d in recon.dispositions
        ],
        "projections": [
            {
                "projection_id": p.projection_id,
                "leaf_id": p.leaf_id,
                "chunk_id": p.chunk_id,
                "role": p.role,
                "cover_start": p.cover_start,
                "cover_end": p.cover_end,
            }
            for p in recon.projections
        ],
        "findings": {
            "gaps": list(recon.findings.gaps),
            "overlaps": list(recon.findings.overlaps),
            "orphans": list(recon.findings.orphans),
            "duplications": list(recon.findings.duplications),
            "unresolved": list(recon.findings.unresolved),
        },
        "accounting": {
            "inventoried_leaves": recon.inventoried_leaves,
            "represented_leaves": recon.represented_leaves,
            "excluded_leaves": recon.excluded_leaves,
            "unresolved_leaves": recon.unresolved_leaves,
        },
    }


def reconciliation_hash(recon: ReconciliationMember) -> str:
    return hash_obj(reconciliation_payload(recon))


def build_bundle(
    ledger: SourceLedger,
    members: CorpusBundleMembers,
    recon: ReconciliationMember,
) -> CanonicalBundle:
    """Compute the ordered member manifest and the bundle-root hash (K step b).

    The root covers the members and the manifest; it never covers itself or the
    evidence report (which contains it).
    """
    manifest = (
        BundleMember(
            name="frozen_source_ledger",
            kind="ledger",
            member_hash=ledger_hash(ledger),
        ),
        BundleMember(
            name="canonical_corpus_members",
            kind="corpus",
            member_hash=hash_obj(corpus_members_payload(members)),
        ),
        BundleMember(
            name="reconciliation_member",
            kind="reconciliation",
            member_hash=reconciliation_hash(recon),
        ),
    )
    root = hash_obj(
        {
            "members": [
                {"name": m.name, "kind": m.kind, "member_hash": m.member_hash}
                for m in manifest
            ],
            "ledger": ledger_payload(ledger),
            "corpus": corpus_members_payload(members),
            "reconciliation": reconciliation_payload(recon),
        }
    )
    return CanonicalBundle(member_manifest=manifest, bundle_root_hash=root)


# ---------------------------------------------------------------------------
# Package identity (Owner Decision 1) — new yet reproducible
# ---------------------------------------------------------------------------


def derive_package_uuid(source_hash: str, transform_hash: str) -> str:
    """New-yet-deterministic package UUID from source + transform identities."""
    return content_id("package", source_hash, transform_hash)


def derive_release_version(source_hash: str, transform_hash: str) -> str:
    """Deterministic release version derived from **both** the authoritative
    source identity and the transform identity — consistent with
    :func:`derive_package_uuid`.

    ``rp_packages`` uniquely constrains ``(name, version, system)`` and the
    corpus always uses the fixed name ``SRD 5.2.1 Corpus``; if the version were
    derived from the transform hash alone (PR #134 defect family 3), a changed
    authoritative source with unchanged extraction/policy config would mint a
    *new* ``package_uuid`` but collide on the *old* version, hitting the
    uniqueness constraint instead of creating the expected new draft release.
    Binding both identities into the version guarantees: identical inputs →
    identical UUID *and* version (idempotent); a change to *either* source or
    transform → both a new UUID *and* a new version, never mutating the
    published predecessor.
    """
    # A short content-derived tag over both identities. Deterministic and stable
    # across clean rebuilds; the same reproducibility discipline as the UUID.
    version_tag = content_id("release_version", source_hash, transform_hash)[:12]
    return f"{RELEASE_VERSION_PREFIX}.{version_tag}"


# ---------------------------------------------------------------------------
# Persisted-corpus digest (Component A step d)
# ---------------------------------------------------------------------------


def _chunk_provenance_payload(members: CorpusBundleMembers) -> list[dict[str, object]]:
    """The runtime-visible RuleChunk provenance/source-membership (Component G).

    Bound into the digest so that tampering any persisted citation field
    (``source_document``, ``source_locator_type``, ``source_locator_value``) or
    reassigning a chunk to a different ``source_id`` (PR #134 defect family 3)
    changes the digest and fails verification/gating. ``members`` here are the
    *reconstructed* members, whose provenance was read back from the actual
    ``rp_chunks`` rows.
    """
    return [
        {
            "chunk_id": c.chunk_id,
            "source_id": c.source_id,
            "source_document": c.source_document,
            "source_locator_type": c.source_locator_type,
            "source_locator_value": c.source_locator_value,
        }
        for c in members.chunks
    ]


def source_membership_payload(
    sources: tuple[PersistedSource, ...],
) -> list[dict[str, object]]:
    """The complete canonically-ordered logical ``RuleSource`` set (Component G).

    Bound into the digest so an extra, missing, altered (name/category/
    precedence), disabled, or reassigned source fails verification (PR #134
    defect family 3). Operational fields (``created_at``) are excluded — the
    proof binds logical source identity/authority/enablement, not row timing.
    """
    return [
        {
            "source_id": s.source_id,
            "rules_package_id": s.rules_package_id,
            "name": s.name,
            "category": s.category,
            "precedence_rank": s.precedence_rank,
            "is_enabled": s.is_enabled,
        }
        for s in sources
    ]


def persisted_corpus_payload(
    package_uuid: str,
    release_version: str,
    ledger: SourceLedger,
    members: CorpusBundleMembers,
    recon: ReconciliationMember,
    policy: ReconciliationPolicy,
    sources: tuple[PersistedSource, ...],
    vector_state: dict[str, object],
) -> dict[str, object]:
    """The complete authoritative logical persisted state (Component A).

    Binds package/release identity, ledger leaf/container relationships, final
    dispositions and reasons, the policy reference, projection identities/roles/
    subspans, findings, the authoritative RuleChunks (including their
    runtime-visible provenance), and the **actual verified vector logical
    state** (``vector_state``). Excludes raw DB files, embedding bytes, the
    evidence report, and the external release record.

    ``vector_state`` is the canonical logical projection *read back from the
    real Chroma collection* (document IDs, content, required metadata, count,
    and embedding-model id) — never an intended payload synthesized from SQL
    alone (PR #134 defect family 1). Computing the digest over the actual
    read-back is what makes a missing/empty/stale/tampered vector collection
    change the digest and fail publication or reuse.
    """
    return {
        "package_uuid": package_uuid,
        "release_version": release_version,
        "ledger": ledger_payload(ledger),
        "reconciliation": reconciliation_payload(recon),
        "policy_reference": {
            "policy_version": policy.policy_version,
            "policy_hash": policy_hash(policy),
        },
        "chunks": corpus_members_payload(members)["chunks"],
        "chunk_provenance": _chunk_provenance_payload(members),
        "source_membership": source_membership_payload(sources),
        "vector_logical_state": vector_state,
    }


def persisted_corpus_digest(
    package_uuid: str,
    release_version: str,
    ledger: SourceLedger,
    members: CorpusBundleMembers,
    recon: ReconciliationMember,
    policy: ReconciliationPolicy,
    sources: tuple[PersistedSource, ...],
    vector_state: dict[str, object],
) -> str:
    return hash_obj(
        persisted_corpus_payload(
            package_uuid,
            release_version,
            ledger,
            members,
            recon,
            policy,
            sources,
            vector_state,
        )
    )
