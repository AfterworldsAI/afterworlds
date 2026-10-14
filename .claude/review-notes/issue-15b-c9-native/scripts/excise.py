"""Remove a group of accepted batches' contribution from accepted inputs.

REVIEW MATERIAL for the CRD Issue 15c native preview; not a supersession
operation and not shipped. It generalizes the Advisor-reviewed G1 rule
(``issue-2b-g1-candidate/scripts/excise.py``) from one batch to a group that is
replaced together:

* batch-keyed evidence leaves by ``batch_id``;
* a span leaves when a group batch's ``resolved_scope`` names it;
* a representation element leaves only when a group proposal (replayed and
  identity-matched) states it **and** every provenance claim on it is one a
  group proposal states, so an element another batch also claimed stays;
* a provenance claim leaves when a group proposal states it.

Claims, not span scope, decide removal: Animals components bind
Monsters-scoped stat-block spans contextually (``reports/placement.json``),
so G1's scope test would keep them although only the Animals proposal claims
them. Excising Animals and Monsters jointly is not an option: re-accepting
Monsters first strands the accepted resolutions that name Animals records.
For a batch whose claims all lie in its own scope the two rules agree;
``identity_control.py`` proves the result per batch.
Reference resolutions, lifts and policy transitions are kept whole; native
acceptance re-checks them against the merged result.
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
    prior: AcceptedInputs, group: dict[str, RepresentationDraft]
) -> tuple[AcceptedInputs, dict[str, dict[str, int]]]:
    """*prior* without the batches in *group* (batch id -> its proposal's
    representation), and per-collection removed/kept counts."""
    ids = set(group)
    batches = [b for b in prior.batches if b.batch_id in ids]
    assert {b.batch_id for b in batches} == ids, ids
    scope = {s for b in batches for s in b.resolved_scope}
    units = {a.unit_id for a in prior.review_unit_acceptances if a.batch_id in ids}
    rep = prior.oracle.representation

    stated_claims = {_claim_key(c) for r in group.values() for c in r.provenance}
    claims_of: dict[tuple[str, tuple[str, ...]], set[tuple[str, ...]]] = defaultdict(set)
    for c in rep.provenance:
        claims_of[(c.target_kind.value, tuple(c.target_key))].add(_claim_key(c))

    report: dict[str, dict[str, int]] = {}
    kept: dict[str, tuple[Any, ...]] = {}
    for field, kind, key_of in _KEYED:
        stated = {key_of(x) for r in group.values() for x in getattr(r, field)}
        out, removed, shared = [], 0, 0
        for x in getattr(rep, field):
            k = key_of(x)
            if k in stated:
                if not claims_of.get((kind.value, k), set()) - stated_claims:
                    removed += 1
                    continue
                shared += 1
            out.append(x)
        kept[field] = tuple(out)
        report[field] = {"removed": removed, "kept_shared": shared}

    claims, removed = [], 0
    for c in rep.provenance:
        if _claim_key(c) in stated_claims:
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
            batches=tuple(b for b in prior.batches if b.batch_id not in ids),
            acceptances=tuple(a for a in prior.acceptances if a.batch_id not in ids),
            review_unit_acceptances=tuple(
                a for a in prior.review_unit_acceptances if a.batch_id not in ids
            ),
            schema_anchors=tuple(a for a in prior.schema_anchors if a.batch_id not in ids),
        ),
        report,
    )
