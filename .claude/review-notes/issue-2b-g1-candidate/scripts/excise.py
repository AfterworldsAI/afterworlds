"""Remove one accepted batch's contribution from accepted inputs.

REVIEW MATERIAL for the CRD Issue 2b G1 candidate. Not a supersession
operation and not shipped: it produces an in-memory *prior* that native
``accept_proposal`` then extends with the replacement proposal, so every check
the build runs on accepted authority still runs on the result.

Rule (Advisor-reviewed): batch-keyed evidence leaves by ``batch_id``; a span
leaves when the batch's ``resolved_scope`` names it; a representation element
leaves only when the batch's own (regenerated, identity-matched) proposal
states it **and** none of its provenance spans lies outside that scope. An
element another batch also stated keeps a provenance span from that batch's
scope and stays. Reference resolutions, lifts and policy transitions are kept
whole; native acceptance re-checks the resolutions against the merged result.
"""

from __future__ import annotations

import dataclasses
from collections import defaultdict
from typing import Any

from afterworlds.ingestion.mechanical.oracle import AcceptedInputs, derive_obligations
from afterworlds.ingestion.mechanical.representation import (
    ProvenanceTargetKind,
    RepresentationDraft,
    component_target_key,
    prose_binding_target_key,
    record_target_key,
    reference_target_key,
    relationship_target_key,
)

_KEYED = (
    ("records", ProvenanceTargetKind.RECORD, record_target_key),
    ("components", ProvenanceTargetKind.COMPONENT, component_target_key),
    ("prose_bindings", ProvenanceTargetKind.PROSE_BINDING, prose_binding_target_key),
    ("relationships", ProvenanceTargetKind.RELATIONSHIP, relationship_target_key),
    ("references", ProvenanceTargetKind.REFERENCE, reference_target_key),
)


def _claim_key(claim: Any) -> tuple[str, ...]:
    return (claim.target_kind.value, *claim.target_key, claim.span_id, claim.role.value)


def excise(
    prior: AcceptedInputs, batch_id: str, batch_representation: RepresentationDraft
) -> tuple[AcceptedInputs, dict[str, dict[str, int]]]:
    """*prior* without *batch_id*, and per-collection removed/kept counts."""
    (batch,) = [b for b in prior.batches if b.batch_id == batch_id]
    scope = set(batch.resolved_scope)
    units = {
        a.unit_id for a in prior.review_unit_acceptances if a.batch_id == batch_id
    }
    rep = prior.oracle.representation

    spans_of: dict[tuple[str, tuple[str, ...]], set[str]] = defaultdict(set)
    for c in rep.provenance:
        spans_of[(c.target_kind.value, tuple(c.target_key))].add(c.span_id)

    report: dict[str, dict[str, int]] = {}
    kept: dict[str, tuple[Any, ...]] = {}
    for field, kind, key_of in _KEYED:
        stated = {key_of(x) for x in getattr(batch_representation, field)}
        out, removed, shared = [], 0, 0
        for x in getattr(rep, field):
            k = key_of(x)
            if k in stated:
                outside = spans_of.get((kind.value, k), set()) - scope
                if not outside:
                    removed += 1
                    continue
                shared += 1
            out.append(x)
        kept[field] = tuple(out)
        report[field] = {"removed": removed, "kept_shared": shared}

    stated_claims = {_claim_key(c) for c in batch_representation.provenance}
    claims, removed = [], 0
    for c in rep.provenance:
        if _claim_key(c) in stated_claims and c.span_id in scope:
            removed += 1
            continue
        claims.append(c)
    report["provenance"] = {"removed": removed, "kept_shared": 0}

    representation = RepresentationDraft(provenance=tuple(claims), **kept)
    oracle = dataclasses.replace(
        prior.oracle,
        spans=tuple(s for s in prior.oracle.spans if s.span_id not in scope),
        representation=representation,
        obligations=derive_obligations(representation),
        review_units=tuple(u for u in prior.oracle.review_units if u.unit_id not in units),
    )
    report["spans"] = {"removed": len(scope), "kept_shared": 0}
    report["review_units"] = {"removed": len(units), "kept_shared": 0}
    return (
        dataclasses.replace(
            prior,
            oracle=oracle,
            batches=tuple(b for b in prior.batches if b.batch_id != batch_id),
            acceptances=tuple(a for a in prior.acceptances if a.batch_id != batch_id),
            review_unit_acceptances=tuple(
                a for a in prior.review_unit_acceptances if a.batch_id != batch_id
            ),
            schema_anchors=tuple(
                a for a in prior.schema_anchors if a.batch_id != batch_id
            ),
        ),
        report,
    )
