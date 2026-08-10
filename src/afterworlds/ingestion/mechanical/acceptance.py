"""The explicit acceptance action — CRD Issue 5d, contract 2.

One function, because acceptance is one thing: a named reviewer, at a named
time, accepting an exact scope of proposed claims, with the full semantic diff
of what that changed retained as evidence.

    machine proposal  →  human semantic review  →  explicit acceptance

:mod:`proposal` owns the first arrow's output. This module owns the third, and
what it produces — an :class:`~.oracle.AcceptedInputs` — is the committed
artifact a reviewer commits and the build consumes.

Three properties this is built to keep:

* **Silence is not acceptance.** Only span ids named in ``resolved_scope`` are
  accepted. A proposed span the reviewer did not name is dropped, not carried
  forward as "probably fine". The resulting artifact then fails the publication
  gate's population check until every represented leaf is covered, which is the
  honest state rather than an optimistic one.
* **The evidence is the diff, not a digest of it.** The batch retains every
  :class:`~.models.SemanticDiffEntry` in full, and its hash identifies that diff
  rather than substituting for it (see :mod:`accounting`).
* **Evidence never becomes identity.** Reviewer, timestamp, batch grouping, and
  rule wording travel with the ledger and are excluded from
  :func:`~.oracle.oracle_payload`, so re-reviewing an unchanged classification
  cannot remint a projection.

Accepting over a prior artifact is a merge, not a replacement: prior accepted
spans survive unless this scope re-accepts them, and prior batches stay in the
record. That is what lets full-corpus review proceed in reviewable content
batches without any batch quietly discarding an earlier one's work.
"""

from __future__ import annotations

from dataclasses import replace

from afterworlds.ingestion.mechanical.accounting import batch_diff_hash
from afterworlds.ingestion.mechanical.models import (
    AcceptanceBatch,
    AcceptanceRecord,
    ReviewState,
    SemanticDiffEntry,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    AcceptedOracle,
    derive_obligations,
)
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal
from afterworlds.ingestion.mechanical.representation import RepresentationDraft

__all__ = ["AcceptanceError", "accept_proposal"]


class AcceptanceError(ValueError):
    """Raised when an acceptance action cannot be recorded as stated.

    Raised rather than reported: a half-recorded acceptance is worse than none,
    because the artifact would claim review that did not happen.
    """


def _merge_representation(
    prior: RepresentationDraft | None, proposed: RepresentationDraft
) -> RepresentationDraft:
    """Combine a prior accepted representation with a newly accepted one.

    Concatenation, with one guard: a record or component semantic key that
    appears in both must appear *identically*. A batch that redefines an earlier
    batch's record under the same key is not a merge, it is a silent
    replacement of authority somebody already accepted, and the reviewer of the
    second batch never saw the first.

    Every other collection concatenates freely — a duplicated fact, relationship,
    reference, or provenance edge is already a violation :mod:`validation`
    reports by name, and re-checking it here would be a second opinion about
    what "the same element" means.
    """
    if prior is None:
        return proposed

    for label, prior_items, new_items, key in (
        (
            "record",
            prior.records,
            proposed.records,
            lambda r: (r.semantic_key,),
        ),
        (
            "component",
            prior.components,
            proposed.components,
            lambda c: (c.record_key, c.semantic_key),
        ),
    ):
        existing = {key(item): item for item in prior_items}
        for item in new_items:
            clash = existing.get(key(item))
            if clash is not None and clash != item:
                raise AcceptanceError(
                    f"{label} {list(key(item))}: this acceptance redefines a "
                    "record already accepted under the same semantic key"
                )

    return RepresentationDraft(
        records=prior.records + proposed.records,
        components=prior.components + proposed.components,
        prose_bindings=prior.prose_bindings + proposed.prose_bindings,
        relationships=prior.relationships + proposed.relationships,
        references=prior.references + proposed.references,
        provenance=prior.provenance + proposed.provenance,
    )


def accept_proposal(
    proposal: MechanicalProposal,
    *,
    batch_id: str,
    rule: str,
    resolved_scope: tuple[str, ...],
    reviewer: str,
    accepted_at: str,
    prior: AcceptedInputs | None = None,
) -> AcceptedInputs:
    """Record one explicit acceptance of *resolved_scope* from *proposal*.

    ``rule`` is how the reviewer selected the scope. It is retained as evidence
    and is **never re-run**: re-evaluating a selector against changed inputs
    would resolve to a different set than the reviewer actually saw, which is
    why ``resolved_scope`` carries the exact span ids alongside it.
    """
    if not resolved_scope:
        raise AcceptanceError("an acceptance action must name at least one span")
    if not reviewer.strip():
        raise AcceptanceError("an acceptance action must name its reviewer")
    if not rule.strip():
        raise AcceptanceError("an acceptance action must record its selection rule")

    proposed_by_id = {p.span.span_id: p.span for p in proposal.proposed_spans}
    if duplicates := sorted({s for s in resolved_scope if resolved_scope.count(s) > 1}):
        raise AcceptanceError(f"resolved scope repeats spans {duplicates}")
    if unknown := sorted(set(resolved_scope) - proposed_by_id.keys()):
        raise AcceptanceError(
            f"resolved scope names spans this proposal did not propose: {unknown}"
        )

    if prior is not None and prior.oracle.binding != proposal.binding:
        raise AcceptanceError(
            "this proposal binds a different 5c release than the prior accepted "
            "authority it would extend"
        )
    if prior is not None and (
        prior.oracle.policy_version,
        prior.oracle.policy_hash,
    ) != (proposal.policy_version, proposal.policy_hash):
        raise AcceptanceError(
            "this proposal declares a different semantic policy than the prior "
            "accepted authority it would extend"
        )

    prior_spans = {s.span_id: s for s in (prior.oracle.spans if prior else ())}
    if batch_id in {b.batch_id for b in (prior.batches if prior else ())}:
        raise AcceptanceError(f"batch {batch_id!r} is already recorded")

    accepted_spans = tuple(
        replace(proposed_by_id[span_id], review_state=ReviewState.ACCEPTED)
        for span_id in resolved_scope
    )
    diff = tuple(
        SemanticDiffEntry(
            span_id=span.span_id,
            prior_disposition=(
                prior_spans[span.span_id].disposition
                if span.span_id in prior_spans
                else None
            ),
            prior_reason_code=(
                prior_spans[span.span_id].non_mechanical_reason_code
                if span.span_id in prior_spans
                else None
            ),
            accepted_disposition=span.disposition,
            accepted_reason_code=span.non_mechanical_reason_code,
        )
        for span in accepted_spans
    )
    batch = AcceptanceBatch(
        batch_id=batch_id,
        rule=rule,
        resolved_scope=tuple(resolved_scope),
        diff=diff,
        semantic_diff_hash="",
    )
    batch = replace(batch, semantic_diff_hash=batch_diff_hash(batch))

    re_accepted = set(resolved_scope)
    spans = (
        tuple(
            s
            for s in (prior.oracle.spans if prior else ())
            if s.span_id not in re_accepted
        )
        + accepted_spans
    )
    acceptances = tuple(
        a for a in (prior.acceptances if prior else ()) if a.span_id not in re_accepted
    ) + tuple(
        AcceptanceRecord(
            span_id=span_id,
            batch_id=batch_id,
            reviewer=reviewer,
            accepted_at=accepted_at,
        )
        for span_id in resolved_scope
    )

    representation = _merge_representation(
        prior.oracle.representation if prior else None,
        proposal.proposed_representation,
    )
    return AcceptedInputs(
        oracle=AcceptedOracle(
            binding=proposal.binding,
            policy_version=proposal.policy_version,
            policy_hash=proposal.policy_hash,
            spans=_ordered(spans),
            representation=representation,
            obligations=derive_obligations(representation),
        ),
        batches=tuple(prior.batches if prior else ()) + (batch,),
        acceptances=acceptances,
    )


def _ordered(spans: tuple[SemanticSpan, ...]) -> tuple[SemanticSpan, ...]:
    """Spans in a deterministic order, so two equal acceptances write one file.

    Ordered by content — leaf then offsets — rather than by acceptance sequence,
    because the order review happened in is evidence, not part of the accepted
    result, and letting it into the file would make the artifact depend on which
    batch ran first.
    """
    return tuple(sorted(spans, key=lambda s: (s.leaf_id, s.char_start, s.char_end)))
