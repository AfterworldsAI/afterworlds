"""Projection identity and candidate assembly — CRD Issue 5d, Decisions 6 and 8.

Identity derivation is acyclic, and the order matters:

1. the **payload** is assembled from the exact 5c release binding, the accepted
   classification, the declared semantic policy, and the keyed representation —
   semantic keys only, no derived identity anywhere inside it;
2. the **projection UUID** is content-derived from that payload; then
3. stable record, component, and fact IDs are derived from the projection UUID
   plus their committed semantic keys.

Doing it the other way — putting derived IDs into the payload the UUID is
computed from — would be circular, and deriving IDs from list positions would
churn every identity whenever an unrelated sibling was inserted.

**A computed identity is not a publishable projection.** This module can
identify any candidate, including a dishonest one; that is what makes the
identity useful for comparing candidates at all. Before a projection may be
published or activated, every one of these must succeed: the declared policy
binding, the span partition, explicit acceptance, representation validation,
persistence reconstruction, and the later exact completeness gate.
:func:`validate_candidate` covers the first four; the rest belong to the
persistence and gate layers. Nothing here activates anything.
"""

from __future__ import annotations

from dataclasses import dataclass

from afterworlds.ingestion.corpus.hashing import content_id, hash_obj
from afterworlds.ingestion.mechanical.accounting import (
    classification_payload,
    validate_acceptance,
    validate_partition,
    validate_policy_binding,
    validate_reason_codes,
)
from afterworlds.ingestion.mechanical.bound_corpus import BoundCorpusSnapshot
from afterworlds.ingestion.mechanical.canonical import canonical_order
from afterworlds.ingestion.mechanical.models import ClassificationLedger
from afterworlds.ingestion.mechanical.representation import (
    RepresentationDraft,
    fact_key,
    fact_payload,
)
from afterworlds.ingestion.mechanical.validation import validate_representation

__all__ = [
    "IdentifiedProjection",
    "ProjectionCandidate",
    "ReleaseBinding",
    "derive_component_id",
    "derive_fact_id",
    "derive_record_id",
    "identify_projection",
    "projection_payload",
    "projection_uuid",
    "release_binding_payload",
    "representation_payload",
    "validate_candidate",
]


@dataclass(frozen=True)
class ReleaseBinding:
    """The exact published 5c release a projection is built over (#137 contract 1).

    All six values are required. A matching slug, display name, source label, or
    filename is not a binding — these are the reconstructable proof identities
    CRD Issue 5c already publishes, so a projection cannot claim a release it
    was not actually built from.
    """

    package_uuid: str
    release_version: str
    authoritative_source_hash: str
    transform_config_hash: str
    bundle_root_hash: str
    persisted_corpus_digest: str


@dataclass(frozen=True)
class ProjectionCandidate:
    """A built-but-unproven projection: identifiable, not yet publishable."""

    binding: ReleaseBinding
    classification: ClassificationLedger
    representation: RepresentationDraft


def release_binding_payload(binding: ReleaseBinding) -> dict[str, object]:
    """Canonical payload of the 5c release binding."""
    return {
        "package_uuid": binding.package_uuid,
        "release_version": binding.release_version,
        "authoritative_source_hash": binding.authoritative_source_hash,
        "transform_config_hash": binding.transform_config_hash,
        "bundle_root_hash": binding.bundle_root_hash,
        "persisted_corpus_digest": binding.persisted_corpus_digest,
    }


def representation_payload(draft: RepresentationDraft) -> dict[str, object]:
    """Canonical, identity-bearing payload of the keyed representation.

    Every collection here is unordered by meaning, so each is ordered by its
    elements' complete canonical payload rather than by a chosen subset of
    fields — see :mod:`canonical` for why a partial sort key is a defect
    waiting for the next field. Keyed throughout, so nothing derived from the
    identity is inside the thing the identity is computed from.
    """
    return {
        "records": canonical_order(
            {
                "semantic_key": r.semantic_key,
                "kind": r.kind.value,
                "parent_key": r.parent_key,
            }
            for r in draft.records
        ),
        "components": canonical_order(
            {
                "record_key": c.record_key,
                "semantic_key": c.semantic_key,
                "handling": c.handling.value,
                "irreducibility_reason_code": c.irreducibility_reason_code,
                "facts": canonical_order(fact_payload(f) for f in c.facts),
            }
            for c in draft.components
        ),
        "prose_bindings": canonical_order(
            {
                "record_key": b.record_key,
                "component_key": b.component_key,
                "chunk_id": b.chunk_id,
                # The accepted span and its extent are meaning-bearing. A
                # binding moved to a different clause of the same chunk governs
                # different text, so it is a different projection — the same
                # reason the chunk itself has always been in this payload.
                "span_id": b.span_id,
                "chunk_char_start": b.chunk_char_start,
                "chunk_char_end": b.chunk_char_end,
                "irreducibility_reason_code": b.irreducibility_reason_code,
            }
            for b in draft.prose_bindings
        ),
        "relationships": canonical_order(
            {
                "source_record_key": r.source_record_key,
                "target_record_key": r.target_record_key,
                "kind": r.kind.value,
            }
            for r in draft.relationships
        ),
        "references": canonical_order(
            {
                "from_record_key": r.from_record_key,
                "from_component_key": r.from_component_key,
                "source_text": r.source_text,
                "scope_key": r.scope_key,
                "target_record_key": r.target_record_key,
            }
            for r in draft.references
        ),
        "provenance": canonical_order(
            {
                "target_kind": p.target_kind.value,
                "target_key": list(p.target_key),
                "span_id": p.span_id,
                "role": p.role.value,
            }
            for p in draft.provenance
        ),
    }


def projection_payload(candidate: ProjectionCandidate) -> dict[str, object]:
    """The complete meaning-bearing payload a projection identity covers."""
    return {
        "release_binding": release_binding_payload(candidate.binding),
        "classification": classification_payload(candidate.classification),
        "representation": representation_payload(candidate.representation),
    }


def projection_uuid(candidate: ProjectionCandidate) -> str:
    """Content-derived projection identity.

    Any change to the bound release, the accepted classification, the declared
    semantic policy, record assembly, components, facts, prose bindings,
    relationships, references, or provenance mints a different projection.
    """
    return content_id("mechanical_projection", projection_payload(candidate))


def derive_record_id(projection_uuid_: str, record_key: str) -> str:
    """Stable record ID — projection identity plus the committed semantic key."""
    return content_id("mechanical_record", projection_uuid_, record_key)


def derive_component_id(
    projection_uuid_: str, record_key: str, component_key: str
) -> str:
    """Stable component ID."""
    return content_id(
        "mechanical_component", projection_uuid_, record_key, component_key
    )


def derive_fact_id(
    projection_uuid_: str, record_key: str, component_key: str, fact: object
) -> str:
    """Stable fact ID, keyed by the fact's content rather than its position."""
    return content_id(
        "mechanical_fact",
        projection_uuid_,
        record_key,
        component_key,
        fact_key(fact),
    )


@dataclass(frozen=True)
class IdentifiedProjection:
    """A candidate plus the identities derived from it, in that order."""

    candidate: ProjectionCandidate
    projection_uuid: str
    payload_hash: str
    record_ids: dict[str, str]
    component_ids: dict[tuple[str, str], str]
    fact_ids: dict[tuple[str, str, str], str]


def identify_projection(candidate: ProjectionCandidate) -> IdentifiedProjection:
    """Compute the projection identity, then every stable subidentity from it.

    Identification is not proof: the result may still be unpublishable. See
    :func:`validate_candidate` and the persistence/gate layers.
    """
    payload = projection_payload(candidate)
    uuid_ = content_id("mechanical_projection", payload)
    draft = candidate.representation

    record_ids = {
        r.semantic_key: derive_record_id(uuid_, r.semantic_key) for r in draft.records
    }
    component_ids = {
        (c.record_key, c.semantic_key): derive_component_id(
            uuid_, c.record_key, c.semantic_key
        )
        for c in draft.components
    }
    fact_ids = {
        (c.record_key, c.semantic_key, fact_key(f)): derive_fact_id(
            uuid_, c.record_key, c.semantic_key, f
        )
        for c in draft.components
        for f in c.facts
    }

    return IdentifiedProjection(
        candidate=candidate,
        projection_uuid=uuid_,
        payload_hash=hash_obj(payload),
        record_ids=record_ids,
        component_ids=component_ids,
        fact_ids=fact_ids,
    )


def validate_candidate(
    candidate: ProjectionCandidate, corpus: BoundCorpusSnapshot
) -> tuple[str, ...]:
    """Return every violation that blocks this candidate from being published.

    Covers the bound release's agreement with the candidate, the declared
    policy binding, the span partition over each represented leaf, closed
    reason codes, explicit acceptance, and the keyed representation. An empty
    result means the candidate is internally honest — it does *not* mean the
    projection is complete, persisted, reconstructable, or publishable. Those
    are proven by the persistence layer and the exact completeness gate,
    against reconstructed state.

    *corpus* is the single resolved view of the bound 5c release, so every
    release-scoped check reads the same source rather than querying its own.
    """
    findings: list[str] = []
    ledger = candidate.classification
    binding = candidate.binding

    # The candidate, its classification, and the snapshot must all name one
    # release. Two of the three agreeing is not agreement.
    if binding.package_uuid != corpus.package_uuid:
        findings.append(
            f"binding names package {binding.package_uuid}, corpus snapshot is "
            f"{corpus.package_uuid}"
        )
    if binding.release_version != corpus.release_version:
        findings.append(
            f"binding names release {binding.release_version}, corpus snapshot is "
            f"{corpus.release_version}"
        )
    if ledger.package_uuid != binding.package_uuid:
        findings.append(
            f"classification names package {ledger.package_uuid}, binding is "
            f"{binding.package_uuid}"
        )
    if ledger.release_version != binding.release_version:
        findings.append(
            f"classification names release {ledger.release_version}, binding is "
            f"{binding.release_version}"
        )

    findings.extend(validate_policy_binding(ledger))

    leaf_lengths = corpus.leaf_lengths
    claimed_leaves = {s.leaf_id for s in ledger.spans}
    for leaf_id in sorted(claimed_leaves | set(leaf_lengths)):
        if leaf_id not in leaf_lengths:
            findings.append(f"leaf {leaf_id}: classified but not in the bound release")
            continue
        findings.extend(
            validate_partition(leaf_id, leaf_lengths[leaf_id], ledger.spans)
        )

    findings.extend(validate_reason_codes(ledger.spans))
    findings.extend(validate_acceptance(ledger))
    findings.extend(validate_representation(candidate.representation, ledger, corpus))
    return tuple(findings)
